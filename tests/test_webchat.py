"""La mecánica de manejar el chat: tipeo, foco, bloqueos y extracción.

Todo esto corre SIN navegador. Es a propósito: lo que se prueba acá es la lógica
que rodea a Selenium, no Selenium, y una suite que necesitara Chrome no se
correría nunca.
"""

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from support import png_bytes

from core import engines, webchat
from core.errors import GenerationBlocked
from core.webchat import applescript_string, chunk_prompt

Gemini = engines.load("gemini")
CHROME = webchat.CHROME_PROCESS_NAME


def unescape_applescript(literal: str) -> str:
    """Inversa de `applescript_string`: qué caracteres tipearía de verdad."""
    if not (literal.startswith('"') and literal.endswith('"')):
        raise AssertionError(f"literal AppleScript mal formado: {literal!r}")
    return literal[1:-1].replace('\\"', '"').replace("\\\\", "\\")


class BlockDetectionTests(unittest.TestCase):
    """El aviso preventivo comparte substring con el bloqueo real."""

    def test_the_approaching_limit_banner_is_not_a_block(self):
        page = (
            "<div>Estás por alcanzar el límite de uso de Gemini Pro</div>"
            "<div>respuesta normal</div>"
        )
        self.assertIsNone(Gemini.contains_error(page))

    def test_the_real_limit_message_is_still_detected(self):
        self.assertEqual(
            Gemini.contains_error("<div>Llegaste a tu límite de uso</div>"),
            "Gemini alcanzó su límite de uso",
        )

    def test_other_blocks_are_untouched(self):
        self.assertIsNotNone(Gemini.contains_error("<div>Something went wrong</div>"))
        self.assertIsNotNone(Gemini.contains_error("<div>Resolve the CAPTCHA</div>"))


