# Índice — 20 assets de Urbetrack

Uno por imagen, `NN_clave.md` → `output/<clave>.png`. El `00_` no se genera.
El sistema de marca y de dónde salió cada cosa están en `../OBJETIVO.md`.

| # | clave | qué es | referencia |
|---|---|---|---|
| 01 | `key_visual_marca` | key visual sobre el degradado | identidad |
| 02 | `patron_pines` | patrón de pines y trazas | identidad |
| 03 | `set_iconos` | 12 íconos de producto | identidad |
| 04 | `avatar_perfil` | avatar circular para redes | identidad |
| 05 | `banner_linkedin` | portada de LinkedIn 4:1 | web |
| 06 | `dashboard_hero` | UI del panel de flota | foto |
| 07 | `mockup_mobile_app` | app en la mano | foto |
| 08 | `mockup_tablet_campo` | tablet en operación | foto |
| 09 | `mapa_cobertura` | los cinco países | identidad |
| 10 | `placa_estadisticas` | las cifras de impacto | web |
| 11 | `camion_aseo_hud` | camión de aseo con telemetría | foto |
| 12 | `centro_control` | sala de control | foto |
| 13 | `flota_mineria` | flota minera monitoreada | foto |
| 14 | `flota_oil_gas` | operación oil & gas | foto |
| 15 | `ciudad_smart` | ciudad conectada desde el aire | foto |
| 16 | `tarjeta_personal` | tarjetas | identidad |
| 17 | `credencial_evento` | credencial y lanyard | identidad |
| 18 | `roll_up_feria` | roll-up 1:2.4 | identidad |
| 19 | `plantilla_slide` | slide corporativa | web |
| 20 | `merch_corporativo` | chaleco, casco y termo | identidad |

Las tres referencias son `references/board_{identidad,foto,web}.png`.

## Lo que se aprendió generando estas 20

- **Los formatos no cuadrados destaparon dos supuestos del script.** El banner de
  LinkedIn (1024x254) y el roll-up (420x1024) se generaron bien las dos veces y
  el script los tiró igual: uno lo rechazó `verify_png` y al otro ni lo dejó
  competir el filtro de candidatos, porque los dos medían contra el lado corto o
  contra el ancho. Ahora los dos miden el lado largo.
- **"Realistic corporate photography, not an illustration and not a 3D render"**
  es obligatorio en las piezas fotográficas: sin la segunda mitad el modelo
  entrega renders 3D de stock.
- **Los overlays de datos se piden "crisp and flat" sobre foto real.** Es el
  recurso del sitio y lo que separa estas piezas de una foto de banco.
