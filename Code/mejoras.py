# mejoras.py
# Modulo de mejoras para el sistema de busqueda

import os
import json
import pickle
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

CARPETA_DB = Path(__file__).parent.parent / "lexis_vectordb"
CARPETA_LOGS = CARPETA_DB / "logs"
CARPETA_CACHE = CARPETA_DB / "cache"

CARPETA_LOGS.mkdir(exist_ok=True)
CARPETA_CACHE.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ==========================================
# NORMALIZACIÓN DE TEXTO (Sinónimos/Stemming)
# ==========================================

DICCIONARIO_SINONIMOS = {
    'despido': ['despido', 'despedido', 'despedida', 'despedir', 'despedirme', 'despidieron', 'despidido'],
    'despido_injustificado': ['despido injustificado', 'despido injusta', 'despedir sin causa', 'despedir sin motivo'],
    'renuncia': ['renuncia', 'renunciar', 'renuncie', 'renunciado'],
    'salario': ['salario', 'sueldo', 'pago', 'remuneración', 'nomina', 'nómina'],
    'indemnización': ['indemnización', 'indemnizacion', 'liquidación', 'liquidacion', 'finiquito'],
    'contrato': ['contrato', 'contratación', 'contratacion', 'convenio', 'acuerdo'],
    'trabajador': ['trabajador', 'trabajadora', 'empleado', 'empleada', 'laborador'],
    'patrón': ['patrón', 'patron', 'empleador', 'empresa', 'jefe', 'gerente'],
    'robo': ['robo', 'robado', 'robaron', 'hurto', 'asalto', 'asaltado', 'asaltar'],
    'delito': ['delito', 'crimen', 'falta', 'infracción', 'infraccion'],
    'amenaza': ['amenaza', 'amenazar', 'amenazo', 'amenazado', 'amenazas'],
    'violencia': ['violencia', 'violento', 'agresión', 'agresion', 'golpe', 'golpes', 'pegar', 'agredir'],
    'demanda': ['demanda', 'demandar', 'demando', 'reclamación', 'reclamacion', 'reclamar'],
    'deuda': ['deuda', 'deudas', 'adeudo', 'adeudar', 'cobrar', 'cobranza'],
    'divorcio': ['divorcio', 'divorciarme', 'divorciar', 'separación', 'separacion'],
    'embargo': ['embargo', 'embargar', 'secuestro', 'incautación', 'incautacion'],
    'herencia': ['herencia', 'heredar', 'heredero', 'testamento', 'legado'],
    'propiedad': ['propiedad', 'posesión', 'posesion', 'bienes', 'inmueble', 'casa', 'vivienda'],
    'arrendamiento': ['arrendamiento', 'arrendar', 'renta', 'inquilino', 'arrendador', 'deposito', 'depósito'],
}

SINONIMOS_NORMALIZADOS = {}
for forma_canonica, variantes in DICCIONARIO_SINONIMOS.items():
    for variante in variantes:
        SINONIMOS_NORMALIZADOS[variante.lower()] = forma_canonica

def normalizar_termino(texto: str) -> str:
    """Normaliza un término a su forma canónica usando sinónimos."""
    texto_lower = texto.lower().strip()
    return SINONIMOS_NORMALIZADOS.get(texto_lower, texto_lower)

def expandir_consulta(consulta: str) -> str:
    """Expande la consulta con formas canónicas de sinónimos."""
    palabras = consulta.lower().split()
    palabras_expandidas = []
    
    for palabra in palabras:
        # Agregar la palabra original
        palabras_expandidas.append(palabra)
        # Agregar la forma canónica si existe
        canonica = normalizar_termino(palabra)
        if canonica != palabra:
            palabras_expandidas.append(canonica)
    
    return ' '.join(palabras_expandidas)

# ==========================================
# PERSISTENCIA DE ÍNDICE BM25
# ==========================================

def guardar_indice_bm25(motor_bm25, corpus_tokenizado: List[List[str]], ruta: Path) -> bool:
    """Guarda el índice BM25 en disco."""
    try:
        datos = {
            'motor': motor_bm25,
            'corpus': corpus_tokenizado,
            'fecha': datetime.now().isoformat()
        }
        with open(ruta, 'wb') as f:
            pickle.dump(datos, f)
        log.info(f"Índice BM25 guardado en {ruta}")
        return True
    except Exception as e:
        log.error(f"Error al guardar índice BM25: {e}")
        return False

