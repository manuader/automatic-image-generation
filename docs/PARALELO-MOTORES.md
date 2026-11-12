# Gemini y ChatGPT en paralelo

Pedido del dueño (2026-11-12): con `--rotate gemini:50,chat-gpt:50` un motor
trabaja y el otro espera, y si el que tiene el turno está sin cuota quedan los
dos quietos. ¿Pueden trabajar los dos a la vez, cada uno con su cola de tandas
de 50, sin robarse el foco ni pisarse el tipeo?

## Veredicto: SEGURO CON CAMBIOS

El tipeo y el foco no se pisan: cada motor escribe por CDP en su propio Chrome.
Lo que sí se pisaba era el estado compartido y el reinicio duro. Las dos cosas
quedaron arregladas en la rama `paralelo-motores`, con el modo
`--parallel gemini:50,chat-gpt:50`.

## Evidencia

Los números de línea son de `00e1500`, el commit del que sale la rama.

### Lo que ya era seguro

- **Un Chrome por motor, con su puerto y su perfil.** Gemini usa 9222
  (`gemini/browser.py:15`) y ChatGPT 9223 (`chat-gpt/browser.py:47`). Cada uno
  tiene su `--user-data-dir` (`core/chrome.py:31`) y Selenium se engancha por
  `debugger_address` a su puerto (`core/webchat.py`, `_driver`). Son dos
  procesos de Chrome distintos con dos sesiones CDP distintas.
- **El tipeo no pasa por el teclado del sistema.** El default es `cdp`
  (`generate.py:92`, `TYPING_DEFAULT = "cdp"`). El prompt entra con
  `Input.insertText` (`core/webchat.py:697`), que va por la conexión CDP de ESE
  Chrome directo a su documento, sin pasar por la cola de eventos de macOS. El
  propio archivo lo deja anotado: «no le roba el frente a nadie»
  (`core/webchat.py:71`). Así que el texto de un motor no puede terminar en la
  ventana del otro. `football-evolution/project.json` no pisa `typing`, así que
  usa `cdp`.
- **El foco que se pide es foco del DOM, no del sistema.** `_focus_editor_dom`
  hace `Page.bringToFront` y `focus()` por JS y comprueba
  `document.activeElement` (`core/webchat.py:427`). Funciona con la ventana
  tapada; está medido y comentado en el mismo archivo. Además, `_send_now`
  (`core/webchat.py:652`) no envía si el prompt no está entero en el editor. Si
  algo raro se metiera en el medio, el pedido se aborta como fallo del
  navegador, sin gastar cuota.
- **El único camino que SÍ comparte foco** es `--typing keystroke`: hace
  `osascript … activate` y teclea con System Events (`core/webchat.py:556`,
  `:701`, `:711`). Con dos motores se pisarían. Por eso `--parallel` se niega a
  arrancar si el proyecto tiene `"typing": "keystroke"`.
- La trampa conocida de «Gemini acumula texto» (guarda el borrador y lo
  devuelve) es de cada Chrome por separado y ya la resuelve `_clear_draft`
  (`core/webchat.py:359`). No tiene nada que ver con correr dos motores.

### Lo que NO era seguro (y se cambió)

1. **`state/run.json` con dos escritores.** `RunCheckpoint` leía el archivo una
   vez al arrancar (`core/checkpoint.py:31`) y en cada anotación lo reescribía
   entero (`:38-39`). Con dos `generate.py` a la vez, el segundo borraba el
   motivo de fallo que había escrito el primero. El supervisor lo leía como
   «terminó sin anotar motivo» y lo clasificaba mal. El supervisor también lo
   reescribía al limpiar el motivo viejo (`supervisor.py:311`).
2. **El reinicio duro mataba lo del otro motor.** `_kill_engine` hacía
   `pkill -f "generate.py --project"` y `pkill -f chromedriver`
   (`supervisor.py:282-284`). En paralelo, tres fallos de un motor se llevaban
   puesto el pedido en curso del otro.
3. **Contadores globales.** `failures_in_a_row`, `stuck_in_a_row`,
   `resets_without_progress` y `verified` eran uno solo para todos los motores
   (`supervisor.py:165-166`). En paralelo, los fallos de uno disparaban el
   reinicio del otro.
4. **`state/supervisor.json`.** Tiene un solo escritor (el supervisor), pero con
   dos hilos haría falta un candado. Sin él, `json.dump` puede leer un dict
   mientras el otro hilo lo cambia.
5. **`state/generate.log` compartido** (`supervisor.py:163`). Las salidas de
   dos generadores quedarían intercaladas y no se podrían leer.

