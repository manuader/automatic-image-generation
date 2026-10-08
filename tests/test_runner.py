"""El runner y los dos modos de salida."""

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from support import make_project, png_bytes, subject_on_white, write_prompt

from core.checkpoint import RunCheckpoint
from core.images import verify_png
from core.postprocess import derive_for_project
from core.project import Project
from core.queue import parse_asset
from core.runner import AssetRunner


class FakeBrowser:
    """Devuelve bytes fijos y anota con qué referencia lo llamaron."""

    def __init__(self, payload: bytes):
        self.payload = payload
        self.calls = []

    def generate(self, asset, reference):
        self.calls.append((asset.key, reference))
        return self.payload


class ExplodingBrowser:
    def __init__(self, error):
        self.error = error

    def generate(self, _asset, _reference):
        raise self.error


class VerifyPngTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_rejects_non_png_and_undersized_files(self):
        text = self.root / "not-image.png"
        text.write_text("not a png", encoding="utf-8")
        self.assertFalse(verify_png(text, minimum_bytes=1))

        tiny = self.root / "tiny.png"
        Image.new("RGB", (8, 8), "white").save(tiny)
        self.assertFalse(verify_png(tiny, minimum_bytes=100_000))

    def test_accepts_a_decodable_sufficiently_large_file(self):
        image = self.root / "valid.png"
        Image.effect_noise((512, 512), 100).convert("RGB").save(image)
        self.assertTrue(verify_png(image, minimum_bytes=100_000))

    def test_accepts_a_flat_icon_far_below_a_bytes_gate(self):
        # Regresión: un ícono plano de 1024x1024 comprime muy por debajo de
        # 100 KB pero es válido. El gate es dimensional, no de bytes.
        icon = self.root / "flat_icon.png"
        Image.linear_gradient("L").resize((1024, 1024)).convert("RGB").save(icon)
        self.assertLess(icon.stat().st_size, 100_000)
        self.assertTrue(verify_png(icon))

    def test_rejects_small_dimensions_even_if_bytes_are_fine(self):
        small = self.root / "small.png"
        Image.effect_noise((128, 128), 100).convert("RGB").save(small)
        self.assertFalse(verify_png(small, minimum_bytes=1))


class CheckpointTests(unittest.TestCase):
    def test_records_success_and_failure_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = RunCheckpoint(Path(tmp) / "state" / "run.json")
            checkpoint.record_failure("next", "timeout")
            checkpoint.record_success("next", Path(tmp) / "next.png")

            saved = json.loads(checkpoint.path.read_text(encoding="utf-8"))
            self.assertEqual(saved["completed"], ["next"])
            self.assertEqual(saved["failures"]["next"], "timeout")
            self.assertEqual(saved["last_success"], "next")


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.valid = png_bytes(subject_on_white())

    def tearDown(self):
        self.temp.cleanup()

    def _asset(self, project, name="03_next", **kwargs):
        return parse_asset(write_prompt(project.prompts, name, **kwargs), base=project.root)

    def test_a_good_generation_saves_verifies_and_marks_the_md_done(self):
        project = make_project(self.root / "p")
        asset = self._asset(project)
        checkpoint = RunCheckpoint(project.checkpoint)

        self.assertTrue(AssetRunner(FakeBrowser(self.valid), project, checkpoint).run(asset))

        self.assertTrue((project.output / "next.png").is_file())
        self.assertIn("estado**: hecho", asset.path.read_text(encoding="utf-8"))
        self.assertEqual(checkpoint.data["completed"], ["next"])

    def test_something_that_is_not_a_png_keeps_the_md_pending(self):
        """El orden importa: el .md se marca hecho DESPUÉS de verificar. Al revés,
        un fallo a mitad de camino dejaría un prompt hecho sin imagen."""
        project = make_project(self.root / "p")
        asset = self._asset(project)
        checkpoint = RunCheckpoint(project.checkpoint)

        runner = AssetRunner(FakeBrowser(b"esto no es un png"), project, checkpoint)

        self.assertFalse(runner.run(asset))
        self.assertIn("estado**: pendiente", asset.path.read_text(encoding="utf-8"))
        self.assertIn("next", checkpoint.data["failures"])

    def test_a_selenium_error_sinks_only_that_image(self):
        """Un error del DOM no puede llevarse la corrida entera. Pasó el
        2026-08-10 con 8 imágenes por delante: `StaleElementReferenceException`
        subió hasta `main` y mató el proceso, porque el `except` atrapaba
        `(GenerationBlocked, OSError, RuntimeError)` y las de Selenium no son
        ninguna de las tres."""
        from selenium.common.exceptions import WebDriverException

        project = make_project(self.root / "p")
        asset = self._asset(project, "04_boom")
        checkpoint = RunCheckpoint(project.checkpoint)

        runner = AssetRunner(
            ExplodingBrowser(WebDriverException("stale element reference")),
            project, checkpoint,
        )

        self.assertFalse(runner.run(asset))
        self.assertIn("boom", checkpoint.data["failures"])
        self.assertIn("estado**: pendiente", asset.path.read_text(encoding="utf-8"))

    def test_the_runner_passes_the_prompts_own_reference(self):
        project = make_project(self.root / "p")
        asset = self._asset(project, "41_god__dorado", reference="output/god.png")
        browser = FakeBrowser(self.valid)

        AssetRunner(browser, project, RunCheckpoint(project.checkpoint)).run(asset)

        self.assertEqual(browser.calls, [("god__dorado", project.output / "god.png")])