def cargar_indice_bm25(ruta: Path) -> Optional[dict]:
    """Carga el índice BM25 desde disco si existe y está actualizado."""
    if not ruta.exists():
        return None
    
    try:
        with open(ruta, 'rb') as f:
            datos = pickle.load(f)
        
        fecha_guardado = datetime.fromisoformat(datos['fecha'])
        edad = (datetime.now() - fecha_guardado).total_seconds()
        
        # Considerar válido por 24 horas
        if edad < 86400:
            log.info(f"Índice BM25 cargado desde caché (edad: {edad/3600:.1f}h)")
            return datos
        else:
            log.info(f"Índice BM25 obsoleto ({edad/3600:.1f}h), recreando...")
            return None
    except Exception as e:
        log.warning(f"Error al cargar índice BM25: {e}")
        return None

# ==========================================
# CACHEO DE EMBEDDINGS
# ==========================================

def obtener_embedding_cacheado(consulta: str, modelo, ruta_cache: Path) -> Optional[List[float]]:
    """Obtiene un embedding desde caché si existe."""
    hash_consulta = hashlib.md5(consulta.encode()).hexdigest()
    archivo_cache = ruta_cache / f"emb_{hash_consulta}.json"
    
    if archivo_cache.exists():
        try:
            with open(archivo_cache, 'r') as f:
                datos = json.load(f)
            return datos['embedding']
        except:
            pass
    return None

def guardar_embedding_cacheado(consulta: str, embedding: List[float], ruta_cache: Path) -> bool:
    """Guarda un embedding en caché."""
    try:
        hash_consulta = hashlib.md5(consulta.encode()).hexdigest()
        archivo_cache = ruta_cache / f"emb_{hash_consulta}.json"
        
        with open(archivo_cache, 'w') as f:
            json.dump({
                'consulta': consulta,
                'embedding': embedding,
                'fecha': datetime.now().isoformat()
            }, f)
        return True
    except Exception as e:
        log.warning(f"Error al guardar embedding en caché: {e}")
        return False

# ==========================================
# LOGGING DE BÚSQUEDAS
# ==========================================

def guardar_log_busqueda(
    consulta: str,
    filtro_documento: Optional[str],
    filtro_jerarquia: Optional[str],
    num_resultados: int,
    tiempo_respuesta: float,
    errores: Optional[str] = None
) -> None:
    """Guarda un registro de cada búsqueda para análisis."""
    try:
        archivo_log = CARPETA_LOGS / f"busquedas_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        registro = {
            'timestamp': datetime.now().isoformat(),
            'consulta': consulta,
            'filtro_documento': filtro_documento,
            'filtro_jerarquia': filtro_jerarquia,
            'num_resultados': num_resultados,
            'tiempo_respuesta': tiempo_respuesta,
            'errores': errores
        }
        
        with open(archivo_log, 'a') as f:
            f.write(json.dumps(registro, ensure_ascii=False) + '\n')
    except Exception as e:
        log.warning(f"Error al guardar log de búsqueda: {e}")

def obtener_estadisticas_busquedas(dias: int = 7) -> Dict[str, Any]:
    """Obtiene estadísticas de búsquedas de los últimos N días."""
    stats = {
        'total_busquedas': 0,
        'consultas_unicas': set(),
        'filtros_mas_usados': {},
        'promedio_resultados': 0,
        'promedio_tiempo': 0,
    }
    
    tiempos = []
    resultados = []
    
    for i in range(dias):
        fecha = datetime.now() - timedelta(days=i)
        archivo_log = CARPETA_LOGS / f"busquedas_{fecha.strftime('%Y%m%d')}.jsonl"
        
        if archivo_log.exists():
            with open(archivo_log, 'r') as f:
                for linea in f:
                    try:
                        reg = json.loads(linea)
                        stats['total_busquedas'] += 1
                        stats['consultas_unicas'].add(reg['consulta'])
                        
                        filtro = reg.get('filtro_documento', 'ninguno')
                        stats['filtros_mas_usados'][filtro] = stats['filtros_mas_usados'].get(filtro, 0) + 1
                        
                        tiempos.append(reg.get('tiempo_respuesta', 0))
                        resultados.append(reg.get('num_resultados', 0))
                    except:
                        pass
    
    stats['consultas_unicas'] = len(stats['consultas_unicas'])
    stats['promedio_tiempo'] = sum(tiempos) / len(tiempos) if tiempos else 0
    stats['promedio_resultados'] = sum(resultados) / len(resultados) if resultados else 0
    
    return stats

# ==========================================
# DETECCIÓN DINÁMICA DE PESOS
# ==========================================

