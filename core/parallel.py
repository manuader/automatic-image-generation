"""Motores en paralelo: cada uno con su propia cola de tandas, sin pisarse.

    --parallel gemini:50,chat-gpt:50

quiere decir que Gemini y ChatGPT trabajan A LA VEZ. Cada motor reserva una
tanda de hasta 50 imágenes del frente de la cola, la pide entera y recién ahí
reserva la siguiente. Una imagen reservada por un motor no la pide el otro.

Lo que viaja junto se reserva junto, en una **unidad**:

- una familia de continuidad (`- **familia**: <id>` en el .md) —un NPC y su
  talk/action/face, un personaje y sus skins—;
- y una imagen cuya referencia es la salida de otra imagen pendiente
  (`output/<clave>.png`): sin esto el otro motor se quedaría esperando un PNG
  que fabrica su vecino.

Una tanda corta ANTES de una unidad que no le entra entera, como en la
rotación (`core/rotation.py`); sólo una unidad más grande que la tanda entera
la excede.

Este módulo es puro —no abre navegadores ni procesos—: decide qué reserva cada
motor y nada más. El que corre los motores es `supervisor.py`.
"""

from __future__ import annotations

from core.queue import Asset
from core.rotation import Turn, family_order, fits, parse_rotation


def parse_parallel(spec: str, known_engines: list[str] | None = None) -> list[Turn]:
    """`gemini:50,chat-gpt:50` → un carril por motor. Un motor repetido sería
    dos carriles manejando el mismo Chrome, que es justo lo que no se puede."""
    try:
        turns = parse_rotation(spec, known_engines)
    except ValueError as error:
        raise ValueError(str(error).replace("--rotate", "--parallel")) from None
    engines = [turn.engine for turn in turns]
    if len(set(engines)) != len(engines):
        raise ValueError("--parallel lleva cada motor una sola vez: cada uno maneja "
                         "su propio Chrome")
    return turns


def units(queue: list[Asset]) -> list[list[Asset]]:
    """La cola partida en lo que tiene que ir al mismo motor, en orden.

    Cada unidad queda en el lugar de su primer miembro; adentro, el orden es el
    de la cola, así que la base de un NPC sale antes que su talk."""
    ordered = family_order(queue)
    keys = {asset.key for asset in ordered}
    parent = {asset.key: asset.key for asset in ordered}

    def root(key: str) -> str:
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    def join(a: str, b: str) -> None:
        parent[root(b)] = root(a)

    first_of_family: dict[str, str] = {}
    for asset in ordered:
        if asset.family is not None:
            join(first_of_family.setdefault(asset.family, asset.key), asset.key)
        reference = asset.reference
        if reference is not None and reference.parent.name == "output" \
                and reference.stem in keys:
            join(reference.stem, asset.key)

    grouped: dict[str, list[Asset]] = {}
    for asset in ordered:
        grouped.setdefault(root(asset.key), []).append(asset)
    return list(grouped.values())


def claim_batch(queue: list[Asset], size: int, taken: set[str]) -> list[list[str]]:
    """La próxima tanda de un motor: unidades del frente de la cola que nadie
    reservó, hasta `size` imágenes, sin partir ninguna. Devuelve las claves por
    unidad; vacío si no queda nada libre."""
    batch: list[list[str]] = []
    count = 0
    for unit in units(queue):
        unit_keys = [asset.key for asset in unit]
        if any(key in taken for key in unit_keys):
            continue
        if not fits(count, len(unit_keys), size):
            break
        batch.append(unit_keys)
        count += len(unit_keys)
    return batch
