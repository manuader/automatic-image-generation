# Indice - FisuEvolution 2.0 (epica E8)

**El runner lee la carpeta, no esta tabla.** La tabla es para ver el orden y el
encadenamiento de un vistazo. Todos los numeros tienen tres cifras, asi el orden
alfabetico de los archivos (que es el que usa la cola) coincide con el numerico.

## Orden

| Tramo | Que | Cuantos |
|---|---|---|
| 001-005 | **Piloto**: 2 visitantes canonicos, 1 pose, 1 skin de familia y 1 fondo | 5 |
| 010-098 | Visitantes, especiales, Paquete, Colchon, Ruleta, tienda de ORO, Album y fondos | 89 |
| 100-227 | Familias: Pijama de Ositos, Gaucho y Disfraz de Dinosaurio (43 c/u) | 128 |

Por grupo (piloto incluido): Visitantes nuevos 32, Familias de skins 129, Fondos 10, Especiales existentes 20, Paquete de la Aduana 5, El Colchon 3, Ruleta 6, Tienda de ORO 14, Album de especiales 3.
Total: 222.

## Encadenamiento

- La **canonica** de cada visitante nuevo adjunta `references/fisura.png` (solo estilo).
  Su pose hablando, su pose de accion y su cara adjuntan `output/npc_<nombre>.png`, que
  genero el prompt anterior. Por eso la canonica va siempre primero.
- Los **especiales** adjuntan su PNG de la v1 (`references/chars/sp_<id>.png`).
- Cada **skin de familia** adjunta el PNG original de SU personaje
  (`references/chars/<tipo>.png`), nunca el Fisura.
- Cada **fondo** adjunta su original (`references/bg/<clave>.png`).
- Los **iconos** adjuntan `references/style/icon.png` (el trofeo del menu) solo como guia de
  estilo; las variantes del Paquete, el Colchon y la Ruleta adjuntan su pieza base desde
  `output/`.

## Frases fijas

Los cuerpos enteros (canonicas, poses y skins) arrancan y cierran con las frases del
Anexo B del plan. Las caras arrancan igual, pero cierran con el cierre de cara de las 43
caras de la v1, porque "Full body standing character" contradice un primer plano. Iconos
y fondos usan sus propias frases fijas (las de la v1), porque las del Anexo B piden un
personaje de cuerpo entero.

## Tabla

