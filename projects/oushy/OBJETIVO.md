# Objetivo — OUSHY Studio

**Qué:** 20 assets creativos de marca para **OUSHY Studio**, estudio creativo
integral (ARG, working globally). Identidad, plantillas de social, papelería,
merch y mockups de ambiente. La imagen es el producto final: modo `raw`.

**De dónde salió todo:** de https://oushy-web.vercel.app/ — nada se inventó.
Los PNG del sitio (`/assets/`) están en `references/brand/`, y las capturas de
la página viva se usaron para armar `references/board_web.png`.

**No se usa el feed de la web como referencia**: esas piezas son trabajo para
otras marcas (Haiku, JB Sport Horses, etc.), no identidad de OUSHY.

## El sistema

| | |
|---|---|
| crema (fondo) | `#F6EFE9` |
| naranja (acento) | `#EA6330` |
| naranja profundo | `#C94D1D` |
| tinta (texto) | `#54574F` |
| grises suaves | `#6D7065` · `#63665C` · `#8B8E82` |

- **Wordmark:** `oushy` en minúscula, sans geométrica redondeada (Fredoka), en
  tinta, con la `u` en naranja y la estrella encima.
- **Símbolo:** estrella de 8 puntas de trazo a mano, puntas afinadas.
- **Tipografías:** Fredoka (display), Archivo (texto), Space Mono (etiquetas en
  mayúscula con tracking), Homemade Apple (manuscrita, siempre en naranja).
- **Aire editorial:** mucho blanco, filetes finos, etiquetas `01 · SECCIÓN`,
  logos fantasma en outline como marca de agua, estrellitas sueltas.

## Las cuatro referencias

Una por prompt (el script adjunta una sola), y cada board es un collage armado
localmente con los assets reales — no costó cuota:

- `board_identidad.png` — wordmark, marca, estrellas, íconos y paleta con hex.
  Va en las piezas gráficas de identidad.
- `board_trazo.png` — los 4 íconos + la estrella gris en grande. Va en el set de
  íconos: define grosor y temblor de la línea.
- `board_logo.png` — logo limpio y grande. Va en los mockups fotográficos, que
  necesitan reproducir el logo sobre un objeto.
- `board_web.png` — 4 capturas de la página. Va en las piezas con maquetación:
  jerarquía tipográfica, etiquetas mono, script naranja.

## Decisiones que no se re-discuten

- **El prompt arranca por el sistema de marca, no por la pieza.** Lo primero que
  lee el modelo es lo que más pesa, y acá lo que tiene que sobrevivir a las 20
  imágenes es la paleta y el logo.
- **La composición se describe en porcentajes del cuadro**, no en adjetivos.
- **Las piezas fotográficas piden explícitamente "realistic photography, not an
  illustration"**; las gráficas piden "flat vector". Sin eso el modelo mezcla.
- **Se prohíbe el texto inventado** en todos los prompts: si hay letras, son
  palabras reales y escritas bien.

## Estado

**20 de 20 generadas.** Las dos últimas —`welcome_kit` y `mockup_presentacion`—
quedaron trabadas un día por la cuota de imágenes de Gemini, que se agota sin
avisar: deja el cartel «Creando tu imagen» puesto para siempre. Se completaron al
día siguiente con el mismo comando, porque la cola retoma sola por los PNG que ya
están en `output/`.