## Qué cambió

- **`core/checkpoint.py`**: `locked()` y `update_json()`, que toman un candado
  `fcntl` sobre `run.json.lock`. `RunCheckpoint` relee el archivo bajo ese
  candado en cada anotación, así que lo que escribió el otro proceso queda.
  `Supervisor.attempt` limpia el motivo viejo con el mismo candado.
- **`core/parallel.py`** (nuevo, puro):
  - `parse_parallel`: cada motor una sola vez.
  - `units`: lo que va al mismo motor. Una familia entera, por ejemplo
    `npc_hincha` + `_talk` / `_action` / `_face`, y también una imagen cuya
    referencia es `output/<otra pendiente>.png`.
  - `claim_batch`: la próxima tanda de hasta N imágenes con unidades libres del
    frente de la cola, sin partir ninguna (la misma regla `fits` de la rotación).
- **`supervisor.py`**:
  - `Lane`: un hilo por motor. Tiene sus propios contadores, su `verified` y su
    `generate-<motor>.log`. Todo lo que decide y anota lo hace con un candado
    compartido tomado; lo suelta sólo mientras espera afuera (el generador, el
    probe, un sleep), mediante `blocking()`. Así los dos navegadores trabajan
    a la vez y el estado nunca se toca desde dos hilos.
  - El reinicio duro de un carril mata sólo **su** grupo de procesos (el
    generador y su chromedriver, que hereda el grupo) y **su** Chrome, por el
    perfil.
  - **Pausas por motor**: se siguen guardando en `blocks`, igual que antes.
    Cuando un motor entra en pausa, suelta las unidades de su tanda que no
    empezó y el otro las toma cuando reserva su tanda siguiente. Si una
    familia ya tiene alguna imagen hecha por ese motor, la conserva y el resto
    de la familia espera su cuota. La única excepción: si al otro motor no le
    queda nada que hacer, se la lleva y lo avisa con ⚠ en la bitácora, como la
    rotación cuando la cuota parte una familia.
  - Las reservas se guardan en `supervisor.json`, en el campo `parallel`:
    `{"spec", "claims": {motor: [{"keys", "started"}]}}`. Si se corta con
    Ctrl-C, el mismo comando sigue con las mismas tandas. Si se cambia el
    `--parallel`, las reservas se tiran y se arma un reparto nuevo.
  - `--dry-run` con `--parallel` muestra la primera tanda de cada motor.
  - `--parallel` no se combina con `--rotate` ni con `--engine-for`.
- **Tests**: `tests/test_parallel.py` (14 tests). Cubren:
  - el parseo, las unidades y las tandas;
  - el candado de `run.json` (dos escritores que antes se borraban);
  - que los dos motores se solapan de verdad (intervalos medidos);
  - que ninguna imagen se pide dos veces y que una familia va entera a un motor;
  - que la cuota de un motor le pasa la tanda al otro;
  - que el reinicio mata sólo lo propio;
  - que las reservas sobreviven a un reinicio y que una familia empezada espera
    a su motor;
  - el `--dry-run` y que no se combina con `--rotate`.

  `tests/fake_generate.py` ahora escribe bajo candado, como el generador real.
  Suite completa: `.venv/bin/python -m unittest discover -s tests -t tests` →
  **143 tests OK**. No se probó contra los navegadores reales.

## Lo que el paralelo NO cambia (ojo)

- **Cada sitio sigue viendo su ritmo de siempre**: una imagen por vez. Lo que
  cambia es que los dos trabajan al mismo tiempo. Antes, el que no tenía el
  turno descansaba; ahora un motor sólo descansa cuando se le acaba la cuota.
  Si la idea de la rotación era también que cada cuenta descansara, eso se
  pierde.
- **La máquina carga el doble**: dos Chromes generando y dos recortes a la vez.
  El 2026-11-11, con carga alta, ChatGPT tardaba en mostrar el editor (por eso
  existe `COMPOSE_WAIT_SECONDS`). Conviene no correr nada pesado en paralelo.
- `Page.bringToFront` puede traer al frente la ventana del Chrome que está
  escribiendo. Pasaba igual con la rotación, y no afecta al tipeo `cdp`.
- Hallazgo aparte, no tocado: 5 de las 11 claves que quedaron afuera
  (`npc_dirigente_talk`, `npc_hincha`, `npc_hincha_talk`, `npc_masajista_action`,
  `npc_ojeador`) se fueron por `stale element reference`. Es un fallo del
  DOM/navegador, pero `classify` lo cuenta como fallo de la imagen y les quemó
  los 3 intentos. Vale la pena sumar `"stale element reference"` a
  `BROWSER_MARKERS` en otro commit.

