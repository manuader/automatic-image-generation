# Índice — Football Evolution (E18-F4)

420 prompts, uno por imagen generada: los 416 PNG/JPG de `evo manifest futbol` (sin `adergames-logo`, que es el logo
del estudio y se reusa del Fisu; los @2x/@3x de un mismo id salen de UNA generación) más 4 que el manifiesto no lista:
las dos cinemáticas fijas de El Túnel y los dos ornamentos del tema. Sin animaciones ni audio.

**El runner lee la carpeta, no esta tabla.** El `estado` de cada `.md` lo pasa a `hecho` el script.

Orden: personajes primero, por piso (cada tipo con su original, sus 3 skins de familia, sus skins especiales y su cara,
todos con `familia: <id_del_tipo>`), después el guía, los visitantes y los especiales (cada uno su familia), los fondos,
las fijas y ornamentos, la UI y el ícono de la app. `Docs/E18-futbol-assets.json` no existía al cerrar F4: si aparece
con otras tandas, se renumera para seguirlas.

| Grupo | NN | Cuántos |
|---|---|---|
| piso 1 | 001–022 | 22 |
| piso 2 | 023–042 | 20 |
| piso 3 | 043–093 | 51 |
| piso 4 | 094–113 | 20 |
| piso 5 | 114–133 | 20 |
| piso 6 | 134–153 | 20 |
| piso 7 | 154–173 | 20 |
| piso 8 | 174–193 | 20 |
| piso 9 | 194–213 | 20 |
| piso 10 | 214–220 | 7 |
| guia | 221–222 | 2 |
| visitantes | 223–259 | 37 |
| especiales | 260–289 | 30 |
| fondos | 290–299 | 10 |
| fijas y ornamentos | 300–303 | 4 |
| ui | 304–419 | 116 |
| icono | 420–420 | 1 |
| **total** | | **420** |

