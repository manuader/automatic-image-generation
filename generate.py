#!/usr/bin/env python3
"""Generador de imágenes por chat web. Un solo comando para todo.

    python3 generate.py --project mi-proyecto

Leé el README.md: dice dónde escribir los prompts y qué queda dónde. Lo mínimo
para no perderse acá abajo:

    --launch      abre el Chrome aislado (una vez, para iniciar sesión)
    --probe       comprueba que el motor reconoce la página, sin gastar cuota
    --dry-run     muestra la cola y no genera nada
    --reprocess   rehace los assets desde los originales, sin tocar el navegador
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core import chrome, engines  # noqa: E402
from core.checkpoint import RunCheckpoint  # noqa: E402
from core.postprocess import derive_for_project  # noqa: E402
from core.project import OUTPUT_MODES, Project  # noqa: E402
from core.queue import pending_assets  # noqa: E402
from core.runner import AssetRunner  # noqa: E402

PROJECTS = ROOT / "projects"


def resolve_project(value: str) -> Path:
    """Acepta el nombre corto (`skins`) o un path. El nombre corto es el camino
    normal: los proyectos viven todos en `projects/`."""
    candidate = Path(value)
    if candidate.is_dir():
        return candidate
    return PROJECTS / value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--project", help="nombre del directorio en projects/ (o un path)")
    parser.add_argument("--engine", help=f"motor a usar: {' | '.join(engines.available())}")
    parser.add_argument("--output", choices=OUTPUT_MODES,
                        help="pisa el modo de salida del project.json")
    parser.add_argument("--launch", action="store_true",
                        help="abre el Chrome aislado del motor y sale")
    parser.add_argument("--probe", action="store_true",
                        help="verifica que el motor reconoce la página y sale (cuota: cero)")
    parser.add_argument("--reprocess", action="store_true",
                        help="rehace la salida procesada desde los originales ya "
                             "generados; no abre el navegador")
    parser.add_argument("--dry-run", action="store_true", help="muestra la cola y sale")
    parser.add_argument("--only", help="una sola clave")
    parser.add_argument("--limit", type=int, default=0, help="máximo de imágenes (0 = todas)")
    parser.add_argument("--pause", type=float, default=4, help="segundos entre imágenes")
    parser.add_argument("--port", type=int, default=chrome.DEFAULT_PORT, help="puerto Chrome debug")
    parser.add_argument("--timeout", type=int, default=180, help="timeout de UI por imagen")
    parser.add_argument("--retries", type=int, default=1,
                        help="reintentos por imagen ante un fallo transitorio")
    parser.add_argument("--max-consecutive-failures", type=int, default=3,
                        help="frena el batch tras N fallos SEGUIDOS (bloqueo/logout/cuota)")
    parser.add_argument("--type-chunk", type=int, default=None,
                        help="caracteres por tanda de tipeo. Bajalo si la máquina "
                             "está cargada y se pierden caracteres")
    parser.add_argument("--type-pause", type=float, default=None,
                        help="segundos de respiro entre tandas de tipeo")
    parser.add_argument("--ref-threshold", type=float, default=None,
                        help="distancia MAE bajo la cual se descarta una imagen por "
                             "ser la referencia adjunta")
    return parser.parse_args()


def build_browser(browser_class, project: Project | None, args) -> object:
    from core.webchat import TYPE_CHUNK_CHARS, TYPE_PAUSE_SECONDS

    settings = project.settings if project else {}
    threshold = args.ref_threshold
    if threshold is None:
        threshold = settings.get("reference_threshold", 4.0)
    return browser_class(
        port=args.port,
        timeout=args.timeout,
        ref_threshold=threshold,
        discards_dir=project.discards if project else None,
        type_chunk=args.type_chunk if args.type_chunk is not None else TYPE_CHUNK_CHARS,
        type_pause=args.type_pause if args.type_pause is not None else TYPE_PAUSE_SECONDS,
    )


def available_projects() -> str:
    return ", ".join(sorted(path.name for path in PROJECTS.iterdir() if path.is_dir())) or "ninguno"


def load_project(args) -> Project:
    if not args.project:
        raise SystemExit(f"Falta --project. Los que hay: {available_projects()}")
    try:
        project = Project.load(resolve_project(args.project))
    except FileNotFoundError as error:
        # Un traceback acá no ayuda a nadie: el error casi siempre es un nombre
        # mal tipeado, y lo único que hace falta es la lista de los que hay.
        raise SystemExit(f"{error}. Los que hay: {available_projects()}") from None
    if args.output:
        project.settings["output"] = args.output
    project.ensure_directories()
    return project


def reprocess(project: Project) -> None:
    """Rehace la salida procesada desde los originales, sin generar nada nuevo.

    Existe porque cambiar los tamaños o arreglar un recorte no tiene por qué
    costar cuota: el original ya está en `output/`. Es también la salida del
    único hueco del camino normal — si el post-proceso falla después de que la
    imagen se guardó, la cola no la va a volver a pedir (y hace bien), así que
    tiene que haber una forma de completarla sin el navegador."""
    originals = sorted(project.output.glob("*.png"))
    if not originals:
        print(f"No hay originales en {project.output}")
        return
    written = 0
    for original in originals:
        written += len(derive_for_project(project, original.stem, original))
    print(f"{len(originals)} originales → {written} archivos en {project.assets}")


def main() -> None:
    args = parse_args()
    project = None if (args.launch or args.probe) and not args.project else load_project(args)
    engine = args.engine or (project.settings["engine"] if project else "gemini")

    if args.reprocess:
        reprocess(project)
        return

    browser_class = engines.load(engine)

    if args.launch:
        launched = chrome.ensure_debug_chrome(
            browser_class.HOME_URL, chrome.profile_for(engine), args.port
        )
        state = "abierto" if launched else "ya estaba abierto"
        print(f"Chrome aislado de {engine} {state}: {chrome.debug_url(args.port)}")
        print("Iniciá sesión en ESA ventana si te lo pide; después corré el generador.")
        return

    if args.probe:
        print(json.dumps(build_browser(browser_class, project, args).probe(),
                         indent=2, ensure_ascii=False))
        return

    queue = pending_assets(project.prompts, project.output, project.root)
    if args.only:
        queue = [asset for asset in queue if asset.key == args.only]
    if args.limit:
        queue = queue[:args.limit]
    print("Cola:", ", ".join(f"{asset.order:02d}_{asset.key}" for asset in queue) or "vacía")
    for asset in queue:
        if asset.reference is not None and not asset.reference.is_file():
            print(f"  ⚠️  {asset.key}: falta la referencia {asset.reference}", file=sys.stderr)
    if args.dry_run or not queue:
        return

    runner = AssetRunner(
        build_browser(browser_class, project, args),
        project,
        RunCheckpoint(project.checkpoint),
    )
    completed: list[str] = []
    consecutive_failures = 0
    for index, asset in enumerate(queue, 1):
        print(f"[{index}/{len(queue)}] {asset.key}…", flush=True)
        # Un fallo transitorio (timeout de red/UI) no debe voltear todo el batch:
        # se reintenta la imagen y, si igual falla, se salta a la siguiente. Sólo
        # se frena ante N fallos SEGUIDOS (síntoma de bloqueo/logout/cuota).
        ok = False
        for attempt in range(args.retries + 1):
            ok = runner.run(asset)
            if ok:
                break
            if attempt < args.retries:
                print(f"  … reintento {attempt + 1}/{args.retries}", file=sys.stderr)
                time.sleep(args.pause)
        if ok:
            completed.append(asset.key)
            consecutive_failures = 0
            print(f"  ✓ output/{asset.key}.png")
        else:
            consecutive_failures += 1
            print(f"  ✗ {asset.key} falló ({consecutive_failures} seguidas); "
                  "sigo con la próxima", file=sys.stderr)
            if consecutive_failures >= args.max_consecutive_failures:
                print(f"  ⨯ {consecutive_failures} fallos seguidos: freno para no "
                      "gastar tu cuota (¿bloqueo/logout?)", file=sys.stderr)
                break
        if index < len(queue):
            time.sleep(args.pause)
    print(f"=== FIN: {len(completed)}/{len(queue)} OK, "
          f"{len(queue) - len(completed)} pendientes ===")
    failures = RunCheckpoint(project.checkpoint).data.get("failures", {})
    if failures:
        print(f"Los fallos quedaron anotados en {project.checkpoint}")


if __name__ == "__main__":
    main()
