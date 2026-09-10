# Objetivo — los mundos de Mathy

**Qué:** un paisaje por área del curriculum de Mathy
(`~/Desktop/projects/Mathy`), que va detrás del lienzo de cada actividad, y un
mapa del mundo para la pantalla de conceptos. El plan está en
`Mathy/docs/U-desarrollo/U4-rediseno-juego.md`.

**Estilo común:** pintura digital estilizada, formas limpias y degradados
suaves, en la línea de Monument Valley y Alto's Odyssey. Crepúsculo: cielo
turquesa e índigo, faroles dorados, luz de borde, bruma, luciérnagas.

**La regla que manda sobre todo lo demás: el centro es del juego.** Del 25 % al
85 % de la altura y del 20 % al 80 % del ancho, el suelo es oscuro, quieto y
vacío, porque ahí se dibuja el tablero. Todo el detalle va en los bordes y en el
cielo. En el centro no se usa rojo, verde menta ni ámbar vivo: son los colores con
los que el juego dice algo (una colección, "coincide", "mirá acá"), y un fondo
que los usa compite con la explicación.

**Referencia:** `output/bg_found.png`, el primero. Todos los demás lo adjuntan
para heredar el estilo, y el prompt les pide explícitamente no copiar sus objetos.

| # | clave | área | se usa en |
|---|---|---|---|
| 01 | `bg_found` | contar | nodos 1, 2 (y 45, 51) |
| 02 | `bg_arith` | aritmética | nodos 3 a 9 (y 47) |
| 03 | `bg_prealg` | prealgebra | nodos 10 a 12 |
| 04 | `bg_alg` | álgebra | nodos 13 a 24 |
| 05 | `bg_calc` | precálculo y cálculo | nodos 25 a 29 |
| 06 | `bg_linalg` | álgebra lineal | nodos 30 a 33 |
| 07 | `bg_prob` | probabilidad | nodos 34 a 36 |
| 08 | `bg_graph` | grafos | nodo 37 |
| 09 | `bg_geom` | geometría y trigonometría | nodos 38 a 44, 52 |
| 10 | `bg_disc` | discreta | nodos 53, 54 |
| 11 | `bg_world` | — | mapa de conceptos |

**Salida:** `raw`. En Mathy, `python3 tools/art/sync_art.py` los baja a JPEG de
1920 px en `apps/mathy/assets/art/mundos/`.

**Decisiones que no se re-discuten:**
- Prompts en ASCII puro (FisuEvolution, bug 7).
- Sin personajes en los paisajes: Lumi va aparte, como imagen recortada.
