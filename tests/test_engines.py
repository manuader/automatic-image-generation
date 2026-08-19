"""El contrato que todo motor tiene que cumplir.

Vale más de lo que parece: el motor de ChatGPT se escribió SIN poder abrirlo
—macOS pide permiso de Accesibilidad para mandar teclas y el entorno que lo
escribió no lo tiene—, así que estas pruebas son lo único que separa "un perfil
incompleto" de "un perfil que hay que verificar contra la página". No dicen que
los selectores sean los correctos; dicen que están todos, que son buscables y
que las frases de bloqueo pueden llegar a matchear.
"""

import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401  (pone la raíz en sys.path)

from core import chrome, engines

ENGINES = engines.available()


class EngineRegistryTests(unittest.TestCase):
    def test_both_engines_are_discoverable(self):
        self.assertEqual(ENGINES, ["chat-gpt", "gemini"])

    def test_an_unknown_engine_says_which_ones_hay(self):
        with self.assertRaises(SystemExit) as caught:
            engines.load("midjourney")
        self.assertIn("gemini", str(caught.exception))

    def test_a_directory_name_with_a_dash_still_loads(self):
        # `chat-gpt` no es un identificador de Python; se carga por path a
        # propósito para no tener que renombrar el directorio que eligió el dueño.
        self.assertEqual(engines.load("chat-gpt").NAME, "chat-gpt")


class EngineProfileTests(unittest.TestCase):
    """Un test por motor, generado desde la lista: agregar un motor nuevo lo
    somete a lo mismo sin tocar este archivo."""

    def test_every_engine_declares_a_complete_profile(self):
        for name in ENGINES:
            with self.subTest(engine=name):
                browser = engines.load(name)
                self.assertEqual(browser.NAME, name)
                self.assertTrue(browser.HOME_URL.startswith("https://"))
                self.assertTrue(browser.NEW_CHAT_URL.startswith("https://"))
                self.assertTrue(browser.CONVERSATION_URL_MARK)
                self.assertTrue(browser.SEND_BUTTON_SELECTORS, "sin botón de enviar no envía")
                self.assertTrue(browser.COMPOSE_SELECTORS)
                self.assertTrue(browser.ERROR_PATTERNS, "sin frases de error nunca detecta un bloqueo")

    def test_the_conversation_mark_does_not_appear_in_the_new_chat_url(self):
        """La marca es la ÚNICA confirmación honesta de que el envío salió: el
        botón de enviar se habilita con la imagen adjunta sola. Si la marca ya
        estuviera en la URL de chat nuevo, confirmaría siempre — incluso cuando
        no se mandó nada."""
        for name in ENGINES:
            with self.subTest(engine=name):
                browser = engines.load(name)
                self.assertNotIn(browser.CONVERSATION_URL_MARK, browser.NEW_CHAT_URL)

    def test_every_selector_uses_a_strategy_that_selenium_conoce(self):
        from selenium.webdriver.common.by import By

        for name in ENGINES:
            browser = engines.load(name)
            for kind, value in [*browser.COMPOSE_SELECTORS, *browser.SEND_BUTTON_SELECTORS]:
                with self.subTest(engine=name, selector=value):
                    self.assertTrue(hasattr(By, kind), f"By.{kind} no existe")
                    self.assertTrue(value.strip())

    def test_error_and_benign_phrases_are_lowercase(self):
        """`contains_error` pasa la página a minúsculas antes de buscar. Una
        frase declarada con mayúsculas no matchearía NUNCA, y el fallo sería
        silencioso: el batch seguiría mandando prompts contra una cuota agotada."""
        for name in ENGINES:
            browser = engines.load(name)
            for phrase in [*browser.ERROR_PATTERNS, *browser.BENIGN_NOTICES]:
                with self.subTest(engine=name, phrase=phrase):
                    self.assertEqual(phrase, phrase.lower())

    def test_every_benign_notice_actually_neutralises_the_block(self):
        """El aviso preventivo comparte substring con el bloqueo real. Si no lo
        descontara primero, TODAS las imágenes fallarían con "límite alcanzado"
        y el batch se frenaría con la cuota intacta."""
        for name in ENGINES:
            browser = engines.load(name)
            for notice in browser.BENIGN_NOTICES:
                with self.subTest(engine=name, notice=notice):
                    self.assertIsNone(browser.contains_error(f"<div>{notice}</div>"))

    def test_every_error_phrase_is_detected_on_its_own(self):
        for name in ENGINES:
            browser = engines.load(name)
            for phrase, reason in browser.ERROR_PATTERNS.items():
                with self.subTest(engine=name, phrase=phrase):
                    self.assertEqual(browser.contains_error(f"<p>{phrase}</p>"), reason)


class ChromeLauncherTests(unittest.TestCase):
    def test_the_launcher_uses_the_debug_port_and_a_profile_per_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "gemini"
            command = chrome.chrome_command(profile, "https://gemini.google.com/", 9222)

        self.assertEqual(chrome.debug_url(), "http://127.0.0.1:9222/json/version")
        self.assertIn("--remote-debugging-port=9222", command)
        self.assertIn(f"--user-data-dir={profile}", command)
        self.assertIn("https://gemini.google.com/", command)

    def test_each_engine_gets_its_own_profile_and_its_own_port(self):
        """Perfil propio Y puerto propio, o el perfil no sirve de nada.

        `ensure_debug_chrome` da por buena cualquier Chrome que ya conteste en el
        puerto. Con un puerto compartido, `--launch` del segundo motor encuentra
        el Chrome del primero, devuelve "ya estaba abierto" y el batch termina
        manejando la sesión equivocada sin decir una palabra. Pasó de verdad el
        2026-08-19: un `--probe` de chat-gpt se conectó al Chrome de Gemini que
        estaba abierto en 9222."""
        puertos = {name: engines.load(name).DEBUG_PORT for name in ENGINES}
        perfiles = {name: chrome.profile_for(name) for name in ENGINES}

        self.assertEqual(len(set(puertos.values())), len(ENGINES), f"puertos repetidos: {puertos}")
        self.assertEqual(len(set(perfiles.values())), len(ENGINES))

    def test_a_browser_without_an_explicit_port_uses_its_engines_own(self):
        for name in ENGINES:
            with self.subTest(engine=name):
                browser = engines.load(name)
                self.assertEqual(browser().port, browser.DEBUG_PORT)
                self.assertEqual(browser(port=9999).port, 9999)


if __name__ == "__main__":
    unittest.main()
