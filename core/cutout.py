#!/usr/bin/env python3
"""Recorte de fondo blanco por conectividad — el que NO se come lo blanco del sujeto.

El camino obvio es un modelo de saliencia (`rembg`, isnet-general-use): decide
"qué es el sujeto" mirando la imagen entera y, con arte cartoon sobre fondo
blanco, confunde un guardapolvo blanco con el fondo y lo deja transparente.

Acá el criterio no es semántico sino topológico, que es el que corresponde:
**fondo = lo blanco que se toca con el borde del lienzo**. Una camisa blanca está
rodeada por la línea del dibujo, no se conecta con el borde, y por lo tanto JAMÁS
se recorta. No hay modelo, no hay umbral mágico sobre "qué es un personaje": hay
componentes conexas.

El borde queda con alpha fraccional por matting (`alpha = d / d_solido`) y con el
blanco descontaminado del color, así no queda el halo claro típico del recorte
por umbral.
"""

from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

# Un píxel es "blanco de fondo" si ningún canal baja de 255 - WHITE_TOLERANCE.
# Los modelos devuelven el fondo en 253-255, y el antialias del dibujo arranca
# bien por debajo: 14 separa los dos sin tocar el gris más claro de un sujeto.
WHITE_TOLERANCE = 14

# Ancho en píxeles del anillo de antialias alrededor del fondo. Todo lo que esté
# más adentro es sujeto opaco aunque sea casi blanco, y además es de donde se
# saca el color de referencia para calcular la opacidad del anillo.
FEATHER = 3

# Sólo con `punch_holes`: una isla más chica que esto es ruido de compresión
# dentro de una zona clara, no un hueco que el dibujo quiso dejar.
MIN_HOLE_AREA = 256


def white_distance(rgb: np.ndarray) -> np.ndarray:
    """Cuánto se aleja cada píxel del blanco puro, por el canal que más se aleja.

    Usa el mínimo de los canales y no la luminancia para que un amarillo saturado
    (255, 255, 0) cuente como color pleno y no como "casi blanco"."""
    return 255 - rgb.min(axis=2).astype(np.int16)


def background_mask(distance: np.ndarray, punch_holes: bool = False) -> np.ndarray:
    """Lo blanco conectado con el borde del lienzo. El resto es dibujo.

    Los primeros planos apoyan los hombros contra el marco: ahí el borde tiene
    píxeles de sujeto, y por eso las semillas se toman sólo de los píxeles de
    borde que además son blancos.

    `punch_holes` suma también las islas blancas que el dibujo encierra. Es la
    excepción, no la regla: medido sobre 219 originales, de 1183 islas encerradas
    la enorme mayoría es dibujo —camisas, ojos, papeles— así que el default
    correcto es tratarlas como sujeto. El color no las distingue (un guardapolvo
    blanco puro mide igual que el fondo), de modo que la excepción se declara a
    mano, por clave, en el `project.json`."""
    whiteish = distance <= WHITE_TOLERANCE
    labels, count = ndimage.label(whiteish)
    if count == 0:
        return np.zeros_like(whiteish)

    border = np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]])
    seeds = np.unique(border[border > 0])
    if seeds.size == 0:
        # Un dibujo que llena el lienzo de lado a lado no tiene fondo que sacar.
        return np.zeros_like(whiteish)

    background = np.isin(labels, seeds)

    if not punch_holes:
        return background

    interior = whiteish & ~background
    interior_labels, interior_count = ndimage.label(interior)
    if interior_count:
        areas = ndimage.sum_labels(
            interior, interior_labels, index=np.arange(1, interior_count + 1)
        )
        big = np.flatnonzero(areas >= MIN_HOLE_AREA) + 1
        background |= np.isin(interior_labels, big)

    return background


def alpha_from_background(distance: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Opacidad 0 en el fondo, 1 en el dibujo y rampa en el anillo de antialias.

    En el anillo el píxel observado es una mezcla del color del dibujo con el
    blanco del fondo, así que su opacidad real es `d / d_del_color_sin_mezclar`.
    Ese color de referencia se toma del píxel **de adentro** más cercano, no del
    más oscuro: quien define si un píxel ya es color pleno es la geometría (estar
    lejos del fondo), no su tono. Con un umbral de tono, un filo que es 80% blanco
    da lo bastante oscuro como para pasar por pleno y se queda opaco — que es
    justo el halo claro que se quiere evitar."""
    alpha = np.ones(distance.shape, dtype=np.float32)
    alpha[background] = 0.0

    outside = ndimage.binary_dilation(background, iterations=FEATHER)
    ring = outside & ~background
    inside = ~outside
    if not ring.any() or not inside.any():
        # Un dibujo tan fino que es todo filo: mejor entero que comido.
        return alpha

    _, nearest = ndimage.distance_transform_edt(~inside, return_indices=True)
    reference = distance[nearest[0], nearest[1]].astype(np.float32)
    alpha[ring] = np.clip(distance[ring] / np.maximum(reference[ring], 1.0), 0.0, 1.0)
    return alpha


def undo_white_matte(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Le saca al borde el blanco del fondo que tiene mezclado.

    Sin esto, los píxeles semitransparentes conservan su tono lavado y el sprite
    queda con un halo claro alrededor cuando se dibuja sobre otro fondo."""
    safe = np.maximum(alpha, 1e-3)[..., None]
    recovered = (rgb.astype(np.float32) - 255.0 * (1.0 - alpha[..., None])) / safe
    blended = np.where(alpha[..., None] > 0.0, recovered, rgb.astype(np.float32))
    return np.clip(blended, 0, 255).astype(np.uint8)


def cutout(image: Image.Image, punch_holes: bool = False) -> Image.Image:
    """PNG sin fondo, con el sujeto entero — incluido todo lo blanco que tenga."""
    rgb = np.array(image.convert("RGB"))
    distance = white_distance(rgb)
    background = background_mask(distance, punch_holes=punch_holes)
    alpha = alpha_from_background(distance, background)
    clean = undo_white_matte(rgb, alpha)
    return Image.fromarray(
        np.dstack([clean, (alpha * 255).round().astype(np.uint8)]), mode="RGBA"
    )
