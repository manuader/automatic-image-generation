# football-evolution — todo el arte estático de Football Evolution (E18-F4)

El segundo juego del motor de FisuEvolution (paquete `Games/futbol/` en la rama `motor-evolution`): un bebé que patea
todo lo que rueda fusiona hasta convertirse en el Dios del Fútbol, en 37 niveles y 10 pisos. Este proyecto tiene **un
`.md` por imagen** de `evo manifest futbol`, más las cinemáticas fijas y los ornamentos que el manifiesto no lista.
Fuentes: `Docs/PLAN-v2-E18-futbol.md` (E18-F4), `Docs/E18-futbol-brief.md` y `Games/futbol/content/` en el repo del
juego. El orden y las familias están en `prompts/00_INDICE.md`.

## Total y corrida completa

- **420 prompts**: 416 del manifiesto (sin `adergames-logo`, el logo del estudio, que se reusa) + `tunel_cerrado`,
  `tunel_abierto`, `orn_banderin_corner` y `orn_marcador_cabecera`.
- `--dry-run` los cuenta todos: `.venv/bin/python generate.py --project football-evolution --dry-run`.
- El plan de tandas (9 tandas, ninguna familia partida):
  `.venv/bin/python supervisor.py --project football-evolution --rotate gemini:50,chat-gpt:50 --dry-run`.
- **La corrida completa** (regla del dueño: 50 en Gemini, 50 en ChatGPT, y así; nunca se cambia):

```bash
.venv/bin/python supervisor.py --project football-evolution --rotate gemini:50,chat-gpt:50
```

Antes: el dueño se loguea en las dos ventanas aisladas (`--engine gemini --launch` y `--engine chat-gpt --launch`) y
el piloto F6 (`projects/football-evolution-piloto/`) tiene su OK. Sin ese OK no se corre.

## La biblia de estilo

**Decisión del dueño (2026-11-11 14:40): estilo 3, juguete 3D de vinilo coleccionable.** No se re-discute.

### Cómo empieza cada prompt

Todos los prompts arrancan con el párrafo canónico de `briefs/estilo-elegido/prompt_hoja.md` del run AVO del Fisu, y
la orden de copiar la referencia:

> Art style first: glossy 3D collectible vinyl toy figure render, bobblehead proportions with a huge round head and a
> small chunky body, smooth plastic and soft rubber materials with subtle specular highlights, soft studio lighting
> from the top left, gentle ambient occlusion, vivid saturated colors, playful premium mobile game look. Match EXACTLY
> the art style, proportions, materials and lighting of the attached reference.

Después, una frase que dice qué hacer con la referencia (dibujar UNA etapa del protagonista; o usarla sólo de guía de
estilo para otro personaje o para UI), el sujeto, la **lista negra legal** y el cierre de encuadre. El cuerpo del
prompt es **ASCII puro** (las tildes pierden caracteres al tipear); el título del `.md` puede tener tildes.

### Referencias (obligatorias)

| archivo | se adjunta a |
|---|---|
| `references/protagonista_hoja.png` | todo personaje: los 43 tipos, sus skins y caras, el Aguatero, visitantes, especiales y el ícono de la app |
| `references/pantalla.png` | UI, fondos, cinemáticas fijas y ornamentos |

Una referencia por prompt. Las dos vienen de `briefs/estilo-elegido/` del run `2026-10-06-fisu-v2`.

### Paleta (del brief y de `Games/futbol/theme.json`)

| color | hex | para |
|---|---|---|
| verde césped | `#1F5133` (fondo `#173F27`) | la cancha, las placas, lo del club |
| blanco cal | `#F4F7F2` | líneas de cal de los fondos (`bg_*`, `tunel_*`, a sangre) |
| crema | `#FFF3DC` | todo lo que en un personaje o un ícono sería blanco: cuellos, vivos, curita, suelas, alas, pelotas |
| negro tablero | `#111418` | el tablero LED, los marcos |
| amarillo tarjeta | `#FFD400` | la acción: botones, cinta de capitán, banderines |
| dorado premium | `#E2B93B` | lo premium: estrellas, skins Doradas, el Dios |

La camiseta del club del protagonista es **verde azulado (teal) con cuello crema y el 22** (la de la hoja, con el
blanco pasado a crema por la regla de recorte). Las demás son inventadas y se eligieron para no coincidir con ninguna
real: escuelita **naranja y crema**, ascenso **mostaza y
negra**, el club europeo **azul noche y cobre**, la selección **violeta con naranja**. Nunca celeste y blanca.

### El protagonista: un solo chico creciendo

