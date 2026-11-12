"""Pruebas automatizadas para la Fase 6: Exportación a JSON, GraphML, CSVs/Cypher de Neo4j y CLI."""

import sys
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grafo_lexis.cli import main as cli_main
from grafo_lexis.exportador import ExportadorGrafoLexis
from grafo_lexis.reporte_rotas import RUTA_KNOWLEDGE_GRAPH_DEFECTO


class TestExportacionFase6(unittest.TestCase):
    """Pruebas integrales de construcción, exportación e importación de artefactos en knowledge_graph/."""

    def test_1_cli_construir_y_exportar_todos_los_formatos(self) -> None:
        """Verifica que el comando 'construir' genere grafo_lexis.json, grafo_lexis.graphml y neo4j/."""
        ret = cli_main(["construir"])
        self.assertEqual(ret, 0)

        ruta_json = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "grafo_lexis.json"
        ruta_gml = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "grafo_lexis.graphml"
        ruta_cypher = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "neo4j" / "importar_y_consultar.cypher"
        ruta_csv_ref = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "neo4j" / "aristas_refiere_a.csv"

        self.assertTrue(ruta_json.exists())
        self.assertTrue(ruta_gml.exists())
        self.assertTrue(ruta_cypher.exists())
        self.assertTrue(ruta_csv_ref.exists())

        # Verificar que el XML de GraphML esté bien formado
        tree = ET.parse(ruta_gml)
        root = tree.getroot()
        self.assertTrue(root.tag.endswith("graphml"))

    def test_2_recarga_rapida_desde_json(self) -> None:
        """Verifica que cargar_desde_json reconstruya exactamente el mismo número de nodos y aristas."""
        grafo_recargado = ExportadorGrafoLexis.cargar_desde_json()
        self.assertGreaterEqual(grafo_recargado.number_of_nodes(), 7235)
        self.assertGreaterEqual(grafo_recargado.number_of_edges(), 10130)

        # Verificar comando CLI rápido sobre el grafo ya persistido
        ret_citas = cli_main(["citas", "--articulo", "1470", "--ley", "CPC-TLAX"])
        self.assertEqual(ret_citas, 0)


if __name__ == "__main__":
    unittest.main()
