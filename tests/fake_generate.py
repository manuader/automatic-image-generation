"""Un `generate.py` de mentira para los tests del supervisor.

Lee qué hacer de `scenario.json`, en el directorio de `FAKE_GENERATE_DIR`, y anota cada llamada en
`calls.json`, así los tests pueden contar cuántas veces se pidió cada imagen.

    {"probe": {"chat-gpt": {...}}, "fail": {"clave": "motivo"}, "hang": ["clave"],
     "fail_times": {"clave": 2}, "delay": 0.3}

Con `--parallel` corren dos a la vez: `calls.json` se toca bajo candado y cada
pedido con `delay` deja su intervalo en `spans.json`, para ver que se solaparon.
"""

import fcntl
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.checkpoint import update_json  # noqa: E402

args = sys.argv[1:]


@contextmanager
def exclusive(path):
    with open(str(path) + ".lock", "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def append(path, item):
    with exclusive(path):
        items = json.loads(path.read_text()) if path.exists() else []
        items.append(item)
        path.write_text(json.dumps(items))
        return items


def value(flag):
    return args[args.index(flag) + 1] if flag in args else None


engine = value("--engine")
project = value("--project")
base = Path(os.environ["FAKE_GENERATE_DIR"])
scenario = json.loads((base / "scenario.json").read_text())
calls_path = base / "calls.json"

if "--launch" in args:
    sys.exit(0)
if "--probe" in args:
    print(json.dumps(scenario.get("probe", {}).get(
        engine, {"compose_box": "div", "send_button": "x", "blocked": None})))
    sys.exit(0)

key = value("--only")
calls = append(calls_path, [key, engine])

root = Path(project)
checkpoint = root / "state" / "run.json"

if key in scenario.get("hang", []):
    time.sleep(30)
if scenario.get("delay"):
    start = time.time()
    time.sleep(scenario["delay"])
    append(base / "spans.json", [key, engine, start, time.time()])
reason = scenario.get("fail", {}).get(key) or scenario.get("fail_engine", {}).get(engine)
remaining = scenario.get("fail_times", {}).get(key)
if remaining is not None:
    attempts = sum(1 for call in calls if call[0] == key)
    reason = (scenario.get("fail_reason", "timeout esperando la imagen generada")
              if attempts <= remaining else None)
if reason:
    update_json(checkpoint,
                lambda data: data.setdefault("failures", {}).__setitem__(key, reason), {})
    sys.exit(0)
(root / "output" / f"{key}.png").write_bytes(b"png")
