"""Verificación de las imágenes que devuelve el modelo."""

from __future__ import annotations

from pathlib import Path

#: Lado mínimo aceptable. El gate real es dimensional, no de bytes: un ícono UI
#: plano comprime a ~30-90 KB (mucho menos que un personaje detallado) pero sigue
#: siendo un 1024x1024 real, y un umbral de 100 KB rechazaba íconos válidos.
MINIMUM_SIDE = 512


def verify_png(path: Path, minimum_bytes: int = 1_000, minimum_side: int = MINIMUM_SIDE) -> bool:
    """Comprueba firma, decodificación y DIMENSIONES de un PNG generado.

    El piso de bytes queda mínimo, sólo para descartar archivos vacíos o
    truncados; quien decide es el lado más corto de la imagen.
    """
    if not path.is_file() or path.stat().st_size < minimum_bytes:
        return False
    try:
        from PIL import Image

        with Image.open(path) as image:
            image.verify()  # integridad del stream
        with Image.open(path) as image:
            width, height = image.size
        if min(width, height) < minimum_side:
            return False
        return path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    except (OSError, ValueError):
        return False
