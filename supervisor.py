#!/usr/bin/env python3
"""Corre un proyecto entero sin nadie mirando, y lo vuelve a lanzar si se cae.

    .venv/bin/python supervisor.py --project fisu-evolution-v2

`generate.py` ya retoma solo (saltea lo que tiene PNG en `output/`) y frena tras
tres fallos seguidos para no gastar cuota. Lo que no hace es volver a arrancar:
un logout, un Chrome colgado o la cuota agotada a las 3 de la mañana dejan el
batch parado hasta que alguien lo ve. Este archivo es ese alguien.

Corre las imágenes de a una (`generate.py --only <clave> --retries 0`) para
llevar la cuenta por imagen, y separa los fallos según de quién es la culpa:

- **cuota o bloqueo del sitio** — no es de la imagen: el motor queda en pausa
  (30 min, 1 h, 2 h, 3 h) y se pasa al otro motor si hay uno disponible.
  Antes de volver se hace un `--probe`, que no gasta cuota.
- **del navegador** (Chrome caído, no encuentra el chat, el guard que aborta
  antes de enviar) — el prompt no salió, así que tampoco cuenta contra la imagen.
- **de la imagen** (timeout esperando la imagen, PNG inválido, el sitio no pudo
  generarla, un proceso colgado) — cuenta. A los 3 intentos la imagen se
  saltea y se anota por qué: así ninguna imagen se paga muchas veces.

Tres fallos seguidos de cualquier tipo salvo la cuota son un reinicio duro: se
matan el generador, chromedriver y el Chrome del motor, y se vuelve a abrir
(el perfil guarda la sesión). Si los reinicios se repiten sin avanzar, se espera
cada vez más antes del próximo.

Con `--rotate gemini:50,chat-gpt:50` los motores se turnan en tandas de
imágenes ENVIADAS, para que ningún sitio vea el batch entero. Una familia de
continuidad (`- **familia**: <id>` en el .md) no se parte entre tandas; un motor
sin cuota cede su turno al siguiente y la cola sigue en el mismo orden. Con
`--dry-run` se ve el plan de tandas sin abrir nada. Ver `core/rotation.py`.

Estado en `state/supervisor.json`, bitácora en `state/supervisor.log` y la
salida del generador en `state/generate.log`. Cortarlo con Ctrl-C y volver a
correr el mismo comando sigue donde quedó.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core import engines as engine_registry  # noqa: E402
from core.chrome import profile_for  # noqa: E402
from core.checkpoint import read_json, write_json  # noqa: E402
from core.project import Project  # noqa: E402
from core.queue import Asset, pending_assets  # noqa: E402
from core.rotation import Turn, describe, family_order, fits, parse_rotation, plan, unit_size  # noqa: E402,E501

GENERATE = ROOT / "generate.py"

# Qué tipo de fallo es, mirando el motivo que `generate.py` deja en run.json.
QUOTA = "cuota"
BROWSER = "navegador"
ASSET = "imagen"

QUOTA_MARKERS = (
    "límite de uso", "limite de uso", "cuota de imágenes", "captcha",
    "actividad inusual", "exceso de pedidos", "reintentar más tarde",
)
BROWSER_MARKERS = (
    "no pude conectar selenium", "no encontré el cuadro", "no encontré el editor",
    "no envío", "el prompt no llegó", "abra la conversación tras enviar", "no pude devolverle el foco", "el editor no aceptó",
    "falta selenium", "chrome abrió pero",
)

#: Así dice Gemini que aceptó el pedido y no devolvió nada (ver `_explain_silence`).
STUCK_MARKER = "se quedó en «"

#: Pausas de un motor bloqueado, en minutos, según cuántas veces seguidas lo fue.
COOLDOWN_MINUTES = (30, 60, 120, 180)
#: Un motor que no muestra el chat (sesión cerrada) se vuelve a mirar seguido:
#: lo arregla una persona, y cuando lo haga no tiene que esperar horas.
LOGIN_COOLDOWN_MINUTES = 10


def classify(reason: str) -> str:
    text = reason.lower()
    if any(marker in text for marker in QUOTA_MARKERS):
        return QUOTA
    if any(marker in text for marker in BROWSER_MARKERS):
        return BROWSER
    return ASSET


@dataclass
class State:
    """Lo que tiene que sobrevivir a un Ctrl-C o a un corte de luz."""

    path: Path
    attempts: dict[str, int] = field(default_factory=dict)
    skipped: dict[str, str] = field(default_factory=dict)
    blocks: dict[str, dict] = field(default_factory=dict)
    resets: int = 0
    #: Dónde va la rotación: {"spec", "slot", "sent", "family"}. Vacío sin `--rotate`.
    rotation: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "State":
        data = read_json(path, {}) or {}
        return cls(
            path=path,
            attempts=data.get("attempts", {}),
            skipped=data.get("skipped", {}),
            blocks=data.get("blocks", {}),
            resets=data.get("resets", 0),
            rotation=data.get("rotation", {}),
        )

    def save(self) -> None:
        write_json(self.path, {
            "attempts": self.attempts,
            "skipped": self.skipped,
            "blocks": self.blocks,
            "resets": self.resets,
            "rotation": self.rotation,
        })


class Supervisor:
    def __init__(self, project: Project, engines: list[str], engine_rules: dict[str, str],
                 *, max_asset_attempts: int = 3, max_failures_in_a_row: int = 3,
                 asset_timeout: int = 600, python: str = sys.executable,
                 generator: Path = GENERATE, sleep=time.sleep, now=time.time,
                 notify=None, kill=None, rotation: list[Turn] | None = None):
        self.project = project
        self.rotation = rotation
        if rotation:
            # Con rotación los motores son los de la rotación, y nada más.
            engines = list(dict.fromkeys(turn.engine for turn in rotation))
        self.engines = engines
        self.engine_rules = engine_rules
        self.max_asset_attempts = max_asset_attempts
        self.max_failures_in_a_row = max_failures_in_a_row
        self.asset_timeout = asset_timeout
        self.python = python
        self.generator = generator
        self.sleep = sleep
        self.now = now
        self.notify = notify or notify_mac
        self.kill = kill or self._kill_engine
        self.state = State.load(project.state / "supervisor.json")
        if rotation:
            spec = rotation_spec(rotation)
            if self.state.rotation.get("spec") != spec:
                # Otra rotación que la de la corrida anterior: se arranca de cero.
                self.state.rotation = {"spec": spec, "slot": 0, "sent": 0, "family": None}
        self.log_path = project.state / "supervisor.log"
        self.generate_log = project.state / "generate.log"
        #: Motores con un probe bueno desde el último bloqueo o reinicio.
        self.verified: set[str] = set()
        self.failures_in_a_row = 0
        self.resets_without_progress = 0
        self.stuck_in_a_row = 0
        self.generated = 0

    # ------------------------------------------------------------------ bitácora

    def log(self, message: str) -> None:
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}"
        print(line, flush=True)
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    # --------------------------------------------------------------------- cola

    def pending(self) -> list[Asset]:
        return [
            asset for asset in pending_assets(self.project.prompts, self.project.output,
                                              self.project.root)
            if asset.key not in self.state.skipped
        ]

    def skip(self, asset: Asset, reason: str) -> None:
        self.state.skipped[asset.key] = reason
        self.state.attempts.pop(asset.key, None)
        self.state.save()
        self.log(f"⏭  {asset.key} queda afuera: {reason}")

    def ready(self, queue: list[Asset]) -> list[Asset]:
        """Las imágenes que se pueden pedir ya: su referencia está en disco.

        Una referencia que es la salida de otra imagen salteada no va a llegar
        nunca, y esa imagen se saltea también; una que todavía está en la cola
        sólo hace esperar (va antes en el orden, así que sale primero)."""
        keys = {asset.key for asset in queue}
        ready = []
        for asset in queue:
            reference = asset.reference
            if reference is None or reference.is_file():
                ready.append(asset)
            elif reference.stem not in keys:
                self.skip(asset, f"falta su referencia {reference.name}")
        return ready

    # ------------------------------------------------------------------- motores

    def allowed_engines(self, asset: Asset) -> list[str]:
        for prefix, engine in self.engine_rules.items():
            if asset.key.startswith(prefix):
                return [engine]
        return self.engines

    def blocked_until(self, engine: str) -> float:
        return self.state.blocks.get(engine, {}).get("until", 0)

    def is_available(self, engine: str) -> bool:
        return self.blocked_until(engine) <= self.now()

    def block(self, engine: str, reason: str, minutes: int | None = None) -> None:
        entry = self.state.blocks.setdefault(engine, {"strikes": 0})
        if minutes is None:
            entry["strikes"] = entry.get("strikes", 0) + 1
            minutes = COOLDOWN_MINUTES[min(entry["strikes"], len(COOLDOWN_MINUTES)) - 1]
        entry["until"] = self.now() + minutes * 60
        entry["reason"] = reason
        self.state.save()
        self.verified.discard(engine)
        resume = time.strftime("%H:%M", time.localtime(entry["until"]))
        self.log(f"⏸  {engine} en pausa {minutes} min (hasta las {resume}): {reason}")

    def clear_block(self, engine: str) -> None:
        if engine in self.state.blocks:
            del self.state.blocks[engine]
            self.state.save()

    def generator_cmd(self, *args: str) -> list[str]:
        return [self.python, str(self.generator), *args]

    def ensure_ready(self, engine: str) -> bool:
        """Chrome abierto y el chat reconocido, sin gastar cuota (`--probe`)."""
        if engine in self.verified:
            return True
        launch = subprocess.run(self.generator_cmd("--engine", engine, "--launch"),
                                capture_output=True, text=True, timeout=60)
        if launch.returncode != 0:
            self.block(engine, f"no pude abrir su Chrome: {launch.stderr.strip()[-200:]}",
                       LOGIN_COOLDOWN_MINUTES)
            return False
        # Dos probes: el primero a veces mira la página antes de que termine de
        # cargar (medido en ChatGPT: "compose_box": null y al rato "div").
        for _ in range(2):
            try:
                probe = subprocess.run(self.generator_cmd("--engine", engine, "--probe"),
                                       capture_output=True, text=True, timeout=120)
                result = json.loads(probe.stdout)
            except (subprocess.TimeoutExpired, ValueError):
                self.block(engine, "el probe no contestó", LOGIN_COOLDOWN_MINUTES)
                return False
            if result.get("blocked") or result.get("compose_box"):
                break
            self.sleep(5)
        if result.get("blocked"):
            self.block(engine, result["blocked"])
            return False
        if not result.get("compose_box"):
            self.block(engine, "no veo el cuadro del chat: ¿la sesión está iniciada?",
                       LOGIN_COOLDOWN_MINUTES)
            self.notify(f"Iniciá sesión en {engine}",
                        f"Corré: .venv/bin/python generate.py --engine {engine} --launch")
            return False
        self.verified.add(engine)
        self.log(f"✓ {engine} listo")
        return True

    def _kill_engine(self, engine: str) -> None:
        """El reinicio duro: generador, chromedriver y el Chrome del motor."""
        for pattern in (f"{self.generator.name} --project", "chromedriver",
                        f"--user-data-dir={profile_for(engine)}"):
            subprocess.run(["pkill", "-f", pattern], capture_output=True)
        self.sleep(3)

    def hard_reset(self, engine: str) -> None:
        self.state.resets += 1
        self.state.save()
        self.resets_without_progress += 1
        self.failures_in_a_row = 0
        self.verified.discard(engine)
        self.log(f"↻  {self.max_failures_in_a_row} fallos seguidos: reinicio {engine} "
                 f"(reinicio {self.resets_without_progress} sin avanzar)")
        self.kill(engine)
        if self.resets_without_progress >= 4:
            # Cuatro reinicios sin una sola imagen: el motor no está para esto
            # ahora. Se lo deja descansar como si fuera la cuota.
            self.block(engine, "cuatro reinicios seguidos sin generar nada")
            self.notify("El batch no avanza", f"{engine} en pausa; ver state/supervisor.log")
            self.resets_without_progress = 0
        elif self.resets_without_progress > 1:
            self.sleep(min(5 * 2 ** (self.resets_without_progress - 2), 60) * 60)

    # ------------------------------------------------------------------ un pedido

    def attempt(self, asset: Asset, engine: str) -> tuple[bool, str, str]:
        """Pide UNA imagen. Devuelve (salió, tipo de fallo, motivo)."""
        checkpoint = read_json(self.project.checkpoint, {}) or {}
        # El motivo de un intento viejo no puede pasar por el de éste.
        if checkpoint.get("failures", {}).pop(asset.key, None) is not None:
            write_json(self.project.checkpoint, checkpoint)
        command = self.generator_cmd(
            "--project", str(self.project.root), "--engine", engine, "--only", asset.key,
            "--retries", "0", "--max-consecutive-failures", "1",
        )
        with open(self.generate_log, "a", encoding="utf-8") as output:
            process = subprocess.Popen(command, stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            try:
                code = process.wait(timeout=self.asset_timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                code = None
        if (self.project.output / f"{asset.key}.png").exists():
            return True, "", ""
        failures = (read_json(self.project.checkpoint, {}) or {}).get("failures", {})
        reason = failures.get(asset.key)
        if reason:
            return False, classify(reason), reason
        if code is None:
            return False, ASSET, f"colgado más de {self.asset_timeout // 60} min"
        return False, BROWSER, f"el generador terminó con código {code} sin anotar motivo"

    # ------------------------------------------------------------------ rotación

    def rotation_plan(self) -> str:
        """El plan de tandas desde donde está la corrida, sin tocar nada."""
        turns = self.rotation
        state = self.state.rotation
        return describe(plan(self.pending(), turns, state["slot"], state["sent"]), turns)

    def advance_turn(self, why: str) -> None:
        state = self.state.rotation
        state["slot"] = (state["slot"] + 1) % len(self.rotation)
        state["sent"] = 0
        self.state.save()
        turn = self.rotation[state["slot"]]
        self.log(f"⇄  {why}: le toca a {turn.engine} ({turn.size})")

    def rotation_job(self, queue: list[Asset], ready: list[Asset]) -> tuple[Asset, str] | None:
        """La próxima imagen y el motor del turno, o None si todos están en pausa.

        La imagen es siempre la primera de la cola que se puede pedir: ni la
        tanda ni la cuota cambian el orden, sólo quién la pide."""
        state = self.state.rotation
        ready_keys = {asset.key for asset in ready}
        asset = next(asset for asset in family_order(queue) if asset.key in ready_keys)
        in_open_family = asset.family is not None and asset.family == state.get("family")
        if not in_open_family:
            state["family"] = None
            turn = self.rotation[state["slot"]]
            if not fits(state["sent"], unit_size(asset, queue), turn.size):
                self.advance_turn(f"tanda de {turn.engine} completa ({state['sent']} enviadas)")
        turns = len(self.rotation)
        offset = next((step for step in range(turns)
                       if self.is_available(self.rotation[(state["slot"] + step) % turns].engine)),
                      None)
        if offset is None:
            return None
        for _ in range(offset):
            engine = self.rotation[state["slot"]].engine
            if in_open_family:
                self.log(f"⚠  la familia {asset.family} se parte: {engine} se quedó sin "
                         "cuota a mitad de ella")
            self.advance_turn(f"{engine} en pausa")
        return asset, self.rotation[state["slot"]].engine

    def count_sent(self, asset: Asset, ok: bool, kind: str, reason: str) -> None:
        """Suma a la tanda lo que llegó al sitio. Un fallo del navegador no salió;
        una cuota avisada de entrada, tampoco. Una imagen trabada sí: se pidió."""
        sent = ok or kind == ASSET or (kind == QUOTA and STUCK_MARKER in reason)
        if not sent:
            return
        state = self.state.rotation
        state["sent"] += 1
        state["family"] = asset.family
        self.state.save()

    # -------------------------------------------------------------------- bucle

    def next_job(self, ready: list[Asset]) -> tuple[Asset, str] | None:
        for asset in ready:
            for engine in self.allowed_engines(asset):
                if self.is_available(engine):
                    return asset, engine
        return None

    def wait_for_an_engine(self, ready: list[Asset]) -> None:
        engines = {engine for asset in ready for engine in self.allowed_engines(asset)}
        until = min(self.blocked_until(engine) for engine in engines)
        seconds = max(until - self.now(), 30)
        self.log(f"…  todos los motores en pausa; espero {round(seconds / 60)} min")
        self.sleep(seconds)

    def handle(self, asset: Asset, engine: str, ok: bool, kind: str, reason: str) -> None:
        if ok:
            self.generated += 1
            self.failures_in_a_row = 0
            self.resets_without_progress = 0
            self.state.attempts.pop(asset.key, None)
            self.state.save()
            self.clear_block(engine)
            self.stuck_in_a_row = 0
            self.log(f"✓  {asset.key} ({engine}) — {self.generated} en esta corrida")
            return
        if kind == QUOTA and STUCK_MARKER in reason and self.stuck_in_a_row == 0:
            # Medido 2026-10-08: Gemini se traba en «creating your image» en un
            # pedido suelto y el mismo pedido sale al reintentar. Recién dos
            # seguidos son la cuota de imágenes; pausar por uno cuesta 30 min.
            self.stuck_in_a_row = 1
            self.log(f"↺  {asset.key} ({engine}) se trabó generando; reintento antes de pausar")
            return
        if kind == QUOTA:
            self.stuck_in_a_row = 0
            self.block(engine, reason)
            return
        self.failures_in_a_row += 1
        if kind == ASSET:
            tries = self.state.attempts.get(asset.key, 0) + 1
            self.state.attempts[asset.key] = tries
            self.state.save()
            self.log(f"✗  {asset.key} ({engine}) intento {tries}/{self.max_asset_attempts}: {reason}")
            if tries >= self.max_asset_attempts:
                self.skip(asset, f"{tries} intentos fallidos; el último: {reason}")
        else:
            self.verified.discard(engine)
            self.log(f"✗  {asset.key} ({engine}) sin gastar la imagen: {reason}")
        if self.failures_in_a_row >= self.max_failures_in_a_row:
            self.hard_reset(engine)

    def step(self) -> bool:
        """Un paso del bucle. Devuelve False cuando no queda nada por hacer."""
        queue = self.pending()
        if not queue:
            return False
        ready = self.ready(queue)
        if not ready:
            # Lo que queda espera referencias que esperan a su vez: un ciclo.
            for asset in self.pending():
                self.skip(asset, "su referencia no va a llegar (dependencia circular)")
            return False
        job = self.rotation_job(queue, ready) if self.rotation else self.next_job(ready)
        if job is None:
            self.wait_for_an_engine(ready)
            return True
        asset, engine = job
        if not self.ensure_ready(engine):
            return True
        self.log(f"→  {asset.key} con {engine} (quedan {len(queue)})")
        outcome = self.attempt(asset, engine)
        if self.rotation:
            self.count_sent(asset, *outcome)
        self.handle(asset, engine, *outcome)
        return True

    def run(self) -> int:
        self.log(f"=== arranca {self.project.root.name}: {len(self.pending())} pendientes, "
                 f"motores {', '.join(self.engines)} ===")
        while True:
            try:
                if not self.step():
                    break
            except Exception as error:  # noqa: BLE001 — el supervisor no se cae por un paso
                self.log(f"!  error del supervisor: {error!r}; sigo en 10 s")
                self.failures_in_a_row += 1
                self.sleep(10)
        skipped = self.state.skipped
        self.log(f"=== FIN: {self.generated} generadas en esta corrida, "
                 f"{len(skipped)} afuera ===")
        for key, reason in skipped.items():
            self.log(f"   afuera: {key} — {reason}")
        self.notify("Batch terminado",
                    f"{self.generated} generadas, {len(skipped)} quedaron afuera")
        return 0 if not skipped else 1


def rotation_spec(turns: list[Turn]) -> str:
    return ",".join(f"{turn.engine}:{turn.size}" for turn in turns)


def notify_mac(title: str, message: str) -> None:
    script = f"display notification {json.dumps(message)} with title {json.dumps(title)}"
    subprocess.run(["osascript", "-e", script], capture_output=True)


def keep_awake() -> None:
    """Que la Mac no se duerma mientras viva este proceso."""
    if sys.platform == "darwin":
        subprocess.Popen(["caffeinate", "-dimsu", "-w", str(os.getpid())])


def single_instance(project: Project) -> None:
    """Dos supervisores sobre el mismo proyecto pedirían cada imagen dos veces."""
    pidfile = project.state / "supervisor.pid"
    if pidfile.exists():
        try:
            os.kill(int(pidfile.read_text()), 0)
        except (ValueError, ProcessLookupError, PermissionError):
            pass
        else:
            raise SystemExit(f"Ya hay un supervisor corriendo (pid {pidfile.read_text()}).")
    pidfile.write_text(str(os.getpid()))


def parse_rules(values: list[str]) -> dict[str, str]:
    rules = {}
    for value in values:
        prefix, _, engine = value.partition("=")
        if not engine:
            raise SystemExit(f"--engine-for espera prefijo=motor, no {value!r}")
        rules[prefix] = engine
    return rules


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    parser.add_argument("--engines", default="chat-gpt,gemini",
                        help="motores en orden de preferencia, separados por coma")
    parser.add_argument("--engine-for", action="append", default=None, metavar="PREFIJO=MOTOR",
                        help="las claves con ese prefijo sólo con ese motor "
                             "(por defecto bg_=chat-gpt: los fondos van a 2048 px)")
    parser.add_argument("--max-asset-attempts", type=int, default=3)
    parser.add_argument("--max-failures-in-a-row", type=int, default=3)
    parser.add_argument("--asset-timeout", type=int, default=600,
                        help="segundos antes de dar por colgado un pedido")
    parser.add_argument("--rotate", metavar="MOTOR:N,MOTOR:N",
                        help="tandas alternadas de N imágenes enviadas por motor, "
                             "p. ej. gemini:50,chat-gpt:50 (reemplaza a --engines)")
    parser.add_argument("--dry-run", action="store_true",
                        help="con --rotate: muestra el plan de tandas y sale, sin "
                             "abrir navegadores")
    args = parser.parse_args()

    rotation = None
    if args.rotate:
        if args.engine_for is not None:
            raise SystemExit("--rotate y --engine-for no se combinan: la rotación "
                             "decide el motor de cada imagen")
        try:
            rotation = parse_rotation(args.rotate, engine_registry.available())
        except ValueError as error:
            raise SystemExit(str(error)) from None
    elif args.dry_run:
        raise SystemExit("--dry-run muestra el plan de --rotate; para la cola "
                         "sola: generate.py --dry-run")

    from generate import resolve_project

    project = Project.load(resolve_project(args.project))
    if args.dry_run:
        print(Supervisor(project, [], {}, rotation=rotation).rotation_plan())
        return 0
    project.ensure_directories()
    single_instance(project)
    keep_awake()
    supervisor = Supervisor(
        project,
        engines=[engine.strip() for engine in args.engines.split(",") if engine.strip()],
        engine_rules={} if rotation else parse_rules(
            args.engine_for if args.engine_for is not None else ["bg_=chat-gpt"]),
        max_asset_attempts=args.max_asset_attempts,
        max_failures_in_a_row=args.max_failures_in_a_row,
        asset_timeout=args.asset_timeout,
        rotation=rotation,
    )
    try:
        return supervisor.run()
    except KeyboardInterrupt:
        supervisor.log("=== cortado a mano; el mismo comando sigue donde quedó ===")
        return 130
    finally:
        (project.state / "supervisor.pid").unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