def analizar_tipo_consulta(consulta: str) -> Dict[str, Any]:
    """Analiza el tipo de consulta para determinar los pesos óptimos."""
    consulta_lower = consulta.lower()
    palabras = set(consulta_lower.split())
    
    # Términos jurídicos exactos -> favorecer BM25
    terminos_exactos = {
        'artículo', 'articulo', 'fraccion', 'fracción', 'inciso', 'ley',
        'código', 'codigo', 'título', 'titulo', 'capítulo', 'capitulo',
        'constitución', 'constitucion', 'fraccion', 'numeral'
    }
    
    # Términos conceptuales/vagos -> favorecer semántico
    terminos_conceptuales = {
        'qué', 'que', 'cómo', 'como', 'puedo', 'tengo', 'necesito',
        'ayuda', 'problema', 'situación', 'situacion', 'derecho',
        'puedo', 'debo', 'obligo', 'debería', 'deberia'
    }
    
    tiene_exactos = bool(palabras.intersection(terminos_exactos))
    tiene_conceptuales = bool(palabras.intersection(terminos_conceptuales))
    
    if tiene_exactos and not tiene_conceptuales:
        return {'tipo': 'lexico', 'peso_semantico': 0.1, 'peso_lexico': 0.9}
    elif tiene_conceptuales and not tiene_exactos:
        return {'tipo': 'semantico', 'peso_semantico': 0.7, 'peso_lexico': 0.3}
    else:
        return {'tipo': 'hibrido', 'peso_semantico': 0.4, 'peso_lexico': 0.6}

# ==========================================
# HISTORIAL DE BÚSQUEDAS
# ==========================================

