# Videos de Higgsfield para E14 C26 — el cofre y la Ruleta

Método aprobado (memoria `videos-higgsfield`): imagen de referencia como primer y último cuadro, lo
que cambia al mínimo, lo que queda congelado nombrado, 2D plano, cámara quieta, sin manos.

**Fondo:** blanco puro (#FFFFFF) en los loops de espera y sacudida (se recortan con
`whitebg_cutout.py`, como los 135 aprobados). **Verde croma puro (#00FF00)** sólo en los dos clips con
destello (abrir el cofre y el premio de la Ruleta): los rayos, chispas y brillos blancos se perderían
recortando blanco. El verde se saca con el `matte: "verde"` que ya usa la cabina.

**Encastre con el juego:** el premio NUNCA va en el video (lo decide el juego y lo dibuja el código
encima, C4). Por eso el cofre abre a un brillo vacío y la Ruleta trae el disco liso.

| clip | ref | fondo | dur. | loop | uso |
|---|---|---|---|---|---|
| cofre_espera | ui_chest_closed | blanco | 4 s | sí | el cofre esperando el toque |
| cofre_sacude | ui_chest_closed | blanco | 1 s | no | cada toque (1.º y 2.º) |
| cofre_abre | ui_chest_closed | verde | 3 s | no | 3.er toque: abre; el premio aparece encima |
| ruleta_espera | wheel_frame + wheel_pointer | blanco | 4 s | sí | la Ruleta quieta, luces que corren |
| ruleta_premio | wheel_frame + wheel_pointer | verde | 2 s | no | al caer en el gajo: festejo del marco |
