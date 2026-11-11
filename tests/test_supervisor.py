"""El supervisor: que reintente lo justo y no pague dos veces la misma imagen."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from support import make_project, write_prompt

from supervisor import ASSET, BROWSER, QUOTA, Supervisor, classify

FAKE = Path(__file__).with_name("fake_generate.py")


class Clock:
    """Tiempo de mentira: `sleep` avanza el reloj en vez de esperar."""

    def __init__(self):
        self.t = 1_000_000.0
        self.slept = []

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.t += seconds


class SupervisorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = make_project(self.base / "proj")
        os.environ["FAKE_GENERATE_DIR"] = str(self.base)
        self.clock = Clock()
        self.kills = []
        self.notes = []

    def tearDown(self):
        os.environ.pop("FAKE_GENERATE_DIR", None)
        self.tmp.cleanup()

    def prompts(self, *names, references=None):
        references = references or {}
        for name in names:
            write_prompt(self.project.prompts, name, reference=references.get(name))

    def scenario(self, **data):
        (self.base / "scenario.json").write_text(json.dumps(data))

    def calls(self):
        path = self.base / "calls.json"
        return json.loads(path.read_text()) if path.exists() else []

    def supervisor(self, engines=("chat-gpt", "gemini"), rules=None, **kwargs):
        return Supervisor(
            self.project, list(engines), rules or {}, python=sys.executable,
            generator=FAKE, sleep=self.clock.sleep, now=self.clock.now,
            notify=lambda *a: self.notes.append(a), kill=self.kills.append, **kwargs,
        )

    def test_generates_everything_once(self):
        self.prompts("01_a", "02_b", "03_c")
        self.scenario()
        self.assertEqual(self.supervisor().run(), 0)
        self.assertEqual([key for key, _ in self.calls()], ["a", "b", "c"])

    def test_a_failing_image_is_asked_three_times_then_left_out(self):
        self.prompts("01_a", "02_b")
        self.scenario(fail={"a": "timeout esperando la imagen generada"})
        supervisor = self.supervisor()
        self.assertEqual(supervisor.run(), 1)
        keys = [key for key, _ in self.calls()]
        self.assertEqual(keys.count("a"), 3)
        self.assertEqual(keys.count("b"), 1)
        self.assertIn("a", supervisor.state.skipped)

    def test_a_flaky_image_succeeds_on_retry_without_extra_requests(self):
        self.prompts("01_a")
        self.scenario(fail_times={"a": 1})
        self.assertEqual(self.supervisor().run(), 0)
        self.assertEqual([key for key, _ in self.calls()], ["a", "a"])

    def test_dependents_of_a_skipped_image_are_never_requested(self):
        self.prompts("01_a", "02_b", references={"02_b": "output/a.png"})
        self.scenario(fail={"a": "no se pudo generar"})
        supervisor = self.supervisor()
        supervisor.run()
        self.assertNotIn("b", [key for key, _ in self.calls()])
        self.assertIn("b", supervisor.state.skipped)

    def test_quota_pauses_the_engine_and_moves_to_the_next_without_counting(self):
        self.prompts("01_a")
        self.scenario(fail_engine={"chat-gpt": "ChatGPT alcanzó su límite de uso"})
        supervisor = self.supervisor()
        self.assertEqual(supervisor.run(), 0)
        self.assertEqual(self.calls(), [["a", "chat-gpt"], ["a", "gemini"]])
        self.assertEqual(supervisor.state.attempts, {})
        self.assertGreater(supervisor.blocked_until("chat-gpt"), self.clock.now() - 1)

    def test_one_stuck_generation_is_retried_before_pausing(self):
        self.prompts("01_a")
        self.scenario(fail_times={"a": 1}, fail_reason="gemini aceptó el pedido y se quedó en "
                      "«creating your image» sin devolver imagen. así se ve la cuota de IMÁGENES")
        supervisor = self.supervisor(engines=("gemini",))
        self.assertEqual(supervisor.run(), 0)
        self.assertEqual(self.calls(), [["a", "gemini"], ["a", "gemini"]])
        self.assertEqual(self.clock.slept, [])

    def test_two_stuck_generations_in_a_row_pause_the_engine(self):
        self.prompts("01_a")
        self.scenario(fail_engine={"gemini": "gemini se quedó en «creating your image». "
                                             "así se ve la cuota de IMÁGENES"})
        supervisor = self.supervisor(engines=("gemini",))
        original = supervisor.wait_for_an_engine

        def wait_then_unblock(ready):
            original(ready)
            self.scenario()
        supervisor.wait_for_an_engine = wait_then_unblock
        self.assertEqual(supervisor.run(), 0)
        self.assertEqual(len(self.calls()), 3)
        self.assertIn(30 * 60, [round(s) for s in self.clock.slept])

    def test_a_blocked_probe_costs_no_request(self):
        self.prompts("01_a")
        self.scenario(probe={"chat-gpt": {"compose_box": None, "send_button": None,
                                          "blocked": "ChatGPT alcanzó su límite de uso"}})
        self.supervisor().run()
        self.assertEqual(self.calls(), [["a", "gemini"]])

    def test_an_engine_only_prefix_waits_for_its_engine(self):
        self.prompts("01_bg_alley")
        self.scenario(probe={"chat-gpt": {"compose_box": None, "send_button": None,
                                          "blocked": "ChatGPT alcanzó su límite de uso"}})
        # Se libera recién después de la pausa: el fondo espera y no prueba Gemini.
        supervisor = self.supervisor(rules={"bg_": "chat-gpt"})
        original = supervisor.wait_for_an_engine

        def wait_then_unblock(ready):
            original(ready)
            self.scenario()
        supervisor.wait_for_an_engine = wait_then_unblock
        self.assertEqual(supervisor.run(), 0)
        self.assertEqual(self.calls(), [["bg_alley", "chat-gpt"]])
        self.assertIn(30 * 60, [round(s) for s in self.clock.slept])

    def test_three_browser_failures_in_a_row_restart_the_engine(self):
        self.prompts("01_a")
        self.scenario(fail_times={"a": 3},
                      fail={})
        supervisor = self.supervisor(engines=("gemini",), max_asset_attempts=5)
        supervisor.run()
        self.assertEqual(self.kills, ["gemini"])
        self.assertEqual(len(self.calls()), 4)

    def test_a_hung_request_is_killed_and_counted(self):
        self.prompts("01_a")
        self.scenario(hang=["a"])
        supervisor = self.supervisor(engines=("gemini",), asset_timeout=1,
                                     max_asset_attempts=1)
        self.assertEqual(supervisor.run(), 1)
        self.assertIn("colgado", supervisor.state.skipped["a"])

    def test_state_survives_a_restart(self):
        self.prompts("01_a", "02_b")
        self.scenario(fail={"a": "timeout esperando la imagen generada"})
        first = self.supervisor(max_asset_attempts=3)
        first.step()
        first.step()
        second = self.supervisor(max_asset_attempts=3)
        second.run()
        self.assertEqual([key for key, _ in self.calls()].count("a"), 3)


class ClassifyTest(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(classify("Gemini alcanzó su límite de uso"), QUOTA)
        self.assertEqual(classify("gemini aceptó el pedido y se quedó en «creando tu imagen» "
                                  "sin devolver imagen. No es el timeout: así se ve la cuota "
                                  "de IMÁGENES agotada"), QUOTA)
        self.assertEqual(classify("no pude conectar Selenium al Chrome aislado"), BROWSER)
        self.assertEqual(classify("el prompt no llegó entero. No envío: sería cuota gastada"),
                         BROWSER)
        self.assertEqual(classify("el prompt no llegó al editor: se escribieron 2998 de 1478 "
                                  "caracteres"), BROWSER)
        self.assertEqual(classify("timeout esperando que gemini abra la conversación tras "
                                  "enviar"), BROWSER)
        self.assertEqual(classify("Message: invalid session id: session deleted as the "
                                  "browser has closed the connection"), BROWSER)
        self.assertEqual(classify("timeout esperando la imagen generada"), ASSET)
        self.assertEqual(classify("Gemini no pudo generar la imagen"), ASSET)


if __name__ == "__main__":
    unittest.main()
