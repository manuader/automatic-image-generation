# automatic-image-generation

Genera imágenes con IA **usando tu cuenta del navegador, sin API key y sin pagar
por token**. El script maneja el chat web como lo haría una persona: abre una
conversación nueva, adjunta la referencia, escribe el prompt, espera la imagen y
la guarda con el nombre que corresponde. Vos escribís los prompts; él hace las
tres horas de clicks.

Está pensado para tandas grandes de imágenes que tienen que parecerse entre sí:
las skins de un videojuego, los assets de una identidad de marca, una serie de
ilustraciones con el mismo estilo. Para una imagen suelta no vale la pena.

> **Si sos un agente y venís a generar imágenes: leé este archivo entero y no
> hace falta más.** Todo lo que necesitás saber está acá. Los cuatro directorios
> de un proyecto siempre se llaman igual y el comando siempre es el mismo.

---

## 1. Instalación (una sola vez)

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

Y nada más: **no hace falta ningún permiso de macOS**. Ojo con el intérprete, que
es el error de arranque más común: las dependencias viven en el venv, así que el
comando es `.venv/bin/python generate.py`, no `python3 generate.py`.

Por qué esto merece un párrafo: hasta el 2026-08-19 sí hacía falta un permiso, el
de Accesibilidad, y era la mitad de los problemas de instalación. Los chats web
exigen input "trusted", y de ahí se había concluido que el prompt tenía que
tipearse con teclas reales del sistema (System Events), lo que además obligaba a
darle **la máquina entera al batch**: si otra ventana se ponía adelante, las
teclas se las llevaba ella. Resultó que la conclusión era más fuerte que el
hecho. Lo que no funciona es `send_keys` de Selenium; `Input.insertText` del
DevTools Protocol llega a la página con `isTrusted == true`, que es lo único que
el sitio mira, y habilita el botón de enviar igual que un humano. Es el default
desde entonces (`--typing cdp`) y por eso ahora se puede seguir usando la
computadora mientras corre la tanda.

El camino viejo sigue estando en `--typing keystroke`, y **ése sí** pide el
permiso: Ajustes del Sistema → Privacidad y seguridad → Accesibilidad → habilitar
la app desde la que corrés el script. Sin eso todas las imágenes fallan con
`osascript is not allowed to send keystrokes (1002)`.

---

## 2. De un objetivo a las imágenes, en cinco pasos

Supongamos el objetivo: *"las cinco skins alternativas de los personajes de mi
juego"*, o *"los assets de marca de una cafetería: logo, ícono, patrón, packaging"*.

**1 · Creá el proyecto** copiando la plantilla:

```bash
cp -R projects/_template projects/cafeteria
```

**2 · Escribí el objetivo** en `projects/cafeteria/OBJETIVO.md`. El script no lo
lee: es para vos y para el próximo agente. Va el qué, el estilo común y las
decisiones que no se re-discuten.

**3 · Poné una referencia** en `projects/cafeteria/references/` si querés que las
imágenes se parezcan a algo que ya existe. Es *la* palanca de consistencia: sin
referencia cada imagen sale con su propio estilo.

**4 · Escribí un `.md` por imagen** en `projects/cafeteria/prompts/` (formato en
el §4). Uno por imagen, numerados, con la clave que va a tener el archivo.

**5 · Corré**:

```bash
.venv/bin/python generate.py --engine gemini --launch          # una vez: abre el Chrome aislado y logueás
.venv/bin/python generate.py --project cafeteria --dry-run     # ¿qué va a generar?
.venv/bin/python generate.py --project cafeteria               # a laburar
```

Las imágenes aparecen en `projects/cafeteria/output/<clave>.png`.

---

## 3. La estructura de un proyecto

Fija a propósito. Que los directorios se llamen siempre igual es lo que permite
que alguien que nunca vio esto sepa dónde escribir sin preguntar.

```
projects/<nombre>/
├── OBJETIVO.md      para qué son estas imágenes. Lo leés vos, no el script.
├── project.json     ajustes. Todo opcional.
├── prompts/         NN_clave.md — UNO POR IMAGEN. Acá escribís.
├── references/      las imágenes que se adjuntan al chat y vienen de afuera.
├── output/          ⬅ ACÁ QUEDAN LAS IMÁGENES: <clave>.png
│   └── assets/      sólo en modo game-asset: los PNG recortados y escalados.
└── state/           checkpoint de la corrida y descartes, para auditar.
```

