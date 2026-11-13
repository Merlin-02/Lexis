#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitarios e integrales para el sistema de búsqueda y análisis legal LEXIS.
Compatible con unittest y pytest.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))


class TestAnalizadorLegal(unittest.TestCase):
    """Tests para el módulo de análisis legal."""

    def test_normalizar_texto(self):
        """Test de normalización de texto."""
        from analizador_legal import normalizar_texto

        assert normalizar_texto("HOLA MUNDO") == "hola mundo"
        assert normalizar_texto("café") == "cafe"
        assert normalizar_texto("niño") == "nino"
        assert normalizar_texto("¡Hola!") == "hola"

    def test_detectar_area_laboral(self):
        """Test de detección de área laboral."""
        from analizador_legal import detectar_area_legal

        assert detectar_area_legal("me despidieron del trabajo") == "laboral"
        assert detectar_area_legal("no me quieren pagar mi salario") == "laboral"
        assert detectar_area_legal("me discriminaron en mi empleo") == "laboral"

    def test_detectar_area_penal(self):
        """Test de detección de área penal."""
        from analizador_legal import detectar_area_legal

        assert detectar_area_legal("me robaron mi coche") == "penal"
        assert detectar_area_legal("me amenazó con un cuchillo") == "penal"
        assert detectar_area_legal("denunciar un delito") == "penal"

    def test_detectar_area_civil(self):
        """Test de detección de área civil."""
        from analizador_legal import detectar_area_legal

        assert detectar_area_legal("tengo una deuda que pagar") == "civil"
        assert detectar_area_legal("quiero divorciarme") == "civil"
        assert detectar_area_legal("problema con mi casa") == "civil"

    def test_detectar_normativa(self):
        """Test de detección de normativa."""
        from analizador_legal import detectar_normativa

        documentos = [
            "Ley Trabajo",
            "Código Penal Tlaxcala",
            "Codigo Civil Tlaxcala",
            "Constitucion",
        ]

        doc, _ = detectar_normativa("me despidieron", documentos)
        assert doc == "Ley Trabajo"

        doc, _ = detectar_normativa("me robaron", documentos)
        assert doc == "Código Penal Tlaxcala"

        doc, _ = detectar_normativa("tengo una deuda", documentos)
        assert doc == "Codigo Civil Tlaxcala"

    def test_analizar_coherencia_y_correccion_consulta(self):
        """Test de análisis de coherencia y expansión/corrección de consulta."""
        from analizador_legal import analizar_coherencia_consulta, generar_consulta_corregida

        es_coherente, _ = analizar_coherencia_consulta("ayuda")
        assert es_coherente is False

        es_coherente, _ = analizar_coherencia_consulta("me despidieron del trabajo")
        assert es_coherente is True

        corregida = generar_consulta_corregida("hola disculpe art. 47 de la lft")
        assert "artículo 47" in corregida.lower()
        assert "ley federal del trabajo" in corregida.lower()
        assert "hola" not in corregida.lower()


class TestMejoras(unittest.TestCase):
    """Tests para el módulo de mejoras usando directorios temporales aislados."""

    def test_expandir_consulta(self):
        """Test de expansión de consulta con sinónimos."""
        from mejoras import expandir_consulta

        resultado = expandir_consulta("me despidieron")
        assert "despido" in resultado

    def test_analizar_tipo_consulta_lexica(self):
        """Test de análisis de tipo de consulta léxica."""
        from mejoras import analizar_tipo_consulta

        info = analizar_tipo_consulta("artículo 47 de la ley del trabajo")
        assert info["tipo"] == "lexico"

    def test_analizar_tipo_consulta_semantica(self):
        """Test de análisis de tipo de consulta semántica."""
        from mejoras import analizar_tipo_consulta

        info = analizar_tipo_consulta("qué puedo hacer si me despiden")
        assert info["tipo"] in ["semantico", "hibrido"]

    def test_normalizar_termino(self):
        """Test de normalización de términos."""
        from mejoras import normalizar_termino

        assert normalizar_termino("despedido") == "despido"
        assert normalizar_termino("robaron") == "robo"
        assert normalizar_termino("salario") == "salario"

    def test_historial_busquedas(self):
        """Test del historial de búsquedas en directorio temporal aislado."""
        from mejoras import HistorialBusquedas

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mejoras.CARPETA_CACHE", Path(tmpdir)):
                historial = HistorialBusquedas(maximo=3)
                historial.agregar("consulta 1", "doc1", [{"id": 1}])
                historial.agregar("consulta 2", "doc2", [{"id": 2}])
                historial.agregar("consulta 3", "doc3", [{"id": 3}])
                historial.agregar("consulta 4", "doc4", [{"id": 4}])

                recientes = historial.obtener_recientes(2)
                assert "consulta 4" in recientes
                assert "consulta 3" in recientes
                assert "consulta 1" not in recientes

    def test_sugerencias_historial(self):
        """Test de sugerencias basadas en historial en directorio temporal aislado."""
        from mejoras import HistorialBusquedas

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mejoras.CARPETA_CACHE", Path(tmpdir)):
                historial = HistorialBusedas = HistorialBusquedas(maximo=10)
                historial.agregar("despido injustificado", "Ley Trabajo", [])
                historial.agregar("me robaron", "Código Penal", [])
                historial.agregar("problema de deuda", "Código Civil", [])

                sugerencias = historial.obtener_sugerencias("despido")
                assert len(sugerencias) > 0
                assert "despido" in sugerencias[0].lower()


