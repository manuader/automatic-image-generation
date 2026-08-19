"""Estado de una corrida: qué se generó, qué falló y dónde quedó cada cosa."""

from __future__ import annotations

import json
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


class RunCheckpoint:
    """Estado pequeño, atómico y legible para pausar/reanudar el batch."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = read_json(
            self.path,
            {"completed": [], "failures": {}, "last_success": None},
        )

    def _save(self) -> None:
        write_json(self.path, self.data)

    def record_success(self, key: str, destination: Path) -> None:
        if key not in self.data["completed"]:
            self.data["completed"].append(key)
        self.data["last_success"] = key
        self.data.setdefault("downloads", {})[key] = str(destination)
        self._save()

    def record_failure(self, key: str, reason: str) -> None:
        self.data.setdefault("failures", {})[key] = reason
        self._save()