**`output/` es también la memoria del proyecto.** La cola saltea todo prompt que
ya tenga su PNG ahí. Eso es lo que hace que un Ctrl-C, un logout o una cuota
agotada no cuesten nada: volvés a correr el mismo comando y sigue donde quedó. Y
es lo que hace que copiar imágenes viejas a `output/` alcance para no volver a
pagarlas.

⚠️ `output/` y `state/` **no se versionan** (ver `.gitignore`): son cientos de
megas y crecen para siempre. Pero eso significa que un clon limpio del repo
vuelve a generar todo. Los originales son el activo del proyecto — copialos
aparte, no confíes en git para eso.

### `project.json`

```json
{
  "engine": "gemini",
  "output": "raw",
  "sizes": [],
  "punch_holes": [],
  "reference_threshold": 4
}
```

| clave | qué hace |
|---|---|
| `engine` | motor por defecto: `gemini` o `chat-gpt`. `--engine` lo pisa. |
| `output` | `raw` o `game-asset`. Ver §5. |
| `sizes` | lados a exportar en `game-asset`. Vacío = sólo el recorte, en resolución nativa. |
| `punch_holes` | claves cuyo blanco encerrado SÍ es un hueco calado (ver §5). |
| `reference_threshold` | ver §6, "cuando la referencia se parece demasiado". |
| `typing` | `cdp` (default) o `keystroke`. Ver §1. `--typing` lo pisa. |

---

## 4. El formato de un prompt

Un archivo por imagen, en `prompts/`, llamado `NN_clave.md`:

- **`NN`** es el orden en que se generan (dos o tres dígitos). `00_` está
  reservado para un índice y nunca se genera.
- **`clave`** es el nombre que va a tener el PNG: `12_logo_principal.md` →
  `output/logo_principal.png`.

```markdown
# 12 — Logo principal

- **estado**: pendiente
- **referencia**: adjuntar `references/paleta.png`

## Prompt

El texto exacto que se le manda al modelo. Todo lo que esté debajo de
`## Prompt` se tipea tal cual, sin que el script le agregue ni le saque nada.
```

Sólo tres cosas importan (y una cuarta opcional, sólo para la rotación):

- **`estado`**: `pendiente` o `hecho`. Lo cambia el script solo, **después** de
  verificar el PNG. Ponerlo en `hecho` a mano es la forma de saltear un prompt.
- **`referencia`**: opcional. El path de la imagen a adjuntar (§6). Sin este
  campo, no se adjunta nada.
- **`## Prompt`**: obligatorio. Un `.md` sin esta sección hace fallar la cola
  ruidosamente, que es lo que se quiere: mejor un error que una imagen contra un
  prompt vacío.
- **`familia`**: opcional, una palabra (`- **familia**: ceo`). Las imágenes con
  la misma familia salen del mismo motor y en la misma tanda de la rotación
  (§9, "Rotación"): un personaje y sus skins, por ejemplo. Va arriba de
  `## Prompt`; sin el campo, la imagen es suelta.

### Cómo se escribe un prompt que sale bien

Lo aprendido en 335 imágenes:

- **Poné el estilo primero, no al final.** Lo primero que lee el modelo es lo que
  más pesa en la composición.
- **Si querés que se parezca a la referencia, decilo explícitamente**: *"Match
  EXACTLY the art style, line weight, proportions and color treatment of the
  attached reference"*. Adjuntarla no alcanza.
- **Describí la composición en términos medibles**, no estéticos. "El horizonte
  a media altura del cuadro" funciona; "que se vea espacioso" no.
- **Si vas a usar modo `game-asset`, pedí fondo blanco liso**: *"centered on a
  plain pure white background, square image, no text, no watermark, no cropping"*.
  El recorte depende de eso (§5).
- **Nombrar lo que NO querés funciona.** Si la referencia tiene un encuadre que
  no querés repetir, decí que ese encuadre está mal.

---

## 5. Los dos modos de salida

Se elige con `output` en el `project.json`, o con `--output` en la línea de
comandos. **El original crudo se guarda siempre en los dos**: es lo que costó
cuota, y el post-proceso se puede repetir mil veces sobre él sin gastar nada.

### `raw` — sólo guardar la imagen

