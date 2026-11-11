"""El recorte con la regla de recorte de football-evolution: sombra de piso y huecos."""

import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

from core.cutout import cutout
from core.project import Project

CREMA = (255, 243, 220)
GRIS_SOMBRA = (225, 225, 225)
TEAL = (20, 120, 120)


def figura_con_sombra() -> Image.Image:
    """Dos piernas teal con una sombra gris que las une por abajo y blanco entre ellas.

    El blanco entre las piernas queda encerrado: lo rodean las piernas, el torso
    y la sombra. Un parche crema en el torso hace de cuello."""
    lienzo = np.full((200, 200, 3), 255, dtype=np.uint8)
    lienzo[40:90, 60:140] = TEAL          # torso
    lienzo[50:60, 90:110] = CREMA         # cuello crema
    lienzo[90:170, 60:85] = TEAL          # pierna izquierda
    lienzo[90:170, 115:140] = TEAL        # pierna derecha
    lienzo[165:180, 50:150] = GRIS_SOMBRA  # sombra de piso
    lienzo[165:170, 60:85] = TEAL
    lienzo[165:170, 115:140] = TEAL
    return Image.fromarray(lienzo)


def alpha(imagen: Image.Image) -> np.ndarray:
    return np.array(imagen)[..., 3]


class FloorShadowTests(unittest.TestCase):
    def test_sin_la_opcion_la_sombra_y_el_hueco_quedan(self):
        a = alpha(cutout(figura_con_sombra()))
        self.assertEqual(a[175, 100], 255)  # sombra
        self.assertEqual(a[130, 100], 255)  # blanco entre las piernas

    def test_la_sombra_y_el_blanco_que_encerraba_se_van(self):
        a = alpha(cutout(figura_con_sombra(), floor_shadow=True))
        self.assertEqual(a[175, 100], 0)
        self.assertEqual(a[130, 100], 0)

    def test_el_crema_y_las_piernas_quedan_opacos(self):
        a = alpha(cutout(figura_con_sombra(), floor_shadow=True))
        self.assertEqual(a[55, 100], 255)   # cuello crema
        self.assertEqual(a[130, 70], 255)   # pierna
        self.assertEqual(a[167, 70], 255)   # pie

    def test_un_gris_neutro_arriba_de_la_franja_no_se_toca(self):
        imagen = np.array(figura_con_sombra())
        imagen[20:40, 90:110] = GRIS_SOMBRA  # pelo gris pegado al fondo, arriba
        a = alpha(cutout(Image.fromarray(imagen), floor_shadow=True))
        self.assertEqual(a[30, 100], 255)


class PunchHolesTodasTests(unittest.TestCase):
    def proyecto(self, ajustes: str) -> Project:
        raiz = Path(tempfile.mkdtemp())
        (raiz / "project.json").write_text(ajustes, encoding="utf-8")
        return Project.load(raiz)

    def test_asterisco_vale_para_cualquier_clave(self):
        p = self.proyecto('{"punch_holes": "*"}')
        self.assertTrue(p.punches_holes("bebe_futbolero_idle"))

    def test_lista_vale_solo_para_sus_claves(self):
        p = self.proyecto('{"punch_holes": ["wheel_frame"]}')
        self.assertTrue(p.punches_holes("wheel_frame"))
        self.assertFalse(p.punches_holes("bebe_futbolero_idle"))

    def test_floor_shadow_apagado_por_defecto(self):
        self.assertFalse(self.proyecto("{}").settings["floor_shadow"])


if __name__ == "__main__":
    unittest.main()
