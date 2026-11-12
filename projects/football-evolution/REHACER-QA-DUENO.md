# E18-F7 — lo que se rehace al final de F7 (QA del dueño, 2026-11-11 ~22:45)

Los prompts ya están corregidos (relevo 400). Al final de F7: mover cada salida a `discards/` para que vuelva a la
cola y correrla. **Las Retro van con Gemini** (ChatGPT ignora «perfectly round»).

1. Primeras Patadas, pelota bajo el brazo: primeras_patadas_idle primeras_patadas_idle__barro primeras_patadas_idle__dorada
2. Promesa del Barrio, pelota fuera del pie: promesa_barrio_idle__barro promesa_barrio_idle__retro
3. Dorsales (sólo 22, 1, 2, 5, 9): campeon_nacional_idle (24) capitan_primera_idle (23) capitan_primera_idle__barro (23);
   las Retro con 7/33/31/23/6/3/4 entran en el punto 6. El prompt de la Retro ahora repite el número de la base.
4. Rey del Potrero descalzo: rey_del_potrero_idle__retro rey_del_potrero_idle__barro rey_del_potrero_idle__dorada
5. Sexta, sin copa salvo el nueve: arquero_sexta_idle arquero_sexta_idle__retro arquero_sexta_idle__barro arquero_sexta_idle__dorada
   central_sexta_idle central_sexta_idle__retro central_sexta_idle__barro central_sexta_idle__dorada
   volante_sexta_idle volante_sexta_idle__retro volante_sexta_idle__barro volante_sexta_idle__dorada
6. Pelotas ovaladas → todas las Retro con pelota de cuero, CON GEMINI (40):
   arquero_septima_idle__retro arquero_sexta_idle__retro bebe_futbolero_idle__retro campeon_ascenso_idle__retro campeon_continental_clubes_idle__retro campeon_continental_idle__retro campeon_del_mundo_idle__retro campeon_liga_exterior_idle__retro campeon_nacional_idle__retro campeon_planetario_clubes_idle__retro capitan_primera_idle__retro capitan_seleccion_idle__retro central_septima_idle__retro central_sexta_idle__retro convocado_seleccion_idle__retro debutante_profesional_idle__retro estrella_exterior_idle__retro fichaje_europeo_idle__retro figura_ascenso_idle__retro goleador_infantil_idle__retro goleador_primera_idle__retro infantil_idle__retro jugador_reserva_idle__retro jugador_seleccion_idle__retro leyenda_eterna_idle__retro mejor_del_planeta_idle__retro nueve_septima_idle__retro nueve_sexta_idle__retro pibe_cuarta_idle__retro pibe_de_plaza_idle__retro pibe_escuelita_idle__retro pibe_novena_idle__retro pibe_octava_idle__retro pibe_quinta_idle__retro primeras_patadas_idle__retro promesa_barrio_idle__retro rey_del_potrero_idle__retro titular_ascenso_idle__retro volante_septima_idle__retro volante_sexta_idle__retro 
7. goleador_primera_idle__retro (tercera mano) — ya está en el 6.
8. Campeón planetario de clubes, copa de dos asas con estrella: campeon_planetario_clubes_idle _idle__retro _idle__barro _idle__dorada (la cara, si muestra el globo)
9. capitan_seleccion_idle__retro a tamaño normal — ya está en el 6.
10. dios_futbol_idle__aureola: aureola pegada a la cabeza.
11. Ojeador: npc_ojeador (base, está afuera) PRIMERO; después npc_ojeador_talk _action _face, que ahora adjuntan output/npc_ojeador.png.
    Decisión del relevo 400: el ojeador va sin barba (el prompt base no la pedía).

Más los 11 que quedaron afuera en las tandas 6–9 (`skipped` de supervisor.json).
