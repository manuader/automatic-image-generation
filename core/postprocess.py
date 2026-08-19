"""Qué se hace con la imagen después de que el modelo la devuelve.

Dos modos, y la diferencia es sólo lo que pasa DESPUÉS de guardar:

- `raw`         se guarda el PNG tal cual. Es el default y el que sirve para
                identidad de marca, ilustración, referencia visual.
- `game-asset`  además se le saca el fondo blanco por conectividad y se exportan
                los tamaños que el proyecto declare.

El original crudo se guarda SIEMPRE, en los dos modos: es lo que costó cuota y
es lo que hace que la cola no lo vuelva a pedir. El post-proceso se puede repetir
mil veces sobre él sin gastar nada.
"""

from __future__ import annotations

from pathlib import Path

from core.project import OUTPUT_GAME_ASSET, Project


def save_original(png_bytes: bytes, output_dir: Path, key: str) -> Path:
    """Escribe `output/<clave>.png`, que es lo que la cola mira para no repetir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{key}.png"
    destination.write_bytes(png_bytes)
    return destination


def derive_game_assets(
    original: Path,
    assets_dir: Path,
    key: str,
    sizes: list[int],
    punch_holes: bool = False,
) -> list[Path]:
    """Recorta el fondo y exporta los tamaños pedidos. Devuelve lo escrito.

    Sin `sizes` escribe un solo archivo con el recorte en resolución nativa; con
    `sizes` escribe además un `<clave>_<lado>.png` por tamaño. El escalado
    respeta la proporción: forzar el cuadrado deformaría cualquier arte que no
    venga cuadrado, y el lado pedido se aplica al más largo.
    """
    from PIL import Image

    from core.cutout import cutout

    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(original) as image:
        transparent = cutout(image.convert("RGBA"), punch_holes=punch_holes)

    written = [assets_dir / f"{key}.png"]
    transparent.save(written[0])
    for side in sizes:
        scale = int(side) / max(transparent.size)
        resized = transparent.resize(
            (max(1, round(transparent.width * scale)), max(1, round(transparent.height * scale))),
            Image.LANCZOS,
        )
        path = assets_dir / f"{key}_{int(side)}.png"
        resized.save(path)
        written.append(path)
    return written


def derive_for_project(project: Project, key: str, original: Path) -> list[Path]:
    """Aplica el modo de salida del proyecto a un original ya guardado.

    En `raw` no hace nada y devuelve la lista vacía. Va acá y no en el runner
    porque también corre sin navegador ni checkpoint: cambiar los tamaños o
    arreglar un recorte no tiene por qué volver a pedirle nada al modelo (ver
    `--reprocess`)."""
    if project.settings["output"] != OUTPUT_GAME_ASSET:
        return []
    return derive_game_assets(
        original,
        project.assets,
        key,
        project.settings["sizes"],
        punch_holes=key in set(project.settings["punch_holes"]),
    )