| NN | clave | grupo | referencia | |
|---|---|---|---|---|
| 001 | `npc_comisario` | Visitantes nuevos | `references/fisura.png` | PILOTO |
| 002 | `npc_vecina` | Visitantes nuevos | `references/fisura.png` | PILOTO |
| 003 | `npc_comisario_talk` | Visitantes nuevos | `output/npc_comisario.png` | PILOTO |
| 004 | `homeless__dinosaurio` | Familias de skins | `references/chars/homeless.png` | PILOTO |
| 005 | `bg_alley` | Fondos | `references/bg/bg_alley.png` | PILOTO |
| 010 | `npc_comisario_action` | Visitantes nuevos | `output/npc_comisario.png` |  |
| 011 | `npc_comisario_face` | Visitantes nuevos | `output/npc_comisario.png` |  |
| 012 | `npc_sindicalista` | Visitantes nuevos | `references/fisura.png` |  |
| 013 | `npc_sindicalista_talk` | Visitantes nuevos | `output/npc_sindicalista.png` |  |
| 014 | `npc_sindicalista_action` | Visitantes nuevos | `output/npc_sindicalista.png` |  |
| 015 | `npc_sindicalista_face` | Visitantes nuevos | `output/npc_sindicalista.png` |  |
| 016 | `npc_turista` | Visitantes nuevos | `references/fisura.png` |  |
| 017 | `npc_turista_talk` | Visitantes nuevos | `output/npc_turista.png` |  |
| 018 | `npc_turista_action` | Visitantes nuevos | `output/npc_turista.png` |  |
| 019 | `npc_turista_face` | Visitantes nuevos | `output/npc_turista.png` |  |
| 020 | `npc_puntero` | Visitantes nuevos | `references/fisura.png` |  |
| 021 | `npc_puntero_talk` | Visitantes nuevos | `output/npc_puntero.png` |  |
| 022 | `npc_puntero_action` | Visitantes nuevos | `output/npc_puntero.png` |  |
| 023 | `npc_puntero_face` | Visitantes nuevos | `output/npc_puntero.png` |  |
| 024 | `npc_ministro` | Visitantes nuevos | `references/fisura.png` |  |
| 025 | `npc_ministro_talk` | Visitantes nuevos | `output/npc_ministro.png` |  |
| 026 | `npc_ministro_action` | Visitantes nuevos | `output/npc_ministro.png` |  |
| 027 | `npc_ministro_face` | Visitantes nuevos | `output/npc_ministro.png` |  |
| 028 | `npc_vecina_talk` | Visitantes nuevos | `output/npc_vecina.png` |  |
| 029 | `npc_vecina_action` | Visitantes nuevos | `output/npc_vecina.png` |  |
| 030 | `npc_vecina_face` | Visitantes nuevos | `output/npc_vecina.png` |  |
| 031 | `npc_vendedor` | Visitantes nuevos | `references/fisura.png` |  |
| 032 | `npc_vendedor_talk` | Visitantes nuevos | `output/npc_vendedor.png` |  |
| 033 | `npc_vendedor_action` | Visitantes nuevos | `output/npc_vendedor.png` |  |
| 034 | `npc_vendedor_face` | Visitantes nuevos | `output/npc_vendedor.png` |  |
| 035 | `npc_conductor` | Visitantes nuevos | `references/fisura.png` |  |
| 036 | `npc_conductor_talk` | Visitantes nuevos | `output/npc_conductor.png` |  |
| 037 | `npc_conductor_action` | Visitantes nuevos | `output/npc_conductor.png` |  |
| 038 | `npc_conductor_face` | Visitantes nuevos | `output/npc_conductor.png` |  |
| 039 | `sp_cryptobro_talk` | Especiales existentes | `references/chars/sp_cryptobro.png` |  |
| 040 | `sp_cryptobro_face` | Especiales existentes | `references/chars/sp_cryptobro.png` |  |
| 041 | `sp_demonio_arca_talk` | Especiales existentes | `references/chars/sp_demonio_arca.png` |  |
| 042 | `sp_demonio_arca_face` | Especiales existentes | `references/chars/sp_demonio_arca.png` |  |
| 043 | `sp_contador_dios_talk` | Especiales existentes | `references/chars/sp_contador_dios.png` |  |
| 044 | `sp_contador_dios_face` | Especiales existentes | `references/chars/sp_contador_dios.png` |  |
| 045 | `sp_zombie_ceo_talk` | Especiales existentes | `references/chars/sp_zombie_ceo.png` |  |
| 046 | `sp_zombie_ceo_face` | Especiales existentes | `references/chars/sp_zombie_ceo.png` |  |
| 047 | `sp_lizard_talk` | Especiales existentes | `references/chars/sp_lizard.png` |  |
| 048 | `sp_lizard_face` | Especiales existentes | `references/chars/sp_lizard.png` |  |
| 049 | `sp_alien_investor_talk` | Especiales existentes | `references/chars/sp_alien_investor.png` |  |
| 050 | `sp_alien_investor_face` | Especiales existentes | `references/chars/sp_alien_investor.png` |  |
| 051 | `sp_bug_simulacion_talk` | Especiales existentes | `references/chars/sp_bug_simulacion.png` |  |
| 052 | `sp_bug_simulacion_face` | Especiales existentes | `references/chars/sp_bug_simulacion.png` |  |
| 053 | `sp_arbolito_talk` | Especiales existentes | `references/chars/sp_arbolito.png` |  |
| 054 | `sp_arbolito_face` | Especiales existentes | `references/chars/sp_arbolito.png` |  |
| 055 | `sp_coach_talk` | Especiales existentes | `references/chars/sp_coach.png` |  |
| 056 | `sp_coach_face` | Especiales existentes | `references/chars/sp_coach.png` |  |
| 057 | `sp_influencer_talk` | Especiales existentes | `references/chars/sp_influencer.png` |  |
| 058 | `sp_influencer_face` | Especiales existentes | `references/chars/sp_influencer.png` |  |
| 059 | `ui_package_closed` | Paquete de la Aduana | `references/style/icon.png` |  |
| 060 | `ui_package_opening` | Paquete de la Aduana | `output/ui_package_closed.png` |  |
| 061 | `ui_package_open` | Paquete de la Aduana | `output/ui_package_closed.png` |  |
| 062 | `ui_package_lid` | Paquete de la Aduana | `output/ui_package_closed.png` |  |
| 063 | `ui_package_full` | Paquete de la Aduana | `references/style/icon.png` |  |
| 064 | `ui_mattress_closed` | El Colchon | `references/style/icon.png` |  |
| 065 | `ui_mattress_open` | El Colchon | `output/ui_mattress_closed.png` |  |
| 066 | `ui_mattress_icon` | El Colchon | `output/ui_mattress_closed.png` |  |
| 067 | `ui_wheel_button` | Ruleta | `references/style/icon.png` |  |
| 068 | `ui_wheel_frame` | Ruleta | `output/ui_wheel_button.png` |  |
| 069 | `ui_wheel_pointer` | Ruleta | `output/ui_wheel_button.png` |  |
| 070 | `ui_wheel_hub` | Ruleta | `output/ui_wheel_button.png` |  |
| 071 | `ui_wheel_seg_jackpot` | Ruleta | `references/style/icon.png` |  |
| 072 | `ui_wheel_seg_respin` | Ruleta | `references/style/icon.png` |  |
| 073 | `ui_oro_income_boost` | Tienda de ORO | `references/style/icon.png` |  |
| 074 | `ui_oro_package_rain` | Tienda de ORO | `references/style/icon.png` |  |
| 075 | `ui_oro_autotap` | Tienda de ORO | `references/style/icon.png` |  |
| 076 | `ui_oro_time_skip` | Tienda de ORO | `references/style/icon.png` |  |
| 077 | `ui_oro_time_skip_big` | Tienda de ORO | `references/style/icon.png` |  |
| 078 | `ui_oro_offline_boost` | Tienda de ORO | `references/style/icon.png` |  |
| 079 | `ui_oro_daily_boost` | Tienda de ORO | `references/style/icon.png` |  |
| 080 | `ui_oro_skip_cooldown` | Tienda de ORO | `references/style/icon.png` |  |
| 081 | `ui_oro_extra_slots` | Tienda de ORO | `references/style/icon.png` |  |
| 082 | `ui_oro_merge_all` | Tienda de ORO | `references/style/icon.png` |  |
| 083 | `ui_oro_better_supplier` | Tienda de ORO | `references/style/icon.png` |  |
| 084 | `ui_oro_extra_spins` | Tienda de ORO | `references/style/icon.png` |  |
| 085 | `ui_oro_skin_effect` | Tienda de ORO | `references/style/icon.png` |  |
| 086 | `ui_oro_skin_family` | Tienda de ORO | `references/style/icon.png` |  |
| 087 | `ui_album_card_frame` | Album de especiales | `references/style/icon.png` |  |
| 088 | `ui_album_locked` | Album de especiales | `references/style/icon.png` |  |
| 089 | `ui_menu_album` | Album de especiales | `references/style/icon.png` |  |
| 090 | `bg_urban` | Fondos | `references/bg/bg_urban.png` |  |
| 091 | `bg_corporate` | Fondos | `references/bg/bg_corporate.png` |  |
| 092 | `bg_luxury` | Fondos | `references/bg/bg_luxury.png` |  |
| 093 | `bg_island` | Fondos | `references/bg/bg_island.png` |  |
| 094 | `bg_moon` | Fondos | `references/bg/bg_moon.png` |  |
| 095 | `bg_mars` | Fondos | `references/bg/bg_mars.png` |  |
| 096 | `bg_solar` | Fondos | `references/bg/bg_solar.png` |  |
| 097 | `bg_galaxy` | Fondos | `references/bg/bg_galaxy.png` |  |
| 098 | `bg_god_realm` | Fondos | `references/bg/bg_god_realm.png` |  |
| 100 | `homeless__pijama` | Familias de skins | `references/chars/homeless.png` |  |
| 101 | `trapito__pijama` | Familias de skins | `references/chars/trapito.png` |  |
| 102 | `limpiavidrios__pijama` | Familias de skins | `references/chars/limpiavidrios.png` |  |
| 103 | `cartonero__pijama` | Familias de skins | `references/chars/cartonero.png` |  |
| 104 | `mantero__pijama` | Familias de skins | `references/chars/mantero.png` |  |
| 105 | `repartidor__pijama` | Familias de skins | `references/chars/repartidor.png` |  |
| 106 | `chofer_app__pijama` | Familias de skins | `references/chars/chofer_app.png` |  |
| 107 | `fast_food__pijama` | Familias de skins | `references/chars/fast_food.png` |  |
| 108 | `oficinista__pijama` | Familias de skins | `references/chars/oficinista.png` |  |
| 109 | `administrativo__pijama` | Familias de skins | `references/chars/administrativo.png` |  |
| 110 | `junior_programmer__pijama` | Familias de skins | `references/chars/junior_programmer.png` |  |
| 111 | `junior_architect__pijama` | Familias de skins | `references/chars/junior_architect.png` |  |
| 112 | `junior_doctor__pijama` | Familias de skins | `references/chars/junior_doctor.png` |  |
| 113 | `junior_lawyer__pijama` | Familias de skins | `references/chars/junior_lawyer.png` |  |
| 114 | `senior_programmer__pijama` | Familias de skins | `references/chars/senior_programmer.png` |  |
| 115 | `senior_architect__pijama` | Familias de skins | `references/chars/senior_architect.png` |  |
| 116 | `senior_doctor__pijama` | Familias de skins | `references/chars/senior_doctor.png` |  |
| 117 | `senior_lawyer__pijama` | Familias de skins | `references/chars/senior_lawyer.png` |  |
| 118 | `director__pijama` | Familias de skins | `references/chars/director.png` |  |
| 119 | `fundador_startup__pijama` | Familias de skins | `references/chars/fundador_startup.png` |  |
| 120 | `dueno_pyme__pijama` | Familias de skins | `references/chars/dueno_pyme.png` |  |
| 121 | `emprendedor__pijama` | Familias de skins | `references/chars/emprendedor.png` |  |
| 122 | `ceo__pijama` | Familias de skins | `references/chars/ceo.png` |  |
| 123 | `millonario__pijama` | Familias de skins | `references/chars/millonario.png` |  |
| 124 | `multimillonario__pijama` | Familias de skins | `references/chars/multimillonario.png` |  |
| 125 | `rey_ladrillo__pijama` | Familias de skins | `references/chars/rey_ladrillo.png` |  |
| 126 | `magnate_petrolero__pijama` | Familias de skins | `references/chars/magnate_petrolero.png` |  |
| 127 | `space_billionaire__pijama` | Familias de skins | `references/chars/space_billionaire.png` |  |
| 128 | `trillonario__pijama` | Familias de skins | `references/chars/trillonario.png` |  |
| 129 | `dueno_luna__pijama` | Familias de skins | `references/chars/dueno_luna.png` |  |
| 130 | `dueno_marte__pijama` | Familias de skins | `references/chars/dueno_marte.png` |  |
| 131 | `rey_asteroides__pijama` | Familias de skins | `references/chars/rey_asteroides.png` |  |
| 132 | `magnate_solar__pijama` | Familias de skins | `references/chars/magnate_solar.png` |  |
| 133 | `fondo_buitre__pijama` | Familias de skins | `references/chars/fondo_buitre.png` |  |
| 134 | `rentista_soles__pijama` | Familias de skins | `references/chars/rentista_soles.png` |  |
| 135 | `estanciero_estelar__pijama` | Familias de skins | `references/chars/estanciero_estelar.png` |  |
| 136 | `senor_galaxia__pijama` | Familias de skins | `references/chars/senor_galaxia.png` |  |
| 137 | `coleccionista_galaxias__pijama` | Familias de skins | `references/chars/coleccionista_galaxias.png` |  |
| 138 | `emperador_cosmico__pijama` | Familias de skins | `references/chars/emperador_cosmico.png` |  |
| 139 | `ser_ascendido__pijama` | Familias de skins | `references/chars/ser_ascendido.png` |  |
| 140 | `semidios__pijama` | Familias de skins | `references/chars/semidios.png` |  |
| 141 | `deidad__pijama` | Familias de skins | `references/chars/deidad.png` |  |
| 142 | `god__pijama` | Familias de skins | `references/chars/god.png` |  |
| 143 | `homeless__gaucho` | Familias de skins | `references/chars/homeless.png` |  |
| 144 | `trapito__gaucho` | Familias de skins | `references/chars/trapito.png` |  |
| 145 | `limpiavidrios__gaucho` | Familias de skins | `references/chars/limpiavidrios.png` |  |
| 146 | `cartonero__gaucho` | Familias de skins | `references/chars/cartonero.png` |  |
| 147 | `mantero__gaucho` | Familias de skins | `references/chars/mantero.png` |  |
| 148 | `repartidor__gaucho` | Familias de skins | `references/chars/repartidor.png` |  |
| 149 | `chofer_app__gaucho` | Familias de skins | `references/chars/chofer_app.png` |  |
| 150 | `fast_food__gaucho` | Familias de skins | `references/chars/fast_food.png` |  |
| 151 | `oficinista__gaucho` | Familias de skins | `references/chars/oficinista.png` |  |
| 152 | `administrativo__gaucho` | Familias de skins | `references/chars/administrativo.png` |  |
| 153 | `junior_programmer__gaucho` | Familias de skins | `references/chars/junior_programmer.png` |  |
| 154 | `junior_architect__gaucho` | Familias de skins | `references/chars/junior_architect.png` |  |
| 155 | `junior_doctor__gaucho` | Familias de skins | `references/chars/junior_doctor.png` |  |
| 156 | `junior_lawyer__gaucho` | Familias de skins | `references/chars/junior_lawyer.png` |  |
| 157 | `senior_programmer__gaucho` | Familias de skins | `references/chars/senior_programmer.png` |  |
| 158 | `senior_architect__gaucho` | Familias de skins | `references/chars/senior_architect.png` |  |
| 159 | `senior_doctor__gaucho` | Familias de skins | `references/chars/senior_doctor.png` |  |
| 160 | `senior_lawyer__gaucho` | Familias de skins | `references/chars/senior_lawyer.png` |  |
| 161 | `director__gaucho` | Familias de skins | `references/chars/director.png` |  |
| 162 | `fundador_startup__gaucho` | Familias de skins | `references/chars/fundador_startup.png` |  |
| 163 | `dueno_pyme__gaucho` | Familias de skins | `references/chars/dueno_pyme.png` |  |
| 164 | `emprendedor__gaucho` | Familias de skins | `references/chars/emprendedor.png` |  |
| 165 | `ceo__gaucho` | Familias de skins | `references/chars/ceo.png` |  |
| 166 | `millonario__gaucho` | Familias de skins | `references/chars/millonario.png` |  |
| 167 | `multimillonario__gaucho` | Familias de skins | `references/chars/multimillonario.png` |  |
| 168 | `rey_ladrillo__gaucho` | Familias de skins | `references/chars/rey_ladrillo.png` |  |
| 169 | `magnate_petrolero__gaucho` | Familias de skins | `references/chars/magnate_petrolero.png` |  |
| 170 | `space_billionaire__gaucho` | Familias de skins | `references/chars/space_billionaire.png` |  |
| 171 | `trillonario__gaucho` | Familias de skins | `references/chars/trillonario.png` |  |
| 172 | `dueno_luna__gaucho` | Familias de skins | `references/chars/dueno_luna.png` |  |
| 173 | `dueno_marte__gaucho` | Familias de skins | `references/chars/dueno_marte.png` |  |
| 174 | `rey_asteroides__gaucho` | Familias de skins | `references/chars/rey_asteroides.png` |  |
| 175 | `magnate_solar__gaucho` | Familias de skins | `references/chars/magnate_solar.png` |  |
| 176 | `fondo_buitre__gaucho` | Familias de skins | `references/chars/fondo_buitre.png` |  |
| 177 | `rentista_soles__gaucho` | Familias de skins | `references/chars/rentista_soles.png` |  |
| 178 | `estanciero_estelar__gaucho` | Familias de skins | `references/chars/estanciero_estelar.png` |  |
| 179 | `senor_galaxia__gaucho` | Familias de skins | `references/chars/senor_galaxia.png` |  |
| 180 | `coleccionista_galaxias__gaucho` | Familias de skins | `references/chars/coleccionista_galaxias.png` |  |
| 181 | `emperador_cosmico__gaucho` | Familias de skins | `references/chars/emperador_cosmico.png` |  |
| 182 | `ser_ascendido__gaucho` | Familias de skins | `references/chars/ser_ascendido.png` |  |
| 183 | `semidios__gaucho` | Familias de skins | `references/chars/semidios.png` |  |
| 184 | `deidad__gaucho` | Familias de skins | `references/chars/deidad.png` |  |
| 185 | `god__gaucho` | Familias de skins | `references/chars/god.png` |  |
| 186 | `trapito__dinosaurio` | Familias de skins | `references/chars/trapito.png` |  |
| 187 | `limpiavidrios__dinosaurio` | Familias de skins | `references/chars/limpiavidrios.png` |  |
| 188 | `cartonero__dinosaurio` | Familias de skins | `references/chars/cartonero.png` |  |
| 189 | `mantero__dinosaurio` | Familias de skins | `references/chars/mantero.png` |  |
| 190 | `repartidor__dinosaurio` | Familias de skins | `references/chars/repartidor.png` |  |
| 191 | `chofer_app__dinosaurio` | Familias de skins | `references/chars/chofer_app.png` |  |
| 192 | `fast_food__dinosaurio` | Familias de skins | `references/chars/fast_food.png` |  |
| 193 | `oficinista__dinosaurio` | Familias de skins | `references/chars/oficinista.png` |  |
| 194 | `administrativo__dinosaurio` | Familias de skins | `references/chars/administrativo.png` |  |
| 195 | `junior_programmer__dinosaurio` | Familias de skins | `references/chars/junior_programmer.png` |  |
| 196 | `junior_architect__dinosaurio` | Familias de skins | `references/chars/junior_architect.png` |  |
| 197 | `junior_doctor__dinosaurio` | Familias de skins | `references/chars/junior_doctor.png` |  |
| 198 | `junior_lawyer__dinosaurio` | Familias de skins | `references/chars/junior_lawyer.png` |  |
| 199 | `senior_programmer__dinosaurio` | Familias de skins | `references/chars/senior_programmer.png` |  |
| 200 | `senior_architect__dinosaurio` | Familias de skins | `references/chars/senior_architect.png` |  |
| 201 | `senior_doctor__dinosaurio` | Familias de skins | `references/chars/senior_doctor.png` |  |
| 202 | `senior_lawyer__dinosaurio` | Familias de skins | `references/chars/senior_lawyer.png` |  |
| 203 | `director__dinosaurio` | Familias de skins | `references/chars/director.png` |  |
| 204 | `fundador_startup__dinosaurio` | Familias de skins | `references/chars/fundador_startup.png` |  |
| 205 | `dueno_pyme__dinosaurio` | Familias de skins | `references/chars/dueno_pyme.png` |  |
| 206 | `emprendedor__dinosaurio` | Familias de skins | `references/chars/emprendedor.png` |  |
| 207 | `ceo__dinosaurio` | Familias de skins | `references/chars/ceo.png` |  |
| 208 | `millonario__dinosaurio` | Familias de skins | `references/chars/millonario.png` |  |
| 209 | `multimillonario__dinosaurio` | Familias de skins | `references/chars/multimillonario.png` |  |
| 210 | `rey_ladrillo__dinosaurio` | Familias de skins | `references/chars/rey_ladrillo.png` |  |
| 211 | `magnate_petrolero__dinosaurio` | Familias de skins | `references/chars/magnate_petrolero.png` |  |
| 212 | `space_billionaire__dinosaurio` | Familias de skins | `references/chars/space_billionaire.png` |  |
| 213 | `trillonario__dinosaurio` | Familias de skins | `references/chars/trillonario.png` |  |
| 214 | `dueno_luna__dinosaurio` | Familias de skins | `references/chars/dueno_luna.png` |  |
| 215 | `dueno_marte__dinosaurio` | Familias de skins | `references/chars/dueno_marte.png` |  |
| 216 | `rey_asteroides__dinosaurio` | Familias de skins | `references/chars/rey_asteroides.png` |  |
| 217 | `magnate_solar__dinosaurio` | Familias de skins | `references/chars/magnate_solar.png` |  |
| 218 | `fondo_buitre__dinosaurio` | Familias de skins | `references/chars/fondo_buitre.png` |  |
| 219 | `rentista_soles__dinosaurio` | Familias de skins | `references/chars/rentista_soles.png` |  |
| 220 | `estanciero_estelar__dinosaurio` | Familias de skins | `references/chars/estanciero_estelar.png` |  |
| 221 | `senor_galaxia__dinosaurio` | Familias de skins | `references/chars/senor_galaxia.png` |  |
| 222 | `coleccionista_galaxias__dinosaurio` | Familias de skins | `references/chars/coleccionista_galaxias.png` |  |
| 223 | `emperador_cosmico__dinosaurio` | Familias de skins | `references/chars/emperador_cosmico.png` |  |
| 224 | `ser_ascendido__dinosaurio` | Familias de skins | `references/chars/ser_ascendido.png` |  |
| 225 | `semidios__dinosaurio` | Familias de skins | `references/chars/semidios.png` |  |
| 226 | `deidad__dinosaurio` | Familias de skins | `references/chars/deidad.png` |  |
| 227 | `god__dinosaurio` | Familias de skins | `references/chars/god.png` |  |