| NN | clave | grupo | familia |
|---|---|---|---|
| 001 | `bebe_futbolero_idle` | piso 1 | bebe_futbolero |
| 002 | `bebe_futbolero_idle__retro` | piso 1 | bebe_futbolero |
| 003 | `bebe_futbolero_idle__barro` | piso 1 | bebe_futbolero |
| 004 | `bebe_futbolero_idle__dorada` | piso 1 | bebe_futbolero |
| 005 | `bebe_futbolero_idle__primera_camiseta` | piso 1 | bebe_futbolero |
| 006 | `bebe_futbolero_idle__despedida` | piso 1 | bebe_futbolero |
| 007 | `bebe_futbolero_face` | piso 1 | bebe_futbolero |
| 008 | `primeras_patadas_idle` | piso 1 | primeras_patadas |
| 009 | `primeras_patadas_idle__retro` | piso 1 | primeras_patadas |
| 010 | `primeras_patadas_idle__barro` | piso 1 | primeras_patadas |
| 011 | `primeras_patadas_idle__dorada` | piso 1 | primeras_patadas |
| 012 | `primeras_patadas_face` | piso 1 | primeras_patadas |
| 013 | `pibe_de_plaza_idle` | piso 1 | pibe_de_plaza |
| 014 | `pibe_de_plaza_idle__retro` | piso 1 | pibe_de_plaza |
| 015 | `pibe_de_plaza_idle__barro` | piso 1 | pibe_de_plaza |
| 016 | `pibe_de_plaza_idle__dorada` | piso 1 | pibe_de_plaza |
| 017 | `pibe_de_plaza_face` | piso 1 | pibe_de_plaza |
| 018 | `rey_del_potrero_idle` | piso 1 | rey_del_potrero |
| 019 | `rey_del_potrero_idle__retro` | piso 1 | rey_del_potrero |
| 020 | `rey_del_potrero_idle__barro` | piso 1 | rey_del_potrero |
| 021 | `rey_del_potrero_idle__dorada` | piso 1 | rey_del_potrero |
| 022 | `rey_del_potrero_face` | piso 1 | rey_del_potrero |
| 023 | `pibe_escuelita_idle` | piso 2 | pibe_escuelita |
| 024 | `pibe_escuelita_idle__retro` | piso 2 | pibe_escuelita |
| 025 | `pibe_escuelita_idle__barro` | piso 2 | pibe_escuelita |
| 026 | `pibe_escuelita_idle__dorada` | piso 2 | pibe_escuelita |
| 027 | `pibe_escuelita_face` | piso 2 | pibe_escuelita |
| 028 | `infantil_idle` | piso 2 | infantil |
| 029 | `infantil_idle__retro` | piso 2 | infantil |
| 030 | `infantil_idle__barro` | piso 2 | infantil |
| 031 | `infantil_idle__dorada` | piso 2 | infantil |
| 032 | `infantil_face` | piso 2 | infantil |
| 033 | `goleador_infantil_idle` | piso 2 | goleador_infantil |
| 034 | `goleador_infantil_idle__retro` | piso 2 | goleador_infantil |
| 035 | `goleador_infantil_idle__barro` | piso 2 | goleador_infantil |
| 036 | `goleador_infantil_idle__dorada` | piso 2 | goleador_infantil |
| 037 | `goleador_infantil_face` | piso 2 | goleador_infantil |
| 038 | `promesa_barrio_idle` | piso 2 | promesa_barrio |
| 039 | `promesa_barrio_idle__retro` | piso 2 | promesa_barrio |
| 040 | `promesa_barrio_idle__barro` | piso 2 | promesa_barrio |
| 041 | `promesa_barrio_idle__dorada` | piso 2 | promesa_barrio |
| 042 | `promesa_barrio_face` | piso 2 | promesa_barrio |
| 043 | `pibe_novena_idle` | piso 3 | pibe_novena |
| 044 | `pibe_novena_idle__retro` | piso 3 | pibe_novena |
| 045 | `pibe_novena_idle__barro` | piso 3 | pibe_novena |
| 046 | `pibe_novena_idle__dorada` | piso 3 | pibe_novena |
| 047 | `pibe_novena_face` | piso 3 | pibe_novena |
| 048 | `pibe_octava_idle` | piso 3 | pibe_octava |
| 049 | `pibe_octava_idle__retro` | piso 3 | pibe_octava |
| 050 | `pibe_octava_idle__barro` | piso 3 | pibe_octava |
| 051 | `pibe_octava_idle__dorada` | piso 3 | pibe_octava |
| 052 | `pibe_octava_face` | piso 3 | pibe_octava |
| 053 | `arquero_septima_idle` | piso 3 | arquero_septima |
| 054 | `arquero_septima_idle__retro` | piso 3 | arquero_septima |
| 055 | `arquero_septima_idle__barro` | piso 3 | arquero_septima |
| 056 | `arquero_septima_idle__dorada` | piso 3 | arquero_septima |
| 057 | `arquero_septima_idle__buzo_fluor` | piso 3 | arquero_septima |
| 058 | `arquero_septima_face` | piso 3 | arquero_septima |
| 059 | `central_septima_idle` | piso 3 | central_septima |
| 060 | `central_septima_idle__retro` | piso 3 | central_septima |
| 061 | `central_septima_idle__barro` | piso 3 | central_septima |
| 062 | `central_septima_idle__dorada` | piso 3 | central_septima |
| 063 | `central_septima_face` | piso 3 | central_septima |
| 064 | `volante_septima_idle` | piso 3 | volante_septima |
| 065 | `volante_septima_idle__retro` | piso 3 | volante_septima |
| 066 | `volante_septima_idle__barro` | piso 3 | volante_septima |
| 067 | `volante_septima_idle__dorada` | piso 3 | volante_septima |
| 068 | `volante_septima_face` | piso 3 | volante_septima |
| 069 | `nueve_septima_idle` | piso 3 | nueve_septima |
| 070 | `nueve_septima_idle__retro` | piso 3 | nueve_septima |
| 071 | `nueve_septima_idle__barro` | piso 3 | nueve_septima |
| 072 | `nueve_septima_idle__dorada` | piso 3 | nueve_septima |
| 073 | `nueve_septima_face` | piso 3 | nueve_septima |
| 074 | `arquero_sexta_idle` | piso 3 | arquero_sexta |
| 075 | `arquero_sexta_idle__retro` | piso 3 | arquero_sexta |
| 076 | `arquero_sexta_idle__barro` | piso 3 | arquero_sexta |
| 077 | `arquero_sexta_idle__dorada` | piso 3 | arquero_sexta |
| 078 | `arquero_sexta_face` | piso 3 | arquero_sexta |
| 079 | `central_sexta_idle` | piso 3 | central_sexta |
| 080 | `central_sexta_idle__retro` | piso 3 | central_sexta |
| 081 | `central_sexta_idle__barro` | piso 3 | central_sexta |
| 082 | `central_sexta_idle__dorada` | piso 3 | central_sexta |
| 083 | `central_sexta_face` | piso 3 | central_sexta |
| 084 | `volante_sexta_idle` | piso 3 | volante_sexta |
| 085 | `volante_sexta_idle__retro` | piso 3 | volante_sexta |
| 086 | `volante_sexta_idle__barro` | piso 3 | volante_sexta |
| 087 | `volante_sexta_idle__dorada` | piso 3 | volante_sexta |
| 088 | `volante_sexta_face` | piso 3 | volante_sexta |
| 089 | `nueve_sexta_idle` | piso 3 | nueve_sexta |
| 090 | `nueve_sexta_idle__retro` | piso 3 | nueve_sexta |
| 091 | `nueve_sexta_idle__barro` | piso 3 | nueve_sexta |
| 092 | `nueve_sexta_idle__dorada` | piso 3 | nueve_sexta |
| 093 | `nueve_sexta_face` | piso 3 | nueve_sexta |
| 094 | `pibe_quinta_idle` | piso 4 | pibe_quinta |
| 095 | `pibe_quinta_idle__retro` | piso 4 | pibe_quinta |
| 096 | `pibe_quinta_idle__barro` | piso 4 | pibe_quinta |
| 097 | `pibe_quinta_idle__dorada` | piso 4 | pibe_quinta |
| 098 | `pibe_quinta_face` | piso 4 | pibe_quinta |
| 099 | `pibe_cuarta_idle` | piso 4 | pibe_cuarta |
| 100 | `pibe_cuarta_idle__retro` | piso 4 | pibe_cuarta |
| 101 | `pibe_cuarta_idle__barro` | piso 4 | pibe_cuarta |
| 102 | `pibe_cuarta_idle__dorada` | piso 4 | pibe_cuarta |
| 103 | `pibe_cuarta_face` | piso 4 | pibe_cuarta |
| 104 | `jugador_reserva_idle` | piso 4 | jugador_reserva |
| 105 | `jugador_reserva_idle__retro` | piso 4 | jugador_reserva |
| 106 | `jugador_reserva_idle__barro` | piso 4 | jugador_reserva |
| 107 | `jugador_reserva_idle__dorada` | piso 4 | jugador_reserva |
| 108 | `jugador_reserva_face` | piso 4 | jugador_reserva |
| 109 | `debutante_profesional_idle` | piso 4 | debutante_profesional |
| 110 | `debutante_profesional_idle__retro` | piso 4 | debutante_profesional |
| 111 | `debutante_profesional_idle__barro` | piso 4 | debutante_profesional |
| 112 | `debutante_profesional_idle__dorada` | piso 4 | debutante_profesional |
| 113 | `debutante_profesional_face` | piso 4 | debutante_profesional |
| 114 | `titular_ascenso_idle` | piso 5 | titular_ascenso |
| 115 | `titular_ascenso_idle__retro` | piso 5 | titular_ascenso |
| 116 | `titular_ascenso_idle__barro` | piso 5 | titular_ascenso |
| 117 | `titular_ascenso_idle__dorada` | piso 5 | titular_ascenso |
| 118 | `titular_ascenso_face` | piso 5 | titular_ascenso |
| 119 | `figura_ascenso_idle` | piso 5 | figura_ascenso |
| 120 | `figura_ascenso_idle__retro` | piso 5 | figura_ascenso |
| 121 | `figura_ascenso_idle__barro` | piso 5 | figura_ascenso |
| 122 | `figura_ascenso_idle__dorada` | piso 5 | figura_ascenso |
| 123 | `figura_ascenso_face` | piso 5 | figura_ascenso |
| 124 | `campeon_ascenso_idle` | piso 5 | campeon_ascenso |
| 125 | `campeon_ascenso_idle__retro` | piso 5 | campeon_ascenso |
| 126 | `campeon_ascenso_idle__barro` | piso 5 | campeon_ascenso |
| 127 | `campeon_ascenso_idle__dorada` | piso 5 | campeon_ascenso |
| 128 | `campeon_ascenso_face` | piso 5 | campeon_ascenso |
| 129 | `debutante_primera_idle` | piso 5 | debutante_primera |
| 130 | `debutante_primera_idle__retro` | piso 5 | debutante_primera |
| 131 | `debutante_primera_idle__barro` | piso 5 | debutante_primera |
| 132 | `debutante_primera_idle__dorada` | piso 5 | debutante_primera |
| 133 | `debutante_primera_face` | piso 5 | debutante_primera |
| 134 | `titular_primera_idle` | piso 6 | titular_primera |
| 135 | `titular_primera_idle__retro` | piso 6 | titular_primera |
| 136 | `titular_primera_idle__barro` | piso 6 | titular_primera |
| 137 | `titular_primera_idle__dorada` | piso 6 | titular_primera |
| 138 | `titular_primera_face` | piso 6 | titular_primera |
| 139 | `goleador_primera_idle` | piso 6 | goleador_primera |
| 140 | `goleador_primera_idle__retro` | piso 6 | goleador_primera |
| 141 | `goleador_primera_idle__barro` | piso 6 | goleador_primera |
| 142 | `goleador_primera_idle__dorada` | piso 6 | goleador_primera |
| 143 | `goleador_primera_face` | piso 6 | goleador_primera |
| 144 | `capitan_primera_idle` | piso 6 | capitan_primera |
| 145 | `capitan_primera_idle__retro` | piso 6 | capitan_primera |
| 146 | `capitan_primera_idle__barro` | piso 6 | capitan_primera |
| 147 | `capitan_primera_idle__dorada` | piso 6 | capitan_primera |
| 148 | `capitan_primera_face` | piso 6 | capitan_primera |
| 149 | `campeon_nacional_idle` | piso 6 | campeon_nacional |
| 150 | `campeon_nacional_idle__retro` | piso 6 | campeon_nacional |
| 151 | `campeon_nacional_idle__barro` | piso 6 | campeon_nacional |
| 152 | `campeon_nacional_idle__dorada` | piso 6 | campeon_nacional |
| 153 | `campeon_nacional_face` | piso 6 | campeon_nacional |
| 154 | `convocado_seleccion_idle` | piso 7 | convocado_seleccion |
| 155 | `convocado_seleccion_idle__retro` | piso 7 | convocado_seleccion |
| 156 | `convocado_seleccion_idle__barro` | piso 7 | convocado_seleccion |
| 157 | `convocado_seleccion_idle__dorada` | piso 7 | convocado_seleccion |
| 158 | `convocado_seleccion_face` | piso 7 | convocado_seleccion |
| 159 | `jugador_seleccion_idle` | piso 7 | jugador_seleccion |
| 160 | `jugador_seleccion_idle__retro` | piso 7 | jugador_seleccion |
| 161 | `jugador_seleccion_idle__barro` | piso 7 | jugador_seleccion |
| 162 | `jugador_seleccion_idle__dorada` | piso 7 | jugador_seleccion |
| 163 | `jugador_seleccion_face` | piso 7 | jugador_seleccion |
| 164 | `fichaje_europeo_idle` | piso 7 | fichaje_europeo |
| 165 | `fichaje_europeo_idle__retro` | piso 7 | fichaje_europeo |
| 166 | `fichaje_europeo_idle__barro` | piso 7 | fichaje_europeo |
| 167 | `fichaje_europeo_idle__dorada` | piso 7 | fichaje_europeo |
| 168 | `fichaje_europeo_face` | piso 7 | fichaje_europeo |
| 169 | `estrella_exterior_idle` | piso 7 | estrella_exterior |
| 170 | `estrella_exterior_idle__retro` | piso 7 | estrella_exterior |
| 171 | `estrella_exterior_idle__barro` | piso 7 | estrella_exterior |
| 172 | `estrella_exterior_idle__dorada` | piso 7 | estrella_exterior |
| 173 | `estrella_exterior_face` | piso 7 | estrella_exterior |
| 174 | `campeon_liga_exterior_idle` | piso 8 | campeon_liga_exterior |
| 175 | `campeon_liga_exterior_idle__retro` | piso 8 | campeon_liga_exterior |
| 176 | `campeon_liga_exterior_idle__barro` | piso 8 | campeon_liga_exterior |
| 177 | `campeon_liga_exterior_idle__dorada` | piso 8 | campeon_liga_exterior |
| 178 | `campeon_liga_exterior_face` | piso 8 | campeon_liga_exterior |
| 179 | `campeon_continental_clubes_idle` | piso 8 | campeon_continental_clubes |
| 180 | `campeon_continental_clubes_idle__retro` | piso 8 | campeon_continental_clubes |
| 181 | `campeon_continental_clubes_idle__barro` | piso 8 | campeon_continental_clubes |
| 182 | `campeon_continental_clubes_idle__dorada` | piso 8 | campeon_continental_clubes |
| 183 | `campeon_continental_clubes_face` | piso 8 | campeon_continental_clubes |
| 184 | `campeon_planetario_clubes_idle` | piso 8 | campeon_planetario_clubes |
| 185 | `campeon_planetario_clubes_idle__retro` | piso 8 | campeon_planetario_clubes |
| 186 | `campeon_planetario_clubes_idle__barro` | piso 8 | campeon_planetario_clubes |
| 187 | `campeon_planetario_clubes_idle__dorada` | piso 8 | campeon_planetario_clubes |
| 188 | `campeon_planetario_clubes_face` | piso 8 | campeon_planetario_clubes |
| 189 | `capitan_seleccion_idle` | piso 8 | capitan_seleccion |
| 190 | `capitan_seleccion_idle__retro` | piso 8 | capitan_seleccion |
| 191 | `capitan_seleccion_idle__barro` | piso 8 | capitan_seleccion |
| 192 | `capitan_seleccion_idle__dorada` | piso 8 | capitan_seleccion |
| 193 | `capitan_seleccion_face` | piso 8 | capitan_seleccion |
| 194 | `campeon_continental_idle` | piso 9 | campeon_continental |
| 195 | `campeon_continental_idle__retro` | piso 9 | campeon_continental |
| 196 | `campeon_continental_idle__barro` | piso 9 | campeon_continental |
| 197 | `campeon_continental_idle__dorada` | piso 9 | campeon_continental |
| 198 | `campeon_continental_face` | piso 9 | campeon_continental |
| 199 | `campeon_del_mundo_idle` | piso 9 | campeon_del_mundo |
| 200 | `campeon_del_mundo_idle__retro` | piso 9 | campeon_del_mundo |
| 201 | `campeon_del_mundo_idle__barro` | piso 9 | campeon_del_mundo |
| 202 | `campeon_del_mundo_idle__dorada` | piso 9 | campeon_del_mundo |
| 203 | `campeon_del_mundo_face` | piso 9 | campeon_del_mundo |
| 204 | `mejor_del_planeta_idle` | piso 9 | mejor_del_planeta |
| 205 | `mejor_del_planeta_idle__retro` | piso 9 | mejor_del_planeta |
| 206 | `mejor_del_planeta_idle__barro` | piso 9 | mejor_del_planeta |
| 207 | `mejor_del_planeta_idle__dorada` | piso 9 | mejor_del_planeta |
| 208 | `mejor_del_planeta_face` | piso 9 | mejor_del_planeta |
| 209 | `leyenda_eterna_idle` | piso 9 | leyenda_eterna |
| 210 | `leyenda_eterna_idle__retro` | piso 9 | leyenda_eterna |
| 211 | `leyenda_eterna_idle__barro` | piso 9 | leyenda_eterna |
| 212 | `leyenda_eterna_idle__dorada` | piso 9 | leyenda_eterna |
| 213 | `leyenda_eterna_face` | piso 9 | leyenda_eterna |
| 214 | `dios_futbol_idle` | piso 10 | dios_futbol |
| 215 | `dios_futbol_idle__retro` | piso 10 | dios_futbol |
| 216 | `dios_futbol_idle__barro` | piso 10 | dios_futbol |
| 217 | `dios_futbol_idle__dorada` | piso 10 | dios_futbol |
| 218 | `dios_futbol_idle__aureola` | piso 10 | dios_futbol |
| 219 | `dios_futbol_idle__de_gala` | piso 10 | dios_futbol |
| 220 | `dios_futbol_face` | piso 10 | dios_futbol |
| 221 | `aguatero_saluda` | guia | aguatero |
| 222 | `aguatero_festeja` | guia | aguatero |
| 223 | `npc_arbitro` | visitantes | npc_arbitro |
| 224 | `npc_arbitro_talk` | visitantes | npc_arbitro |
| 225 | `npc_arbitro_action` | visitantes | npc_arbitro |
| 226 | `npc_arbitro_face` | visitantes | npc_arbitro |
| 227 | `npc_dirigente` | visitantes | npc_dirigente |
| 228 | `npc_dirigente_talk` | visitantes | npc_dirigente |
| 229 | `npc_dirigente_action` | visitantes | npc_dirigente |
| 230 | `npc_dirigente_face` | visitantes | npc_dirigente |
| 231 | `npc_hincha` | visitantes | npc_hincha |
| 232 | `npc_hincha_talk` | visitantes | npc_hincha |
| 233 | `npc_hincha_action` | visitantes | npc_hincha |
| 234 | `npc_hincha_face` | visitantes | npc_hincha |
| 235 | `npc_masajista` | visitantes | npc_masajista |
| 236 | `npc_masajista_talk` | visitantes | npc_masajista |
| 237 | `npc_masajista_action` | visitantes | npc_masajista |
| 238 | `npc_masajista_face` | visitantes | npc_masajista |
| 239 | `npc_ojeador` | visitantes | npc_ojeador |
| 240 | `npc_ojeador_talk` | visitantes | npc_ojeador |
| 241 | `npc_ojeador_action` | visitantes | npc_ojeador |
| 242 | `npc_ojeador_face` | visitantes | npc_ojeador |
| 243 | `npc_periodista` | visitantes | npc_periodista |
| 244 | `npc_periodista_talk` | visitantes | npc_periodista |
| 245 | `npc_periodista_action` | visitantes | npc_periodista |
| 246 | `npc_periodista_face` | visitantes | npc_periodista |
| 247 | `npc_representante` | visitantes | npc_representante |
| 248 | `npc_representante_talk` | visitantes | npc_representante |
| 249 | `npc_representante_action` | visitantes | npc_representante |
| 250 | `npc_representante_face` | visitantes | npc_representante |
| 251 | `npc_utilero` | visitantes | npc_utilero |
| 252 | `npc_utilero_talk` | visitantes | npc_utilero |
| 253 | `npc_utilero_action` | visitantes | npc_utilero |
| 254 | `npc_utilero_enojado` | visitantes | npc_utilero |
| 255 | `npc_utilero_face` | visitantes | npc_utilero |
| 256 | `npc_vecina_club` | visitantes | npc_vecina_club |
| 257 | `npc_vecina_club_talk` | visitantes | npc_vecina_club |
| 258 | `npc_vecina_club_action` | visitantes | npc_vecina_club |
| 259 | `npc_vecina_club_face` | visitantes | npc_vecina_club |
| 260 | `sp_alien_ojeador` | especiales | sp_alien_ojeador |
| 261 | `sp_alien_ojeador_talk` | especiales | sp_alien_ojeador |
| 262 | `sp_alien_ojeador_face` | especiales | sp_alien_ojeador |
| 263 | `sp_arbitro_robot` | especiales | sp_arbitro_robot |
| 264 | `sp_arbitro_robot_talk` | especiales | sp_arbitro_robot |
| 265 | `sp_arbitro_robot_face` | especiales | sp_arbitro_robot |
| 266 | `sp_dt_motivacional` | especiales | sp_dt_motivacional |
| 267 | `sp_dt_motivacional_talk` | especiales | sp_dt_motivacional |
| 268 | `sp_dt_motivacional_face` | especiales | sp_dt_motivacional |
| 269 | `sp_dt_rival` | especiales | sp_dt_rival |
| 270 | `sp_dt_rival_talk` | especiales | sp_dt_rival |
| 271 | `sp_dt_rival_face` | especiales | sp_dt_rival |
| 272 | `sp_fantasma_estadio` | especiales | sp_fantasma_estadio |
| 273 | `sp_fantasma_estadio_talk` | especiales | sp_fantasma_estadio |
| 274 | `sp_fantasma_estadio_face` | especiales | sp_fantasma_estadio |
| 275 | `sp_freestyler` | especiales | sp_freestyler |
| 276 | `sp_freestyler_talk` | especiales | sp_freestyler |
| 277 | `sp_freestyler_face` | especiales | sp_freestyler |
| 278 | `sp_gato_cancha` | especiales | sp_gato_cancha |
| 279 | `sp_gato_cancha_talk` | especiales | sp_gato_cancha |
| 280 | `sp_gato_cancha_face` | especiales | sp_gato_cancha |
| 281 | `sp_pelota_maldita` | especiales | sp_pelota_maldita |
| 282 | `sp_pelota_maldita_talk` | especiales | sp_pelota_maldita |
| 283 | `sp_pelota_maldita_face` | especiales | sp_pelota_maldita |
| 284 | `sp_revendedor` | especiales | sp_revendedor |
| 285 | `sp_revendedor_talk` | especiales | sp_revendedor |
| 286 | `sp_revendedor_face` | especiales | sp_revendedor |
| 287 | `sp_sponsor` | especiales | sp_sponsor |
| 288 | `sp_sponsor_talk` | especiales | sp_sponsor |
| 289 | `sp_sponsor_face` | especiales | sp_sponsor |
| 290 | `bg_potrero` | fondos |  |
| 291 | `bg_baby` | fondos |  |
| 292 | `bg_inferiores` | fondos |  |
| 293 | `bg_camino_primera` | fondos |  |
| 294 | `bg_ascenso` | fondos |  |
| 295 | `bg_primera` | fondos |  |
| 296 | `bg_internacional` | fondos |  |
| 297 | `bg_elite` | fondos |  |
| 298 | `bg_leyendas` | fondos |  |
| 299 | `bg_celestial` | fondos |  |
| 300 | `tunel_cerrado` | fijas y ornamentos |  |
| 301 | `tunel_abierto` | fijas y ornamentos |  |
| 302 | `orn_banderin_corner` | fijas y ornamentos |  |
| 303 | `orn_marcador_cabecera` | fijas y ornamentos |  |
| 304 | `fx_evolution_flash` | ui |  |
| 305 | `fx_papelitos` | ui |  |
| 306 | `logo` | ui |  |
| 307 | `mattress_icon` | ui |  |
| 308 | `pickup_mattress` | ui |  |
| 309 | `pickup_mattress_open` | ui |  |
| 310 | `pickup_package` | ui |  |
| 311 | `pickup_package_full` | ui |  |
| 312 | `pickup_package_lid` | ui |  |
| 313 | `pickup_package_open` | ui |  |
| 314 | `pickup_package_opening` | ui |  |
| 315 | `rw_arrest` | ui |  |
| 316 | `rw_boost_refresh` | ui |  |
| 317 | `rw_coins` | ui |  |
| 318 | `rw_evolve` | ui |  |
| 319 | `rw_exchange` | ui |  |
| 320 | `rw_fine` | ui |  |
| 321 | `rw_free_unit` | ui |  |
| 322 | `rw_frozen` | ui |  |
| 323 | `rw_hire_discount` | ui |  |
| 324 | `rw_income_mult` | ui |  |
| 325 | `rw_mattress_hero` | ui |  |
| 326 | `rw_mattress_treasure` | ui |  |
| 327 | `rw_mystery_all` | ui |  |
| 328 | `rw_pack_bienvenida` | ui |  |
| 329 | `rw_pack_nueva_carrera` | ui |  |
| 330 | `rw_pack_pretemporada` | ui |  |
| 331 | `rw_package_employee` | ui |  |
| 332 | `rw_reencarnar` | ui |  |
| 333 | `rw_tap_mult` | ui |  |
| 334 | `ui_album_card_frame` | ui |  |
| 335 | `ui_album_locked` | ui |  |
| 336 | `ui_badge` | ui |  |
| 337 | `ui_blue_pack_large` | ui |  |
| 338 | `ui_blue_pack_medium` | ui |  |
| 339 | `ui_blue_pack_small` | ui |  |
| 340 | `ui_boost_bidon` | ui |  |
| 341 | `ui_boost_charla_tecnica` | ui |  |
| 342 | `ui_boost_concentracion` | ui |  |
| 343 | `ui_boost_isotonica` | ui |  |
| 344 | `ui_boost_pizza_del_plantel` | ui |  |
| 345 | `ui_boost_tercer_tiempo` | ui |  |
| 346 | `ui_btn_buy` | ui |  |
| 347 | `ui_btn_close` | ui |  |
| 348 | `ui_chest_closed` | ui |  |
| 349 | `ui_coin` | ui |  |
| 350 | `ui_coin_plus` | ui |  |
| 351 | `ui_daily_calendar` | ui |  |
| 352 | `ui_dolar_blue` | ui |  |
| 353 | `ui_elevator` | ui |  |
| 354 | `ui_event_inhibicion` | ui |  |
| 355 | `ui_event_lesion` | ui |  |
| 356 | `ui_event_ojeo_intergalactico` | ui |  |
| 357 | `ui_event_pases_por_las_nubes` | ui |  |
| 358 | `ui_event_prima_por_ganar` | ui |  |
| 359 | `ui_event_recaudacion_record` | ui |  |
| 360 | `ui_event_refuerzo_de_invierno` | ui |  |
| 361 | `ui_event_subido_a_primera` | ui |  |
| 362 | `ui_gift_bow` | ui |  |
| 363 | `ui_icon_check` | ui |  |
| 364 | `ui_icon_clock` | ui |  |
| 365 | `ui_icon_lock` | ui |  |
| 366 | `ui_icon_video` | ui |  |
| 367 | `ui_menu_orgchart` | ui |  |
| 368 | `ui_menu_ranking` | ui |  |
| 369 | `ui_menu_settings` | ui |  |
| 370 | `ui_menu_specials` | ui |  |
| 371 | `ui_menu_stats` | ui |  |
| 372 | `ui_menu_trophy` | ui |  |
| 373 | `ui_money` | ui |  |
| 374 | `ui_notif_campana` | ui |  |
| 375 | `ui_offer_bienvenida` | ui |  |
| 376 | `ui_offer_nueva_carrera` | ui |  |
| 377 | `ui_offer_pretemporada` | ui |  |
| 378 | `ui_rail_mattress` | ui |  |
| 379 | `ui_rail_merge_all` | ui |  |
| 380 | `ui_rail_package` | ui |  |
| 381 | `ui_rail_wheel` | ui |  |
| 382 | `ui_reset_demolicion` | ui |  |
| 383 | `ui_save_rescate` | ui |  |
| 384 | `ui_shop_auto_tap` | ui |  |
| 385 | `ui_shop_better_supplier` | ui |  |
| 386 | `ui_shop_daily_x3` | ui |  |
| 387 | `ui_shop_extra_slots` | ui |  |
| 388 | `ui_shop_income_x2` | ui |  |
| 389 | `ui_shop_income_x3` | ui |  |
| 390 | `ui_shop_merge_all` | ui |  |
| 391 | `ui_shop_offline_x3` | ui |  |
| 392 | `ui_shop_package_rain` | ui |  |
| 393 | `ui_shop_skin_family` | ui |  |
| 394 | `ui_shop_skip_cooldowns` | ui |  |
| 395 | `ui_shop_time_jump_1h` | ui |  |
| 396 | `ui_shop_time_jump_4h` | ui |  |
| 397 | `ui_shop_wheel_spins` | ui |  |
| 398 | `ui_tab_active` | ui |  |
| 399 | `ui_tab_gifts` | ui |  |
| 400 | `ui_tab_inactive` | ui |  |
| 401 | `ui_tab_menu` | ui |  |
| 402 | `ui_tab_shop` | ui |  |
| 403 | `ui_tab_skins` | ui |  |
| 404 | `ui_tab_upgrades` | ui |  |
| 405 | `ui_trophy_bronze` | ui |  |
| 406 | `ui_trophy_gold` | ui |  |
| 407 | `ui_trophy_silver` | ui |  |
| 408 | `ui_up_crit` | ui |  |
| 409 | `ui_up_golden` | ui |  |
| 410 | `ui_up_income` | ui |  |
| 411 | `ui_up_offline` | ui |  |
| 412 | `ui_up_prestige` | ui |  |
| 413 | `ui_up_spawn` | ui |  |
| 414 | `ui_up_tap` | ui |  |
| 415 | `wheel_frame` | ui |  |
| 416 | `wheel_hub` | ui |  |
| 417 | `wheel_icon` | ui |  |
| 418 | `wheel_pointer` | ui |  |
| 419 | `wheel_seg_respin` | ui |  |
| 420 | `AppIcon` | icono |  |