El default. La imagen tal cual la devolvió el modelo, en `output/<clave>.png`.
Es lo que querés para identidad de marca, ilustración, referencia visual,
moodboards: cualquier cosa donde la imagen es el producto final.

### `game-asset` — procesar el PNG para un videojuego

Además del original, escribe en `output/assets/`:

- `<clave>.png` — la imagen **sin fondo**, en resolución nativa;
- `<clave>_<lado>.png` — una por cada tamaño de `sizes`, con la proporción
  respetada.

El recorte es **por conectividad, no por saliencia**: fondo es lo blanco que se
toca con el borde del lienzo, y nada más. Suena a detalle y es la diferencia
entre que funcione y que no. Un modelo de saliencia (`rembg` y compañía) mira la
imagen y decide "qué es el sujeto": con arte cartoon sobre fondo blanco confunde
un guardapolvo blanco con el fondo y lo deja transparente. Acá una camisa blanca
está rodeada por la línea del dibujo, no se conecta con el borde, y por lo tanto
**jamás** se recorta.

La excepción es el hueco calado de verdad —el aire entre dos anillos
concéntricos, el ojo del asa de una copa—, que sí es blanco encerrado y sí hay
que sacar. Como el color no lo distingue de una camisa, se declara a mano:

```json
{ "punch_holes": ["fx_tap", "ui_trophy_gold"] }
```

Para rehacer el recorte o cambiar los tamaños sin generar nada de nuevo:

```bash
.venv/bin/python generate.py --project cafeteria --reprocess
```

---

## 6. Cómo se linkea una imagen a un prompt

El campo `**referencia**` de cada `.md` lleva un path que se resuelve **desde la
raíz del proyecto**. Hay dos orígenes válidos y la diferencia es de dónde vino la
imagen:

```markdown
- **referencia**: adjuntar `references/paleta.png`     ← algo que trajiste vos
- **referencia**: adjuntar `output/logo_principal.png` ← algo que este script generó
```

El segundo caso es el que hace posible una serie coherente: **el prompt 20 puede
adjuntar la imagen que generó el prompt 12 en la misma corrida.** El logo se
genera primero y los cinco assets que derivan de él lo adjuntan; una skin adjunta
al personaje del que es variante. No hace falta ninguna opción extra: el PNG se
guarda apenas se genera, y el prompt que viene después ya lo encuentra.

Es una referencia por prompt. Si hacen falta dos imágenes de contexto, la salida
sana es generar primero una imagen que las combine y adjuntar ésa.

### Cuando la referencia se parece demasiado

El script tiene que distinguir la imagen generada de la referencia adjunta,
porque en la pantalla del chat están las dos y las dos son grandes. Lo hace con
una huella de píxeles: si la candidata se parece mucho a la referencia, la
descarta y sigue esperando.

Eso se rompe cuando lo que estás generando **es** casi la referencia (una
variante del mismo personaje con otra ropa): el resultado legítimo queda tan
cerca que el filtro se lo come, y el script espera el timeout entero sin
encontrar nada. Ahí se baja el umbral:

```json
{ "reference_threshold": 4 }
```

Lo descartado queda en `state/discards/` con la distancia en el nombre del
archivo, justamente para que puedas mirarlo y decidir el número mirando en vez
de adivinando. Referencia: la misma imagen re-codificada mide < 0.15; una
variante que conserva la pose midió 9.51; un sujeto enteramente negro contra su
referencia, 25.8.

---

## 7. Todos los comandos

```bash
.venv/bin/python generate.py --engine gemini --launch      # abre el Chrome aislado del motor (logueate ahí)
.venv/bin/python generate.py --engine chat-gpt --probe     # ¿el motor reconoce la página? cuota: cero
.venv/bin/python generate.py --project X --dry-run         # la cola, sin generar
.venv/bin/python generate.py --project X                   # generar
.venv/bin/python generate.py --project X --only logo       # una sola
.venv/bin/python generate.py --project X --limit 5         # las cinco primeras
.venv/bin/python generate.py --project X --reprocess       # rehacer la salida, sin navegador
.venv/bin/python supervisor.py --project X                 # todo el proyecto, sin nadie mirando
.venv/bin/python supervisor.py --project X --rotate gemini:50,chat-gpt:50 --dry-run   # el plan de tandas
.venv/bin/python supervisor.py --project X --rotate gemini:50,chat-gpt:50             # tandas alternadas
.venv/bin/python -m unittest discover -s tests -t tests   # los tests
```

