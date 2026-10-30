"""Pruebas automatizadas para la Fase 5: Reporte de referencias rotas y motor de consultas."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grafo_lexis.constructor_grafo import ConstructorGrafoLexis
from grafo_lexis.consultas import ConsultasGrafoLexis
from grafo_lexis.reporte_rotas import GeneradorReporteRotas


class TestConsultasFase5(unittest.TestCase):
    """Pruebas unitarias e integrales para las consultas jurídicas y el reporte de rotas."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.constructor = ConstructorGrafoLexis()
        cls.constructor.cargar_y_construir_estructura_base()
        cls.constructor.detectar_y_agregar_referencias_fase4()
        cls.consultas = ConsultasGrafoLexis(cls.constructor.grafo)
        cls.reporte_gen = GeneradorReporteRotas(cls.constructor.referencias_rotas)

    def test_reporte_referencias_rotas_y_guardado(self) -> None:
        """Verifica la estructura del reporte de referencias rotas y su exportación a knowledge_graph/."""
        reporte = self.reporte_gen.generar_reporte()
        resumen = reporte["resumen"]
        self.assertEqual(resumen["total_rotas_estrictas_en_corpus"], 1)
        self.assertGreaterEqual(resumen["total_hacia_leyes_externas"], 14)
        self.assertGreaterEqual(resumen["total_ambiguas_o_indeterminadas"], 65)

        ruta = self.reporte_gen.guardar_json()
        self.assertTrue(ruta.exists())

    def test_consulta_citas_directas(self) -> None:
        """Verifica consulta '¿qué artículos cita directamente el artículo X?'."""
        # Consultar usando clave de ley y número con espacio ("1470", "CPC-TLAX")
        res = self.consultas.citas_directas("1470", ley="CPC-TLAX")
        self.assertEqual(res["articulo_origen"]["id"], "articulo:cpc_tlax:1470")
        self.assertEqual(res["total_articulos_citados"], 2)
        destinos = {c["destino_id"] for c in res["articulos_citados"]}
        self.assertEqual(destinos, {"articulo:cc_tlax:240-C", "articulo:cc_tlax:240-D"})

    def test_consulta_afectados_impacto_directo_y_transitivo(self) -> None:
        """Verifica consulta '¿qué artículos se ven afectados si modifico el artículo X?'."""
        # Artículo 123 de la CPEUM es citado tanto por artículos de CPEUM como de LFT
        imp_1 = self.consultas.afectados("123", ley="CPEUM", profundidad=1)
        self.assertGreaterEqual(imp_1["total_articulos_unicos_afectados"], 12)
        self.assertIn("ley:lft", imp_1["por_ley_afectada"])
        self.assertIn("ley:cpeum", imp_1["por_ley_afectada"])

        # Profundidad 2 debe ser mayor o igual que profundidad 1
        imp_2 = self.consultas.afectados("123", ley="CPEUM", profundidad=2)
        self.assertGreaterEqual(
            imp_2["total_articulos_unicos_afectados"],
            imp_1["total_articulos_unicos_afectados"],
        )

    def test_consulta_leyes_mas_referenciadas_y_top_articulos(self) -> None:
        """Verifica ranking de leyes que más se referencian entre sí y artículos más citados."""
        res_leyes = self.consultas.leyes_mas_referenciadas()
        pares = res_leyes["pares_entre_leyes_distintas"]
        self.assertGreaterEqual(len(pares), 6)
        # El par más frecuente es CPC-TLAX -> CC-TLAX
        self.assertEqual(pares[0]["ley_origen_id"], "ley:cpc_tlax")
        self.assertEqual(pares[0]["ley_destino_id"], "ley:cc_tlax")
        self.assertGreaterEqual(pares[0]["total_referencias"], 150)

        top_arts = self.consultas.articulos_mas_citados(top_n=10)
        self.assertEqual(len(top_arts), 10)
        self.assertGreaterEqual(
            top_arts[0]["total_citas_recibidas"],
            top_arts[-1]["total_citas_recibidas"],
        )

    def test_camino_entre_articulos_y_estadisticas(self) -> None:
        """Verifica búsqueda de camino más corto entre artículos de distintas leyes y guardado de estadísticas."""
        # cpc_tlax:1470 cita a cc_tlax:240-C (1 salto dirigido)
        camino = self.consultas.camino_entre(
            "articulo:cpc_tlax:1470", "articulo:cc_tlax:240-C", dirigido=True
        )
        self.assertTrue(camino["existe_camino"])
        self.assertEqual(camino["saltos"], 1)

        ruta_est = self.consultas.guardar_estadisticas_json()
        self.assertTrue(ruta_est.exists())


if __name__ == "__main__":
    unittest.main()
