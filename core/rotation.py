"""Rotación de motores: tandas alternadas para que ningún sitio vea un batch entero.

    --rotate gemini:50,chat-gpt:50

quiere decir 50 imágenes **enviadas** con Gemini, 50 con ChatGPT, 50 con Gemini…
hasta vaciar la cola. Lo que cuenta es lo enviado y no lo logrado: el sitio ve
el pedido aunque la imagen no salga, y el ritmo que hay que cuidar es el suyo.

Las familias de continuidad (`- **familia**: <id>` en el .md) no se parten: una
tanda corta ANTES de una familia que no le entra entera, nunca en el medio. La
tanda queda más corta y la familia arranca la siguiente; sólo una familia más
grande que la tanda entera la excede, porque no hay otra forma de no partirla.

Este módulo es puro —no abre navegadores ni procesos—: lo usan el supervisor
para decidir y `--dry-run` para mostrar el plan, y por eso los dos coinciden.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.queue import Asset


@dataclass(frozen=True)
class Turn:
    """Un turno de la rotación: qué motor y cuántas imágenes enviadas."""

    engine: str
    size: int


@dataclass
class Batch:
    """Una tanda del plan: un motor y las imágenes que le tocan, en orden."""

    engine: str
    size: int
    assets: list[Asset] = field(default_factory=list)
    #: Cuántas de esta tanda ya se enviaron antes de este plan (corrida retomada).
    already_sent: int = 0

    @property
    def families(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for asset in self.assets:
            if asset.family:
                counts[asset.family] = counts.get(asset.family, 0) + 1
        return counts


def parse_rotation(spec: str, known_engines: list[str] | None = None) -> list[Turn]:
    """`gemini:50,chat-gpt:50` → dos turnos. Falla fuerte ante algo mal escrito:
    una rotación mal leída manda todo a un solo motor, que es justo lo que se
    quiere evitar."""
    turns = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        engine, _, size = chunk.partition(":")
        engine = engine.strip()
        if not engine or not size.strip().isdigit() or int(size) <= 0:
            raise ValueError(f"--rotate espera motor:cantidad,…, no {chunk!r}")
        if known_engines is not None and engine not in known_engines:
            raise ValueError(f"motor desconocido en --rotate: {engine!r} "
                             f"(los que hay: {', '.join(known_engines)})")
        turns.append(Turn(engine, int(size)))
    if len(turns) < 2:
        raise ValueError("--rotate necesita al menos dos turnos para alternar")
    return turns


def family_order(assets: list[Asset]) -> list[Asset]:
    """El orden de la cola, con cada familia junta en el lugar de su primer
    miembro. Si los miembros ya son consecutivos —lo normal— no cambia nada."""
    ordered: list[Asset] = []
    placed: set[str] = set()
    for asset in assets:
        if asset.family is None:
            ordered.append(asset)
        elif asset.family not in placed:
            placed.add(asset.family)
            ordered.extend(other for other in assets if other.family == asset.family)
    return ordered


def unit_size(asset: Asset, pending: list[Asset]) -> int:
    """Cuántas imágenes van juntas con ésta: su familia pendiente, o ella sola."""
    if asset.family is None:
        return 1
    return sum(1 for other in pending if other.family == asset.family)


def fits(sent: int, unit: int, size: int) -> bool:
    """¿Esta unidad entra en la tanda en curso sin pasarse ni partirse?

    Una tanda vacía acepta cualquier unidad: es el único caso en que una familia
    más grande que la tanda la excede."""
    return sent == 0 or sent + unit <= size


def plan(assets: list[Asset], turns: list[Turn], slot: int = 0,
         sent: int = 0) -> list[Batch]:
    """Las tandas que saldrían de esta cola si ningún motor se quedara sin cuota.

    `slot` y `sent` son el turno en curso y lo que ya se envió en él, para que
    el plan de una corrida retomada siga desde donde quedó la anterior."""
    ordered = family_order(assets)
    batches: list[Batch] = []
    slot %= len(turns)
    current = Batch(turns[slot].engine, turns[slot].size, already_sent=sent)
    count = sent
    index = 0
    while index < len(ordered):
        asset = ordered[index]
        unit = unit_size(asset, ordered)
        if not fits(count, unit, current.size):
            batches.append(current)
            slot = (slot + 1) % len(turns)
            current = Batch(turns[slot].engine, turns[slot].size)
            count = 0
        current.assets.extend(ordered[index:index + unit])
        count += unit
        index += unit
    if current.assets:
        batches.append(current)
    return batches


def describe(batches: list[Batch], turns: list[Turn]) -> str:
    """El plan en texto, para `--dry-run`."""
    spec = " → ".join(f"{turn.engine}:{turn.size}" for turn in turns)
    total = sum(len(batch.assets) for batch in batches)
    lines = [f"Rotación {spec}: {total} pendientes en {len(batches)} tandas"]
    for number, batch in enumerate(batches, 1):
        families = ", ".join(f"{name} ({count})" for name, count in batch.families.items())
        loose = sum(1 for asset in batch.assets if asset.family is None)
        detail = []
        if families:
            detail.append(f"familias: {families}")
        if loose:
            detail.append(f"sueltas: {loose}")
        if batch.already_sent:
            detail.append(f"ya enviadas antes: {batch.already_sent}")
        lines.append(f"  tanda {number:>3}  {batch.engine:<10} {len(batch.assets):>3} "
                     f"de {batch.size}  {' · '.join(detail)}")
        first, last = batch.assets[0], batch.assets[-1]
        lines.append(f"             {first.order:02d}_{first.key} … {last.order:02d}_{last.key}")
    lines.append("Sin cuota, un motor cede su turno al siguiente: el plan real "
                 "puede correrse, el orden de la cola no.")
    return "\n".join(lines)
