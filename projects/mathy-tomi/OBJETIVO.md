# Objetivo — Tomi, el compañero que da pistas

**Qué:** el segundo personaje de Mathy (`~/Desktop/projects/Mathy`), compañero de
Lumi. Lumi enseña (la guía, las tarjetas, las llaves); Tomi aparece cuando el
jugador no sabe qué hacer y le ofrece una pista, de a una y sin costo. Vive en el
rincón de la actividad y en el mapa de conceptos, al lado de Lumi.

**Personaje (pedido del dueño, 2026-09-10):** un tomate redondo y brillante, rojo
con sombra más profunda abajo, corona de hojitas verdes en estrella con un tallo
corto, ojos grandes con dos brillos, cachetes rosados, sonrisa abierta con lengua,
bracitos y patitas cortas con zapatos marrones. Su objeto es **la lamparita
amarilla**: encendida cuando da una pista, apagada cuando espera. La imagen que
mostró el dueño no está en disco: el personaje está descrito en los prompts y la
héroe adjunta a Lumi (`references/lumi.png`) sólo como referencia de estilo.

**Estilo común:** el de Lumi. Contorno oscuro grueso, sombreado cel brillante,
chibi, fondo blanco liso y nada fuera del contorno (el recorte es por
conectividad).

| # | clave | qué es | dónde se usa |
|---|---|---|---|
| 01 | `tomi_hero` | saluda con la lamparita | referencia del set |
| 02 | `tomi_icon` | primer plano | el botón de pista del rincón |
| 03 | `tomi_idea` | levanta la lamparita encendida | la tarjeta de la pista |
| 04 | `tomi_point` | señala hacia el tablero | la pista que muestra dónde mirar |
| 05 | `tomi_think` | espera, lamparita apagada | ofrece una pista |
| 06 | `tomi_cheer` | festeja | cuando la pista sirvió |
| 07 | `tomi_duo` | choca los cinco con Lumi | el mapa de conceptos |

**Decisiones que no se re-discuten:**
- **El tomate nunca aparece como fruta para contar**, igual que el limón. Las
  frutas del tablero no tienen cara.
- Prompts en ASCII puro. Motor `chat-gpt`. Mathy recorta desde el original con
  `tools/art/sync_art.py`.
