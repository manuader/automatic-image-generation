# Objetivo — Lumi, la mascota de Mathy

**Qué:** la mascota que guía al jugador en Mathy, un juego de matemática para
cualquier edad (`~/Desktop/projects/Mathy`). Aparece en el cartel de la guía, en
las tarjetas de entrada y cierre de cada nivel, en la chuleta y en los mapas. El
plan completo está en `Mathy/docs/U-desarrollo/U4-rediseno-juego.md`.

**Personaje (desde 2026-09-10, a pedido del dueño):** Lumi es **un limón profe**:
redondo y amarillo brillante, hoja verde arriba, ojos grandes, cachetes rosados,
birrete índigo inclinado con borla dorada, bracitos cortos, patitas marrones y un
puntero de madera. La primera versión era una luciérnaga; el dueño pidió que se
pareciera a las mascotas de fruta de sus imágenes de referencia, y quedó
archivada en `archivo/luciernaga/`.

**Estilo común:** chibi, contorno oscuro grueso y parejo, formas simples, sombreado
cel brillante con un reflejo, expresión grande y alegre. Paleta fija: cuerpo
`#FFD84A` con sombra `#F2B42E`, hoja `#52D485`, cachetes `#FF9E8A`, birrete
`#2B2F6B`, borla `#FFD166`. Fondo blanco liso, y ningún brillo, halo ni chispa
fuera del contorno: el recorte es por conectividad.

**Referencias:** la héroe adjunta `references/estilo_mascota.png`, una captura
del dueño (el limón con birrete que saluda) agrandada 3 veces. Las otras dos
imágenes que mostró —el limón profe con puntero y el tomate con la lamparita— no
estaban en disco: sus rasgos (puntero, ojos cerrados de felicidad, lamparita de
la idea) están descritos en los prompts. Todas las poses adjuntan
`output/lumi_hero.png`.

| # | clave | qué es | dónde se usa |
|---|---|---|---|
| 01 | `lumi_hero` | saluda con el puntero | referencia; mapa de conceptos |
| 02 | `lumi_icon` | primer plano | avatar del cartel de la guía |
| 03 | `lumi_point` | señala con el puntero | guía, pasos de "hacelo"; el nivel que sigue |
| 04 | `lumi_cheer` | festeja | cierre sin llave |
| 05 | `lumi_think` | piensa | tarjeta de entrada |
| 06 | `lumi_wow` | la idea, con lamparita | paso que explica el resultado |
| 07 | `lumi_key` | levanta la llave | cierre con llave nueva |
| 08 | `lumi_read` | lee el cuaderno | chuleta |
| 09 | `lumi_sleep` | dormida | chuleta vacía |
| 10 | `lumi_encourage` | pulgar arriba | cuando algo no avanzó |

**Salida:** `game-asset`, pero Mathy no usa el recorte de `output/assets/`:
`Mathy/tools/art/sync_art.py` recorta desde el original (ver abajo).

**Decisiones que no se re-discuten:**
- **El limón nunca aparece como fruta para contar.** Lumi es la única fruta con
  cara; las frutas del tablero (manzana, naranja, ciruela) no tienen cara y no
  incluyen limones, para que nadie confunda a la guía con algo que se cuenta.
- Prompts en ASCII puro: el tipeo por teclas reales pierde las tildes
  (FisuEvolution, bug 7).
- **El recorte de `output/assets/` no se usa.** Gemini pinta el brillo como un
  halo crema sobre el blanco y la tolerancia de fábrica (14) lo deja pegado a la
  figura. Mathy recorta desde el original con tolerancia 110, medido en la
  luciérnaga: 40 dejaba el halo en las antenas, 70 un flequillo bajo la panza,
  110 salía limpio sin tocar el dorado. Hay que volver a medirlo con el limón,
  cuyo amarillo es más claro.
- El permiso de Accesibilidad no se comprueba con `keystroke ""`: pasa aunque
  falte. La prueba es correr una sola imagen; sin permiso falla con el error 1002
  antes de enviar, sin gastar cuota.