Las que se tocan cuando algo va mal: `--timeout`, `--retries`, `--ref-threshold`,
`--max-consecutive-failures`, `--typing` (§1). Y sólo con `--typing keystroke`,
que es el único modo que pasa por la cola de eventos de macOS: `--type-chunk`
(bajalo si la máquina está cargada y se pierden caracteres) y `--type-pause`.

---

## 8. Cuando falla

| Síntoma | Qué pasa |
|---|---|
| `ModuleNotFoundError: No module named 'selenium'` | Corriste con `python3` en vez de `.venv/bin/python` (§1). |
| `osascript is not allowed to send keystrokes (1002)` | Estás en `--typing keystroke` y falta el permiso de Accesibilidad. Con el default (`cdp`) este error no existe (§1). |
| `no pude conectar Selenium al Chrome aislado` | No corriste `--launch`, o cerraste esa ventana. |
| `timeout esperando el cuadro de prompt` | La sesión se cerró: logueate de nuevo en la ventana aislada. |
| `el editor no tomó el foco` | La ventana aislada se cerró mientras corría la tanda. |
| `timeout esperando la miniatura de la referencia adjunta` | El paste no pegó. Casi siempre es la ventana aislada cerrada o la pestaña en otra URL. |
| `no pude devolverle el foco a Chrome […] al frente está «X»` | Sólo en `--typing keystroke`: la ventana X se quedó adelante. Cerrala o minimizala. |
| `el editor no coincide con lo tipeado hasta acá` | Sólo en `--typing keystroke`: el cursor se movió y la tanda se intercaló. **No se envió nada**: cuota intacta. Reintentá. |
| `alcanzó su límite de uso` | Cuota de **mensajes** agotada. El batch se frena solo tras 3 fallos seguidos. |
| `se quedó en «creando tu imagen» sin devolver imagen` | Cuota de **imágenes** agotada, que Gemini no informa: deja el cartel puesto para siempre (medido: 10 min sin cambio, y con un prompt trivial sin referencia pasa igual). Subir `--timeout` no sirve. Esperá a que se renueve y volvé a correr el mismo comando. |
| La cola sale vacía y no debería | Ya hay un PNG en `output/` con esa clave, o el `.md` dice `hecho`. |
| `timeout esperando la imagen generada (distinta de la referencia)` | El filtro de huella se comió el resultado: bajá `reference_threshold` y mirá `state/discards/`. |

Todos los fallos quedan anotados con su motivo en `state/run.json`.

---

## 9. Los motores

| motor | puerto | estado |
|---|---|---|
| `gemini` | 9222 | **Verificado en producción**: 335 imágenes generadas con él. |
| `chat-gpt` | 9223 | **Escrito y medio verificado.** Ver abajo. |

Cada motor abre **su** Chrome en **su** puerto, y no es un detalle: el launcher
da por buena cualquier ventana que ya conteste en el puerto pedido, así que con
un puerto compartido el segundo motor reusaría en silencio la sesión del primero.

La mecánica que hace el trabajo pesado —el tipeo, el foco, el paste de la
referencia, la extracción por canvas, la huella de píxeles— vive en
`core/webchat.py` y **no tiene nada de ningún proveedor adentro**. Un motor es un
archivo de cuatro constantes: la URL, el selector del botón de enviar, la marca
de la URL de conversación y las frases con las que ese sitio dice "no puedo".

De ChatGPT se comprobó contra la página lo más importante:

- `chatgpt.com` carga sin redirigir y el cuadro de texto (`#prompt-textarea`, un
  ProseMirror) lo encuentra el selector genérico;
- **`send_keys` de Selenium no aterriza en ese editor** — se tipeó "hola" y el
  composer quedó vacío.

⚠️ De ese segundo punto se había concluido que ChatGPT necesitaba teclas reales
del sistema. La conclusión no se sostiene: el 2026-08-19 se midió contra Gemini
que `Input.insertText` de CDP **sí** aterriza y **sí** habilita el botón de
enviar (§1). O sea que lo que falla es `send_keys`, no todo lo que no sea una
tecla de macOS, y lo primero que conviene probar en ChatGPT es el default `cdp`
—no el camino de teclas— porque los dos editores son contenteditable y el
mecanismo es el mismo.

Lo que falta verificar es el botón de enviar, y por una razón concreta: con el
composer vacío ese botón **no existe** (en su lugar está el de voz), así que
revelarlo exige tipear de verdad. Cuesta un comando y cero cuota:

