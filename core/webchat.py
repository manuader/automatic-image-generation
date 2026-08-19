"""Manejar un chat web de IA desde macOS como si fuera una persona.

**Todo lo de este archivo es mecánica, no proveedor.** Nada de acá se descubrió
leyendo documentación: son las defensas anti-bot de un chat web, medidas a los
golpes contra Gemini durante meses. Cada rareza tiene su comentario con la fecha
y el síntoma, porque la que parece de más es siempre la que arregló algo:

- se tipea con `keystroke` de System Events y no con `send_keys`, porque el
  editor exige input "trusted" y con Selenium el botón de enviar no se habilita;
- se tipea POR TANDAS y se pregunta quién está al frente antes de cada una,
  porque una ventana que roba el foco a mitad de camino se lleva el prompt entero;
- la referencia se adjunta por portapapeles, porque no hay `<input type=file>`
  al que llegar;
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
    ):
        self.port = self.DEBUG_PORT if port is None else int(port)
        self.timeout = timeout
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
                f"Abrilo con: python3 generate.py --engine {self.NAME} --launch"
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

    def _check_blocked(self) -> None:
        reason = self.contains_error(self._driver().page_source)
        if reason:
            raise GenerationBlocked(reason)

    def _find_first(self, selectors: list[tuple[str, str]]):
        from selenium.webdriver.common.by import By

        driver = self._driver()
        for kind, value in selectors:
            elements = driver.find_elements(getattr(By, kind), value)
            for element in elements:
                if element.is_displayed() and element.is_enabled():
                    return element
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

    def _focus_compose(self) -> None:
        """Clickea el compose box para darle foco DOM (imágenes sin referencia,
        que no tienen paste). Sin esto los keystrokes de System Events se pierden."""
        field = self._find_first(self.COMPOSE_SELECTORS)
        if field is not None:
            field.click()
            time.sleep(0.3)

    def _upload_reference(self, reference: Path | None) -> None:
        # Ninguno de los dos sitios expone un `<input type=file>` accesible; el
        # camino confiable es pegar la imagen desde el portapapeles del sistema
        # (macOS) con cmd+v.
        if reference is None or not Path(reference).is_file():
            raise GenerationBlocked(f"el prompt pide una referencia y no existe: {reference}")
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        script = (
            'set the clipboard to (read (POSIX file "%s") as «class PNGf»)'
            % str(Path(reference).resolve())
        )
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode != 0:
            raise GenerationBlocked(
                f"no pude cargar la referencia al portapapeles: {result.stderr.strip()}"
            )

        field = self._find_first(self.COMPOSE_SELECTORS)
        if field is None:
            raise GenerationBlocked("no encontré el cuadro de prompt para pegar la referencia")
        field.click()
        time.sleep(0.4)
        field.send_keys(Keys.COMMAND, "v")

        driver = self._driver()
        self._wait_for(
            lambda: any(
                int(img.get_attribute("naturalWidth") or 0) > 100
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
        # El prompt es el texto EXACTO del .md (nunca inventado). El sitio exige
        # input "trusted": send_keys/CDP no habilitan el botón de enviar. Se
        # escribe con keystrokes reales de macOS (System Events), indistinguibles
        # de un humano.
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

        # ⚠️ El botón de enviar NO sirve como confirmación de que el texto entró:
        # la imagen adjunta sola ya lo habilita (medido: `disabled == False` con
        # el editor vacío). Por eso el runner mandó referencias sin prompt sin
        # enterarse. Se comprueba el editor, que es el único que sabe.
        written_text = editor.get_attribute("innerText") or ""
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
        return self._wait_for(
            lambda: self._extract_generated_png(reference if asset.needs_reference else None),
            f"la imagen generada por {self.NAME} (distinta de la referencia)",
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
            "blocked": self.contains_error(driver.page_source),
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
        widths = sorted(
            (int(i.get_attribute("naturalWidth") or 0) for i in images), reverse=True
        )
        # Diagnóstico: si la generada entra como preview chico, el filtro de 512
        # la deja afuera y el único candidato es la referencia. Se imprime sólo
        # cuando cambia, para no inundar el log en cada poll de `_wait_for`.
        report = ",".join(str(width) for width in widths[:8] if width)
        if getattr(self, "_last_report", None) != report:
            self._last_report = report
            print(f"  · imgs en pantalla (ancho natural): {report or 'ninguna'}",
                  file=sys.stderr, flush=True)

        candidates = sorted(
            (i for i in images if int(i.get_attribute("naturalWidth") or 0) >= 512),
            key=lambda i: int(i.get_attribute("naturalWidth")),
            reverse=True,
        )
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
