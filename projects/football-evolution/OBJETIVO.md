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
| blanco cal | `#F4F7F2` | líneas de cal, ribetes |
| negro tablero | `#111418` | el tablero LED, los marcos |
| amarillo tarjeta | `#FFD400` | la acción: botones, cinta de capitán, banderines |
| dorado premium | `#E2B93B` | lo premium: estrellas, skins Doradas, el Dios |

La camiseta del club del protagonista es **verde azulado (teal) con cuello blanco y el 22** (la de la hoja). Las demás
son inventadas y se eligieron para no coincidir con ninguna real: escuelita **naranja y blanca**, ascenso **mostaza y
negra**, el club europeo **azul noche y cobre**, la selección **violeta con naranja**. Nunca celeste y blanca.

### El protagonista: un solo chico creciendo

Los 37 niveles y los 8 de los puestos son **el mismo protagonista**. Cuatro rasgos fijos, escritos igual en TODOS los
prompts de personaje:

1. remolino de pelo castaño oscuro parado en la coronilla, sobre pelo corto y lacio (**nunca rulos**);
2. pecas en nariz y mejillas;
3. curita blanca en la rodilla **IZQUIERDA**;
4. botines verde lima de suela blanca (el Rey del Potrero los lleva colgados al hombro; el bebé, botitas).

Sin barba en ningún nivel. En las caras (`*_face`, retrato de cabeza y hombros) la curita y los botines quedan fuera de
cuadro y el prompt lo dice: los rasgos 1 y 2 se ven siempre.

### Hojas de continuidad: tipo + skins + cara

Cada tipo tiene un bloque fijo «Look of this level» (edad, ropa, pose, objetos, expresión) que se repite **palabra por
palabra** en su original, en sus 3 skins de familia (Retro, Barro de Potrero, Dorada), en sus skins especiales y en su
cara. La skin sólo cambia el tratamiento de la ropa («keep EXACTLY the same face, age, body, silhouette and pose»).
Todos esos `.md` llevan `- **familia**: <id_del_tipo>`, así la rotación los manda juntos al mismo motor.

- **Retro** (común): camiseta de algodón vieja con cuello de cordones y número cosido, short largo, medias de lana,
  pelota de cuero con tiento, colores un poco sepia.
- **Barro de Potrero** (rara): la misma ropa embarrada después de un partido con lluvia; la curita y el lima se leen.
- **Dorada** (épica; **legendaria en los pisos 9 y 10**, con aura y destellos): la ropa en vinilo dorado pulido; los
  botines siguen lima con cordones dorados.
- Skins especiales: Buzo Flúor (arquero), La Primera Camiseta y Camiseta de Despedida (bebé), Aureola y De Gala (Dios).

Visitantes, especiales y el Aguatero son **otros personajes**, mismo estilo: la referencia se adjunta sólo como guía y
el prompt pide «a different, new character». Cada uno repite su «Look» en todas sus poses (retrato, `_talk`, `_action`,
`_face`, y `_enojado` del utilero) y todas llevan `familia: <su id>`.

### Cómo escala cada piso (regla del dueño)

El cuarto de cada piso es **MUCHO** más destacado que el primero. Se escala en cuatro cosas: ropa, equipo, escenario y
brillo.

| posición en el piso | qué pide el prompt |
|---|---|
| 1 | lo más simple del piso: sin base, sin brillo, sólo sombra de contacto |
| 2 | un paso más seguro, todavía sin base ni brillo |
| 3 | más pulido, una luz de borde cálida suave, sin base |
| 4 | pose heroica, su mejor ropa y equipo, luz dorada fuerte, brillo detrás, destellos, y **parado sobre una base de colección redonda con el diorama del piso** |

En el piso 3 el cuarto es el nivel 12 (los cuatro de Sexta). Los dioramas de cada piso:

| piso | diorama de la base (y tema del fondo) |
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

**El 37, Dios del Fútbol, es una divinidad**, no un futbolista: camiseta dorada **sin número** ni escudo, aura dorada,
alitas blancas, una pelota de energía azul y blanca girando sobre la palma, flotando sobre una base de estadio
celestial de nubes. Sin el 10, sin rulos, sin celeste y blanca. El ícono de la app NO lo usa (clasificación 4+): usa al
Debutante Profesional.

### La lista negra legal (va en cada prompt, palabra por palabra)

> Legal blacklist: no likeness of any real football player, no real club or national team crest, kit or color
> combination (no light blue and white stripes, no national team shirts), no sports brand logo, swoosh or brand
> stripes, no real trophy or real stadium, no number 10 anywhere.

Además: las copas son diseños propios (sin orejas de la copa real), los números de camiseta son 22, 1, 2, 5 y 9, nada
de festejos propios de un jugador, y las botellas, micrófonos y paquetes van sin marca ni texto.

### Encuadre y modo de salida

- `project.json`: `game-asset`, tamaños 384 y 512 (los @2x/@3x de los atlas).
- Personajes: «centered on a plain pure white background, square image, no text, no watermark, no cropping».
- UI: un objeto de vinilo con bisel, legible a 60 pt, sobre blanco, sin letras ni números.
- `punch_holes`: las tres copas, el marco del álbum y el marco de la ruleta.
- **Fondos (`bg_*`), `AppIcon` y `tunel_*` son `raw`**: van a sangre, sin fondo blanco. Se integran desde el original
  de `output/<clave>.png`, no desde `output/assets/` (el recorte no les sirve).

## Integración (E18-F8, no es de este proyecto)

`output/` → `Tools/asset-pipeline` del juego → `Games/futbol/assets/`. Cada `.md` dice su destino en
`**destino en el juego**`.
