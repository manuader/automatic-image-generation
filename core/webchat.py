"""Manejar un chat web de IA desde macOS como si fuera una persona.

**Todo lo de este archivo es mecánica, no proveedor.** Nada de acá se descubrió
leyendo documentación: son las defensas anti-bot de un chat web, medidas a los
golpes contra Gemini durante meses. Cada rareza tiene su comentario con la fecha
y el síntoma, porque la que parece de más es siempre la que arregló algo:

- se tipea con `Input.insertText` de CDP y no con `send_keys`, porque el editor
  exige input "trusted" y con Selenium el botón de enviar no se habilita —pero
  sí con CDP, que llega a la página con `isTrusted == true` (§1 del README);
- queda el camino viejo por System Events (`--typing keystroke`), y ahí se tipea
  POR TANDAS preguntando quién está al frente antes de cada una, porque una
  ventana que roba el foco a mitad de camino se lleva el prompt entero;
- la referencia se adjunta con un evento `paste` sintético que lleva el archivo
  adentro, porque no hay `<input type=file>` al que llegar y el portapapeles del
  sistema no se puede leer con la ventana ocluida;
- la imagen se saca por canvas de los píxeles ya renderizados, porque el botón
  de descarga sólo existe con el mouse encima y los blobs se revocan;
- y se compara contra una huella de la referencia, porque la imagen adjunta
  también es grande y sin eso el runner se guarda la referencia creyendo que
  generó algo.

Lo que cambia entre un proveedor y otro es un puñado de constantes declaradas
arriba de cada subclase: la URL, el selector del botón de enviar y las frases con
las que ese sitio dice "no puedo". Nada más.
"""

from __future__ import annotations

import base64
import subprocess
import sys
import time
from pathlib import Path

from core.errors import TRANSIENT_DOM_ERRORS, GenerationBlocked

#: Tipeo por tandas. El 2026-08-16, con la máquina cargada (varios frontends de
#: agente abiertos a la vez), escribir el prompt entero en UN `keystroke` falló
#: tres veces seguidas: dos prompts escribieron 0 de ~2000 caracteres —otra
#: ventana se robó el frente DURANTE los varios segundos que dura esa única
#: llamada, así que las teclas aterrizaron en otra app— y un tercero perdió
#: cuatro caracteres en la cola de eventos. Cortar en tandas acota el daño de
#: cada pérdida y, sobre todo, abre un hueco entre tanda y tanda para volver a
#: preguntar quién está al frente.
TYPE_CHUNK_CHARS = 250
TYPE_PAUSE_SECONDS = 0.25
#: Intentos de recuperar el frente para TODO el prompt (no por tanda): si tres
#: `activate` seguidos no alcanzan, el ladrón no es una ventana de paso.
FOCUS_RECOVERIES = 3
#: Lo que tarda macOS en dejar a Chrome adelante después de `activate`.
FOCUS_SETTLE_SECONDS = 1.0
#: Techo para la consulta de frontmost: corre ~9 veces por imagen, así que un
#: System Events colgado frenaría el batch entero si esperara para siempre.
FRONTMOST_TIMEOUT_SECONDS = 10
#: Nombre del proceso tal como lo reporta System Events (el launcher abre
#: siempre Chrome estable, nunca Canary).
CHROME_PROCESS_NAME = "Google Chrome"

#: Los dos caminos para meter el prompt en el editor.
#:
#: `cdp` — el default. `Input.insertText` del DevTools Protocol: el evento llega
#: a la página con `isTrusted == true`, que es lo único que el sitio mira, así
#: que el botón de enviar se habilita igual que con un humano (medido contra
#: Gemini el 2026-08-19: composer con texto y `send_button` presente y
#: `enabled`). El comentario viejo de `_submit` decía que CDP no habilitaba el
#: botón; se probó y es falso —lo que no funciona es `send_keys` de Selenium, que
#: es otra cosa. Que ande importa por tres motivos, no uno: no pide el permiso de
#: Accesibilidad de macOS, no le roba el frente a nadie —o sea que el batch deja
#: de necesitar la máquina para él solo— y hace imposible el intercalado, porque
#: el texto no pasa por la cola de eventos del sistema.
#:
#: `keystroke` — el camino histórico (System Events). Se queda porque es el que
#: generó 335 imágenes y porque si algún día un sitio empieza a mirar algo más
#: que `isTrusted`, es el que sigue siendo indistinguible de una persona. Exige
#: el permiso de Accesibilidad y la máquina en exclusiva.
TYPING_MODES = ("cdp", "keystroke")
TYPING_DEFAULT = "cdp"

#: "¿Este elemento está visible?" contestado por el DOM: tiene caja, está en el
#: documento y ningún estilo lo esconde. Reemplaza a `is_displayed()` de Selenium
#: por lo que se explica en `_find_first` — con la ventana ocluida aquél contesta
#: `False` para elementos que están perfectamente ahí.
ELEMENT_VISIBLE_JS = """
const el = arguments[0];
if (!el || !el.isConnected) return false;
const rect = el.getBoundingClientRect();
if (rect.width <= 0 || rect.height <= 0) return false;
const style = getComputedStyle(el);
return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
"""

#: Mete un archivo en el editor como si el usuario lo hubiera pegado. Recibe el
#: PNG en base64, el elemento y el nombre; devuelve cuántos archivos llevaba el
#: evento, que es lo que confirma que se construyó bien. El `File` se arma en la
#: página —no viaja como objeto— porque lo único que cruza el puente de Selenium
#: es texto. Ver `_upload_reference` para por qué este camino y no el portapapeles.
PASTE_FILE_JS = """
const [b64, element, name] = [arguments[0], arguments[1], arguments[2]];
const binary = atob(b64);
const bytes = new Uint8Array(binary.length);
for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
const transfer = new DataTransfer();
transfer.items.add(new File([bytes], name, {type: 'image/png'}));
element.dispatchEvent(new ClipboardEvent('paste', {
  clipboardData: transfer, bubbles: true, cancelable: true,
}));
return transfer.files.length;
"""


