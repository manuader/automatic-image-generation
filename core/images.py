"""Verificación de las imágenes que devuelve el modelo."""

from __future__ import annotations

from pathlib import Path

#: El gate es dimensional, no de bytes: un ícono UI plano comprime a ~30-90 KB
#: (mucho menos que un personaje detallado) pero sigue siendo un 1024x1024 real,
#: y un umbral de 100 KB rechazaba íconos válidos.
#:
#: ⚠️ 2026-08-20: el piso se mide sobre el lado LARGO. Antes se medía sobre el
#: corto y con eso una portada de LinkedIn de 1024x254 —correcta, 314 KB, la
#: pieza que se había pedido— se descartaba como "no es un PNG válido del tamaño
#: esperado". Cualquier formato apaisado o muy vertical era imposible por
#: construcción: un roll-up de feria o un banner 4:1 no tienen un lado corto de
#: 512 px ni deberían tenerlo. El criterio venía de un proyecto de arte cuadrado
#: y se coló como si fuera universal.
#:
#: Lo que hay que rechazar es la iconografía del propio sitio, que se cuela entre
#: los candidatos: medidos en Gemini, 150x150, 128x128, 64x64 y 32x32. Un piso de
#: 512 en el lado largo los voltea a todos. El piso del lado corto queda igual
#: para descartar tiras degeneradas (una franja de 1024x20 no es una imagen), muy
#: por debajo de cualquier proporción de diseño real.
MINIMUM_LONG_SIDE = 512
MINIMUM_SHORT_SIDE = 128


def verify_png(
    path: Path,
    minimum_bytes: int = 1_000,
    minimum_side: int = MINIMUM_LONG_SIDE,
    minimum_short_side: int = MINIMUM_SHORT_SIDE,
) -> bool:
    """Comprueba firma, decodificación y DIMENSIONES de un PNG generado.

    El piso de bytes queda mínimo, sólo para descartar archivos vacíos o
    truncados; quien decide es el tamaño: el lado largo tiene que llegar a
    `minimum_side` y el corto no puede bajar de `minimum_short_side`.
    """
    if not path.is_file() or path.stat().st_size < minimum_bytes:
        return False
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()  # integridad del stream
        with Image.open(path) as image:
            width, height = image.size
        if max(width, height) < minimum_side or min(width, height) < minimum_short_side:
            return False
        return path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    except (OSError, ValueError):
        return False
