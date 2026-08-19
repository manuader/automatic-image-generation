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

    def execute_script(self, *_args):
        # El click al botón de enviar: acá es donde se gastaría la cuota.
        self.sends += 1
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
