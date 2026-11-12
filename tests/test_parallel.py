"""Motores en paralelo: los dos trabajan a la vez y nunca piden la misma imagen."""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from support import ROOT, make_project, write_prompt

from core.checkpoint import RunCheckpoint, read_json
from core.parallel import claim_batch, parse_parallel, units
from core.queue import pending_assets
from core.rotation import Turn
from supervisor import ParallelSupervisor
from test_supervisor import FAKE


class ThreadClock:
    """Tiempo de mentira compartido por los carriles: `sleep` avanza el reloj y
    cede de verdad un instante, para que el carril ocioso no acapare el candado."""

    def __init__(self):
        self.t = 1_000_000.0
        self.guard = threading.Lock()

    def now(self):
        return self.t

    def sleep(self, seconds):
        with self.guard:
            self.t += seconds
        time.sleep(0.01)


class PureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.prompts = self.root / "prompts"
        (self.root / "output").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def queue(self, *specs):
        """specs: "01_a", ("01_a", "familia") o ("01_a", None, "output/x.png")."""
        for spec in specs:
            name, family, reference = (spec, None, None) if isinstance(spec, str) else (
                spec + (None,))[:3]
            write_prompt(self.prompts, name, reference=reference, family=family)
        return pending_assets(self.prompts, self.root / "output", self.root)

    def test_parse(self):
        self.assertEqual(parse_parallel("gemini:50,chat-gpt:50"),
                         [Turn("gemini", 50), Turn("chat-gpt", 50)])
        with self.assertRaisesRegex(ValueError, "una sola vez"):
            parse_parallel("gemini:5,gemini:5")
        with self.assertRaisesRegex(ValueError, "--parallel"):
            parse_parallel("gemini:x,chat-gpt:5")

    def test_a_family_is_one_unit_in_the_place_of_its_first_member(self):
        queue = self.queue("01_a", ("02_npc", "npc"), "03_b", ("04_npc_talk", "npc"))
        self.assertEqual([[asset.key for asset in unit] for unit in units(queue)],
                         [["a"], ["npc", "npc_talk"], ["b"]])

    def test_an_image_built_on_another_pending_output_goes_with_it(self):
        queue = self.queue("01_base", "02_x", ("03_skin", None, "output/base.png"))
        self.assertEqual([[asset.key for asset in unit] for unit in units(queue)],
                         [["base", "skin"], ["x"]])

    def test_a_batch_skips_what_is_taken_and_never_cuts_a_unit(self):
        queue = self.queue("01_a", "02_b", ("03_f1", "f"), ("04_f2", "f"), "05_c")
        self.assertEqual(claim_batch(queue, 3, {"a"}), [["b"], ["f1", "f2"]])
        self.assertEqual(claim_batch(queue, 2, set()), [["a"], ["b"]])
        self.assertEqual(claim_batch(queue, 1, {"a", "b"}), [["f1", "f2"]])
        self.assertEqual(claim_batch(queue, 5, {"a", "b", "f1", "c"}), [])


class CheckpointLockTest(unittest.TestCase):
    def test_two_writers_do_not_erase_each_other(self):
        # Lo que pasaba con dos generate.py: cada uno reescribía run.json con
        # lo que había leído al arrancar.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state" / "run.json"
            gemini, chatgpt = RunCheckpoint(path), RunCheckpoint(path)
            gemini.record_failure("a", "timeout")
            chatgpt.record_success("b", Path(tmp) / "b.png")
            data = read_json(path)
            self.assertEqual(data["failures"], {"a": "timeout"})
            self.assertEqual(data["completed"], ["b"])


class ParallelSupervisorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.project = make_project(self.base / "proj")
        os.environ["FAKE_GENERATE_DIR"] = str(self.base)
        self.clock = ThreadClock()
        self.kills = []

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
        return ParallelSupervisor(
            self.project, turns or [Turn("gemini", 2), Turn("chat-gpt", 2)],
            python=sys.executable, generator=FAKE, sleep=self.clock.sleep,
            now=self.clock.now, notify=lambda *a: None, kill=self.kills.append, **kwargs,
        )

    def test_both_engines_work_and_no_image_is_asked_twice(self):
        self.prompts(*(f"{n:02d}_i{n}" for n in range(1, 9)))
        self.scenario()
        self.assertEqual(self.supervisor().run(), 0)
        keys = [key for key, _ in self.calls()]
        self.assertEqual(sorted(keys), sorted(f"i{n}" for n in range(1, 9)))
        self.assertEqual({engine for _, engine in self.calls()}, {"gemini", "chat-gpt"})
        self.assertEqual(len(list(self.project.output.glob("*.png"))), 8)

    def test_the_engines_really_overlap(self):
        self.prompts(*(f"{n:02d}_i{n}" for n in range(1, 5)))
        self.scenario(delay=0.4)
        self.supervisor().run()
        spans = json.loads((self.base / "spans.json").read_text())
        gemini = [(start, end) for _, engine, start, end in spans if engine == "gemini"]
        chatgpt = [(start, end) for _, engine, start, end in spans if engine == "chat-gpt"]
        self.assertTrue(any(a < d and c < b for a, b in gemini for c, d in chatgpt),
                        spans)

    def test_a_family_goes_whole_to_one_engine(self):
        self.prompts("01_a", ("02_npc", "npc"), ("03_npc_talk", "npc"),
                     ("04_npc_action", "npc"), ("05_npc_face", "npc"), "06_b")
        self.scenario(delay=0.05)
        self.supervisor().run()
        engines = {engine for key, engine in self.calls() if key.startswith("npc")}
        self.assertEqual(len(engines), 1, self.calls())

    def test_out_of_quota_releases_the_batch_to_the_other_engine(self):
        self.prompts(*(f"{n:02d}_i{n}" for n in range(1, 7)))
        self.scenario(fail_engine={"gemini": "Gemini alcanzó su límite de uso"})
        supervisor = self.supervisor()
        self.assertEqual(supervisor.run(), 0)
        self.assertEqual(len(list(self.project.output.glob("*.png"))), 6)
        state = read_json(self.project.state / "supervisor.json")
        self.assertIn("gemini", state["blocks"])
        self.assertEqual(state["attempts"], {})
        self.assertEqual(state["skipped"], {})

    def test_a_hard_reset_kills_only_its_own_engine(self):
        self.prompts(*(f"{n:02d}_i{n}" for n in range(1, 9)))
        self.scenario(fail_engine={"gemini": "no pude conectar selenium al Chrome aislado"})
        self.supervisor().run()
        self.assertTrue(self.kills)
        self.assertEqual(set(self.kills), {"gemini"})

    def test_claims_survive_a_restart_and_a_new_spec_drops_them(self):
        self.prompts("01_a", "02_b", "03_c")
        state_path = self.project.state / "supervisor.json"
        state_path.write_text(json.dumps({"parallel": {
            "spec": "gemini:2,chat-gpt:2",
            "claims": {"chat-gpt": [{"keys": ["a"], "started": True}]},
        }}))
        self.scenario()
        self.supervisor().run()
        self.assertIn(["a", "chat-gpt"], self.calls())
        self.assertNotIn(["a", "gemini"], self.calls())
        other = self.supervisor(turns=[Turn("gemini", 3), Turn("chat-gpt", 3)])
        self.assertEqual(other.state.parallel["claims"], {})

    def test_a_started_family_waits_for_its_engine_until_nothing_else_is_left(self):
        self.prompts("01_a", ("02_f1", "f"), ("03_f2", "f"))
        (self.project.output / "f1.png").write_bytes(b"png")
        (self.project.state / "supervisor.json").write_text(json.dumps({
            "blocks": {"gemini": {"strikes": 1, "until": 9e12, "reason": "cuota"}},
            "parallel": {"spec": "gemini:2,chat-gpt:2",
                         "claims": {"gemini": [{"keys": ["f1", "f2"], "started": True}]}},
        }))
        self.scenario()
        self.assertEqual(self.supervisor().run(), 0)
        self.assertEqual(self.calls(), [["a", "chat-gpt"], ["f2", "chat-gpt"]])


class DryRunTest(unittest.TestCase):
    def test_prints_the_first_batches_without_browsers(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = make_project(Path(tmp) / "proj")
            write_prompt(project.prompts, "01_a", reference=None)
            write_prompt(project.prompts, "02_ceo", reference=None, family="ceo")
            write_prompt(project.prompts, "03_ceo_skin", reference=None, family="ceo")
            result = subprocess.run(
                [sys.executable, str(ROOT / "supervisor.py"), "--project", str(project.root),
                 "--parallel", "gemini:1,chat-gpt:2", "--dry-run"],
                capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout, r"gemini +1 de 1 +1 unidades +a … a")
            self.assertRegex(result.stdout, r"chat-gpt +2 de 2 +1 unidades +ceo … ceo_skin")
            self.assertFalse((project.state / "supervisor.json").exists())

    def test_parallel_and_rotate_do_not_mix(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "supervisor.py"), "--project", "x",
             "--parallel", "gemini:1,chat-gpt:2", "--rotate", "gemini:1,chat-gpt:2"],
            capture_output=True, text=True, timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no se combina", result.stderr)


if __name__ == "__main__":
    unittest.main()