Los 37 niveles y los 8 de los puestos son **el mismo protagonista**. Cuatro rasgos fijos, escritos igual en TODOS los
prompts de personaje:

1. remolino de pelo castaño oscuro parado en la coronilla, sobre pelo corto y lacio (**nunca rulos**);
2. pecas en nariz y mejillas;
3. curita **crema** en la rodilla **IZQUIERDA**;
4. botines verde lima de suela **crema** (el Rey del Potrero los lleva colgados al hombro; el bebé, botitas).

Sin barba en ningún nivel. En las caras (`*_face`, retrato de cabeza y hombros) la curita y los botines quedan fuera de
cuadro y el prompt lo dice: los rasgos 1 y 2 se ven siempre.

### Hojas de continuidad: tipo + skins + cara

Cada tipo tiene un bloque fijo «Look of this level» (edad, ropa, pose, objetos, expresión) que se repite **palabra por
palabra** en su original, en sus 3 skins de familia (Retro, Barro de Potrero, Dorada), en sus skins especiales y en su
cara. La skin sólo cambia el tratamiento de la ropa («keep EXACTLY the same face, age, body, silhouette and pose»).
Todos esos `.md` llevan `- **familia**: <id_del_tipo>`, así la rotación los manda juntos al mismo motor.

- **Retro** (común): camiseta de algodón vieja con cuello de cordones y número cosido, short largo, medias de lana,
  pelota de cuero con tiento, colores un poco sepia.
- **Barro de Potrero** (rara): la misma ropa embarrada después de un partido con lluvia; la curita y el lima se leen. El
  barro queda pegado a la ropa: nada de salpicaduras en el aire.
- **Dorada** (épica; **legendaria en los pisos 9 y 10**): la ropa en vinilo dorado pulido; en la legendaria, pulido
  espejo con detalles grabados. Sin aura ni destellos: el dorado sale del material. Los botines siguen lima con suela
  crema y cordones dorados.
- Skins especiales: Buzo Flúor (arquero), La Primera Camiseta y Camiseta de Despedida (bebé), Aureola y De Gala (Dios).
  La Aureola es un aro de oro macizo y opaco, una pieza del juguete fijada a la nuca por un vástago corto, que no emite
  luz.

Visitantes, especiales y el Aguatero son **otros personajes**, mismo estilo: la referencia se adjunta sólo como guía y
el prompt pide «a different, new character». Cada uno repite su «Look» en todas sus poses (retrato, `_talk`, `_action`,
`_face`, y `_enojado` del utilero) y todas llevan `familia: <su id>`.

### Cómo escala cada piso (regla del dueño)

El cuarto de cada piso es **MUCHO** más destacado que el primero. Se escala en el personaje mismo: pose, ropa, equipo
y materiales (y una luz de borde SOBRE la figura). Nunca con base, escenario, brillo detrás ni partículas: ver la
regla de recorte.

| posición en el piso | qué pide el prompt |
|---|---|
| 1 | lo más simple del piso |
| 2 | un paso más seguro, todavía simple |
| 3 | más pulido, una luz de borde cálida suave sobre los bordes de la figura |
| 4 | pose heroica, su mejor ropa y equipo, materiales más ricos y brillantes, una luz de borde dorada fuerte sobre la figura; **parado solo, sin nada bajo los pies ni detrás** |

En el piso 3 el cuarto es el nivel 12 (los cuatro de Sexta). El tema de cada piso vive **sólo en el fondo** (`bg_*`),
nunca bajo los pies del personaje:

| piso | tema del fondo del piso |
|---|---|
| 1 · Los comienzos | potrero de tierra con dos piedras de arco |
| 2 · Fútbol infantil | canchita con alambrado |
| 3 · Inferiores | predio con conos naranjas y pechera amarilla |
| 4 · Camino a Primera | esquina de estadio vacío con una sola tribuna encendida |
| 5 · El ascenso | tablones de madera y un solo reflector |
| 6 · Primera división | estadio lleno, papelitos y humo de colores |
| 7 · Estrella internacional | cancha europea nevada con una valija |
| 8 · La élite mundial | final con fuegos artificiales |
| 9 · Leyendas | pedestal de mármol del salón de la fama |
| 10 · La divinidad | estadio celestial de nubes |

