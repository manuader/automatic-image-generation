# Objetivo — Santa Tuca

**Qué:** 10 assets gráficos para el debut en YouTube de **Santa Tuca** (Alan),
creador cannábico de Buenos Aires (~48-80k en Instagram: tours de cultivo,
cobertura de eventos, activismo y una línea de indumentaria). No son piezas
terminadas: son **elementos sueltos para animar** con un generador de video y
meter en el vlog.

**El nombre es la identidad.** "Tuca" es la colilla del porro, así que *Santa
Tuca* es "Santa Colilla": la marca es una parodia cariñosa de santoral. De ahí
salen la aureola y las alas de los assets que ya existen, y de ahí sale todo lo
que se agregó — los rayos, la estampita, el corazón sagrado.

## El sistema

| | |
|---|---|
| contorno | `#1A1A1A` |
| amarillo aureola | `#FFD32A` + glow `#FFE97A` |
| verde cogollo | `#33A02C` · oscuro `#1B5E20` · claro `#7CC576` |
| papel del porro | `#E8E8E8` + sombra `#C9C9C9` |
| brasa | `#F03A17` |
| dorado (alas, rayos) | `#E8C07A` + sombra `#C9954A` |

**Estilo:** sticker troquelado. Un solo contorno negro de grosor parejo, relleno
plano, un tono más oscuro para sombra y uno más claro para luz. Nada de
degradados, nada de 3D, nada de aerógrafo. Formas gordas y redondeadas.

⚠️ **La paleta está estimada a ojo**, no muestreada: los assets de referencia
llegaron por chat y no como archivos, así que no se pudieron abrir para sacarles
el color exacto. Si aparecen los originales, van a `references/` y se re-corre —
ver abajo.

## Cómo se sostiene la consistencia sin referencia externa

El primer prompt, `01_logo_estampita`, **no adjunta nada**: describe el estilo
entero por texto y es el ancla. Los otros nueve adjuntan
`output/logo_estampita.png`, o sea la imagen que generó el prompt 01 en la misma
corrida. Es el encadenado que el script soporta de fábrica (§6 del README) y acá
es la única forma de tener un estilo común sin un archivo de partida.

Cada uno de esos nueve dice explícitamente **"copiá el estilo, NO el sujeto ni la
composición"**: sin esa frase el modelo devuelve variantes de la estampita en vez
de un asset nuevo.

**Si conseguís los PNG originales** (la aureola, el porro con alas, el cogollo),
copialos a `references/` y cambiá el campo `**referencia**` de los `.md` para que
apunten ahí. Van a pegar más fino que el ancla generada.

## Modo de salida: `game-asset`

Es lo que hace que sirvan para video. Además del original, escribe en
`output/assets/` **el PNG sin fondo** — el recorte es por conectividad, así que
lo blanco que toca el borde se va y el dibujo queda con alpha limpio, listo para
tirar en el editor sin recortar a mano.

Dos cosas que eso obliga y que están en todos los prompts:

- **Fondo blanco puro y márgenes generosos**, sin nada tocando el borde.
- **Ningún blanco puro DENTRO del dibujo.** El papel del porro va en `#E8E8E8` y
  no en blanco: `WHITE_TOLERANCE` es 14, o sea que se considera fondo todo lo que
  esté por encima de 241 en los tres canales, y un papel en `#EDEDED` (237) pasa
  raspando. `#E8E8E8` (232) deja margen.

**Huecos calados: medido, y por eso queda apagado.** Se probó
`punch_holes: ["logo_estampita"]` sobre el emblema y el resultado es mitad y
mitad. Bien: cala el interior de la aureola y el blanco encerrado entre los
rayos, que sobre un video se vería como un manchón. Mal: se lleva también **los
dos brillos del papel del porro**, que el modelo pintó en blanco puro pese a que
el prompt lo prohíbe, y deja dos rayas transparentes en el cuerpo del porro.

No hay forma de pedir "calá los huecos grandes y no los chicos" sin tocar
`core/cutout.py`, así que la decisión queda tuya y sale gratis: si sobre el video
molesta más el manchón que las rayas, poné

```json
{ "punch_holes": ["logo_estampita"] }
```

```bash
.venv/bin/python generate.py --project santatuca --reprocess
```

`--reprocess` rehace el recorte desde el original ya generado: cuota cero.

## Decisiones que no se re-discuten

- **Los 10 son gráficos, no recortes de cara.** Los assets que ya existen usan
  fotos suyas recortadas; eso se hace con la foto real, no con un generador —
  pedirle a un modelo la cara de una persona concreta sale mal y además no hace
  falta: lo que un vlog necesita repetido son elementos gráficos.
- **Todo se piensa para animarse.** Cada asset tiene un movimiento obvio: la
  aureola brilla, los rayos giran, la llama titila, el grinder gira, el estallido
  escala, los carteles entran de costado.
- **El texto va en castellano rioplatense.** `SUSCRIBITE`, no "suscríbete".
## Estado

**10 de 10 generadas**, cada una con su original en `output/` y su PNG con alpha
en `output/assets/`.

### Dos cosas que pasaron y conviene saber

**Hay otro proyecto consumiendo esta salida.** Durante la corrida apareció
`~/Desktop/projects/santa-tuca/` y se fue llevando los recortes a su
`assets/images/` a medida que salían — por eso a mitad de camino faltaban seis
recortes y dos originales acá. No se perdió nada: estaban movidos, no borrados.
Los recortes se copiaron de vuelta (copiados, no movidos: el otro proyecto quedó
intacto) y los dos originales que se habían ido —`nube_humo` y `reloj_420`— se
reconstruyeron componiendo su recorte sobre blanco. Son equivalentes para
`--reprocess`, pero **no son el archivo crudo que devolvió el modelo**.

**Aparecieron los assets originales de la marca.** Estaban en esa misma carpeta
desde junio: `santa-tuca.png`, `tuca.png`, `tuca-big.png` y `weed.png`, todos
1080x1920 con alpha. Se copiaron a `references/`. Son los que faltaban al
empezar, y con ellos se puede hacer una segunda vuelta mejor: cambiar el campo
`**referencia**` de los `.md` para que apunten ahí en vez de a
`output/logo_estampita.png`, y muestrear la paleta real en vez de la estimada.

### Lo aprendido en estas 10

- **El ancla generada funciona.** Los nueve que adjuntaron `logo_estampita.png`
  heredaron contorno, paleta y peso de línea sin excepción. La frase que lo hace
  posible es *"copiá el estilo, NO el sujeto ni la composición"*: sin ella el
  modelo devuelve variantes del emblema.
- **El modelo agrega un borde blanco de sticker aunque se le pida "no frame".**
  Cuando ese borde queda suelto, el recorte por conectividad se lo lleva junto
  con el fondo (pasó en `cogollo_mascota`). Cuando el modelo le dibuja su propio
  contorno gris, queda encerrado y sobrevive — se ve en `corazon_sagrado`,
  `encendedor_llama`, `lower_third` y `cartel_suscribite`. Queda lindo, pero si
  no lo querés hay que pedir explícitamente que el contorno exterior sea del
  color del dibujo y no blanco.
- **El reloj a las 4:20 se ve raro y está bien.** A esa hora el minutero apunta
  al 4 y la horaria queda apenas pasándolo, así que las dos agujas van casi
  superpuestas. Es la hora correcta, no un error de dibujo.