```bash
.venv/bin/python generate.py --engine chat-gpt --launch    # logueate en esa ventana
# escribí una palabra a mano en el composer, y entonces:
.venv/bin/python generate.py --engine chat-gpt --probe
```

Si `send_button` sale `null` **con algo escrito**, lo que hay que corregir es una
línea de `chat-gpt/browser.py`; el archivo explica cuál y cómo. Los tests
(`tests/test_engines.py`) ya garantizan que el perfil está completo, que los
selectores son buscables y que las frases de bloqueo pueden llegar a matchear —
lo que no pueden garantizar es que sean las que el sitio usa hoy.

### Rotación: tandas alternadas entre motores

Para que ningún sitio vea un batch entero —y no banee la cuenta—, el supervisor
puede turnar los motores en tandas:

```bash
.venv/bin/python supervisor.py --project X --rotate gemini:50,chat-gpt:50 --dry-run
.venv/bin/python supervisor.py --project X --rotate gemini:50,chat-gpt:50
```

50 imágenes con Gemini, 50 con ChatGPT, 50 con Gemini… hasta vaciar la cola. Las
reglas:

- **Se cuentan las enviadas, no las logradas.** Un pedido que llegó al sitio
  cuenta aunque la imagen no salga (un reintento cuenta otra vez); un fallo del
  navegador antes de enviar o una cuota avisada de entrada no cuentan.
- **La cola manda.** Lo que ya está `hecho` o tiene su PNG en `output/` no se
  envía, y el orden es siempre el de la cola: la rotación sólo decide qué motor
  pide la próxima imagen.
- **Sin cuota, cede el turno.** Si el motor de turno se queda sin cuota (o su
  sesión se cerró), queda en pausa como siempre y la tanda arranca en el próximo
  motor, con la misma imagen que falló primero. Si todos están en pausa, espera.
- **Una familia no se parte.** Si la familia que sigue (§4, `familia`) no entra
  entera en lo que le queda a la tanda, la tanda **corta antes** y la familia
  arranca la siguiente: las tandas nunca pasan de su tamaño. La única excepción
  es una familia más grande que una tanda entera: va sola en la suya, completa.
  Los miembros de una familia viajan juntos aunque estén desparramados en la
  numeración (en el lugar del primero). Lo único que puede partir una familia es
  la cuota a mitad de ella; queda avisado con ⚠ en `state/supervisor.log`.
- **Se retoma.** El turno y lo enviado en él se guardan en
  `state/supervisor.json`: Ctrl-C y el mismo comando siguen en la misma tanda.
  Cambiar el `--rotate` arranca la rotación de cero.
- **`--dry-run`** muestra el plan —motor, cantidad y familias de cada tanda—
  desde donde quedó la corrida, sin abrir navegadores ni tocar el estado. Es el
  plan sin cuotas: si un motor se queda sin, las tandas se corren, el orden no.

Con `--rotate`, la lista de motores es la de la rotación (`--engines` no se usa)
y `--engine-for` no se combina: la rotación decide el motor de cada imagen.

### Agregar un motor nuevo

Un directorio con un `browser.py` que exponga una clase `Browser` heredando de
`WebChatBrowser` y declare esas constantes. `gemini/browser.py` son 45 líneas y
es el ejemplo a copiar. Los tests de contrato lo agarran solo, sin tocar nada.

---

## 10. Cómo está armado

```
core/         la parte genérica: no sabe qué modelo hay ni para qué son las imágenes
  queue.py        leer los .md, saber qué falta generar
  runner.py       generar → guardar → verificar → marcar hecho, en ese orden
  webchat.py      toda la mecánica de manejar un chat web (tipeo, foco, paste)
  cutout.py       el recorte de fondo por conectividad
  postprocess.py  los dos modos de salida
  project.py      dónde vive cada cosa de un proyecto
gemini/       ┐ un archivo de constantes por proveedor
chat-gpt/     ┘
projects/     los objetivos: prompts, referencias y salida
tests/        68 tests, ninguno necesita navegador
generate.py   el único comando
```

Los 68 tests corren sin Chrome a propósito: una suite que necesitara navegador no se
correría nunca, y lo que hay que proteger —que el prompt llegue entero, que no se
envíe uno barajado, que un error no voltee la tanda— se prueba sin él.