**El 37, Dios del Fútbol, es una divinidad**, no un futbolista: camiseta dorada pulida **sin número** ni escudo,
alitas **crema**, una pelota de energía azul (azul profundo y cian) apoyada en la palma, tocándola, pegada a la
silueta. Flota un poco, con sólo aire bajo los pies: sin nubes, sin base, sin aura ni halo detrás. Lo espectacular
sale de la figura: el oro pulido, las alas, la pelota y una luz de borde sobre él. Sin el 10, sin rulos, sin celeste
y blanca. El ícono de la app NO lo usa (clasificación 4+): usa al Debutante Profesional.

### Regla de recorte (dueño, 2026-11-11 ~15:30)

Las imágenes salen sobre blanco liso y después se recorta el fondo. Palabras del dueño: «tienen como algo en los pies.
Es importante que no tengan nada, ya que se va a ver raro luego cuando pisen el fondo... y no usar el color blanco
adentro del personaje para que después a la hora de cortar el fondo se corte correctamente». Vale para todo personaje,
visitante, especial, skin y cara, y para los objetos sueltos de la UI; no para `bg_*`, `tunel_*` ni el `AppIcon`, que
van a sangre (el `AppIcon` igual lleva el cuello, la curita y las suelas en crema, para que el chico sea el mismo).

1. **Nada debajo ni alrededor de los pies**: ni pedestal, ni base de colección, ni diorama, ni pasto, ni nubes, ni
   charco de luz, ni sombra en el piso. El personaje, parado solo sobre blanco liso; la sombra la pone el motor. El
   Dios flota igual, sin nada debajo.
2. **Nada de blanco puro dentro del personaje**: cuello, vivos, números, curita, medias, suelas, alas del Dios, brillos,
   pelotas → **crema / marfil (cream, ivory, about #FFF3DC)** o un color. Sólo el fondo es blanco puro.
3. **Nada fuera de la silueta**: sin aura, halo, resplandor detrás, glow, rayos de luz, destellos, partículas,
   salpicaduras, líneas de movimiento ni burbujas sueltas. Lo que hace destacar al cuarto de cada piso y al Dios sale
   del personaje: ropa, pose, objetos en la mano, materiales brillantes. Una luz de borde SOBRE el personaje está bien.
   Nada translúcido (el Fantasma es de vinilo opaco).

El cierre de encuadre de todo personaje de cuerpo entero (ASCII puro, palabra por palabra):

> Full body standing character, both feet visible, hands visible, complete figure with generous margins, nothing
> under or around the feet: no base, no pedestal, no ground, no grass, no clouds, no floor shadow; no aura, glow,
> halo, sparkles or particles outside the silhouette; no pure white anywhere on the character (use cream or ivory
> instead), centered on a plain pure white background, square image, no text, no watermark, no cropping.

Visitantes y especiales usan el mismo cierre con «Full body character, complete figure with generous margins, ...».

### La lista negra legal (va en cada prompt, palabra por palabra)

> Legal blacklist: no likeness of any real football player, no real club or national team crest, kit or color
> combination (no light blue and white stripes, no national team shirts), no sports brand logo, swoosh or brand
> stripes, no real trophy or real stadium, no number 10 anywhere.

Además: las copas son diseños propios (sin orejas de la copa real; la del Campeón del Mundo y los trofeos de la UI son
«a classic invented trophy cup with two handles and one star on it», sin pelota arriba ni espiral), los números de camiseta son 22, 1, 2, 5 y 9, nada
de festejos propios de un jugador, y las botellas, micrófonos y paquetes van sin marca ni texto.

### Encuadre y modo de salida

- `project.json`: `game-asset`, tamaños 384 y 512 (los @2x/@3x de los atlas).
- Personajes: el cierre de la regla de recorte (arriba).
- Caras (`*_face`): «..., no aura, glow, halo, sparkles or particles outside the silhouette; no pure white anywhere on
  the character (use cream or ivory instead), centered on a plain pure white background, ...».
- UI: un objeto de vinilo con bisel, legible a 60 pt, sobre blanco, sin letras ni números, y «nothing outside the
  object: no sparkles, glow, light rays or particles around it, no floor shadow; no pure white anywhere on the object
  (use cream or ivory instead)». En la paleta de la UI el blanco cal pasa a «chalk cream #FFF3DC».
- `punch_holes`: las tres copas, el marco del álbum y el marco de la ruleta.
- **Fondos (`bg_*`), `AppIcon` y `tunel_*` son `raw`**: van a sangre, sin fondo blanco. Se integran desde el original
  de `output/<clave>.png`, no desde `output/assets/` (el recorte no les sirve).

## Integración (E18-F8, no es de este proyecto)

`output/` → `Tools/asset-pipeline` del juego → `Games/futbol/assets/`. Cada `.md` dice su destino en
`**destino en el juego**`.