class ExtractionTests(unittest.TestCase):
    def test_has_content_rejects_blank_and_accepts_a_real_image(self):
        transparent = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        solid = Image.new("RGB", (1024, 1024), (255, 255, 255))
        real = Image.linear_gradient("L").resize((1024, 1024)).convert("RGB")

        self.assertFalse(Gemini._has_content(png_bytes(transparent)))
        self.assertFalse(Gemini._has_content(png_bytes(solid)))
        self.assertTrue(Gemini._has_content(png_bytes(real)))

    def test_a_non_http_src_never_opens_the_browser(self):
        browser = Gemini(port=9222)

        self.assertIsNone(browser._download_cross_origin(None))
        self.assertIsNone(browser._download_cross_origin("blob:https://x/abc"))
        self.assertIsNone(browser.driver, "se conectó a Chrome para nada")

    def test_the_fingerprint_cache_is_keyed_by_path(self):
        """Una sola entrada global compararía la variante de un personaje contra
        la referencia de otro."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first, second = root / "a.png", root / "b.png"
            Image.new("RGB", (600, 600), (10, 20, 30)).save(first)
            Image.new("RGB", (600, 600), (200, 180, 160)).save(second)

            browser = Gemini()
            browser._ref_fp_cache = {
                str(path): browser._fingerprint(path.read_bytes())
                for path in (first, second)
            }

            self.assertEqual(len(browser._ref_fp_cache), 2)
            self.assertNotEqual(
                browser._ref_fp_cache[str(first)], browser._ref_fp_cache[str(second)]
            )


class PromptLandedTests(unittest.TestCase):
    """El prompt tiene que llegar al editor ANTES de tocar enviar.

    El 2026-08-06 el runner mandó imágenes sin prompt: el editor suelta el foco
    al `<body>` después de pegar la referencia, así que los keystrokes caían en
    la página. No se notaba porque la única comprobación era que el botón de
    enviar estuviera habilitado — y la imagen adjunta sola ya lo habilita.
    """

    def test_a_blank_editor_never_counts_as_landed(self):
        for empty in ("\n", "", "   \n  "):
            self.assertFalse(Gemini.prompt_landed(empty, "Match EXACTLY the art style"))

    def test_the_prompt_in_the_editor_counts_as_landed(self):
        prompt = "Match EXACTLY the art style, line weight and color treatment."
        self.assertTrue(Gemini.prompt_landed(prompt, prompt))

    def test_a_truncated_prompt_does_not_count(self):
        # Peor que el vacío: genera arte con medio prompt y lo da por bueno.
        prompt = "Match EXACTLY the art style, line weight and color treatment."
        self.assertFalse(Gemini.prompt_landed("Match EXACTLY the art", prompt))

    def test_whitespace_noise_from_the_editor_is_ignored(self):
        prompt = "Full body standing character, centered."
        self.assertTrue(Gemini.prompt_landed("Full body standing character, centered. \n", prompt))


class PromptChunkingTests(unittest.TestCase):
    """El prompt se tipea en tandas, pero tiene que seguir siendo EL prompt.

    Si el corte recortara espacios o normalizara saltos, el texto tipeado ya no
    sería el del .md: `prompt_landed` lo rechazaría (compara el arranque) o, peor,
    lo aceptaría y el modelo generaría contra un prompt levemente distinto.
    """

    PROMPT = (
        'Match EXACTLY the art style — "línea gruesa", barra \\ y comilla ".\n\n'
        "  Dos espacios al empezar la segunda línea y un salto al final.\n"
    )

    def test_chunks_concatenate_back_to_the_exact_prompt(self):
        for size in (1, 7, 64, 250, 10_000):
            self.assertEqual(
                "".join(chunk_prompt(self.PROMPT, size)), self.PROMPT,
                f"el corte de {size} caracteres alteró el prompt",
            )

    def test_no_chunk_is_longer_than_the_requested_size(self):
        chunks = chunk_prompt(self.PROMPT, 64)
        self.assertTrue(all(len(chunk) <= 64 for chunk in chunks))
        self.assertEqual(len(chunks), -(-len(self.PROMPT) // 64))  # ceil

    def test_empty_and_short_prompts_do_not_invent_chunks(self):
        self.assertEqual(chunk_prompt("", 250), [])
        self.assertEqual(chunk_prompt("hola", 250), ["hola"])

    def test_whitespace_and_newlines_survive_the_cut_untouched(self):
        chunks = chunk_prompt(self.PROMPT, 5)
        self.assertEqual("".join(chunks), self.PROMPT)
        self.assertEqual(chunks[0], self.PROMPT[:5])
        self.assertTrue(chunks[-1].endswith("\n"))
        self.assertEqual(sum(chunk.count("\n") for chunk in chunks), self.PROMPT.count("\n"))

    def test_an_absurd_chunk_size_still_yields_a_valid_split(self):
        for size in (0, -5):
            self.assertEqual("".join(chunk_prompt("hola", size)), "hola")

    def test_each_chunk_is_escaped_on_its_own_without_losing_characters(self):
        # El escape es por tanda: cortar en el medio de una comilla escapada
        # rompería el literal AppleScript y osascript se quejaría.
        rebuilt = "".join(
            unescape_applescript(applescript_string(chunk))
            for chunk in chunk_prompt(self.PROMPT, 7)
        )
        self.assertEqual(rebuilt, self.PROMPT)


class FakeCompleted:
    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


class FakeSystemEvents:
    """Emula lo justo de macOS: quién está al frente, dónde quedó el cursor y en
    QUÉ app aterriza cada tecla.

    `frontmost` es la secuencia de respuestas a "¿quién tiene el frente?"; la
    última se repite para siempre, así se modela tanto la ventana que aparece y
    se va como la que se queda.

    Dos detalles que no son adorno: cada app tiene SU buffer —lo que se teclea
    con el ladrón adelante no aparece en el de Chrome, igual que en la vida
    real— y el cursor existe de verdad, así que una tanda se inserta DONDE está
    el cursor y no siempre al final. Sin eso el test no podría fallar nunca por
    un prompt barajado, que es justo el fallo que hay que atrapar.
    """

    TimeoutExpired = subprocess.TimeoutExpired

    def __init__(self, frontmost=(CHROME,), keystroke_returncode=0,
                 frontmost_returncode=0, swallow_caret_reset=False,
                 eat_first_key_after_activate=False):
        self.frontmost = list(frontmost)
        self.keystroke_returncode = keystroke_returncode
        self.frontmost_returncode = frontmost_returncode
        # El editor puede comerse el cmd+↓; es la incógnita que obliga a
        # verificar el texto en vez de confiar en que el cursor volvió al final.
        self.swallow_caret_reset = swallow_caret_reset
        # La razón de ser del pre-tipeo descartable: la primera tecla después de
        # un `activate` se pierde a veces.
        self.eat_first_key_after_activate = eat_first_key_after_activate
        self.current = self.frontmost[0]
        self.buffers = {}
        self.carets = {}
        self.keystroke_log = []
        self.activates = 0
        self.frontmost_queries = 0
        self.keystrokes = 0
        self.caret_resets = 0
        self.keys_eaten = 0
        self._just_activated = False

    @property
    def typed(self) -> str:
        """Lo que hay en el compose box de Chrome."""
        return self.buffers.get(CHROME, "")

    @property
    def foreign_keys(self) -> list:
        """Todo lo que se tecleó en una app que NO era Chrome."""
        return [key for app, key in self.keystroke_log if app != CHROME]

    def click_compose(self) -> None:
        """El click de Selenium cae en el CENTRO del compose box, y ahí queda
        el cursor: ése es el origen del intercalado."""
        self.carets[CHROME] = len(self.buffers.get(CHROME, "")) // 2

    def _insert(self, text: str) -> None:
        app = self.current
        buffer, caret = self.buffers.get(app, ""), self.carets.get(app, 0)
        self.buffers[app] = buffer[:caret] + text + buffer[caret:]
        self.carets[app] = caret + len(text)
        self.keystroke_log.append((app, text))

    def _backspace(self) -> None:
        app = self.current
        buffer, caret = self.buffers.get(app, ""), self.carets.get(app, 0)
        if caret:
            self.buffers[app] = buffer[:caret - 1] + buffer[caret:]
            self.carets[app] = caret - 1
        self.keystroke_log.append((app, "<borrar>"))

    def run(self, command, **_kwargs):
        script = command[-1]
        if "frontmost is true" in script:
            self.frontmost_queries += 1
            if self.frontmost_returncode != 0:
                return FakeCompleted(
                    returncode=self.frontmost_returncode,
                    stderr="System Events got an error: osascript is not allowed "
                           "assistive access. (-25211)",
                )
            name = self.frontmost.pop(0) if len(self.frontmost) > 1 else self.frontmost[0]
            self.current = name
            return FakeCompleted(stdout=name + "\n")
        if "to activate" in script:
            # OJO: `activate` NO cambia quién está al frente en este fake. Es un
            # pedido, no una garantía: lo único que dice quién ganó es la
            # consulta siguiente. Modelarlo al revés esconde justo la carrera
            # que hace falta atrapar (teclear después de activate y antes de
            # confirmar es teclear a ciegas).
            self.activates += 1
            self._just_activated = True
            return FakeCompleted()
        if self._eats(script):
            return FakeCompleted()
        if "key code 51" in script:  # Delete: se come el pre-tipeo descartable
            self._backspace()
            return FakeCompleted()
        if "key code 125" in script:  # cmd+↓: cursor al final del texto
            self.caret_resets += 1
            self.keystroke_log.append((self.current, "<cursor al final>"))
            if not self.swallow_caret_reset:
                self.carets[self.current] = len(self.buffers.get(self.current, ""))
            return FakeCompleted()
        if " to keystroke " in script:
            self.keystrokes += 1
            if self.keystroke_returncode != 0:
                return FakeCompleted(
                    returncode=self.keystroke_returncode,
                    stderr="System Events got an error: osascript is not allowed "
                           "to send keystrokes. (1002)",
                )
            self._insert(unescape_applescript(script.split(" to keystroke ", 1)[1]))
        return FakeCompleted()

    def _eats(self, script: str) -> bool:
        """¿Se pierde esta tecla por venir justo después de un `activate`?"""
        if not ("key code" in script or " to keystroke " in script):
            return False
        lost = self._just_activated and self.eat_first_key_after_activate
        self._just_activated = False
        if lost:
            self.keys_eaten += 1
        return lost


class FakeEditor:
    """El compose box: devuelve lo que el sistema tipeó hasta ahora."""

    def __init__(self, system):
        self.system = system

    def get_attribute(self, name):
        return self.system.typed if name == "innerText" else None


class HeadlessTyping(Gemini):
    """El motor sin navegador: todo lo que toca Selenium queda anulado."""

    def __init__(self, system, **kwargs):
        super().__init__(**kwargs)
        self.system = system
        self.editor = FakeEditor(system)
        self.compose_clicks = 0
        self.sends = 0

    def _focus_compose(self):
        self.compose_clicks += 1
        self.system.click_compose()

    def _find_first(self, _selectors):
        return self.editor

    def _wait_for(self, _action, _description):
        return "el botón de enviar"

    def _driver(self):
        return self

    def execute_script(self, script, *_args):
        # Dos scripts distintos pasan por acá y confundirlos haría que enfocar
        # el editor se contara como una imagen enviada.
        if "click" in script:
            # El click al botón de enviar: acá es donde se gastaría la cuota.
            self.sends += 1
            return None
        if "focus" in script:
            return True  # el editor tomó el foco
        return None


class NoSleep:
    """`time` sin esperas: el camino de tipeo sólo usa `sleep`."""

    @staticmethod
    def sleep(_seconds):
        return None

    @staticmethod
    def monotonic():
        return 0.0


class TypingUnderFocusTheftTests(unittest.TestCase):
    """El 2026-08-16 tres imágenes se perdieron por el tipeo de una sola llamada.

    Con la máquina cargada (varios frontends de agente abiertos), el `keystroke`
    único de 2000+ caracteres tarda segundos: dos prompts escribieron 0 de ~2000
    —otra ventana se puso adelante y se llevó TODO el texto— y un tercero perdió
    cuatro caracteres. El guard `prompt_landed` abortó las tres veces sin gastar
    cuota, pero el prompt igual no entró.
    """

    PROMPT = ("Full body standing character, centered, blanco de fondo. " * 40)[:2099]

    #: La 1ª consulta es la del pre-tipeo; después va una por tanda. Con el
    #: ladrón en la 3ª, el robo cae con la tanda 1 YA escrita: recién ahí la
    #: posición del cursor puede barajar el prompt (con el editor vacío no).
    ROBO_EN_LA_TANDA_2 = [CHROME, CHROME, "Otro Agente", CHROME]

    def setUp(self):
        self.system = FakeSystemEvents()
        self._patch("subprocess", self.system)
        self._patch("time", NoSleep)
        self.stderr = io.StringIO()
        self._enter(contextlib.redirect_stderr(self.stderr))

    def _patch(self, name, value):
        original = getattr(webchat, name)
        setattr(webchat, name, value)
        self.addCleanup(setattr, webchat, name, original)

    def _enter(self, manager):
        manager.__enter__()
        self.addCleanup(manager.__exit__, None, None, None)

    def _browser(self, **kwargs):
        kwargs.setdefault("type_chunk", 250)
        kwargs.setdefault("type_pause", 0)
        # Esta clase entera prueba el camino de System Events: el tipeo por
        # tandas, la recuperación de foco y el intercalado sólo existen ahí. El
        # default es `cdp`, que no tiene nada de eso, así que el modo se pide
        # explícito en vez de heredarlo.
        kwargs.setdefault("typing", "keystroke")
        return HeadlessTyping(self.system, **kwargs)

    def test_the_whole_prompt_is_typed_in_chunks_and_lands_exact(self):
        browser = self._browser()

        browser._submit(self.PROMPT)

        self.assertEqual(self.system.typed, self.PROMPT)
        chunks = -(-len(self.PROMPT) // 250)
        # +1: el espacio descartable del pre-tipeo, que el Delete se lleva.
        self.assertEqual(self.system.keystrokes, chunks + 1)
        # Una consulta por tanda MÁS la del pre-tipeo: ahí está el arreglo.
        self.assertEqual(self.system.frontmost_queries, chunks + 1)
        self.assertEqual(browser.sends, 1)

    def test_the_sacrificial_keys_never_reach_a_foreign_app(self):
        # El espacio y el Delete descartables son teclas REALES. Si salen antes
        # de preguntar quién está al frente, con el ladrón adelante ese Backspace
        # lo cobra la app ajena: en Mail borra el mail seleccionado.
        self.system.frontmost = ["Ladrón Fugaz", CHROME]

        self._browser()._submit(self.PROMPT)

        self.assertEqual(self.system.foreign_keys, [])
        self.assertEqual(self.system.keystroke_log[0], (CHROME, " "))
        self.assertEqual(self.system.typed, self.PROMPT)

    def test_a_window_that_steals_the_focus_mid_prompt_is_recovered(self):
        self.system.frontmost = list(self.ROBO_EN_LA_TANDA_2)

        self._browser()._submit(self.PROMPT)

        # No es una verdad por construcción: el fake tiene cursor, y si el
        # cmd+↓ no lo devolviera al final esto saldría barajado.
        self.assertEqual(self.system.typed, self.PROMPT)
        self.assertEqual(self.system.caret_resets, 2)  # idempotente, va dos veces
        self.assertEqual(self.system.activates, 2)  # el de _submit y el de la recuperación
        self.assertEqual(self.system.foreign_keys, [])

    def test_the_caret_reset_survives_the_key_that_the_activate_eats(self):
        # La primera tecla después de un `activate` se pierde a veces —para eso
        # existe el espacio descartable del arranque—. El cmd+↓ que reordena el
        # cursor corre el mismo riesgo, y por eso se manda dos veces.
        self.system.frontmost = list(self.ROBO_EN_LA_TANDA_2)
        self.system.eat_first_key_after_activate = True

        self._browser()._submit(self.PROMPT)

        self.assertEqual(self.system.typed, self.PROMPT)
        self.assertEqual(self.system.keys_eaten, 2)  # el espacio y un cmd+↓
        self.assertEqual(self.system.caret_resets, 1)  # el que sobrevivió

    def test_a_recovery_is_announced_so_the_owner_can_audit_it(self):
        self.system.frontmost = list(self.ROBO_EN_LA_TANDA_2)

        self._browser()._submit(self.PROMPT)

        self.assertIn("Otro Agente", self.stderr.getvalue())

    def test_a_swallowed_caret_reset_aborts_instead_of_sending_a_shuffled_prompt(self):
        """El fallo caro que introduce la recuperación de foco.

        `_focus_compose` clickea el CENTRO del compose box. Si el cmd+↓ no llega
        al final —el editor puede comérselo— la tanda siguiente entra EN EL MEDIO
        del texto. El resultado tiene el largo justo y el arranque intacto, así
        que `prompt_landed` lo aprueba y se gasta cuota contra un prompt
        barajado. Antes del tipeo por tandas ese caso no existía: toda
        perturbación de foco daba vacío o truncado.
        """
        self.system.frontmost = list(self.ROBO_EN_LA_TANDA_2)
        self.system.swallow_caret_reset = True
        browser = self._browser()

        with self.assertRaises(GenerationBlocked) as caught:
            browser._submit(self.PROMPT)

        self.assertIn("intercal", str(caught.exception))
        self.assertEqual(browser.sends, 0, "se envió un prompt barajado: cuota gastada")
        self.assertNotEqual(self.system.typed, self.PROMPT[:len(self.system.typed)])

    def test_prompt_landed_alone_would_have_approved_a_shuffled_prompt(self):
        # Por qué hace falta comparar contra el prefijo y no alcanza el guard
        # viejo: barajado, el prompt conserva el largo y los primeros 40.
        half = len(self.PROMPT) // 2
        shuffled = self.PROMPT[:half] + self.PROMPT[-250:] + self.PROMPT[half:-250]

        self.assertNotEqual(shuffled, self.PROMPT)
        self.assertTrue(Gemini.prompt_landed(shuffled, self.PROMPT))

    def test_a_thief_that_never_leaves_aborts_naming_it(self):
        self.system.frontmost = ["Nombre Del Ladrón"]

        with self.assertRaises(GenerationBlocked) as caught:
            self._browser()._submit(self.PROMPT)

        # El nombre va al checkpoint: le dice al dueño QUÉ ventana cerrar.
        self.assertIn("Nombre Del Ladrón", str(caught.exception))
        # Ni una tecla, en ninguna app: ni el prompt ni el pre-tipeo descartable.
        self.assertEqual(self.system.keystroke_log, [])
        self.assertEqual(self.system.typed, "")
        self.assertEqual(self.system.activates, 1 + webchat.FOCUS_RECOVERIES)

    def test_a_failed_osascript_still_raises_with_the_accessibility_hint(self):
        self.system.keystroke_returncode = 1

        with self.assertRaises(GenerationBlocked) as caught:
            self._browser()._submit(self.PROMPT)

        self.assertIn("Accesibilidad", str(caught.exception))

    def test_a_prompt_that_never_lands_is_caught_before_sending(self):
        # La red de seguridad no se toca: si el editor quedó vacío (o a medias),
        # se aborta ANTES de tocar Enviar, aunque el tipeo no haya dado error.
        browser = self._browser()
        browser.editor = FakeEditor(FakeSystemEvents())  # editor que nunca recibe nada

        with self.assertRaises(GenerationBlocked) as caught:
            browser._submit(self.PROMPT)

        self.assertIn("el prompt no llegó al editor", str(caught.exception))
        self.assertEqual(browser.sends, 0)

    def test_a_frontmost_query_that_fails_blames_accessibility_not_a_thief(self):
        # Sin permiso de Accesibilidad la consulta falla igual que el keystroke:
        # el abort tiene que decir eso y no inventar una ventana ajena.
        self.system.frontmost_returncode = 1

        with self.assertRaises(GenerationBlocked) as caught:
            self._browser()._submit(self.PROMPT)

        self.assertIn("Accesibilidad", str(caught.exception))
        self.assertIn("assistive access", str(caught.exception))

    def test_chrome_already_frontmost_costs_no_recovery_attempt(self):
        browser = self._browser()

        self.assertEqual(browser._ensure_chrome_frontmost(3), 3)
        self.assertEqual(self.system.activates, 0)
        self.assertEqual(browser.compose_clicks, 0)
        self.assertEqual(self.system.caret_resets, 0)


class TransientDomErrorTests(unittest.TestCase):
    def test_wait_for_survives_a_stale_element_and_retries(self):
        """El DOM se rehace mientras lo leemos: hay que reintentar, no abortar."""
        from selenium.common.exceptions import StaleElementReferenceException

        browser = Gemini(timeout=5)
        # `_wait_for` chequea el bloqueo en cada vuelta, y eso hablaría con el
        # Chrome real. Sin este stub el test es FLAKY: con el navegador
        # levantado cada iteración tarda lo suficiente como para comerse los 5 s
        # antes del tercer intento, y falla por timeout en vez de por la
        # conducta que prueba.
        browser._check_blocked = lambda: None
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise StaleElementReferenceException("stale element not found")
            return "listo"

        self.assertEqual(browser._wait_for(flaky, "algo"), "listo")
        self.assertEqual(calls["n"], 3)


if __name__ == "__main__":
    unittest.main()


class HeadlessCdp(HeadlessTyping):
    """El motor por CDP. La propiedad que el fake tiene que reproducir es UNA:
    `Input.insertText` escribe en el compose box de Chrome tenga el frente quien
    lo tenga, porque el texto no pasa por la cola de eventos de macOS. Es lo que
    separa este camino del de teclas y lo único que estos tests miden."""

    def __init__(self, system, **kwargs):
        kwargs.setdefault("typing", "cdp")
        super().__init__(system, **kwargs)
        self.cdp_calls = []

    def execute_cdp_cmd(self, method, params):
        self.cdp_calls.append((method, params))
        if method == "Input.insertText":
            buffer = self.system.buffers.get(CHROME, "")
            caret = self.system.carets.get(CHROME, 0)
            text = params["text"]
            self.system.buffers[CHROME] = buffer[:caret] + text + buffer[caret:]
            self.system.carets[CHROME] = caret + len(text)
        return {}


class CdpTypingTests(unittest.TestCase):
    """El camino default: escribir por DevTools Protocol en vez de System Events.

    Se midió contra Gemini el 2026-08-19 —`Input.insertText` deja el texto en el
    composer y el botón de enviar aparece habilitado—, y eso desmintió el
    comentario que decía que sólo las teclas reales sirven: lo que no funciona es
    `send_keys` de Selenium, que es otra cosa. Lo que estos tests protegen son
    las tres consecuencias de esa medición, que es donde está el valor: no hace
    falta el permiso de Accesibilidad, no hace falta la máquina en exclusiva, y
    el prompt barajado deja de ser posible.
    """

    PROMPT = ("Match EXACTLY the attached reference, cream background. " * 40)[:2099]

    def setUp(self):
        self.system = FakeSystemEvents()
        self._patch("subprocess", self.system)
        self._patch("time", NoSleep)

    def _patch(self, name, value):
        original = getattr(webchat, name)
        setattr(webchat, name, value)
        self.addCleanup(setattr, webchat, name, original)

    def _browser(self, **kwargs):
        kwargs.setdefault("type_pause", 0)
        return HeadlessCdp(self.system, **kwargs)

    def test_the_prompt_goes_whole_in_one_call_and_sends_once(self):
        browser = self._browser()

        browser._submit(self.PROMPT)

        inserts = [p["text"] for m, p in browser.cdp_calls if m == "Input.insertText"]
        # Una sola llamada, no tandas: las tandas existen para acotar el daño de
        # un robo de foco, y por CDP ese daño no puede ocurrir.
        self.assertEqual(inserts, [self.PROMPT])
        self.assertEqual(self.system.typed, self.PROMPT)
        self.assertEqual(browser.sends, 1)

    def test_a_thief_at_the_front_does_not_cost_a_single_character(self):
        # La ventana ajena está adelante TODO el tiempo. Por el camino de teclas
        # esto era el fallo caro: el prompt entero aterrizaba en la otra app.
        self.system = FakeSystemEvents(frontmost=("Otro Agente",))
        self._patch("subprocess", self.system)

        browser = self._browser()
        browser._submit(self.PROMPT)

        self.assertEqual(self.system.typed, self.PROMPT)
        self.assertEqual(self.system.foreign_keys, [])
        self.assertEqual(browser.sends, 1)

    def test_the_default_path_never_touches_system_events(self):
        browser = self._browser()

        browser._submit(self.PROMPT)

        # Cada una de estas tres es un requisito que vuelve si alguien mete una
        # tecla de vuelta: el permiso de Accesibilidad, el robo de frente y la
        # espera del `activate`.
        self.assertEqual(self.system.keystrokes, 0)
        self.assertEqual(self.system.activates, 0)
        self.assertEqual(self.system.frontmost_queries, 0)

    def test_a_prompt_that_does_not_land_is_caught_before_sending(self):
        class Lossy(HeadlessCdp):
            def execute_cdp_cmd(self, method, params):
                if method == "Input.insertText":
                    params = dict(params, text=params["text"][:10])
                return super().execute_cdp_cmd(method, params)

        browser = Lossy(self.system, type_pause=0)

        with self.assertRaises(GenerationBlocked) as caught:
            browser._submit(self.PROMPT)

        self.assertIn("no llegó al editor", str(caught.exception))
        # Lo que importa: no se gastó cuota contra medio prompt.
        self.assertEqual(browser.sends, 0)


class TypingModeTests(unittest.TestCase):
    """El modo se elige una vez, al construir, y un valor inventado se cae ahí.

    Fallar en el constructor y no en la imagen 7 de 20 es la diferencia entre
    perder un segundo y perder media tanda."""

    def test_an_unknown_mode_is_refused_at_construction(self):
        with self.assertRaises(ValueError) as caught:
            Gemini(typing="teclas")
        self.assertIn("teclas", str(caught.exception))

    def test_the_default_is_cdp(self):
        self.assertEqual(Gemini().typing, "cdp")


class SilentQuotaTests(unittest.TestCase):
    """La cuota de IMÁGENES agotada no dice nada: deja el cartel de "generando".

    El 2026-08-19, con 18 de 20 ya hechas, las dos últimas fallaron con `timeout
    esperando la imagen generada` y ese mensaje mandó a subir `--timeout` a 480s
    y a reintentar tres veces, todo para nada. Lo que este test protege es el
    diagnóstico, no la mecánica: un timeout con el cartel puesto tiene que
    decirse distinto de un timeout a secas, porque la reacción correcta es otra
    —esperar, no insistir—.
    """

    class Silent(Gemini):
        """Un motor cuya página quedó en «Creando tu imagen»."""

        def __init__(self, page):
            super().__init__()
            self.page = page

        def _driver(self):
            return self

        @property
        def page_source(self):
            return self.page

    def test_a_timeout_with_the_generating_sign_up_blames_the_image_quota(self):
        browser = self.Silent("<div>Creando tu imagen</div>")

        explained = browser._explain_silence(GenerationBlocked("timeout esperando la imagen"))

        self.assertIn("cuota de IMÁGENES agotada", str(explained))
        self.assertIn("--timeout no cambia nada", str(explained))

    def test_the_english_sign_counts_too(self):
        browser = self.Silent("<div>Creating your image</div>")
        self.assertIn("creating your image", str(browser._explain_silence(GenerationBlocked("x"))))

    def test_a_timeout_without_the_sign_keeps_its_own_message(self):
        # Sin el cartel el timeout puede ser cualquier cosa —la red, el DOM, un
        # selector viejo—, y culpar a la cuota mandaría a esperar de gusto.
        original = GenerationBlocked("timeout esperando el botón de enviar")
        browser = self.Silent("<div>respuesta normal</div>")

        self.assertIs(browser._explain_silence(original), original)

    def test_a_page_that_cannot_be_read_keeps_the_original_error(self):
        class Broken(SilentQuotaTests.Silent):
            @property
            def page_source(self):
                raise RuntimeError("la pestaña se cerró")

        original = GenerationBlocked("timeout esperando la imagen")
        self.assertIs(Broken("")._explain_silence(original), original)


class VisibleTextTests(unittest.TestCase):
    """El bloqueo se busca en lo que la página muestra, no en su JavaScript."""

    class Page(Gemini):
        def __init__(self, source, visible):
            super().__init__()
            self.source, self.visible = source, visible

        def _driver(self):
            return self

        @property
        def page_source(self):
            return self.source

        def execute_script(self, script, *args):
            return self.visible

    def test_a_limit_template_in_the_code_does_not_block(self):
        # La plantilla real de ChatGPT, con el chat libre en pantalla.
        page = self.Page('{"active_task_limit_message_template":"Llegaste a tu límite de uso"}',
                         "What's on the agenda today?")
        page._check_blocked()

    def test_a_limit_on_screen_blocks(self):
        page = self.Page("<html></html>", "Llegaste a tu límite de uso. Volvé mañana.")
        with self.assertRaises(GenerationBlocked):
            page._check_blocked()


class CandidateSizeTests(unittest.TestCase):
    """Una pieza de diseño puede ser angosta y alta, y sigue siendo la generada.

    El 2026-08-20 un roll-up de feria de 420x1008 se generó bien y quedó en
    pantalla, pero el filtro de candidatos miraba el ANCHO contra 512, así que
    nunca compitió: el pedido murió en `timeout esperando la imagen generada` con
    la imagen a la vista. Es el mismo supuesto cuadrado que rechazaba los banners
    apaisados en `verify_png`.
    """

    def test_a_tall_rollup_competes(self):
        self.assertTrue(Gemini.is_candidate_size(420, 1008))

    def test_a_wide_banner_competes(self):
        self.assertTrue(Gemini.is_candidate_size(1024, 254))

    def test_a_square_generation_still_competes(self):
        self.assertTrue(Gemini.is_candidate_size(1024, 1024))

    def test_the_sites_own_chrome_never_competes(self):
        # Los tamaños medidos en la página de Gemini: sparkle, foto de perfil y
        # los íconos de la barra. Si alguno pasara, se guardaría como si fuera
        # la imagen generada.
        for width, height in ((150, 150), (128, 128), (64, 64), (32, 32)):
            self.assertFalse(
                Gemini.is_candidate_size(width, height), f"pasó un {width}x{height}"
            )
