# Índice — 20 assets de OUSHY Studio

Uno por imagen, `NN_clave.md` → `output/<clave>.png`. El `00_` no se genera.
El sistema de marca y de dónde salió cada referencia están en `../OBJETIVO.md`.

| # | clave | qué es | referencia |
|---|---|---|---|
| 01 | `key_visual_marca` | key visual 1:1: la U con la estrella | identidad |
| 02 | `patron_estrellas` | patrón seamless de estrellas | identidad |
| 03 | `set_iconos` | 9 íconos nuevos del sistema | trazo |
| 04 | `avatar_perfil` | avatar circular para redes | logo |
| 05 | `covers_destacados` | 6 portadas de historias destacadas | identidad |
| 06 | `post_manifiesto` | post 1:1 tipográfico, fondo naranja | web |
| 07 | `carrusel_portada` | portada de carrusel de servicios | web |
| 08 | `story_plantilla` | plantilla de historia 9:16 | web |
| 09 | `placa_proceso` | los 4 pasos sobre la línea ondulada | web |
| 10 | `tarjeta_personal` | mockup de tarjetas | logo |
| 11 | `papeleria` | membrete, sobre y carpeta | logo |
| 12 | `tote_bag` | tote de lona serigrafiado | logo |
| 13 | `remera_bordada` | buzo con el logo bordado | logo |
| 14 | `plancha_stickers` | 10 stickers troquelados | identidad |
| 15 | `set_matero` | mate y termo de marca | logo |
| 16 | `senaletica_estudio` | cartel en la recepción | logo |
| 17 | `wallpaper_mobile` | fondo de pantalla 9:16 | identidad |
| 18 | `banner_web` | banner web / OG image | web |
| 19 | `welcome_kit` | caja de bienvenida a clientes | logo |
| 20 | `mockup_presentacion` | deck en pantalla e impreso | web |

Las cuatro referencias son `references/board_{identidad,trazo,logo,web}.png`.

## Lo que se aprendió generando estas 20

- **Las estrellas hay que pedirlas "8-pointed" cada vez.** La primera imagen
  salió con estrellitas de 5 puntas alrededor de una marca correcta: el modelo
  reproduce bien el símbolo grande que ve en la referencia y default-ea al
  asterisco genérico para los adornos. Decir el número de puntas lo arregla.
- **Las piezas fotográficas y las gráficas no se mezclan solas.** Cada prompt
  cierra con "realistic photography, not an illustration" o con "flat vector":
  sin esa línea salen ilustraciones de mockups, que no sirven para nada.
- **Prohibir el texto inventado es obligatorio** cuando la pieza lleva palabras.
