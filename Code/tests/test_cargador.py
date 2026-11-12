"""Pruebas automatizadas para la Fase 2: Carga, normalización, nodos y aristas CONTIENE."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from grafo_lexis.cargador import normalizar_registro_articulo, cargar_corpus_completo
from grafo_lexis.constructor_grafo import ConstructorGrafoLexis


def test_normalizacion_153_a_y_f_bis():
    """Verifica reconstrucción de 153-A y 153-F Bis en LFT."""
    reg_a = {
        "articulo": "Artículo 153-",
        "jerarquia": "Capitulo III BIS",
        "texto_general": "A. Los patrones tienen la obligación de proporcionar...",
        "fracciones": [],
        "incisos_directos": [],
        "historial_dof": [],
    }
    nodo_a = normalizar_registro_articulo(reg_a, "lft", "ley:lft", 173, False, 0)
    assert nodo_a.id == "articulo:lft:153-A"
    assert nodo_a.numero == "153-A"
    assert nodo_a.numero_base == 153
    assert nodo_a.sufijo == "A"
    assert nodo_a.texto_general.startswith("Los patrones tienen")

    reg_fbis = {
        "articulo": "Artículo 153-",
        "jerarquia": "Capitulo III BIS",
        "texto_general": "F Bis. Los patrones deberán conservar...",
        "fracciones": [],
        "incisos_directos": [],
        "historial_dof": [],
    }
    nodo_fbis = normalizar_registro_articulo(reg_fbis, "lft", "ley:lft", 179, False, 0)
    assert nodo_fbis.id == "articulo:lft:153-F-BIS"
    assert nodo_fbis.numero == "153-F BIS"
    assert nodo_fbis.sufijo == "F-BIS"


def test_normalizacion_135_a_y_640_quater_a():
    """Verifica reconstrucción de 135-A y 640 QUATER A en Código Civil."""
    reg_135a = {
        "articulo": "ARTICULO 135",
        "jerarquia": "Capitulo V",
        "texto_general": "A.- Los cónyuges que pretendan divorciarse...",
        "fracciones": [],
        "incisos_directos": [],
        "historial_dof": [],
    }
    nodo_135a = normalizar_registro_articulo(reg_135a, "cc_tlax", "ley:cc_tlax", 143, False, 0)
    assert nodo_135a.id == "articulo:cc_tlax:135-A"
    assert nodo_135a.numero == "135-A"
    assert nodo_135a.sufijo == "A"

    reg_640qa = {
        "articulo": "ARTICULO 640 QUATER",
        "jerarquia": "Capitulo XI",
        "texto_general": "A. Las personas que requieran el reconocimiento...",
        "fracciones": [],
        "incisos_directos": [],
        "historial_dof": [],
    }
    nodo_640qa = normalizar_registro_articulo(reg_640qa, "cc_tlax", "ley:cc_tlax", 691, False, 0)
    assert nodo_640qa.id == "articulo:cc_tlax:640-QUATER-A"
    assert nodo_640qa.numero == "640 QUATER A"
    assert nodo_640qa.sufijo == "QUATER-A"


def test_normalizacion_229_bis_y_falso_ter():
    """Verifica 229 BIS en Código Penal y reparación de 'Ter' + 'minado'."""
    reg_229bis = {
        "articulo": "Artículo 229",
        "jerarquia": "Capitulo ",
        "texto_general": "bis. A quien cometa feminicidio...",
        "fracciones": [],
        "incisos_directos": [],
        "historial_dof": [],
    }
    nodo_229 = normalizar_registro_articulo(reg_229bis, "cp_tlax", "ley:cp_tlax", 233, False, 0)
    assert nodo_229.id == "articulo:cp_tlax:229-BIS"
    assert nodo_229.numero == "229 BIS"
    assert nodo_229.sufijo == "BIS"

    reg_falso_ter = {
        "articulo": "ARTICULO 1044.- Ter",
        "jerarquia": "Capitulo V",
        "texto_general": "minado el usufructo, los contratos...",
        "fracciones": [],
        "incisos_directos": [],
        "historial_dof": [],
    }
    nodo_1044 = normalizar_registro_articulo(reg_falso_ter, "cc_tlax", "ley:cc_tlax", 1101, False, 0)
    assert nodo_1044.id == "articulo:cc_tlax:1044"
    assert nodo_1044.sufijo is None
    assert nodo_1044.texto_general.startswith("Terminado el usufructo")


def test_integracion_corpus_real_fase2():
    """Prueba de integración con los 6 archivos JSON reales de knowledge_structured."""
    constructor = ConstructorGrafoLexis()
    grafo = constructor.cargar_y_construir_estructura_base()
    stats = constructor.obtener_estadisticas_fase2()

    g_stats = stats["global"]
    assert g_stats["nodos_ley"] == 6
    assert g_stats["nodos_articulo_totales"] == 7221
    assert g_stats["aristas_contiene"] == 7221
    assert g_stats["ids_unicos_verificados"] is True
    assert g_stats["transitorios_excluidos_por_defecto"] == 42  # 8 + 3 + 0 + 13 + 14 + 4
    assert g_stats["articulos_texto_general_vacio"] == 18       # 2 en CC-TLAX + 16 en LFT

    # Verificar IDs específicos requeridos por el criterio de aceptación
    assert "articulo:lft:153-A" in grafo
    assert "articulo:lft:153-F-BIS" in grafo
    assert "articulo:lft:153-C" in grafo
    assert "articulo:cc_tlax:135-A" in grafo
    assert "articulo:cc_tlax:640-QUATER-A" in grafo
    assert "articulo:cp_tlax:229-BIS" in grafo
    assert "articulo:cc_tlax:1044" in grafo
    assert "articulo:cpc_tlax:540" in grafo
    assert "articulo:cpp_tlax:113" in grafo


class TestCargadorFase2(unittest.TestCase):
    def test_153_a_y_f_bis(self):
        test_normalizacion_153_a_y_f_bis()

    def test_135_a_y_640_quater_a(self):
        test_normalizacion_135_a_y_640_quater_a()

    def test_229_bis_y_falso_ter(self):
        test_normalizacion_229_bis_y_falso_ter()

    def test_corpus_real_fase2(self):
        test_integracion_corpus_real_fase2()


if __name__ == "__main__":
    unittest.main(verbosity=2)

