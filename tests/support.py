"""Andamios compartidos por los tests. Nada que use el navegador de verdad."""

from __future__ import annotations

import json
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def write_prompt(directory: Path, name: str, state: str = "pendiente",
                 reference: str | None = "references/style.png",
                 family: str | None = None) -> Path:
    """Un .md de prompt con la forma exacta que lee la cola."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.md"
    lines = [f"# {name}", "", f"- **estado**: {state}"]
    if reference is not None:
        lines.append(f"- **referencia**: adjuntar `{reference}`")
    if family is not None:
        lines.append(f"- **familia**: {family}")
    lines += ["", "## Prompt", "", "Prompt de prueba.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def make_project(root: Path, **settings) -> "object":
    """Un proyecto en disco con la estructura completa."""
    from core.project import Project

    root.mkdir(parents=True, exist_ok=True)
    if settings:
        (root / "project.json").write_text(json.dumps(settings), encoding="utf-8")
    project = Project.load(root)
    project.ensure_directories()
    return project


def subject_on_white(side: int = 600) -> Image.Image:
    """Fondo blanco tocando el borde y un sujeto de color en el medio: la
    situación exacta que el recorte por conectividad tiene que resolver."""
    image = Image.new("RGB", (side, side), (255, 255, 255))
    margin = side // 4
    for x in range(margin, side - margin):
        for y in range(margin, side - margin):
            image.putpixel((x, y), (20, 90, 200))
    return image


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()
