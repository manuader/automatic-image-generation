"""La cola: qué se genera, qué se saltea y de dónde sale cada referencia."""

import tempfile
import unittest
from pathlib import Path

from support import write_prompt

from core.queue import parse_asset, pending_assets


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.prompts = self.root / "prompts"
        self.output = self.root / "output"
        self.prompts.mkdir()
        self.output.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def test_queue_is_ordered_and_skips_done_and_already_generated(self):
        (self.prompts / "00_INDICE.md").write_text("# Índice", encoding="utf-8")
        write_prompt(self.prompts, "03_next")
        write_prompt(self.prompts, "01_done", state="hecho")
        write_prompt(self.prompts, "02_already")
        (self.output / "already.png").write_bytes(b"exists")

        queue = pending_assets(self.prompts, self.output, self.root)

        self.assertEqual([asset.key for asset in queue], ["next"])
        self.assertEqual(queue[0].order, 3)
        self.assertTrue(queue[0].needs_reference)

    def test_an_existing_output_alone_is_enough_to_not_regenerate(self):
        """La garantía de "no volver a pagarlo": copiar imágenes viejas a
        `output/` alcanza para que la cola no las vuelva a pedir, aunque el .md
        siga diciendo `pendiente`."""
        write_prompt(self.prompts, "07_copiada")
        self.assertEqual(len(pending_assets(self.prompts, self.output, self.root)), 1)

        (self.output / "copiada.png").write_bytes(b"la de la corrida anterior")

        self.assertEqual(pending_assets(self.prompts, self.output, self.root), [])

    def test_the_index_is_not_an_image_to_generate(self):
        (self.prompts / "00_INDICE.md").write_text("# Índice\n\n## Prompt\n\nx\n", encoding="utf-8")
        self.assertEqual(pending_assets(self.prompts, self.output, self.root), [])

    def test_reference_path_comes_from_the_md_and_resolves_from_the_project(self):
        """Cada prompt adjunta la SUYA. Antes el campo se leía como un booleano y
        se adjuntaba siempre la misma imagen, lo que mandaba la referencia de un
        personaje como estilo de otro."""
        prompt = write_prompt(self.prompts, "40_ceo__magnate", reference="output/ceo.png")

        asset = parse_asset(prompt, base=self.root)

        self.assertTrue(asset.needs_reference)
        self.assertEqual(asset.reference, self.root / "output" / "ceo.png")

    def test_a_prompt_without_reference_has_none(self):
        prompt = write_prompt(self.prompts, "47_bg_alley", reference=None)

        asset = parse_asset(prompt, base=self.root)

        self.assertIsNone(asset.reference)
        self.assertFalse(asset.needs_reference)

    def test_an_absolute_reference_is_respected(self):
        prompt = write_prompt(self.prompts, "48_logo", reference="/tmp/marca.png")
        self.assertEqual(parse_asset(prompt, base=self.root).reference, Path("/tmp/marca.png"))

    def test_several_backticked_references_are_all_attached_in_order(self):
        """Un personaje nuevo suele pedir más de una imagen de contexto. Van en el
        mismo campo y se adjuntan juntas; la primera es la que manda."""
        path = self.prompts / "01_mascota.md"
        path.write_text(
            "# 01\n\n- **estado**: pendiente\n"
            "- **referencia**: adjuntar `references/a.png`, `references/b.png` y `/tmp/c.png`\n"
            "\n## Prompt\n\nx\n",
            encoding="utf-8",
        )

        asset = parse_asset(path, base=self.root)

        self.assertEqual(asset.reference, self.root / "references" / "a.png")
        self.assertEqual(
            asset.references,
            (self.root / "references" / "a.png", self.root / "references" / "b.png", Path("/tmp/c.png")),
        )

    def test_a_single_reference_keeps_meaning_exactly_what_it_meant(self):
        prompt = write_prompt(self.prompts, "02_uno", reference="output/ceo.png")
        asset = parse_asset(prompt, base=self.root)
        self.assertEqual(asset.references, (self.root / "output" / "ceo.png",))
        self.assertEqual(asset.extra_references, ())

    def test_no_reference_means_no_references(self):
        prompt = write_prompt(self.prompts, "03_nada", reference=None)
        self.assertEqual(parse_asset(prompt, base=self.root).references, ())

    def test_a_prompt_without_a_prompt_section_is_rejected_loudly(self):
        path = self.prompts / "09_vacio.md"
        path.write_text("# Sin prompt\n\n- **estado**: pendiente\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            parse_asset(path, base=self.root)


if __name__ == "__main__":
    unittest.main()
