"""Un proyecto: un objetivo, sus prompts, sus referencias y su salida.

La estructura es fija a propósito. Que los cuatro directorios se llamen siempre
igual es lo que permite que un agente que nunca vio este repo sepa dónde escribir
sin preguntar, y que el comando sea siempre el mismo:

    projects/<nombre>/
    ├── project.json     ajustes (todo opcional; los defaults están acá abajo)
    ├── OBJETIVO.md      para qué son estas imágenes — lo lee el agente, no el script
    ├── prompts/         NN_clave.md, uno por imagen
    ├── references/      lo que se adjunta al chat y viene de afuera
    ├── output/          las imágenes generadas, `<clave>.png`
    │   └── assets/      sólo en modo game-asset: los PNG recortados y escalados
    └── state/           checkpoint de la corrida y descartes para auditar
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

#: Modos de salida. `raw` guarda lo que devolvió el modelo y nada más;
#: `game-asset` además le saca el fondo y exporta los tamaños declarados.
OUTPUT_RAW = "raw"
OUTPUT_GAME_ASSET = "game-asset"
OUTPUT_MODES = (OUTPUT_RAW, OUTPUT_GAME_ASSET)

DEFAULT_SETTINGS: dict = {
    "engine": "gemini",
    "output": OUTPUT_RAW,
    #: Lados a exportar en modo game-asset. Vacío = sólo el recorte, en la
    #: resolución nativa.
    "sizes": [],
    #: Claves cuyo blanco encerrado SÍ es un hueco calado y no parte del dibujo.
    "punch_holes": [],
    #: Distancia MAE bajo la cual una imagen se considera "es la referencia
    #: adjunta" y se descarta. Bajalo cuando la referencia sea casi lo mismo que
    #: se está generando (una variante del mismo personaje).
    "reference_threshold": 4.0,
}


@dataclass(frozen=True)
class Project:
    root: Path
    settings: dict

    @classmethod
    def load(cls, root: Path) -> "Project":
        root = Path(root).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"No existe el proyecto {root}")
        settings = dict(DEFAULT_SETTINGS)
        config = root / "project.json"
        if config.exists():
            settings.update(json.loads(config.read_text(encoding="utf-8")))
        if settings["output"] not in OUTPUT_MODES:
            raise ValueError(
                f"`output` inválido en {config}: {settings['output']!r}. "
                f"Los modos son {' | '.join(OUTPUT_MODES)}."
            )
        return cls(root=root, settings=settings)

    @property
    def prompts(self) -> Path:
        return self.root / "prompts"

    @property
    def references(self) -> Path:
        return self.root / "references"

    @property
    def output(self) -> Path:
        return self.root / "output"

    @property
    def assets(self) -> Path:
        return self.output / "assets"

    @property
    def state(self) -> Path:
        return self.root / "state"

    @property
    def checkpoint(self) -> Path:
        return self.state / "run.json"

    @property
    def discards(self) -> Path:
        """Dónde se guardan las imágenes descartadas por parecerse a la
        referencia. Existe para poder MIRARLAS: distinguir "es la referencia" de
        "es el resultado que se le parece demasiado" no se puede hacer con el
        número solo."""
        return self.state / "discards"

    def ensure_directories(self) -> None:
        for path in (self.prompts, self.references, self.output, self.state):
            path.mkdir(parents=True, exist_ok=True)