class HistorialBusquedas:
    """Gestiona el historial de búsquedas del usuario."""
    
    def __init__(self, maximo: int = 50):
        self.maximo = maximo
        self.historial: List[Dict] = []
        self.cargar()
    
    def agregar(self, consulta: str, filtro: Optional[str], resultados: List[Dict]) -> None:
        """Agrega una búsqueda al historial."""
        self.historial.insert(0, {
            'consulta': consulta,
            'filtro': filtro,
            'num_resultados': len(resultados),
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.historial) > self.maximo:
            self.historial = self.historial[:self.maximo]
        
        self.guardar()
    
    def obtener_recientes(self, n: int = 5) -> List[str]:
        """Obtiene las N consultas más recientes."""
        return [h['consulta'] for h in self.historial[:n]]
    
    def obtener_sugerencias(self, texto: str, n: int = 3) -> List[str]:
        """Obtiene sugerencias basadas en el texto."""
        if not texto:
            return self.obtener_recientes(n)
        
        texto_lower = texto.lower()
        coincidencias = [
            h['consulta'] for h in self.historial 
            if texto_lower in h['consulta'].lower()
        ]
        return coincidencias[:n]
    
    def guardar(self) -> None:
        """Guarda el historial en disco."""
        try:
            ruta = CARPETA_CACHE / "historial.json"
            with open(ruta, 'w') as f:
                json.dump(self.historial, f, ensure_ascii=False)
        except Exception as e:
            log.warning(f"Error al guardar historial: {e}")
    
    def cargar(self) -> None:
        """Carga el historial desde disco."""
        try:
            ruta = CARPETA_CACHE / "historial.json"
            if ruta.exists():
                with open(ruta, 'r') as f:
                    self.historial = json.load(f)
        except Exception as e:
            log.warning(f"Error al cargar historial: {e}")
            self.historial = []

# ==========================================
# RE-RANKEO DE RESULTADOS
# ==========================================

def rerankear_resultados(
    resultados: List[Dict],
    consulta: str,
    modelo,
    top_n: int = 5,
    peso_rrf: float = 0.3,
    peso_semantico: float = 0.7
) -> List[Dict]:
    """
    Re-rankea los resultados combinando puntuación RRF con similitud semántica.
    
    Args:
        resultados: Lista de resultados con 'texto' y 'puntuacion_rrf'
        consulta: Consulta original del usuario
        modelo: Modelo de embeddings
        top_n: Número de resultados a devolver
        peso_rrf: Peso de la puntuación RRF original (0-1)
        peso_semantico: Peso de la similitud semántica (0-1)
    
    Returns:
        Lista de resultados re-renequeados
    """
    if not resultados:
        return resultados
    
    if len(resultados) <= 1:
        return resultados[:top_n]
    
    try:
        from numpy import dot, array, linalg
        
        # Normalizar pesos
        total_peso = peso_rrf + peso_semantico
        peso_rrf_norm = peso_rrf / total_peso
        peso_semantico_norm = peso_semantico / total_peso
        
        # Obtener embedding de la consulta (una sola vez)
        emb_consulta = modelo.encode([consulta], convert_to_numpy=True)[0]
        
        # Obtener embeddings de los documentos (en batch - más eficiente)
        textos = [r['texto'] for r in resultados]
        emb_docs = modelo.encode(textos, convert_to_numpy=True)
        
        # Calcular similitud coseno para cada documento
        normas_consulta = linalg.norm(emb_consulta)
        
        for i, resultado in enumerate(resultados):
            emb_doc = emb_docs[i]
            norma_doc = linalg.norm(emb_doc)
            
            # Similitud coseno
            if normas_consulta > 0 and norma_doc > 0:
                cos_sim = dot(emb_consulta, emb_doc) / (normas_consulta * norma_doc)
            else:
                cos_sim = 0
            
            # Normalizar puntuación RRF (simple max normalization)
            puntuacion_rrf = resultado.get('puntuacion_rrf', 0)
            
            # Combinar puntuaciones
            resultado['puntuacion_rerankeada'] = (
                puntuacion_rrf * peso_rrf_norm +
                cos_sim * peso_semantico_norm
            )
            resultado['similitud_coseno'] = cos_sim
        
        # Ordenar por puntuación re-rankeada
        resultados.sort(key=lambda x: x.get('puntuacion_rerankeada', 0), reverse=True)
        
        log.debug(f"Re-rankeo aplicado: {len(resultados)} resultados")
        
        return resultados[:top_n]
    
    except Exception as e:
        log.warning(f"Error en re-rankeo, devolviendo resultados originales: {e}")
        return resultados[:top_n]


def rerankear_por_palabras_clave(
    resultados: List[Dict],
    consulta: str,
    peso: float = 0.2
) -> List[Dict]:
    """
    Re-rankea resultados favoreciendo aquellos que contienen palabras clave de la consulta.
    Es útil como complemento al re-rankeo semántico.
    """
    if not resultados:
        return resultados
    
    # Extraer palabras significativas de la consulta
    consulta_norm = consulta.lower()
    palabras_consulta = set(
        p for p in consulta_norm.split() 
        if len(p) > 3 and p not in {'que', 'como', 'tengo', 'puedo', 'debo', 'necesito'}
    )
    
    for resultado in resultados:
        texto_norm = resultado.get('texto', '').lower()
        palabras_texto = set(texto_norm.split())
        
        # Contar coincidencias
        coincidencias = len(palabras_consulta.intersection(palabras_texto))
        
        # Calcular puntuación de palabras clave (normalizada)
        if palabras_consulta:
            puntuacion_palabras = coincidencias / len(palabras_consulta)
        else:
            puntuacion_palabras = 0
        
        # Combinar con puntuación existente
        puntuacion_original = resultado.get('puntuacion_rerankeada', resultado.get('puntuacion_rrf', 0))
        resultado['puntuacion_final'] = (
            puntuacion_original * (1 - peso) +
            puntuacion_palabras * peso
        )
    
    # Ordenar por puntuación final
    resultados.sort(key=lambda x: x.get('puntuacion_final', 0), reverse=True)
    
    return resultados


# ==========================================
# MEJORA DEL DETECTOR DE ÁREAS
# ==========================================

def analizar_contexto(consulta: str) -> Dict[str, Any]:
    """Analiza el contexto de la consulta para mejorar la detección."""
    consulta_lower = consulta.lower()
    palabras = set(consulta_lower.split())
    
    # Palabras que indican urgencia/emergencia
    palabras_urgencia = {'ahora', 'ya', 'urgente', 'emergencia', 'inmediato', 'pronto'}
    
    # Palabras que indican acción legal
    palabras_accion = {'denunciar', 'demandar', 'querella', 'procesar', 'judicial'}
    
    # Palabras que indican pregunta
    palabras_pregunta = {'como', 'qué', 'puedo', 'debo', 'puede', 'tengo', 'necesito'}
    
    return {
        'es_urgente': bool(palabras.intersection(palabras_urgencia)),
        'es_accion_legal': bool(palabras.intersection(palabras_accion)),
        'es_pregunta': bool(palabras.intersection(palabras_pregunta)),
        'longitud': len(palabras)
    }

# ==========================================
# MANEJO DE ERRORES MEJORADO
# ==========================================

class GestorErrores:
    """Gestiona errores y excepciones del sistema."""
    
    def __init__(self):
        self.errores: List[Dict] = []
    
    def registrar_error(
        self,
        tipo: str,
        mensaje: str,
        contexto: Optional[Dict] = None
    ) -> None:
        """Registra un error para análisis."""
        error = {
            'timestamp': datetime.now().isoformat(),
            'tipo': tipo,
            'mensaje': mensaje,
            'contexto': contexto or {}
        }
        self.errores.append(error)
        
        # También guardar en archivo
        try:
            archivo_errores = CARPETA_LOGS / "errores.jsonl"
            with open(archivo_errores, 'a') as f:
                f.write(json.dumps(error, ensure_ascii=False) + '\n')
        except:
            pass
    
    def obtener_errores_recientes(self, n: int = 10) -> List[Dict]:
        """Obtiene los N errores más recientes."""
        return self.errores[-n:]
    
    def obtener_estadisticas_errores(self) -> Dict[str, int]:
        """Obtiene estadísticas de errores por tipo."""
        stats = {}
        for error in self.errores:
            tipo = error['tipo']
            stats[tipo] = stats.get(tipo, 0) + 1
        return stats

# Instancia global del gestor de errores
gestor_errores = GestorErrores()

from datetime import timedelta
