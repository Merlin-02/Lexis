"""Pruebas automatizadas para la Fase 3: Referencias explícitas entre leyes distintas y normas externas."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grafo_lexis.constructor_grafo import ConstructorGrafoLexis


class TestReferenciasLey(unittest.TestCase):
    """Pruebas para resolución de referencias cruzadas entre leyes del corpus y normas externas."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.constructor = ConstructorGrafoLexis()
        cls.constructor.cargar_y_construir_estructura_base()
        cls.resumen = cls.constructor.detectar_y_agregar_referencias_fase3()

    def test_referencias_cruzadas_cpc_a_codigo_civil(self) -> None:
        """Verifica que el Código de Procedimientos Civiles cite al Código Civil de Tlaxcala."""
        aristas_cpc_cc = [
            a
            for a in self.constructor.aristas_refiere_a
            if a.origen_ley_id == "ley:cpc_tlax" and a.destino_ley_id == "ley:cc_tlax"
        ]
        self.assertGreaterEqual(len(aristas_cpc_cc), 85)
        # Caso especial: cpc_tlax:1470 -> cc_tlax:240-C y 240-D
        destinos_1470 = {
            a.destino_id
            for a in aristas_cpc_cc
            if a.origen_id == "articulo:cpc_tlax:1470"
        }
        self.assertEqual(destinos_1470, {"articulo:cc_tlax:240-C", "articulo:cc_tlax:240-D"})

    def test_referencias_a_cpeum_y_orden_invertido(self) -> None:
        """Verifica citas a la Constitución Federal (CPEUM), incluyendo orden Ley -> Artículo."""
        aristas_a_cpeum = [
            a
            for a in self.constructor.aristas_refiere_a
            if a.destino_ley_id == "ley:cpeum" and a.relacion == "entre_leyes"
        ]
        self.assertGreaterEqual(len(aristas_a_cpeum), 45)
        # Verificar cp_tlax:6-TER (lista de 11 artículos de la CPEUM)
        citas_6ter = [
            a
            for a in aristas_a_cpeum
            if a.origen_id == "articulo:cp_tlax:6-TER"
        ]
        self.assertEqual(len(citas_6ter), 11)

    def test_normas_externas_y_menciona_norma(self) -> None:
        """Verifica que leyes fuera del corpus creen nodos NormaExterna y aristas MENCIONA_NORMA."""
        self.assertGreaterEqual(len(self.constructor.normas_externas), 10)
        self.assertGreaterEqual(len(self.constructor.aristas_menciona_norma), 12)
        nombres_ext = {n.nombre for n in self.constructor.normas_externas.values()}
        self.assertIn(
            "Constitución Política del Estado Libre y Soberano de Tlaxcala",
            nombres_ext,
        )
        self.assertIn("Ley del Seguro Social", nombres_ext)

    def test_referencia_rota_real_detectada(self) -> None:
        """Verifica que la errata real del art. 2310 del Código Penal en cpp_tlax:8-BIS se reporte como inexistente."""
        inexistentes = [
            r
            for r in self.constructor.referencias_rotas
            if r.motivo == "articulo_inexistente"
        ]
        self.assertEqual(len(inexistentes), 3)
        self.assertEqual(inexistentes[0].origen_id, "articulo:cpp_tlax:8-BIS")
        self.assertEqual(inexistentes[0].destino_mencionado, "articulo:cp_tlax:2310")


if __name__ == "__main__":
    unittest.main()
