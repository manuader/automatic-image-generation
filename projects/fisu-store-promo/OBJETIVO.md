# Objetivo — promos de App Store de FisuEvolution

**Qué:** los cinco fondos ilustrados de las capturas promocionales de la ficha
de App Store (6.5", 1284×2778). Uno por panel del guión de
`Distribution/store-metadata.md`.

**Qué NO hace este proyecto:** el texto y el mockup del teléfono. Eso se compone
por código sobre el fondo generado acá. Dos razones medidas:

1. **El titular lleva tildes** ("Fusioná", "evolucioná", "Elegí"). Los modelos de
   imagen las rompen, y este repo ya tiene el bug documentado (el keystroke que
   pierde vocales con tilde, bug #7 de `HANDOFF-arte-gemini.md`).
2. **App Store exige 1284×2778 exactos.** Un modelo no clava esa medida.

Por eso los prompts piden **explícitamente cero texto**. Si una imagen vuelve con
letras, se descarta: no es un detalle estético, es que el panel no se puede armar.

**Estilo común:** el del juego — cartoon de línea negra gruesa, color plano
saturado, sin gradientes de aerógrafo. Cada prompt lo repite arriba de todo y
adjunta una referencia.

**Composición común:** vertical 9:16. El **tercio superior queda despejado** (ahí
va el titular) y el **centro tiene una zona limpia** donde se pega el mockup.
Eso va dicho en términos medibles en cada prompt, no como "que se vea aireado".

## Decisiones que no se re-discuten

- **`output: raw`.** No es game-asset: no se recorta nada, el fondo es el producto.
- **Cero texto en la imagen.** Ver arriba.
- **La referencia va por panel**, no siempre la misma: el fondo de callejón para
  el panel 1, el reino de dios para el 5, el Fisura para los del medio.
