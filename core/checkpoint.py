"""Estado de una corrida: qué se generó, qué falló y dónde quedó cada cosa."""

from __future__ import annotations

import fcntl
import json
from contextlib import contextmanager
from pathlib import Path


def read_json(path: Path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data) -> None:
    """Escritura atómica: un checkpoint a medio escribir es un checkpoint perdido."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    tmp.replace(path)


@contextmanager
def locked(path: Path):
    """Candado de archivo para un JSON que escriben varios procesos a la vez.

    Con `--parallel` corren dos `generate.py` al mismo tiempo, uno por motor, y
    los dos anotan en el mismo `run.json`. Sin candado cada uno reescribe el
    archivo entero con lo que leyó al arrancar, y el motivo del fallo que anotó
    el otro se pierde: el supervisor lo lee como «terminó sin anotar motivo»."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_name(path.name + ".lock"), "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def update_json(path: Path, mutate, default=None):
    """Lee, cambia y escribe bajo el candado: lo de los otros procesos queda."""
    with locked(path):
        data = read_json(path, default)
        mutate(data)
        write_json(path, data)
        return data


class RunCheckpoint:
    """Estado pequeño, atómico y legible para pausar/reanudar el batch."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = read_json(self.path, self.empty())

    @staticmethod
    def empty() -> dict:
        return {"completed": [], "failures": {}, "last_success": None}

    def _update(self, mutate) -> None:
        # Se relee bajo el candado en cada escritura: otro generador puede haber
        # anotado algo desde que éste arrancó (ver `locked`).
        self.data = update_json(self.path, mutate, self.empty())

    def record_success(self, key: str, destination: Path) -> None:
        def mutate(data: dict) -> None:
            completed = data.setdefault("completed", [])
            if key not in completed:
                completed.append(key)
            data["last_success"] = key
            data.setdefault("downloads", {})[key] = str(destination)
        self._update(mutate)

    def record_failure(self, key: str, reason: str) -> None:
        self._update(lambda data: data.setdefault("failures", {}).__setitem__(key, reason))
