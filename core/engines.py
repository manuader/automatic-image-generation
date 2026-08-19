"""Resuelve el nombre de un motor a su clase de navegador.

Se carga por path y no con `import` normal porque uno de los directorios se
llama `chat-gpt`: el guion no es un identificador válido de Python. El nombre lo
eligió el dueño y vale más que la comodidad de un import — cargar por archivo es
una línea de `importlib` y evita tener que renombrar el directorio.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
#: Un motor es un directorio con un `browser.py` que expone `Browser`.
ENTRY_POINT = "browser.py"


def available() -> list[str]:
    return sorted(
        path.parent.name
        for path in ROOT.glob(f"*/{ENTRY_POINT}")
        if path.parent.name != "core"
    )


def load(name: str):
    """Devuelve la clase `Browser` del motor `name`."""
    path = ROOT / name / ENTRY_POINT
    if not path.is_file():
        raise SystemExit(
            f"No existe el motor «{name}». Los que hay: {', '.join(available()) or 'ninguno'}."
        )
    spec = importlib.util.spec_from_file_location(f"engine_{name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Browser