class OutputModeTests(unittest.TestCase):
    """Los dos modos. La diferencia es sólo lo que pasa DESPUÉS de guardar."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.valid = png_bytes(subject_on_white())

    def tearDown(self):
        self.temp.cleanup()

    def _run(self, project):
        asset = parse_asset(write_prompt(project.prompts, "03_next"), base=project.root)
        runner = AssetRunner(FakeBrowser(self.valid), project, RunCheckpoint(project.checkpoint))
        self.assertTrue(runner.run(asset))

    def test_raw_saves_the_image_and_nothing_else(self):
        project = make_project(self.root / "raw", output="raw")

        self._run(project)

        self.assertTrue((project.output / "next.png").is_file())
        self.assertFalse(project.assets.exists(), "el modo raw no procesa nada")

    def test_game_asset_cuts_the_background_out_and_exports_the_sizes(self):
        project = make_project(self.root / "game", output="game-asset", sizes=[128, 64])

        self._run(project)

        # El original crudo se conserva SIEMPRE: es lo que costó cuota y lo que
        # permite rehacer el recorte sin volver a generar.
        with Image.open(project.output / "next.png") as original:
            self.assertEqual(original.mode, "RGB")

        cut = project.assets / "next.png"
        self.assertTrue(cut.is_file())
        with Image.open(cut) as image:
            self.assertEqual(image.mode, "RGBA")
            self.assertEqual(image.getpixel((0, 0))[3], 0, "el fondo blanco sigue opaco")
            self.assertEqual(image.getpixel((image.width // 2, image.height // 2))[3], 255)

        for side in (128, 64):
            with Image.open(project.assets / f"next_{side}.png") as resized:
                self.assertEqual(max(resized.size), side)

    def test_without_sizes_game_asset_only_writes_the_cutout(self):
        project = make_project(self.root / "solo-recorte", output="game-asset")

        self._run(project)

        self.assertEqual([p.name for p in sorted(project.assets.glob("*.png"))], ["next.png"])

    def test_reprocessing_needs_no_browser_and_no_quota(self):
        """El único hueco del camino normal: si el post-proceso falla después de
        guardar, la cola no vuelve a pedir la imagen (y hace bien). Rehacerla
        desde el original tiene que ser posible sin abrir nada."""
        project = make_project(self.root / "re", output="game-asset", sizes=[256])
        original = project.output / "vieja.png"
        project.output.mkdir(parents=True, exist_ok=True)
        subject_on_white().save(original)

        written = derive_for_project(project, "vieja", original)

        self.assertEqual(
            sorted(path.name for path in written), ["vieja.png", "vieja_256.png"]
        )

    def test_an_invalid_output_mode_is_rejected_when_the_project_loads(self):
        root = self.root / "malo"
        root.mkdir()
        (root / "project.json").write_text('{"output": "recortar-un-poco"}', encoding="utf-8")

        with self.assertRaises(ValueError) as caught:
            Project.load(root)

        self.assertIn("recortar-un-poco", str(caught.exception))


if __name__ == "__main__":
    unittest.main()


class WideFormatTests(unittest.TestCase):
    """Una pieza apaisada es válida: el piso va sobre el lado LARGO.

    El 2026-08-20 una portada de LinkedIn de 1024x254 —correcta, 314 KB, la pieza
    que se había pedido— se rechazó con "no es un PNG válido del tamaño
    esperado". El piso se medía sobre el lado corto, así que ningún banner 4:1 ni
    ningún roll-up podía pasar jamás: el formato entero era imposible por
    construcción. Estos tests fijan las dos mitades del criterio, porque aflojar
    sólo una deja pasar la iconografía del sitio.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def _png(self, name, size):
        path = self.root / name
        Image.effect_noise(size, 100).convert("RGB").save(path)
        return path

    def test_a_wide_banner_is_accepted(self):
        self.assertTrue(verify_png(self._png("banner.png", (1024, 254)), minimum_bytes=1))

    def test_a_tall_rollup_is_accepted(self):
        self.assertTrue(verify_png(self._png("rollup.png", (500, 1200)), minimum_bytes=1))

    def test_the_sites_own_icons_are_still_rejected(self):
        # Los tamaños medidos en la página de Gemini, que compiten como
        # candidatos con la imagen generada.
        for side in (150, 128, 64, 32):
            path = self._png(f"ui{side}.png", (side, side))
            self.assertFalse(verify_png(path, minimum_bytes=1), f"pasó un {side}x{side}")

    def test_a_degenerate_strip_is_rejected(self):
        # Larga pero de 20 px de alto: no es una imagen, es una franja.
        self.assertFalse(verify_png(self._png("strip.png", (1024, 20)), minimum_bytes=1))