class TestGestorErrores(unittest.TestCase):
    """Tests para el gestor de errores en directorio temporal aislado."""

    def test_registrar_error(self):
        """Test de registro de errores."""
        from mejoras import GestorErrores

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mejoras.CARPETA_LOGS", Path(tmpdir)):
                gestor = GestorErrores()
                gestor.registrar_error("test", "Error de prueba", {"contexto": "test"})

                assert len(gestor.errores) == 1
                assert gestor.errores[0]["tipo"] == "test"
                assert gestor.errores[0]["mensaje"] == "Error de prueba"

    def test_estadisticas_errores(self):
        """Test de estadísticas de errores."""
        from mejoras import GestorErrores

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("mejoras.CARPETA_LOGS", Path(tmpdir)):
                gestor = GestorErrores()
                gestor.registrar_error("tipo1", "Error 1", {})
                gestor.registrar_error("tipo1", "Error 2", {})
                gestor.registrar_error("tipo2", "Error 3", {})

                stats = gestor.obtener_estadisticas_errores()
                assert stats["tipo1"] == 2
                assert stats["tipo2"] == 1


class TestBuscador(unittest.TestCase):
    """Tests para el módulo real de búsqueda."""

    def test_preprocesar_texto(self):
        """Verifica que la función real preprocesar_texto de buscador.py elimine puntuación y stopwords."""
        from buscador import preprocesar_texto

        assert preprocesar_texto("Hola Mundo!") == ["hola", "mundo"]
        assert preprocesar_texto("El Artículo 47 de la Ley.") == ["artículo", "47", "ley"]


class TestIndiceTematico(unittest.TestCase):
    """Verifica que el 100% de las entradas de INDICE_TEMATICO existan en grafo_lexis.json."""

    def test_todos_los_articulos_existen_en_grafo(self):
        from indice_tematico import INDICE_TEMATICO
        from grafo_lexis.recuperador_grafo import RecuperadorGrafoLexis

        rec = RecuperadorGrafoLexis()
        for clave, datos in INDICE_TEMATICO.items():
            doc = datos["documento"]
            for art in datos["articulos"]:
                art_id = art.get("articulo_id")
                assert art_id, f"Falta articulo_id en {clave}: {art}"
                assert rec.grafo.has_node(art_id), f"El nodo {art_id} ({clave}) no existe en grafo_lexis.json"
                hit = {
                    "documento": doc,
                    "articulo": art["articulo"],
                    "articulo_id": art_id,
                    "texto": "",
                }
                assert rec.mapear_hit_a_nodo_articulo(hit) == art_id


class TestSinonimos(unittest.TestCase):
    """Tests para el sistema de sinónimos."""

    def test_diccionario_sinonimos_completo(self):
        """Test de que el diccionario de sinónimos está completo."""
        from mejoras import DICCIONARIO_SINONIMOS

        assert "despido" in DICCIONARIO_SINONIMOS
        assert "robo" in DICCIONARIO_SINONIMOS
        assert "demanda" in DICCIONARIO_SINONIMOS
        assert "despedido" in DICCIONARIO_SINONIMOS["despido"]
        assert "robado" in DICCIONARIO_SINONIMOS["robo"]


class TestIntegracion(unittest.TestCase):
    """Tests de integración del sistema."""

    def test_flujo_completo_deteccion(self):
        """Test del flujo completo de detección."""
        from analizador_legal import detectar_normativa, analizar_coherencia_consulta

        documentos = ["Ley Trabajo", "Código Penal Tlaxcala", "Codigo Civil Tlaxcala"]

        consulta = "me despidieron del trabajo"
        es_coherente, _ = analizar_coherencia_consulta(consulta)
        assert es_coherente is True

        doc, info = detectar_normativa(consulta, documentos)
        assert doc == "Ley Trabajo"
        assert info["area"] == "laboral"

    def test_flujo_consulta_ambigua(self):
        """Test con consulta ambigua."""
        from analizador_legal import detectar_normativa

        documentos = ["Ley Trabajo", "Código Penal Tlaxcala", "Codigo Civil Tlaxcala"]
        detectar_normativa("tengo un problema", documentos)


if __name__ == "__main__":
    unittest.main(verbosity=2)
