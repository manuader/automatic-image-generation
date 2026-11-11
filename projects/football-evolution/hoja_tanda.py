"""Hoja de contactos de una tanda de F7: el recorte de cada imagen sobre un gris medio.

    .venv/bin/python projects/football-evolution/hoja_tanda.py <desde> <salida.png> [<hasta>]

`<desde>` es un archivo testigo: entran los originales de `output/` más nuevos que
él (lo que salió en la tanda); con `<hasta>`, sólo los que no son más nuevos que ese
otro testigo (para cerrar una tanda cuando la siguiente ya arrancó). El recorte va sobre gris medio para que se vea si
queda blanco, sombra o halo alrededor; los fondos (`bg_*`, `tunel_*`, `AppIcon`)
van tal cual.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

proyecto = Path(__file__).resolve().parent
desde = Path(sys.argv[1]).stat().st_mtime
salida = Path(sys.argv[2])
hasta = Path(sys.argv[3]).stat().st_mtime if len(sys.argv) > 3 else float("inf")
originales = sorted(
    (p for p in (proyecto / "output").glob("*.png") if desde < p.stat().st_mtime <= hasta),
    key=lambda p: p.stat().st_mtime,
)
celda, margen, columnas = 260, 30, 8
fuente = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 15)
filas = max(1, -(-len(originales) // columnas))
hoja = Image.new("RGB", (columnas * celda, filas * (celda + margen)), (128, 128, 132))
dibujo = ImageDraw.Draw(hoja)
for i, original in enumerate(originales):
    clave = original.stem
    recorte = proyecto / "output" / "assets" / f"{clave}.png"
    a_sangre = clave.startswith(("bg_", "tunel_", "AppIcon"))
    imagen = Image.open(original if a_sangre or not recorte.exists() else recorte).convert("RGBA")
    imagen.thumbnail((celda - 10, celda - 10))
    x, y = (i % columnas) * celda, (i // columnas) * (celda + margen)
    hoja.paste(imagen, (x + (celda - imagen.width) // 2, y + margen + (celda - imagen.height) // 2), imagen)
    dibujo.text((x + 6, y + 6), clave[:34], fill="white", font=fuente)
hoja.save(salida)
print(salida, len(originales), "imágenes")
