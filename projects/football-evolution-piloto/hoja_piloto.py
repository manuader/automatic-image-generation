"""Hoja de contactos del piloto F6: una fila por prompt, columnas Gemini | ChatGPT."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

proyecto = Path(sys.argv[1])
salida = Path(sys.argv[2])
motores = [("Gemini", proyecto / "output-gemini"), ("ChatGPT", proyecto / "output-chat-gpt")]
orden = [p for p in sorted((proyecto / "prompts").glob("[0-9]*.md")) if not p.name.startswith("00_")]
claves = [p.stem.split("_", 1)[1] for p in orden]

celda, margen, etiqueta = 360, 16, 200
fuente = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
chica = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
ancho = etiqueta + len(motores) * (celda + margen) + margen
alto = 60 + len(claves) * (celda + margen) + margen
hoja = Image.new("RGB", (ancho, alto), "white")
d = ImageDraw.Draw(hoja)
for i, (nombre, _) in enumerate(motores):
    d.text((etiqueta + i * (celda + margen) + celda // 2 - 40, 20), nombre, fill="black", font=fuente)
for fila, clave in enumerate(claves):
    y = 60 + fila * (celda + margen)
    d.text((margen, y + celda // 2 - 20), clave.replace("__", "\n__"), fill="black", font=chica)
    for col, (_, carpeta) in enumerate(motores):
        x = etiqueta + col * (celda + margen)
        archivo = carpeta / f"{clave}.png"
        if archivo.exists():
            img = Image.open(archivo).convert("RGB")
            img.thumbnail((celda, celda))
            hoja.paste(img, (x + (celda - img.width) // 2, y + (celda - img.height) // 2))
        else:
            d.rectangle([x, y, x + celda, y + celda], outline="#bbbbbb", width=2)
            d.text((x + 40, y + celda // 2 - 10), "pendiente (sin cuota)", fill="#888888", font=chica)
hoja.save(salida)
print(salida, len(claves), "filas")