def applescript_string(text: str) -> str:
    """Literal AppleScript seguro para `keystroke` (escapa \\ y comillas)."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped + '"'


def chunk_prompt(prompt: str, size: int = TYPE_CHUNK_CHARS) -> list[str]:
    """Parte el prompt en tandas de `size` caracteres sin tocar el contenido.

    Invariante que sostiene todo lo demás: ``"".join(chunk_prompt(p, n)) == p``
    para cualquier `p` y cualquier `n`. Nada de `strip`, nada de normalizar
    saltos de línea, nada de cortar por palabra: el corte es puramente
    posicional, así que lo que se tipea en tandas es carácter por carácter lo
    mismo que tipeaba la llamada única. Si esto se "mejorara" recortando
    espacios, `prompt_landed` —que compara el arranque— lo rechazaría, y con
    razón: sería otro prompt.
    """
    step = max(1, int(size))
    return [prompt[index:index + step] for index in range(0, len(prompt), step)]


class WebChatBrowser:
    """Adaptador pequeño y deliberadamente conservador para un chat web.

    Las subclases sólo declaran las constantes de arriba de la clase. Si alguna
    vez hace falta pisar un método, es señal de que el sitio cambió de mecánica
    y no sólo de nombres.
    """

    #: Cómo se llama este motor en la línea de comandos.
    NAME = "webchat"
    #: Puerto de depuración propio. Uno por motor y no uno solo compartido:
    #: `ensure_debug_chrome` da por buena cualquier Chrome que ya responda en el
    #: puerto, así que con un default único `--launch` reusaría en silencio la
    #: ventana del OTRO motor —o la de otro proyecto— y el batch terminaría
    #: manejando la sesión equivocada. Medido el 2026-08-19 contra un Chrome de
    #: Gemini abierto en 9222.
    DEBUG_PORT = 9222
    #: Dónde abre el launcher la primera vez (para iniciar sesión a mano).
    HOME_URL = ""
    #: A dónde va el runner para empezar UNA conversación limpia por imagen.
    NEW_CHAT_URL = ""
    #: Substring que aparece en la URL recién cuando la conversación arrancó. Es
    #: la única confirmación honesta de que el envío salió: el botón de enviar
    #: puede habilitarse con la imagen adjunta sola.
    CONVERSATION_URL_MARK = ""
    #: El cuadro de texto. Genérico a propósito: los dos sitios usan un editor
    #: contenteditable y ninguno expone un id estable.
    COMPOSE_SELECTORS: list[tuple[str, str]] = [
        ("CSS_SELECTOR", "[contenteditable='true']"),
        ("CSS_SELECTOR", "textarea"),
    ]
    #: El botón de enviar, en el orden en que conviene buscarlo.
    SEND_BUTTON_SELECTORS: list[tuple[str, str]] = []
    #: Frase en la página → por qué está bloqueado. Se busca en minúsculas.
    ERROR_PATTERNS: dict[str, str] = {}
    #: Lado largo mínimo para que una `<img>` de la página compita como imagen
    #: generada. Ver `is_candidate_size`.
    CANDIDATE_LONG_SIDE = 512
    #: Cómo dice este sitio "estoy generando", en minúsculas. No es un bloqueo:
    #: se busca SÓLO cuando ya venció el timeout, para distinguir "tardó" de "no
    #: va a contestar nunca". Ver `_explain_silence`.
    GENERATING_MARKERS: tuple[str, ...] = ()
    #: Frases que comparten substring con un bloqueo real pero NO bloquean nada.
    #: El banner "estás por alcanzar el límite de uso" es un aviso preventivo: el
    #: chat sigue generando. Como contiene "límite de uso", sin sacarlo antes de
    #: buscar errores TODAS las imágenes fallan con "límite alcanzado" y el batch
    #: se frena creyendo que la cuota se agotó.
    BENIGN_NOTICES: tuple[str, ...] = ()

    def __init__(
        self,
        port: int | None = None,
        timeout: int = 180,
        ref_threshold: float = 4,
        discards_dir: Path | None = None,
        type_chunk: int = TYPE_CHUNK_CHARS,
        type_pause: float = TYPE_PAUSE_SECONDS,
        typing: str = TYPING_DEFAULT,
    ):
        self.port = self.DEBUG_PORT if port is None else int(port)
        self.timeout = timeout
        #: Cómo se escribe el prompt: `cdp` o `keystroke`. Ver TYPING_MODES.
        if typing not in TYPING_MODES:
            raise ValueError(f"modo de tipeo desconocido: {typing!r} (hay: {TYPING_MODES})")
        self.typing = typing
        # Tamaño de tanda y respiro entre tandas al tipear el prompt (ver
        # TYPE_CHUNK_CHARS). El piso del tamaño lo pone `chunk_prompt`, que es
        # quien tiene que aguantar cualquier número: una sola fuente de verdad.
        self.type_chunk = int(type_chunk)
        self.type_pause = max(0.0, float(type_pause))
        # Distancia MAE por debajo de la cual una imagen se considera "es la
        # referencia". Bajó de 12 a 4 con las variantes de un mismo personaje
        # (2026-08-19): la huella es un thumbnail de 32x32, así que una variante
        # que conserva la pose queda MUY cerca del original — una versión dorada
        # medía 9.51 y se descartaba sola, y ni un sujeto enteramente NEGRO pasa
        # de 25.8. Medido del otro lado: la misma imagen re-codificada o
        # reescalada no supera 0.14, así que 4 separa las dos poblaciones con
        # margen. Con 12 el runner esperaba el timeout entero de cada imagen sin
        # encontrar nunca un candidato válido.
        self.ref_threshold = ref_threshold
        self.discards_dir = Path(discards_dir) if discards_dir else None
        #: stderr de la última consulta fallida por el proceso al frente.
        self._frontmost_error = ""
        self.driver = None

    # ---------------------------------------------------------------- navegador

    def _driver(self):
        if self.driver is not None:
            return self.driver
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError as error:
            raise GenerationBlocked("falta Selenium: pip install -r requirements.txt") from error
        options = Options()
        options.debugger_address = f"127.0.0.1:{self.port}"
        try:
            self.driver = webdriver.Chrome(options=options)
        except Exception as error:  # Selenium expone tipos distintos según driver.
            raise GenerationBlocked(
                f"no pude conectar Selenium al Chrome aislado en el puerto {self.port}. "
                f"Abrilo con: .venv/bin/python generate.py --engine {self.NAME} --launch"
            ) from error
        return self.driver

    @classmethod
    def contains_error(cls, text: str) -> str | None:
        normalized = text.lower()
        for notice in cls.BENIGN_NOTICES:
            normalized = normalized.replace(notice, "")
        for needle, reason in cls.ERROR_PATTERNS.items():
            if needle in normalized:
                return reason
        return None

    def _visible_text(self) -> str:
        """Lo que la página MUESTRA, no su código.

        ⚠️ 2026-10-08: se buscaba en `page_source`, y ChatGPT trae en su JS la
        plantilla "You've reached your limit of {active_limit} active tasks".
        El probe y cada imagen daban "límite de uso" con el chat libre, y el
        batch tuvo a ChatGPT en pausa toda una noche sin motivo."""
        return self._driver().execute_script(
            "return document.body ? document.body.innerText : '';"
        ) or ""

    def _check_blocked(self) -> None:
        reason = self.contains_error(self._visible_text())
        if reason:
            raise GenerationBlocked(reason)

    @classmethod
    def is_candidate_size(cls, width: int, height: int) -> bool:
        """¿Esta `<img>` de la página puede ser la imagen generada?

        Se mide el lado LARGO. ⚠️ 2026-08-20: se medía el ancho, y con eso un
        roll-up de feria de 420x1008 —generado, correcto, en pantalla— no entraba
        nunca en la lista de candidatos: el pedido moría en `timeout esperando la
        imagen generada` con la imagen ahí. Es el mismo supuesto de "todo es
        cuadrado" que rechazaba las piezas apaisadas en `verify_png`, y en las dos
        el arreglo es el mismo: una pieza de diseño puede ser angosta y alta o
        ancha y baja, y sigue siendo grande.

        El piso sigue volteando lo que tiene que voltear, que es la iconografía
        del propio sitio compitiendo como candidata: medidos en Gemini, 150x150,
        128x128, 64x64 y 32x32 no llegan a 512 por ningún lado.
        """
        return max(width, height) >= cls.CANDIDATE_LONG_SIDE

    def _find_first(self, selectors: list[tuple[str, str]]):
        """El primer elemento visible y habilitado de la lista.

        ⚠️ 2026-08-19: la visibilidad se pregunta en la página y NO con
        `is_displayed()` de Selenium, que acá miente. Con la ventana de Chrome
        tapada por otra app —normal en una tanda larga— la pestaña pasa a
        `visibilityState == "hidden"` y chromedriver empieza a contestar `False`
        para casi todo: medido sobre el botón de enviar, `is_displayed()` daba
        `False` mientras el elemento tenía rect de 32x32, `display: flex`,
        `visibility: visible` y `opacity: 1`. Con eso, `welcome_kit` y
        `mockup_presentacion` murieron en `timeout esperando el botón de enviar`
        con la imagen a un click de distancia.

        Que el DOM sea la única fuente es lo coherente con el resto del archivo:
        esta herramienta maneja una ventana de fondo a propósito, así que si la
        tapan tiene que seguir funcionando igual. Ocluir no es ocultar.
        """
        from selenium.webdriver.common.by import By

        driver = self._driver()
        for kind, value in selectors:
            elements = driver.find_elements(getattr(By, kind), value)
            for element in elements:
                # El DOM se rehace entre el `find_elements` y las preguntas: el
                # sitio reemplaza el composer y la barra de envío mientras la
                # respuesta se arma. Un elemento que se murió en el medio no es
                # un error, es "ése ya no": se pasa al siguiente. Sin esto la
                # excepción sube cruda y se lleva la imagen — pasó con
                # `dashboard_hero`, que después salió bien al reintentar.
                try:
                    if element.is_enabled() and driver.execute_script(ELEMENT_VISIBLE_JS, element):
                        return element
                except TRANSIENT_DOM_ERRORS:
                    continue
        return None

    def _wait_for(self, action, description: str):
        deadline = time.monotonic() + self.timeout
        last_transient = None
        while time.monotonic() < deadline:
            self._check_blocked()
            try:
                result = action()
            except TRANSIENT_DOM_ERRORS as error:
                # El DOM se rehizo mientras lo leíamos. Pasa de verdad: cuando
                # el sitio muestra un mensaje de error propio, o mientras
                # reemplaza el placeholder por la imagen final, el nodo que
                # teníamos en la mano deja de existir. Es exactamente la
                # condición "todavía no está listo", así que se reintenta hasta
                # el deadline en vez de abortar.
                last_transient = error
                time.sleep(0.5)
                continue
            if result:
                return result
            time.sleep(0.5)
        if last_transient is not None:
            raise GenerationBlocked(
                f"timeout esperando {description} (el DOM se rehizo: {type(last_transient).__name__})"
            )
        raise GenerationBlocked(f"timeout esperando {description}")

    def _open_new_chat(self) -> None:
        driver = self._driver()
        driver.get(self.NEW_CHAT_URL)
        self._wait_for(
            lambda: self._find_first(self.COMPOSE_SELECTORS),
            f"el cuadro de prompt de {self.NAME} (confirmá el login en el Chrome aislado)",
        )

    def _clear_draft(self) -> None:
        """Vacía el editor antes de pegar la referencia y escribir.

        ⚠️ 2026-10-07: Gemini guarda el borrador y lo devuelve en el chat nuevo.
        Un intento abortado por el guard dejaba su prompt adentro y el siguiente
        escribía encima: medido, "1503 de 1478" y después "2998 de 1478", y la
        imagen se perdía por un texto que nadie veía. Va antes del paste para no
        tocar el adjunto."""
        field = self._focus_editor_dom()
        if not (field.get_attribute("innerText") or "").strip():
            return
        self._driver().execute_script(
            "document.execCommand('selectAll'); document.execCommand('delete');"
        )
        time.sleep(0.3)
        left = (field.get_attribute("innerText") or "").strip()
        if left:
            raise GenerationBlocked(
                f"el editor no aceptó vaciarse: quedaron {len(left)} caracteres del borrador"
            )

    def _focus_compose(self) -> None:
        """Clickea el compose box para darle foco DOM (imágenes sin referencia,
        que no tienen paste). Sin esto los keystrokes de System Events se pierden."""
        field = self._find_first(self.COMPOSE_SELECTORS)
        if field is not None:
            field.click()
            time.sleep(0.3)

    def _focus_editor_dom(self):
        """Deja el editor enfocado de verdad y devuelve el elemento.

        ⚠️ 2026-08-19: acá alcanzaba con `field.click()` de Selenium y **no
        alcanza**. Con la ventana de Chrome atrás, la pestaña queda
        `visibilityState == "hidden"` y el click no mueve el foco: medido,
        `document.activeElement` seguía siendo `BODY`. De ahí salían los dos
        fallos que parecían distintos y eran el mismo — el paste que no pegaba
        nada y el texto que no aparecía en el composer.

        Las dos mitades hacen falta y ninguna sola sirve. `Page.bringToFront`
        despierta la pestaña (pasa a `visible` y `document.hasFocus()` a `true`,
        que es lo que el navegador exige para leer el portapapeles) y el
        `focus()` por JS pone el cursor DENTRO del contenteditable, que es donde
        `Input.insertText` escribe. Se comprueba el resultado en la misma
        llamada: un foco que no aterrizó es una imagen generada contra un prompt
        vacío, y es más barato abortar acá.
        """
        driver = self._driver()
        driver.execute_cdp_cmd("Page.bringToFront", {})
        field = self._find_first(self.COMPOSE_SELECTORS)
        if field is None:
            raise GenerationBlocked(f"no encontré el cuadro de prompt de {self.NAME}")
        focused = driver.execute_script(
            "arguments[0].focus(); return document.activeElement === arguments[0];", field
        )
        if not focused:
            raise GenerationBlocked(
                "el editor no tomó el foco: lo que se escriba se pierde. "
                "¿Se cerró la ventana aislada de Chrome?"
            )
        time.sleep(0.3)
        return field

    def _upload_reference(self, reference: Path | None) -> None:
        """Adjunta la referencia al chat sin pasar por el portapapeles del sistema.

        Ninguno de los dos sitios expone un `<input type=file>` (medido contra
        Gemini: cero en la página), así que el adjunto tiene que entrar por un
        evento `paste`. La pregunta era de dónde sale el archivo, y se probaron
        los tres caminos en orden de menos a más independiente del entorno:

        1. `send_keys(⌘V)` de Selenium — **no pega nada**. Chromedriver manda la
           combinación como evento de teclado y un ⌘V suelto no invoca el comando
           de edición del navegador.
        2. CDP `Input.dispatchKeyEvent` con `commands: ["paste"]` — sí lo invoca,
           pero lee el portapapeles del SISTEMA, y para eso Chrome exige que el
           documento no esté oculto. Con la ventana ocluida —cosa normal en un
           batch largo: alcanza con que otra app la tape— `visibilityState` pasa
           a `hidden` y el paste devuelve vacío. Así se perdieron `welcome_kit` y
           `mockup_presentacion` con el resto de la tanda ya generada.
        3. El archivo inyectado en un `DataTransfer` y despachado como evento
           `paste` sintético. **Es el que queda.** No toca el portapapeles, así
           que no compite con lo que el dueño de la máquina tenga copiado, y
           sobre todo anda con `visibilityState == "hidden"` —medido—, que es lo
           único que hacía frágil al anterior.
        """
        if reference is None or not Path(reference).is_file():
            raise GenerationBlocked(f"el prompt pide una referencia y no existe: {reference}")
        from selenium.webdriver.common.by import By

        field = self._focus_editor_dom()
        driver = self._driver()
        payload = base64.b64encode(Path(reference).read_bytes()).decode("ascii")
        if not driver.execute_script(PASTE_FILE_JS, payload, field, Path(reference).name):
            raise GenerationBlocked(
                f"el editor no aceptó el evento paste de {Path(reference).name}"
            )

        # ⚠️ El adjunto se reconoce por `blob:`/`data:`, no por el tamaño. Antes
        # alcanzaba con cualquier `<img>` de más de 100px y eso da falso positivo
        # con la UI del propio sitio: en Gemini el sparkle (150x150) y la foto de
        # perfil (128x128) lo cumplen los dos, así que el guard aprobaba pastes
        # que nunca ocurrieron y se generaba contra el prompt sin referencia. Una
        # imagen que subió el usuario vive en un blob de la sesión; una del sitio
        # viene de gstatic.
        self._wait_for(
            lambda: any(
                (img.get_attribute("src") or "").startswith(("blob:", "data:"))
                and int(img.get_attribute("naturalWidth") or 0) > 100
                for img in driver.find_elements(By.TAG_NAME, "img")
            ),
            "la miniatura de la referencia adjunta",
        )
        self._check_blocked()

    # ------------------------------------------------------------------- tipeo

    @staticmethod
    def prompt_landed(editor_text: str, prompt: str) -> bool:
        """¿El prompt llegó de verdad al editor?

        No compara exacto a propósito: `keystroke` de System Events puede
        maltratar algún carácter suelto (la raya larga, sobre todo) y no vale
        abortar una corrida de 53 imágenes por eso. Pide dos cosas que un fallo
        real nunca cumple: que el arranque coincida y que no falte texto.

        Los dos fallos que tiene que atrapar son el vacío —el keystroke cayó en
        otro lado— y el truncado, que es peor: genera arte contra medio prompt
        y lo da por bueno.
        """
        def norm(value: str) -> str:
            return " ".join((value or "").split())

        got, want = norm(editor_text), norm(prompt)
        if not got or not want:
            return False
        head = min(40, len(want))
        return got[:head] == want[:head] and len(got) >= int(len(want) * 0.9)

    #: Quién tiene el frente AHORA. Es la única pregunta que distingue "el
    #: keystroke va a aterrizar en el chat" de "el keystroke se lo come otra app".
    FRONTMOST_SCRIPT = (
        'tell application "System Events" to get name of first application '
        "process whose frontmost is true"
    )

    def _frontmost_app(self) -> str:
        """Nombre del proceso al frente, o "" si System Events no contestó."""
        try:
            result = subprocess.run(
                ["osascript", "-e", self.FRONTMOST_SCRIPT],
                capture_output=True, text=True, timeout=FRONTMOST_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            # Esta consulta corre ~9 veces por imagen: un System Events colgado no
            # puede quedarse con el batch entero. Se trata como "no sé quién está
            # al frente", que ya tiene camino (recuperar y, si insiste, abortar).
            self._frontmost_error = (
                f"System Events no contestó en {FRONTMOST_TIMEOUT_SECONDS}s"
            )
            return ""
        if result.returncode != 0:
            # Sin permiso de Accesibilidad esta consulta falla igual que el
            # keystroke. Se guarda el error para que el abort lo diga en vez de
            # inventar un ladrón que no existe.
            self._frontmost_error = result.stderr.strip()
            return ""
        self._frontmost_error = ""
        return result.stdout.strip()

    def _recover_focus(self) -> None:
        """Pide el frente para Chrome y le devuelve el foco DOM al compose box.

        Acá NO se manda ninguna tecla: `activate` es un pedido, no una garantía,
        y hasta que la próxima consulta no confirme quién está adelante
        cualquier keystroke puede aterrizar en la app ajena. El click de Selenium
        es seguro porque va por CDP al DOM, tenga Chrome el frente o no."""
        subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'])
        time.sleep(FOCUS_SETTLE_SECONDS)
        self._focus_compose()

    def _restore_caret(self) -> None:
        """Manda el cursor al final del texto ya escrito (cmd+↓).

        Hace falta porque `_focus_compose` clickea el CENTRO del compose box: con
        medio prompt adentro, eso deja el cursor en el medio y la tanda siguiente
        se intercalaría. Va DOS veces a propósito: la tecla es idempotente, así
        que la primera hace de pre-tipeo descartable para la que se traga la app
        después de un `activate` —el mismo motivo por el que existe el espacio
        del arranque—. Y si aun así no llega, `_verify_prefix` lo atrapa."""
        for _ in range(2):
            subprocess.run([
                "osascript", "-e",
                'tell application "System Events" to key code 125 using command down',
            ])
            time.sleep(0.2)

    def _ensure_chrome_frontmost(self, remaining: int, restore_caret: bool = False) -> int:
        """Chrome al frente antes de tipear; devuelve los intentos que sobran.

        El presupuesto es de TODO el prompt, no de cada tanda: una ventana que
        aparece y se va cuesta un intento y la corrida sigue, pero una app que se
        queda adelante agota los tres y aborta ANTES de teclear en ella."""
        frontmost = self._frontmost_app()
        recovered = False
        while frontmost != CHROME_PROCESS_NAME:
            if remaining <= 0:
                who = (
                    f"«{frontmost}»" if frontmost else
                    "una app que System Events no supo nombrar (¿falta permiso de "
                    f"Accesibilidad? {self._frontmost_error})"
                )
                raise GenerationBlocked(
                    "no pude devolverle el foco a Chrome para escribir el prompt: al "
                    f"frente está {who} después de {FOCUS_RECOVERIES} intentos. "
                    "Cerrá o minimizá esa ventana antes de reintentar."
                )
            remaining -= 1
            # Que se vea en la corrida: el dueño tiene que poder auditar QUÉ
            # imágenes pasaron por el camino raro sin leer el checkpoint.
            print(
                f"  ⚠️  el foco se lo llevó «{frontmost or '¿?'}»; recupero y sigo "
                f"(quedan {remaining} intentos)",
                file=sys.stderr, flush=True,
            )
            self._recover_focus()
            recovered = True
            frontmost = self._frontmost_app()
        if recovered and restore_caret:
            # Recién ACÁ, con Chrome confirmado adelante, se toca el teclado.
            self._restore_caret()
        return remaining

    @staticmethod
    def _same_text(one: str, other: str) -> bool:
        """Igualdad con el mismo criterio de espacios que `prompt_landed`."""
        return " ".join((one or "").split()) == " ".join((other or "").split())

    def _verify_prefix(self, editor, prompt: str, written: int, moment: str) -> None:
        """Aborta si el editor no tiene EXACTAMENTE lo tipeado hasta acá.

        Es la red del único fallo nuevo que trae la recuperación de foco.
        `_focus_compose` clickea el CENTRO del compose box: si el cursor no
        vuelve al final del texto —el `cmd+↓` puede no alcanzar— la tanda
        siguiente se intercala EN EL MEDIO. Lo que queda tiene el largo justo y
        los primeros 40 caracteres en su lugar, así que `prompt_landed` lo
        aprueba y se gastaría cuota generando contra un prompt barajado. Ese
        fallo no existía antes del tipeo por tandas: toda perturbación de foco
        daba vacío o truncado, y el guard lo atrapaba.

        Compara contra el prefijo esperado, que sí detecta el intercalado, y es
        estricto a propósito: sobre el camino raro un carácter maltratado cuesta
        un reintento (cuota: cero), no una imagen contra un prompt roto.
        """
        written_text = editor.get_attribute("innerText") or ""
        if self._same_text(written_text, prompt[:written]):
            return
        raise GenerationBlocked(
            f"el editor no coincide con lo tipeado hasta acá ({moment}): tiene "
            f"{len(written_text.strip())} caracteres y esperaba {written}. Probable: "
            "el cursor quedó en el medio del texto al volver el foco y la tanda "
            "se intercaló. No envío: sería cuota gastada contra un prompt barajado."
        )

    def _submit(self, prompt: str) -> None:
        """Escribe el prompt en el editor y envía. El prompt es el texto EXACTO
        del .md, nunca inventado; los dos caminos lo escriben carácter por
        carácter y ninguno lo toca."""
        if self.typing == "cdp":
            self._submit_cdp(prompt)
            return
        self._submit_keystroke(prompt)

    def _send_now(self, prompt: str) -> None:
        """Comprueba que el prompt esté entero en el editor y recién ahí envía.

        ⚠️ El botón de enviar NO sirve como confirmación de que el texto entró:
        la imagen adjunta sola ya lo habilita (medido: `disabled == False` con el
        editor vacío). Por eso el runner mandó referencias sin prompt sin
        enterarse. Se comprueba el editor, que es el único que sabe."""
        editor = self._find_first(self.COMPOSE_SELECTORS)
        written_text = (editor.get_attribute("innerText") or "") if editor else ""
        if not self.prompt_landed(written_text, prompt):
            raise GenerationBlocked(
                "el prompt no llegó al editor: se escribieron "
                f"{len(written_text.strip())} de {len(prompt)} caracteres. "
                "Sin esto se enviaría la referencia sin instrucción."
            )
        send = self._wait_for(
            lambda: self._find_first(self.SEND_BUTTON_SELECTORS),
            f"el botón de enviar de {self.NAME}",
        )
        # Click directo del botón (Return no siempre envía); confirmar que la
        # conversación arranca por el cambio de URL.
        driver = self._driver()
        driver.execute_script("arguments[0].click();", send)
        self._wait_for(
            lambda: self.CONVERSATION_URL_MARK in driver.current_url,
            f"que {self.NAME} abra la conversación tras enviar",
        )

    def _submit_cdp(self, prompt: str) -> None:
        """Escribe el prompt con `Input.insertText` del DevTools Protocol.

        Va en UNA llamada y no en tandas a propósito: las tandas existen para
        acotar el daño de un robo de foco a mitad de tipeo (ver
        TYPE_CHUNK_CHARS), y por CDP el texto no pasa por la cola de eventos del
        sistema —entra directo en el documento— así que ese fallo no puede
        ocurrir. Sin tandas tampoco hace falta recuperar el frente, ni el
        pre-tipeo descartable, ni verificar prefijos intermedios: la única
        pregunta que queda es la de siempre, si el prompt entero llegó al
        editor, y la contesta `_send_now`.

        Lo que sí hace falta es el foco DOM: `insertText` escribe en el elemento
        activo, y el editor Quill de Gemini lo suelta al `<body>` después de
        pegar la referencia. Sin `_focus_editor_dom` el texto se pierde.
        """
        self._focus_editor_dom()
        self._driver().execute_cdp_cmd("Input.insertText", {"text": prompt})
        time.sleep(self.type_pause)
        self._send_now(prompt)

    def _submit_keystroke(self, prompt: str) -> None:
        # El sitio exige input "trusted". Se escribe con keystrokes reales de
        # macOS (System Events), indistinguibles de un humano.
        #
        # ⚠️ 2026-08-06: acá decía "NO clickear el campo, el foco OS-level viene
        # del paste". Eso valía para la UI vieja de Gemini. La nueva (un editor
        # Quill) **suelta el foco al `<body>` después de pegar la imagen**, así
        # que los keystrokes caían en la página y se enviaba la referencia sin
        # prompt. Medido con `document.activeElement`.
        self._focus_compose()
        subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'])
        time.sleep(1.0)
        # ⚠️ La pregunta por el frente va ANTES del pre-tipeo: el espacio y el
        # Delete descartables son teclas de verdad, y si el ladrón ya está
        # adelante las cobra él. Un Backspace suelto en Mail borra el mail
        # seleccionado. Hasta no saber quién está al frente no se teclea NADA.
        recoveries = self._ensure_chrome_frontmost(FOCUS_RECOVERIES)
        # Pre-tipeo descartable: la app a veces pierde el primer carácter tras activate.
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke " "'])
        time.sleep(0.3)
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 51'])  # Delete
        time.sleep(0.2)

        # El editor se busca ACÁ, antes de tipear: además de la verificación
        # final hace falta para auditar lo ya escrito cada vez que hubo que
        # recuperar el foco (ver `_verify_prefix`).
        editor = self._find_first(self.COMPOSE_SELECTORS)
        if editor is None:
            raise GenerationBlocked("no encontré el editor para verificar el prompt")

        # ⚠️ 2026-08-16: el prompt entero iba en UN `keystroke` de 2000+ caracteres.
        # Esa llamada tarda varios segundos y en una máquina cargada es una eternidad:
        # si otra ventana se pone adelante mientras dura, TODO el texto se lo lleva
        # ella (0 de 2099 caracteres, medido) y no hay forma de enterarse hasta el
        # final. Ahora se tipea en tandas cortas y ANTES DE CADA UNA se pregunta
        # quién está al frente: el robo de foco cuesta una tanda, no el prompt.
        chunks = chunk_prompt(prompt, self.type_chunk)
        written = 0
        for index, chunk in enumerate(chunks, 1):
            left = recoveries
            recoveries = self._ensure_chrome_frontmost(recoveries, restore_caret=written > 0)
            recovered = recoveries != left
            if recovered and written:
                # ¿Volvió intacto lo que ya estaba escrito?
                self._verify_prefix(editor, prompt, written, "al recuperar el foco")
            script = 'tell application "System Events" to keystroke %s' % applescript_string(chunk)
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if result.returncode != 0:
                raise GenerationBlocked(
                    "System Events no pudo escribir (¿falta permiso de Accesibilidad?): "
                    + result.stderr.strip()
                    + f" [tanda {index} de {len(chunks)}]"
                )
            written += len(chunk)
            time.sleep(self.type_pause)
            if recovered:
                # Y sobre todo: ¿entró DONDE correspondía? Esta es la pregunta
                # cara: si el cursor quedó en el medio, la tanda se intercaló.
                self._verify_prefix(
                    editor, prompt, written, "en la tanda que siguió a la recuperación"
                )

        self._send_now(prompt)

    # ------------------------------------------------------------- generación

    def generate(self, asset, reference: Path | None) -> bytes:
        """Genera una imagen y devuelve sus bytes PNG.

        Devuelve bytes y no un archivo a propósito: quién y dónde se guarda es
        decisión del proyecto, no del navegador. La imagen se extrae por canvas
        —píxeles ya renderizados— sin depender del botón de descarga hover-only
        ni de blobs que el sitio revoca."""
        driver = self._driver()
        driver.set_script_timeout(30)
        self._open_new_chat()
        self._clear_draft()
        if asset.needs_reference:
            self._upload_reference(reference)
        else:
            # Sin referencia no hay paste que enfoque el editor: hay que clickearlo
            # para que los keystrokes de System Events aterricen en el compose box.
            self._focus_compose()
        self._submit(asset.prompt)
        # La imagen GENERADA vive en la respuesta y difiere de la referencia
        # adjunta (que también es grande). Se espera una imagen grande cuya
        # huella de píxeles NO coincida con la referencia.
        try:
            return self._wait_for(
                lambda: self._extract_generated_png(reference if asset.needs_reference else None),
                f"la imagen generada por {self.NAME} (distinta de la referencia)",
            )
        except GenerationBlocked as error:
            raise self._explain_silence(error) from error

    def _explain_silence(self, error: GenerationBlocked) -> GenerationBlocked:
        """Distingue "todavía no llegó" de "no va a llegar nunca".

        El 2026-08-19, con 18 de 20 imágenes ya generadas, las dos últimas
        fallaron con `timeout esperando la imagen generada` y el mensaje mandaba
        a buscar donde no era: se subió el timeout a 480s y se reintentó tres
        veces, y era lo mismo. Lo que pasaba es que Gemini deja el cartel
        «Creando tu imagen» puesto para siempre cuando se acabó la cuota de
        imágenes —medido: sigue igual pasados 10 minutos, y un prompt trivial sin
        referencia hace exactamente lo mismo, así que no es del prompt—. La cuota
        agotada de IMÁGENES no dice nada; la de mensajes sí (ERROR_PATTERNS).

        Un timeout con ese cartel todavía en pantalla, entonces, no es un
        timeout: es la única forma que tiene el sitio de decir que no va a
        contestar. Subir `--timeout` no arregla nada y el mensaje tiene que
        decirlo, porque la reacción correcta es esperar y volver a correr —la
        cola retoma sola por los PNG que ya están en `output/`.
        """
        try:
            page = self._driver().page_source.lower()
        except Exception:  # noqa: BLE001 — si ni la página se puede leer, va el error original
            return error
        marker = next((mark for mark in self.GENERATING_MARKERS if mark in page), None)
        if marker is None:
            return error
        return GenerationBlocked(
            f"{self.NAME} aceptó el pedido y se quedó en «{marker}» sin devolver imagen. "
            "No es el timeout: así se ve la cuota de IMÁGENES agotada, que este sitio "
            "no informa. Subir --timeout no cambia nada. Esperá a que se renueve y "
            "volvé a correr el mismo comando: la cola retoma donde quedó."
        )

    def probe(self) -> dict:
        """Abre el chat y dice qué reconoció, sin escribir ni enviar nada.

        Existe porque los selectores de un sitio son una hipótesis hasta que
        alguien los mira contra la página real, y comprobarlos no tiene por qué
        costar una generación. Es lo primero que hay que correr cuando un motor
        se estrena o cuando un batch empieza a fallar en el mismo punto."""
        driver = self._driver()
        driver.get(self.NEW_CHAT_URL)
        time.sleep(3)
        compose = self._find_first(self.COMPOSE_SELECTORS)
        send = self._find_first(self.SEND_BUTTON_SELECTORS)
        return {
            "engine": self.NAME,
            "url": driver.current_url,
            "compose_box": None if compose is None else compose.tag_name,
            "send_button": None if send is None else (
                send.get_attribute("aria-label") or send.get_attribute("data-testid") or send.tag_name
            ),
            "blocked": self.contains_error(self._visible_text()),
        }

    def _fingerprint(self, png_bytes: bytes) -> tuple:
        from io import BytesIO

        from PIL import Image

        thumb = Image.open(BytesIO(png_bytes)).convert("RGB").resize((32, 32))
        return tuple(thumb.getdata())

    @staticmethod
    def _fingerprint_distance(one: tuple, other: tuple) -> float:
        total = 0
        for (r1, g1, b1), (r2, g2, b2) in zip(one, other):
            total += abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
        return total / (len(one) * 3)

    def _extract_generated_png(self, reference: Path | None):
        """Devuelve los bytes PNG de la primera imagen grande que NO sea la
        referencia. None si todavía no apareció (para que `_wait_for` reintente).

        La imagen recién generada suele ser un `blob:` same-origin y se extrae por
        canvas. Cuando el sitio ya la sirvió desde su CDN el canvas queda
        "tainted" (cross-origin) y `toDataURL` lanza SecurityError; en ese caso se
        baja el `src` con las cookies de la sesión y se re-codifica a PNG."""
        import base64
        from io import BytesIO

        from PIL import Image

        driver = self._driver()
        ref_fp = None
        if reference is not None:
            # Cache POR PATH: con una referencia por prompt, una sola entrada
            # global haría que la variante de un personaje se comparara contra
            # la referencia de otro.
            if not hasattr(self, "_ref_fp_cache"):
                self._ref_fp_cache = {}
            key = str(reference)
            if key not in self._ref_fp_cache:
                self._ref_fp_cache[key] = self._fingerprint(Path(reference).read_bytes())
            ref_fp = self._ref_fp_cache[key]

        images = driver.find_elements("tag name", "img")

        def size(image) -> tuple[int, int]:
            try:
                return (int(image.get_attribute("naturalWidth") or 0),
                        int(image.get_attribute("naturalHeight") or 0))
            except TRANSIENT_DOM_ERRORS:
                return (0, 0)

        sizes = sorted(((i, size(i)) for i in images),
                       key=lambda pair: max(pair[1]), reverse=True)
        # Diagnóstico: si la generada entra como preview chico, el filtro la deja
        # afuera y el único candidato es la referencia. Se imprime sólo cuando
        # cambia, para no inundar el log en cada poll de `_wait_for`.
        #
        # ⚠️ 2026-08-20: se reportan las DOS dimensiones. Antes iba sólo el ancho,
        # y con eso el log de un roll-up decía "420" —que parece chico y parece la
        # causa— cuando la imagen era 420x1008 y el problema era el filtro, no el
        # tamaño. Un diagnóstico que muestra media medida manda a mirar al lugar
        # equivocado.
        report = ",".join(f"{w}x{h}" for _, (w, h) in sizes[:8] if w)
        if getattr(self, "_last_report", None) != report:
            self._last_report = report
            print(f"  · imgs en pantalla (natural): {report or 'ninguna'}",
                  file=sys.stderr, flush=True)

        candidates = [image for image, (w, h) in sizes if self.is_candidate_size(w, h)]
        for image in candidates:
            data_url = driver.execute_script(
                """
                const img = arguments[0];
                const c = document.createElement('canvas');
                c.width = img.naturalWidth; c.height = img.naturalHeight;
                try { c.getContext('2d').drawImage(img, 0, 0); return c.toDataURL('image/png'); }
                catch (e) { return 'TAINT:' + e; }
                """,
                image,
            )
            if data_url.startswith("data:image"):
                raw = base64.b64decode(data_url.split(",", 1)[1])
            else:
                # Canvas "tainted" (imagen cross-origin del CDN del sitio):
                # bajar el original con las cookies de la sesión.
                raw = self._download_cross_origin(image.get_attribute("src"))
                if raw is None:
                    print("  · descarte: no se pudo bajar la imagen cross-origin",
                          file=sys.stderr, flush=True)
                    continue
            if not self._has_content(raw):
                print("  · descarte: imagen vacía o de color plano (aún renderizando)",
                      file=sys.stderr, flush=True)
                continue  # placeholder vacío/transparente: esperar el render real
            if ref_fp is not None:
                distance = self._fingerprint_distance(self._fingerprint(raw), ref_fp)
                if distance < self.ref_threshold:
                    self._save_discard(raw, distance)
                    print(f"  · descarte: se parece a la referencia "
                          f"(MAE {distance:.2f} < {self.ref_threshold})",
                          file=sys.stderr, flush=True)
                    continue  # es la referencia; seguir buscando/esperando
                print(f"  · candidato aceptado (MAE {distance:.2f})",
                      file=sys.stderr, flush=True)
            return raw
        return None

    def _save_discard(self, raw: bytes, distance: float) -> None:
        """Guarda lo descartado para poder MIRARLO: distinguir "es la referencia"
        de "es el resultado que se le parece demasiado" no se puede hacer con el
        número solo."""
        if self.discards_dir is None:
            return
        from io import BytesIO

        from PIL import Image

        self.discards_dir.mkdir(parents=True, exist_ok=True)
        width = Image.open(BytesIO(raw)).width
        (self.discards_dir / f"mae{distance:05.2f}_w{width}.png").write_bytes(raw)

    @staticmethod
    def _has_content(raw: bytes) -> bool:
        """Descarta extracciones vacías: un placeholder transparente o un bloque de
        color uniforme (el canvas leído antes de que la imagen termine de renderizar).
        Una imagen real tiene píxeles opacos Y variación de color."""
        from io import BytesIO

        from PIL import Image

        image = Image.open(BytesIO(raw)).convert("RGBA")
        _, alpha_max = image.getchannel("A").getextrema()
        if alpha_max < 16:
            return False  # totalmente transparente
        ranges = [hi - lo for lo, hi in image.convert("RGB").getextrema()]
        return max(ranges) >= 8  # alguna variación de color (no un bloque plano)

    def _download_cross_origin(self, src: str | None):
        """Baja la imagen generada (los CDN sirven 403 sin auth) con las cookies
        de la sesión de Chrome y la re-codifica a PNG. Devuelve bytes PNG, o None
        si el src no es http o la bajada falla."""
        if not src or not src.startswith("http"):
            return None
        import urllib.request
        from io import BytesIO

        from PIL import Image

        try:
            cookie_header = "; ".join(
                f"{cookie['name']}={cookie['value']}"
                for cookie in self._driver().get_cookies()
            )
            request = urllib.request.Request(
                src, headers={"User-Agent": "Mozilla/5.0", "Cookie": cookie_header}
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
            buffer = BytesIO()
            Image.open(BytesIO(data)).convert("RGB").save(buffer, "PNG")
            return buffer.getvalue()
        except Exception:
            return None
