"""La cola de imágenes a generar, leída de los .md del proyecto.

Un prompt es un archivo `NN_clave.md` con tres cosas que le importan al runner:

    - **estado**: pendiente        ← pasa a `hecho` recién con el PNG verificado
    - **referencia**: `references/logo.png`   ← opcional; se adjunta al chat
    - **familia**: ceo                        ← opcional; ver core/rotation.py
    ## Prompt
    <el texto que se le manda al modelo, tal cual>

Nada de esto depende del proveedor ni de para qué son las imágenes: leer la cola
y verificarla no necesita navegador, y por eso se puede testear sin uno.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FILE_RE = re.compile(r"^(?P<order>\d{2,3})_(?P<key>.+)\.md$")
STATE_RE = re.compile(r"^- \*\*estado\*\*: (?P<state>\w+)$", re.MULTILINE)
# El path de la referencia se lee del propio .md: cada imagen adjunta la suya,
# no una global. Se acepta con o sin backticks.
REFERENCE_RE = re.compile(
    r"^- \*\*referencia\*\*:[^`\n]*`?(?P<path>[^`\n]+?)`?\s*$", re.MULTILINE
)
#: Familia de continuidad: las imágenes que tienen que salir del mismo motor y
#: en la misma tanda (un personaje y sus skins). Una palabra, sin espacios.
FAMILY_RE = re.compile(r"^- \*\*familia\*\*: `?(?P<family>[^`\s]+)`?\s*$", re.MULTILINE)
#: El `00_` es el índice del set de prompts, no una imagen a generar.
INDEX_PREFIX = "00_"


@dataclass(frozen=True)
class Asset:
    order: int
    key: str
    path: Path
    state: str
    prompt: str
    #: Imagen a adjuntar, resuelta desde el campo `**referencia**` del .md.
    #: `None` = este prompt no lleva referencia.
    reference: Path | None
    #: Familia de continuidad (`**familia**` del .md). `None` = imagen suelta.
    family: str | None = None

    @property
    def needs_reference(self) -> bool:
        return self.reference is not None


def parse_reference(text: str, base: Path) -> Path | None:
    """Resuelve el campo `**referencia**` contra la raíz del proyecto.

    Los dos orígenes válidos son `references/` —lo que se trae de afuera— y
    `output/` —lo que esta misma herramienta ya generó—, y por eso el path se
    escribe entero en el .md en vez de deducirse: encadenar una imagen con la
    anterior es el caso normal (una skin adjunta a SU personaje) y una
    convención implícita no lo cubriría.
    """
    match = REFERENCE_RE.search(text)
    if not match:
        return None
    raw = match.group("path").strip()
    candidate = Path(raw)
    return candidate if candidate.is_absolute() else (base / raw)


def parse_asset(path: Path, base: Path) -> Asset:
    """Convierte un `NN_clave.md` en una entrada de cola."""
    match = FILE_RE.match(path.name)
    if not match:
        raise ValueError(f"Nombre de prompt inválido: {path.name}")
    text = path.read_text(encoding="utf-8")
    state = STATE_RE.search(text)
    header, marker, prompt = text.partition("## Prompt")
    family = FAMILY_RE.search(header)
    if not marker or not prompt.strip():
        raise ValueError(f"Falta ## Prompt en {path}")
    return Asset(
        order=int(match.group("order")),
        key=match.group("key"),
        path=path,
        state=state.group("state") if state else "pendiente",
        prompt=prompt.strip(),
        reference=parse_reference(text, base),
        family=family.group("family") if family else None,
    )


def pending_assets(prompts_dir: Path, output_dir: Path, base: Path) -> list[Asset]:
    """Los prompts que todavía no tienen imagen, en orden.

    Dos preguntas, y las dos miran el disco: si el .md ya dice `hecho` o si el
    PNG ya está en la salida, no se vuelve a generar. Que la segunda alcance por
    sí sola es lo que hace la cola reanudable después de un Ctrl-C, un cierre de
    sesión o una cuota agotada — y lo que hace que copiar imágenes viejas a
    `output/` sea suficiente para no volver a pagarlas.
    """
    assets: list[Asset] = []
    for path in sorted(Path(prompts_dir).glob("[0-9][0-9]*.md")):
        if path.name.startswith(INDEX_PREFIX):
            continue
        asset = parse_asset(path, base)
        if asset.state == "hecho":
            continue
        if (Path(output_dir) / f"{asset.key}.png").exists():
            continue
        assets.append(asset)
    return assets


def mark_asset_done(asset: Asset) -> None:
    """Cambia el .md sólo después de haber verificado el PNG de destino."""
    text = asset.path.read_text(encoding="utf-8")
    if asset.state != "hecho":
        asset.path.write_text(
            text.replace("- **estado**: pendiente", "- **estado**: hecho", 1),
            encoding="utf-8",
        )
