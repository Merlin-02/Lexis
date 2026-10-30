"""Pruebas automatizadas para la Fase 7: Integración GraphRAG y módulo opcional Groq."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grafo_lexis.integracion_rag import construir_contexto_graphrag
from grafo_lexis.llm_groq import DesambiguadorGroqLexis
from grafo_lexis.modelos import ReferenciaRota
from grafo_lexis.recuperador_grafo import RecuperadorGrafoLexis
from grafo_lexis.visualizador_obsidian import (
    extraer_datos_subgrafo_consulta,
    generar_html_obsidian,
)


class TestGraphRAGFase7(unittest.TestCase):
    """Pruebas unitarias e integrales del flujo GraphRAG (RecuperadorGrafoLexis + integracion_rag)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.recuperador = RecuperadorGrafoLexis()

    def test_mapeo_hit_chromadb_a_nodo_grafo(self) -> None:
        """Verifica que un hit del buscador híbrido se mapee a su nodo canónico en el grafo."""
        hit_cpc = {
            "documento": "Codigo Procedimientos Civiles Tlaxcala",
            "articulo": "ARTICULO 1470",
            "jerarquia": "Capitulo XIV",
            "texto": "Cuando el o los adoptantes y el adoptado mayor de edad pidan que la adopción sea revocada...",
        }
        nodo_id = self.recuperador.mapear_hit_a_nodo_articulo(hit_cpc)
        self.assertEqual(nodo_id, "articulo:cpc_tlax:1470")

        # Hit con etiqueta truncada original (reparada en el grafo)
        hit_lft_trunc = {
            "documento": "Ley Trabajo",
            "articulo": "Artículo 153-",
            "jerarquia": "Capitulo III BIS",
            "texto": "A. Los patrones tienen la obligación de proporcionar a todos los trabajadores...",
        }
        nodo_lft = self.recuperador.mapear_hit_a_nodo_articulo(hit_lft_trunc)
        self.assertEqual(nodo_lft, "articulo:lft:153-A")

    def test_expansion_graphrag_con_citas_entre_leyes(self) -> None:
        """Verifica que construir_contexto_graphrag expanda un hit de CPC-TLAX trayendo los artículos citados de CC-TLAX."""
        hits_simulados = [
            {
                "documento": "Codigo Procedimientos Civiles Tlaxcala",
                "articulo": "ARTICULO 1470",
                "jerarquia": "Capitulo XIV",
                "texto": "Cuando el o los adoptantes y el adoptado mayor de edad pidan que la adopción sea revocada, el Juez los citará a una junta para dentro de los tres días siguientes, en la que resolverá conforme a los artículos 240 C fracción I y 240 D del Código Civil.",
            }
        ]
        ctx = construir_contexto_graphrag(
            hits_simulados,
            max_fragmentos_base=1,
            max_vecinos_grafo=3,
            recuperador=self.recuperador,
        )
        self.assertIn("ARTÍCULOS RELACIONADOS EN EL GRAFO DE CONOCIMIENTO JURÍDICO", ctx["bloque_prompt"])
        self.assertIn("240-C", ctx["bloque_prompt"])
        self.assertIn("240-D", ctx["bloque_prompt"])
        self.assertIn("Código Civil de Tlaxcala", ctx["resumen_grafo_md"])
        salientes_ids = {
            v["articulo_id"] for v in ctx["expansion"]["vecinos_citados_salientes"]
        }
        self.assertIn("articulo:cc_tlax:240-C", salientes_ids)
        self.assertIn("articulo:cc_tlax:240-D", salientes_ids)

    def test_modulo_opcional_groq_sin_api_key_no_falla(self) -> None:
        """Verifica que DesambiguadorGroqLexis sea 100% opcional y seguro cuando no se pasa API key."""
        desamb = DesambiguadorGroqLexis(api_key="")
        self.assertFalse(desamb.disponible)
        ref_prueba = ReferenciaRota(
            origen_id="articulo:cc_tlax:256",
            ley_origen="ley:cc_tlax",
            texto_referencia="los artículos anteriores",
            destino_mencionado="los artículos anteriores",
            motivo="relativa_ambigua",
            snippet="La nulidad a que se refieren los artículos anteriores...",
            span_inicio=10,
            span_fin=34,
            confianza="baja",
        )
        res = desamb.desambiguar_referencia(ref_prueba)
        self.assertFalse(res["resuelta_por_llm"])

    def test_visualizador_obsidian_subgrafo_consulta(self) -> None:
        """Verifica que el visualizador tipo Cerebro de Obsidian genere los nodos semilla y concatenados."""
        hits_simulados = [
            {
                "documento": "Codigo Procedimientos Civiles Tlaxcala",
                "articulo": "ARTICULO 1470",
                "jerarquia": "Capitulo XIV",
                "texto": "Cuando el o los adoptantes y el adoptado mayor de edad pidan que la adopción sea revocada...",
            }
        ]
        ctx = construir_contexto_graphrag(
            hits_simulados,
            max_fragmentos_base=1,
            max_vecinos_grafo=3,
            recuperador=self.recuperador,
        )
        datos_vis = extraer_datos_subgrafo_consulta(
            self.recuperador.grafo, ctx["expansion"], incluir_nodos_ley=True
        )
        ids_nodos = {n["id"] for n in datos_vis["nodes"]}
        self.assertIn("articulo:cpc_tlax:1470", ids_nodos)
        self.assertIn("articulo:cc_tlax:240-C", ids_nodos)
        self.assertIn("articulo:cc_tlax:240-D", ids_nodos)
        self.assertIn("ley:cpc_tlax", ids_nodos)
        self.assertIn("ley:cc_tlax", ids_nodos)

        html = generar_html_obsidian(datos_vis)
        self.assertIn("vis.Network", html)
        self.assertIn("articulo:cpc_tlax:1470", html)


if __name__ == "__main__":
    unittest.main()