## Pasos para el dueño: reiniciar el supervisor con `--parallel`

El supervisor que corre hoy (pid 97233) usa el código de `main` del checkout
`/Users/manuader/Desktop/projects/automatic-image-generation`. `--parallel`
está en la rama `paralelo-motores` y todavía **no** está en `main`. `main` está
en `00e1500`, el mismo commit del que sale la rama, así que entra con un
fast-forward.

1. **Frenarlo.** En la ventana de Terminal.app donde corre, apretá **Ctrl-C**.
   Va a escribir `=== cortado a mano; el mismo comando sigue donde quedó ===`.
   El estado ya está guardado: `supervisor.json` se escribe de forma atómica
   después de cada imagen, pausa o salto, así que el Ctrl-C no pierde nada. Las
   pausas (`blocks`, con su hora de fin) y la rotación (`rotation`) quedan en
   `projects/football-evolution/state/supervisor.json`.
2. **Esperar al generador en vuelo.** El `generate.py` que estaba pidiendo una
   imagen corre en su propia sesión y **no** se corta con el Ctrl-C: termina
   esa imagen solo (hasta 10 min). Mirá que no quede ninguno antes de seguir:

   ```bash
   pgrep -fl "generate.py --project"     # tiene que no mostrar nada
   ```

   Si arrancás antes, el supervisor nuevo puede pedir esa misma imagen dos veces.
3. **Traer la rama a `main`** (con el supervisor frenado):

   ```bash
   cd /Users/manuader/Desktop/projects/automatic-image-generation
   git merge --ff-only paralelo-motores
   ```

4. **(Opcional) reencolar las 11 claves salteadas.** Ver la sección siguiente.
   Se hace acá, con el supervisor frenado.
5. **Mirar el reparto sin abrir nada:**

   ```bash
   .venv/bin/python supervisor.py --project football-evolution --parallel gemini:50,chat-gpt:50 --dry-run
   ```

6. **Arrancarlo:**

   ```bash
   .venv/bin/python supervisor.py --project football-evolution --parallel gemini:50,chat-gpt:50
   ```

   Las pausas guardadas se respetan. Si Gemini sigue en pausa hasta las 19:27,
   ChatGPT arranca solo y Gemini se suma cuando vence su pausa. El campo
   `rotation` queda en el archivo sin uso; si se vuelve a `--rotate`, la
   rotación sigue donde estaba. La salida de cada motor queda en
   `state/generate-gemini.log` y `state/generate-chat-gpt.log`, y la bitácora
   común en `state/supervisor.log`.

## Reencolar las 11 claves de `skipped`

El supervisor no vuelve a pedir lo que está en el campo **`skipped`** de
`projects/football-evolution/state/supervisor.json`: es un objeto
`{clave: motivo}`, y `pending()` filtra esas claves. Hoy tiene 11:

- `titular_primera_idle__retro`
- `titular_primera_idle__dorada`
- `goleador_primera_idle`
- `npc_dirigente`
- `npc_dirigente_talk`
- `npc_hincha`
- `npc_hincha_talk`
- `npc_hincha_face`
- `npc_masajista_action`
- `npc_masajista_face`
- `npc_ojeador`

Para reencolarlas, **con el supervisor frenado** (paso 4), vaciá ese campo y
dejá todo lo demás igual. `blocks` tiene que quedar, porque son las pausas por
cuota. Desde `/Users/manuader/Desktop/projects/automatic-image-generation`:

```bash
.venv/bin/python - <<'EOF'
import json, pathlib
p = pathlib.Path("projects/football-evolution/state/supervisor.json")
d = json.loads(p.read_text())
print("saco de skipped:", ", ".join(d.get("skipped", {})))
d["skipped"] = {}
d["attempts"] = {}
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
EOF
```

- `"skipped": {}` las vuelve a meter en la cola. Como no tienen PNG en
  `output/` y su `.md` sigue `pendiente`, entran solas en su lugar del orden.
- `"attempts": {}` pone en cero los intentos que quedaron a medias. Hoy ya
  está vacío, así que no cambia nada.
- Para reencolar sólo algunas, en vez de vaciarlo borrá esas claves del objeto
  `skipped`.

Cada una vuelve con 3 intentos nuevos. Las `npc_*` son familias (`npc_hincha`,
`npc_dirigente`, …), así que con `--parallel` cada familia va entera a un mismo
motor.
