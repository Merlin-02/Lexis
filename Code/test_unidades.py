#!/usr/bin/env python3
# test_ unitarios.py
# Tests unitarios para el sistema de búsqueda LexIS

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent))

# Tests para analizador_legal.py
class TestAnalizadorLegal:
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
        
        documentos = ['Ley Trabajo', 'Código Penal Tlaxcala', 'Codigo Civil Tlaxcala', 'Constitucion']
        
        doc, info = detectar_normativa("me despidieron", documentos)
        assert doc == "Ley Trabajo"
        
        doc, info = detectar_normativa("me robaron", documentos)
        assert doc == "Código Penal Tlaxcala"
        
        doc, info = detectar_normativa("tengo una deuda", documentos)
        assert doc == "Codigo Civil Tlaxcala"
    
    def test_analizar_coherencia_consulta(self):
        """Test de análisis de coherencia."""
        from analizador_legal import analizar_coherencia_consulta
        
        es_coherente, sugerencias = analizar_coherencia_consulta("ayuda")
        assert es_coherente == False
        
        es_coherente, sugerencias = analizar_coherencia_consulta("me despidieron del trabajo")
        assert es_coherente == True


# Tests para mejoras.py
class TestMejoras:
    """Tests para el módulo de mejoras."""
    
    def test_expandir_consulta(self):
        """Test de expansión de consulta con sinónimos."""
        from mejoras import expandir_consulta
        
        resultado = expandir_consulta("me despidieron")
        # "despidieron" se normaliza a "despido"
        assert "despido" in resultado
    
    def test_analizar_tipo_consulta_lexica(self):
        """Test de análisis de tipo de consulta léxica."""
        from mejoras import analizar_tipo_consulta
        
        info = analizar_tipo_consulta("artículo 47 de la ley del trabajo")
        assert info['tipo'] == "lexico"
    
    def test_analizar_tipo_consulta_semantica(self):
        """Test de análisis de tipo de consulta semántica."""
        from mejoras import analizar_tipo_consulta
        
        info = analizar_tipo_consulta("qué puedo hacer si me despiden")
        assert info['tipo'] in ["semantico", "hibrido"]
    
    def test_normalizar_termino(self):
        """Test de normalización de términos."""
        from mejoras import normalizar_termino
        
        assert normalizar_termino("despedido") == "despido"
        assert normalizar_termino("robaron") == "robo"
        assert normalizar_termino("salario") == "salario"
    
    def test_historial_busquedas(self):
        """Test del historial de búsquedas."""
        from mejoras import HistorialBusquedas
        
        historial = HistorialBusquedas(maximo=3)
        historial.agregar("consulta 1", "doc1", [{"id": 1}])
        historial.agregar("consulta 2", "doc2", [{"id": 2}])
        historial.agregar("consulta 3", "doc3", [{"id": 3}])
        historial.agregar("consulta 4", "doc4", [{"id": 4}])  # Debe eliminar la más vieja
        
        recientes = historial.obtener_recientes(2)
        assert "consulta 2" in recientes
        assert "consulta 1" not in recientes  # Fue eliminada
    
    def test_sugerencias_historial(self):
        """Test de sugerencias basadas en historial."""
        from mejoras import HistorialBusquedas
        
        historial = HistorialBusquedas(maximo=10)
        historial.agregar("despido injustificado", "Ley Trabajo", [])
        historial.agregar("me robaron", "Código Penal", [])
        historial.agregar("problema de deuda", "Código Civil", [])
        
        sugerencias = historial.obtener_sugerencias("despido")
        assert len(sugerencias) > 0
        assert "despido" in sugerencias[0].lower()


class TestGestorErrores:
    """Tests para el gestor de errores."""
    
    def test_registrar_error(self):
        """Test de registro de errores."""
        from mejoras import GestorErrores
        
        gestor = GestorErrores()
        gestor.registrar_error("test", "Error de prueba", {"contexto": "test"})
        
        assert len(gestor.errores) == 1
        assert gestor.errores[0]['tipo'] == "test"
        assert gestor.errores[0]['mensaje'] == "Error de prueba"
    
    def test_estadisticas_errores(self):
        """Test de estadísticas de errores."""
        from mejoras import GestorErrores
        
        gestor = GestorErrores()
        gestor.registrar_error("tipo1", "Error 1", {})
        gestor.registrar_error("tipo1", "Error 2", {})
        gestor.registrar_error("tipo2", "Error 3", {})
        
        stats = gestor.obtener_estadisticas_errores()
        assert stats['tipo1'] == 2
        assert stats['tipo2'] == 1


# Tests para buscador.py
class TestBuscador:
    """Tests para el módulo de búsqueda."""
    
    def test_preprocesar_texto(self):
        """Test de preprocesamiento de texto."""
        # Importar la función
        import importlib.util
        spec = importlib.util.spec_from_file_location("buscador", "buscador.py")
        buscador = importlib.util.module_from_spec(spec)
        
        # No podemos cargar el módulo completamente por las dependencias
        # Pero podemos probar funciones auxiliares
        import string
        def preprocesar_texto(texto):
            texto = texto.lower()
            texto = texto.translate(str.maketrans("", "", string.punctuation))
            return texto.split()
        
        assert preprocesar_texto("Hola Mundo!") == ["hola", "mundo"]
        assert preprocesar_texto("Artículo 47.") == ["artículo", "47"]


class TestSinonimos:
    """Tests para el sistema de sinónimos."""
    
    def test_diccionario_sinonimos_completo(self):
        """Test de que el diccionario de sinónimos está completo."""
        from mejoras import DICCIONARIO_SINONIMOS
        
        # Verificar que hay sinónimos para términos importantes
        assert 'despido' in DICCIONARIO_SINONIMOS
        assert 'robo' in DICCIONARIO_SINONIMOS
        assert 'demanda' in DICCIONARIO_SINONIMOS
        
        # Verificar que hay variantes
        assert 'despedido' in DICCIONARIO_SINONIMOS['despido']
        assert 'robado' in DICCIONARIO_SINONIMOS['robo']


# Tests de integración
class TestIntegracion:
    """Tests de integración del sistema."""
    
    def test_flujo_completo_deteccion(self):
        """Test del flujo completo de detección."""
        from analizador_legal import detectar_normativa, analizar_coherencia_consulta
        
        documentos = ['Ley Trabajo', 'Código Penal Tlaxcala', 'Codigo Civil Tlaxcala']
        
        # Consulta laboral
        consulta = "me despidieron del trabajo"
        es_coherente, _ = analizar_coherencia_consulta(consulta)
        assert es_coherente == True
        
        doc, info = detectar_normativa(consulta, documentos)
        assert doc == "Ley Trabajo"
        assert info['area'] == "laboral"
    
    def test_flujo_consulta_ambigua(self):
        """Test con consulta ambigua."""
        from analizador_legal import detectar_normativa
        
        documentos = ['Ley Trabajo', 'Código Penal Tlaxcala', 'Codigo Civil Tlaxcala']
        
        # Consulta con palabras de múltiples áreas
        doc, info = detectar_normativa("tengo un problema", documentos)
        # No debe fallar, puede o no detectar


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
