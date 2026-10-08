#!/usr/bin/env python3
"""Arma una hoja de contactos para revisar a ojo todo lo que generó un proyecto.

    .venv/bin/python contact_sheet.py --project fisu-evolution-v2

Deja `projects/<proyecto>/revision/index.html` con una miniatura por prompt, al
lado de la referencia que se le adjuntó (una pose junto a su canónica, una skin
junto a su personaje): así se ve de un vistazo si es el mismo personaje. Cada
tarjeta se marca como rechazada con un click, y el botón de arriba copia la
lista de claves para volver a pedirlas. Se puede regenerar a mitad de un batch:
lo que todavía no salió aparece como pendiente.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.project import Project  # noqa: E402
from core.queue import parse_asset  # noqa: E402
from generate import resolve_project  # noqa: E402

THUMB_PX = 360
FAMILIES = {"pijama": "Familia: Pijama de Ositos", "gaucho": "Familia: Gaucho",
            "dinosaurio": "Familia: Disfraz de Dinosaurio"}
GROUPS = {"npc": "Visitantes", "sp": "Especiales", "ui": "UI e íconos", "bg": "Fondos"}


def group_of(key: str) -> str:
    if "__" in key:
        return FAMILIES.get(key.split("__", 1)[1], "Familias")
    return GROUPS.get(key.split("_", 1)[0], "Otros")


def thumbnail(source: Path, destination: Path) -> bool:
    """JPEG chico aplanado sobre blanco: lo transparente pasado a JPEG sale negro."""
    from PIL import Image

    if not source.is_file():
        return False
    if destination.exists() and destination.stat().st_mtime >= source.stat().st_mtime:
        return True
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image = image.convert("RGBA")
        image.thumbnail((THUMB_PX, THUMB_PX))
        flat = Image.new("RGB", image.size, "white")
        flat.paste(image, mask=image.getchannel("A"))
        flat.save(destination, "JPEG", quality=82)
    return True


def build(project: Project) -> Path:
    out = project.root / "revision"
    thumbs = out / "thumbs"
    cards: dict[str, list[dict]] = {}
    for path in sorted(project.prompts.glob("[0-9][0-9]*.md")):
        if path.name.startswith("00_"):
            continue
        asset = parse_asset(path, project.root)
        original = project.output / f"{asset.key}.png"
        done = thumbnail(original, thumbs / f"{asset.key}.jpg")
        reference = None
        if asset.reference is not None:
            ref_name = f"ref__{asset.reference.parent.name}__{asset.reference.stem}.jpg"
            if thumbnail(asset.reference, thumbs / ref_name):
                reference = ref_name
        width = ""
        if done:
            from PIL import Image

            with Image.open(original) as image:
                width = str(image.width)
        cards.setdefault(group_of(asset.key), []).append({
            "key": asset.key, "order": asset.order, "done": done,
            "reference": reference, "width": width,
            "full": f"../output/{asset.key}.png",
        })
    out.mkdir(parents=True, exist_ok=True)
    page = out / "index.html"
    page.write_text(render(project.root.name, cards), encoding="utf-8")
    return page


def render(name: str, cards: dict[str, list[dict]]) -> str:
    total = sum(len(group) for group in cards.values())
    done = sum(card["done"] for group in cards.values() for card in group)
    sections = []
    for title, group in cards.items():
        items = []
        for card in group:
            key = html.escape(card["key"])
            if card["done"]:
                main = (f'<a href="{card["full"]}" target="_blank">'
                        f'<img loading="lazy" src="thumbs/{key}.jpg" alt="{key}"></a>')
            else:
                main = '<div class="pending">pendiente</div>'
            ref = (f'<img class="ref" loading="lazy" src="thumbs/{html.escape(card["reference"])}" '
                   f'alt="referencia" title="referencia adjunta">' if card["reference"] else "")
            meta = f'{card["order"]:03d} · {card["width"]} px' if card["width"] else f'{card["order"]:03d}'
            items.append(
                f'<figure class="card" data-key="{key}">{main}{ref}'
                f'<figcaption><span class="key">{key}</span><span class="meta">{meta}</span>'
                f'<button type="button" class="reject">Rechazar</button></figcaption></figure>'
            )
        sections.append(f'<section><h2>{html.escape(title)} <small>{len(group)}</small></h2>'
                        f'<div class="grid">{"".join(items)}</div></section>')
    return TEMPLATE.replace("{{NAME}}", html.escape(name)) \
        .replace("{{DONE}}", str(done)).replace("{{TOTAL}}", str(total)) \
        .replace("{{SECTIONS}}", "".join(sections)) \
        .replace("{{STORAGE}}", json.dumps(f"rechazadas:{name}"))


TEMPLATE = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revisión de arte</title>
<style>
:root{--bg:#f6f4ef;--card:#fff;--ink:#1d1b18;--muted:#7a746b;--line:#e3ded4;--bad:#d1372b;--ok:#2f7d4f}
@media (prefers-color-scheme:dark){:root{--bg:#161513;--card:#22201d;--ink:#eeeae2;--muted:#9a948a;--line:#34312c;--bad:#ff6b5e;--ok:#5fc48a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.4 -apple-system,system-ui,sans-serif}
header{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
header h1{font-size:17px;margin:0}header .count{color:var(--muted)}header .bad{color:var(--bad);font-weight:600}
header button{margin-left:auto;font:inherit;padding:7px 12px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
label.filter{color:var(--muted)}
main{padding:8px 16px 48px}h2{font-size:15px;margin:24px 0 10px}h2 small{color:var(--muted);font-weight:400}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.card{margin:0;background:var(--card);border:2px solid var(--line);border-radius:10px;overflow:hidden;position:relative}
.card img{display:block;width:100%;aspect-ratio:1;object-fit:contain;background:#fff}
.card .ref{position:absolute;top:6px;right:6px;width:64px;height:64px;border:1px solid var(--line);border-radius:6px;box-shadow:0 1px 4px #0003}
.pending{aspect-ratio:1;display:grid;place-items:center;color:var(--muted);font-style:italic}
figcaption{padding:8px;display:grid;grid-template-columns:1fr auto;gap:2px 8px;align-items:center}
.key{font-weight:600;word-break:break-all}.meta{grid-column:1;color:var(--muted);font-size:12px}
.reject{grid-column:2;grid-row:1/3;font:inherit;font-size:12px;padding:5px 8px;border-radius:6px;border:1px solid var(--line);background:transparent;color:var(--ink);cursor:pointer}
.card.rejected{border-color:var(--bad)}.card.rejected .reject{background:var(--bad);border-color:var(--bad);color:#fff}
body.only-rejected .card:not(.rejected){display:none}
</style></head><body>
<header><h1>Revisión · {{NAME}}</h1><span class="count">{{DONE}} de {{TOTAL}} generadas</span>
<span class="bad" id="bad">0 rechazadas</span>
<label class="filter"><input type="checkbox" id="only"> ver sólo rechazadas</label>
<button type="button" id="copy">Copiar lista de rechazadas</button></header>
<main>{{SECTIONS}}</main>
<script>
const KEY={{STORAGE}};let set=new Set();
try{set=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'))}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify([...set]))}catch(e){};document.getElementById('bad').textContent=set.size+' rechazadas'};
document.querySelectorAll('.card').forEach(c=>{const k=c.dataset.key;if(set.has(k))c.classList.add('rejected');
 c.querySelector('.reject').onclick=()=>{set.has(k)?set.delete(k):set.add(k);c.classList.toggle('rejected');save()}});
document.getElementById('only').onchange=e=>document.body.classList.toggle('only-rejected',e.target.checked);
document.getElementById('copy').onclick=async()=>{const t=[...set].join('\\n')||'(ninguna)';
 try{await navigator.clipboard.writeText(t);document.getElementById('copy').textContent='Copiado ✓'}catch(e){prompt('Copiá la lista:',t)}};
save();
</script></body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    page = build(Project.load(resolve_project(args.project)))
    print(page)


if __name__ == "__main__":
    main()
