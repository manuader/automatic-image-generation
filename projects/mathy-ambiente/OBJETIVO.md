# Objetivo — lo que se mueve en el fondo de Mathy

**Qué:** sprites sueltos (nubes, pájaros, faroles, mariposas, hojas, engranajes,
un barquito, un globo) que Mathy anima por código **sólo en la periferia** del
paisaje de cada área: la franja del cielo, los costados y las esquinas de abajo.
El centro, donde se explica, queda quieto. El pedido es del dueño (2026-09-10).

**Estilo:** el de los mundos (`../mathy-mundos`), que es otro registro que las
mascotas: pintura digital con formas limpias y degradados, crepúsculo, luz de
borde dorada. La referencia es `references/bg_found.png`, el paisaje de la huerta
achicado.

**Recorte:** por conectividad, con tolerancia 60 en `sync_art.py` (no la 110 de
las mascotas: estos colores son más claros). Por eso los prompts piden bordes
nítidos, nada casi blanco en el contorno y ningún agujero que deje ver el fondo.

| # | clave | se mueve así | dónde |
|---|---|---|---|
| 01 | `amb_cloud` | cruza el cielo, lenta | todos los mundos |
| 02 | `amb_birds` | cruza el cielo | todos |
| 03 | `amb_lantern` | sube por un costado | templo, huerta, mapa |
| 04 | `amb_butterfly` | revolotea en un costado | huerta |
| 05 | `amb_leaf` | cae por un costado, girando | huerta, río |
| 06 | `amb_gear` | gira asomado desde el borde | taller |
| 07 | `amb_boat` | se mece en una esquina de abajo | río |
| 08 | `amb_balloon` | cruza el cielo | taller, mapa |

**Decisiones que no se re-discuten:** prompts en ASCII puro; sin personajes;
sin rojo, menta ni ámbar vivo (son los colores con los que el juego dice algo).
