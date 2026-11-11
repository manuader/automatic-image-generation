"""La rotación de motores: tandas alternadas que no parten familias ni el orden."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import ROOT, make_project, write_prompt

from core.queue import parse_asset, pending_assets
from core.rotation import Turn, family_order, parse_rotation, plan
from supervisor import Supervisor
from test_supervisor import FAKE, Clock

GEMINI_CHATGPT = [Turn("gemini", 3), Turn("chat-gpt", 3)]


def keys(batch):
    return [asset.key for asset in batch.assets]


class QueueFamilyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_family_comes_from_the_header(self):
        path = write_prompt(self.root / "prompts", "10_ceo", family="ceo")
        self.assertEqual(parse_asset(path, self.root).family, "ceo")

    def test_without_the_field_the_image_is_loose(self):
        path = write_prompt(self.root / "prompts", "10_ceo")
        self.assertIsNone(parse_asset(path, self.root).family)

    def test_a_family_line_inside_the_prompt_text_does_not_count(self):
        path = self.root / "11_x.md"
        path.write_text("# x\n\n- **estado**: pendiente\n\n## Prompt\n\n- **familia**: no\n",
                        encoding="utf-8")
        self.assertIsNone(parse_asset(path, self.root).family)


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.prompts = self.root / "prompts"
        (self.root / "output").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def queue(self, *specs):
        """specs: "01_a" o ("01_a", "familia")."""
        for spec in specs:
            name, family = (spec, None) if isinstance(spec, str) else spec
            write_prompt(self.prompts, name, reference=None, family=family)
        return pending_assets(self.prompts, self.root / "output", self.root)

    def test_parse(self):
        self.assertEqual(parse_rotation("gemini:50, chat-gpt:50"),
                         [Turn("gemini", 50), Turn("chat-gpt", 50)])
        for bad in ("gemini:50", "gemini:0,chat-gpt:5", "gemini,chat-gpt:5", "x:1,y"):
            with self.assertRaises(ValueError):
                parse_rotation(bad)
        with self.assertRaises(ValueError):
            parse_rotation("gemini:5,dalle:5", ["chat-gpt", "gemini"])

    def test_engines_alternate_every_n(self):
        queue = self.queue(*(f"{n:02d}_i{n}" for n in range(1, 9)))
        batches = plan(queue, GEMINI_CHATGPT)
        self.assertEqual([b.engine for b in batches], ["gemini", "chat-gpt", "gemini"])
        self.assertEqual([len(b.assets) for b in batches], [3, 3, 2])

    def test_a_family_is_never_cut_the_batch_closes_before_it(self):
        queue = self.queue("01_a", "02_b", ("03_ceo", "ceo"), ("04_ceo_skin", "ceo"), "05_c")
        batches = plan(queue, GEMINI_CHATGPT)
        self.assertEqual([keys(b) for b in batches], [["a", "b"], ["ceo", "ceo_skin", "c"]])
        self.assertEqual(batches[1].families, {"ceo": 2})

    def test_a_family_bigger_than_a_batch_goes_whole_in_its_own(self):
        queue = self.queue("01_a", *((f"{n:02d}_f{n}", "big") for n in range(2, 7)), "07_z")
        batches = plan(queue, GEMINI_CHATGPT)
        self.assertEqual([keys(b) for b in batches],
                         [["a"], ["f2", "f3", "f4", "f5", "f6"], ["z"]])
        self.assertEqual([b.engine for b in batches], ["gemini", "chat-gpt", "gemini"])

    def test_scattered_family_members_travel_together(self):
        queue = self.queue(("01_a", "x"), "02_b", ("03_c", "x"))
        self.assertEqual([a.key for a in family_order(queue)], ["a", "c", "b"])

    def test_a_resumed_plan_starts_where_the_turn_was(self):
        queue = self.queue("01_a", "02_b", "03_c")
        batches = plan(queue, GEMINI_CHATGPT, slot=1, sent=2)
        self.assertEqual([(b.engine, keys(b)) for b in batches],
                         [("chat-gpt", ["a"]), ("gemini", ["b", "c"])])

    def test_done_prompts_are_not_planned(self):
        queue = self.queue("01_a", "02_b")
        write_prompt(self.prompts, "03_hecha", state="hecho", reference=None)
        (self.root / "output" / "b.png").write_bytes(b"png")
        queue = pending_assets(self.prompts, self.root / "output", self.root)
        self.assertEqual([keys(b) for b in plan(queue, GEMINI_CHATGPT)], [["a"]])


class SupervisorRotationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = make_project(self.base / "proj")
        os.environ["FAKE_GENERATE_DIR"] = str(self.base)
        self.clock = Clock()

    def tearDown(self):
        os.environ.pop("FAKE_GENERATE_DIR", None)
        self.tmp.cleanup()

    def prompts(self, *specs):
        for spec in specs:
            name, family = (spec, None) if isinstance(spec, str) else spec
            write_prompt(self.project.prompts, name, reference=None, family=family)

    def scenario(self, **data):
        (self.base / "scenario.json").write_text(json.dumps(data))

    def calls(self):
        path = self.base / "calls.json"
        return json.loads(path.read_text()) if path.exists() else []

    def supervisor(self, turns=None, **kwargs):
        return Supervisor(
            self.project, [], {}, python=sys.executable, generator=FAKE,
            sleep=self.clock.sleep, now=self.clock.now, notify=lambda *a: None,
            kill=lambda engine: None, rotation=turns or [Turn("gemini", 2), Turn("chat-gpt", 2)],
            **kwargs,
        )

    def test_alternates_engines_by_batches(self):
        self.prompts(*(f"{n:02d}_i{n}" for n in range(1, 6)))
        self.scenario()
        self.assertEqual(self.supervisor().run(), 0)
        self.assertEqual([engine for _, engine in self.calls()],
                         ["gemini", "gemini", "chat-gpt", "chat-gpt", "gemini"])

    def test_counts_sent_requests_not_successes(self):
        # «a» falla una vez (se envió: cuenta) y sale al reintento: la tanda de
        # Gemini se completa con dos envíos de la misma imagen.
        self.prompts("01_a", "02_b", "03_c")
        self.scenario(fail_times={"a": 1})
        self.supervisor().run()
        self.assertEqual(self.calls(), [["a", "gemini"], ["a", "gemini"],
                                        ["b", "chat-gpt"], ["c", "chat-gpt"]])

    def test_a_browser_failure_was_not_sent_and_does_not_count(self):
        self.prompts("01_a", "02_b", "03_c")
        self.scenario(fail_times={"a": 1},
                      fail_reason="no pude conectar Selenium al Chrome aislado")
        self.supervisor().run()
        self.assertEqual([engine for _, engine in self.calls()],
                         ["gemini", "gemini", "gemini", "chat-gpt"])

    def test_the_queue_state_is_respected(self):
        self.prompts("01_a", "03_c")
        write_prompt(self.project.prompts, "02_hecha", state="hecho", reference=None)
        (self.project.output / "a.png").write_bytes(b"png")
        self.scenario()
        self.supervisor().run()
        self.assertEqual(self.calls(), [["c", "gemini"]])

    def test_out_of_quota_hands_the_turn_to_the_next_engine_in_order(self):
        self.prompts("01_a", "02_b", "03_c")
        self.scenario(fail_engine={"gemini": "Gemini alcanzó su límite de uso"})
        supervisor = self.supervisor()
        self.assertEqual(supervisor.run(), 0)
        # «a» se reintenta primero en ChatGPT: el orden no se pierde.
        self.assertEqual(self.calls(), [["a", "gemini"], ["a", "chat-gpt"],
                                        ["b", "chat-gpt"], ["c", "chat-gpt"]])

    def test_a_family_is_not_cut_in_a_real_run(self):
        self.prompts("01_a", ("02_f1", "f"), ("03_f2", "f"), "04_z")
        self.scenario()
        self.supervisor().run()
        self.assertEqual(self.calls(), [["a", "gemini"], ["f1", "chat-gpt"],
                                        ["f2", "chat-gpt"], ["z", "gemini"]])

    def test_the_turn_survives_a_restart(self):
        self.prompts("01_a", "02_b", "03_c")
        self.scenario()
        first = self.supervisor()
        first.step()
        self.supervisor().run()
        self.assertEqual([engine for _, engine in self.calls()],
                         ["gemini", "gemini", "chat-gpt"])


class DryRunTest(unittest.TestCase):
    def test_prints_the_plan_without_browsers(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp) / "proj")
            write_prompt(project.prompts, "01_a", reference=None)
            write_prompt(project.prompts, "02_ceo", reference=None, family="ceo")
            write_prompt(project.prompts, "03_ceo_skin", reference=None, family="ceo")
            result = subprocess.run(
                [sys.executable, str(ROOT / "supervisor.py"), "--project", str(project.root),
                 "--rotate", "gemini:2,chat-gpt:2", "--dry-run"],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("2 tandas", result.stdout)
            self.assertRegex(result.stdout, r"tanda +1 +gemini +1 de 2 +sueltas: 1")
            self.assertRegex(result.stdout, r"tanda +2 +chat-gpt +2 de 2 +familias: ceo \(2\)")
            self.assertFalse((project.state / "supervisor.pid").exists())
            self.assertFalse((project.state / "supervisor.json").exists())


if __name__ == "__main__":
    unittest.main()
