"""Coordina navegador, disco y checkpoint. No sabe qué proveedor hay del otro lado."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path

from core.errors import BROWSER_ERRORS, GenerationBlocked
from core.images import verify_png
from core.postprocess import derive_for_project, save_original
from core.project import Project
from core.queue import Asset, mark_asset_done


class AssetRunner:
    """Genera una imagen y la deja lista, o anota por qué no pudo.

    El orden importa y es el mismo de siempre: primero se guarda el original
    —que es lo que costó cuota—, después se verifica, y recién con el PNG
    verificado se marca el .md como hecho. Al revés, un fallo a mitad de camino
    dejaría un prompt "hecho" sin imagen, que es la única forma de perder trabajo
    de manera silenciosa.
    """

    def __init__(self, browser: object, project: Project, checkpoint, minimum_bytes: int = 1_000):
        self.browser = browser
        self.project = project
        self.checkpoint = checkpoint
        self.minimum_bytes = minimum_bytes

    def run(self, asset: Asset) -> bool:
        try:
            raw = self.browser.generate(asset, asset.reference)
            destination = save_original(raw, self.project.output, asset.key)
            if not verify_png(destination, self.minimum_bytes):
                raise GenerationBlocked("lo que llegó no es un PNG válido del tamaño esperado")
            derive_for_project(self.project, asset.key, destination)
        except (GenerationBlocked, OSError, ValueError, RuntimeError) + BROWSER_ERRORS as error:
            # El mensaje de Selenium no dice DÓNDE pasó: sin estas líneas, un
            # "stale element" se depura a ciegas.
            if not isinstance(error, GenerationBlocked):
                where = traceback.format_exc(limit=-4).strip().splitlines()
                print("  · traceback:\n    " + "\n    ".join(where[-8:]), file=sys.stderr, flush=True)
            self.checkpoint.record_failure(asset.key, str(error))
            return False
        mark_asset_done(asset)
        self.checkpoint.record_success(asset.key, destination)
        return True
