"""Un `generate.py` de mentira para los tests del supervisor.

Lee qué hacer de `scenario.json`, en el directorio de `FAKE_GENERATE_DIR`, y anota cada llamada en
`calls.json`, así los tests pueden contar cuántas veces se pidió cada imagen.

    {"probe": {"chat-gpt": {...}}, "fail": {"clave": "motivo"}, "hang": ["clave"],
     "fail_times": {"clave": 2}}
"""

import json
import os
import sys
import time
from pathlib import Path

args = sys.argv[1:]


def value(flag):
    return args[args.index(flag) + 1] if flag in args else None


engine = value("--engine")
project = value("--project")
base = Path(os.environ["FAKE_GENERATE_DIR"])
scenario = json.loads((base / "scenario.json").read_text())
calls_path = base / "calls.json"
calls = json.loads(calls_path.read_text()) if calls_path.exists() else []

if "--launch" in args:
    sys.exit(0)
if "--probe" in args:
    print(json.dumps(scenario.get("probe", {}).get(
        engine, {"compose_box": "div", "send_button": "x", "blocked": None})))
    sys.exit(0)

key = value("--only")
calls.append([key, engine])
calls_path.write_text(json.dumps(calls))

root = Path(project)
checkpoint = root / "state" / "run.json"
data = json.loads(checkpoint.read_text()) if checkpoint.exists() else {"failures": {}}

if key in scenario.get("hang", []):
    time.sleep(30)
reason = scenario.get("fail", {}).get(key) or scenario.get("fail_engine", {}).get(engine)
remaining = scenario.get("fail_times", {}).get(key)
if remaining is not None:
    attempts = sum(1 for call in calls if call[0] == key)
    reason = (scenario.get("fail_reason", "timeout esperando la imagen generada")
              if attempts <= remaining else None)
if reason:
    data.setdefault("failures", {})[key] = reason
    checkpoint.write_text(json.dumps(data))
    sys.exit(0)
(root / "output" / f"{key}.png").write_bytes(b"png")
