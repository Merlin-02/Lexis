"""Pruebas automatizadas para la Fase 4: Expansión de rangos de artículos."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grafo_lexis.constructor_grafo import ConstructorGrafoLexis


class TestRangosFase4(unittest.TestCase):
    """Pruebas unitarias e integrales para expansión de rangos numéricos y con sufijos."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.constructor = ConstructorGrafoLexis()
        cls.constructor.cargar_y_construir_estructura_base()
        cls.resumen = cls.constructor.detectar_y_agregar_referencias_fase4()
        cls.aristas_rango = [
            a for a in cls.constructor.aristas_refiere_a if a.clase == "rango"
        ]

    def test_expansion_rango_simple_misma_ley(self) -> None:
        """Verifica expansión de un rango numérico simple como 'artículos 670 a 676' en CC-TLAX."""
        aristas_682 = [
            a for a in self.aristas_rango if a.origen_id == "articulo:cc_tlax:682"
        ]
        destinos = [a.destino_id for a in aristas_682]
        esperados = [f"articulo:cc_tlax:{n}" for n in range(670, 677)]
        self.assertEqual(destinos, esperados)
        for a in aristas_682:
            self.assertEqual(a.rango, "670..676")
            self.assertIsNotNone(a.grupo_id)

    def test_expansion_rango_con_sufijos_alfabeticos_lft(self) -> None:
        """Verifica expansión secuencial de 'artículos 897-A al 897-G' en LFT."""
        aristas_897 = [
            a for a in self.aristas_rango if a.origen_id == "articulo:lft:897"
        ]
        destinos = [a.destino_id for a in aristas_897]
        esperados = [f"articulo:lft:897-{letra}" for letra in ["A", "B", "C", "D", "E", "F", "G"]]
        self.assertEqual(destinos, esperados)

    def test_rango_incluye_subarticulos_intermedios_bis(self) -> None:
        """Verifica que la expansión por orden secuencial incluya subartículos Bis/Ter intermedios."""
        # En LFT, el rango 982 al 991 (citado en lft:709-C) incluye subartículos intermedios como 985 Bis o 990 Bis si existen,
        # o en CC-TLAX el rango 1383 a 1390 / 2651 a 2672 sigue el orden real de la ley.
        aristas_709c = [
            a for a in self.aristas_rango if a.origen_id == "articulo:lft:709-C"
        ]
        self.assertGreaterEqual(len(aristas_709c), 10)
        self.assertEqual(aristas_709c[0].destino_id, "articulo:lft:982")
        self.assertEqual(aristas_709c[-1].destino_id, "articulo:lft:991")

    def test_rango_entre_leyes_distintas_y_anafora(self) -> None:
        """Verifica rangos que cruzan de CPC-TLAX a CC-TLAX y CPP-TLAX, incluyendo anáfora 'del mismo Código'."""
        # cpc_tlax:166 cita 'artículos 2790 y 2646 a 2648 del Código civil'
        aristas_166 = [
            a
            for a in self.constructor.aristas_refiere_a
            if a.origen_id == "articulo:cpc_tlax:166"
        ]
        destinos_166 = {a.destino_id for a in aristas_166}
        self.assertEqual(
            destinos_166,
            {
                "articulo:cc_tlax:2790",
                "articulo:cc_tlax:2646",
                "articulo:cc_tlax:2647",
                "articulo:cc_tlax:2648",
            },
        )

        # cpc_tlax:1270 cita 'artículos 2969 a 2975 del mismo Código' (heredado de cpc_tlax:1269 -> Código civil)
        aristas_1270 = [
            a for a in self.aristas_rango if a.origen_id == "articulo:cpc_tlax:1270"
        ]
        self.assertEqual(len(aristas_1270), 7)
        self.assertTrue(all(a.destino_ley_id == "ley:cc_tlax" for a in aristas_1270))


if __name__ == "__main__":
    unittest.main()
