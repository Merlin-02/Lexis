#buscador.py
import json
import os
import string
import warnings
import time
from rank_bm25 import BM25Okapi
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    from analizador_legal import detectar_normativa
    ANALIZADOR_DISPONIBLE = True
except ImportError:
    ANALIZADOR_DISPONIBLE = False

try:
    from mejoras import (
        cargar_indice_bm25,
        guardar_indice_bm25,
        expandir_consulta,
        analizar_tipo_consulta,
        guardar_log_busqueda,
        GestorErrores,
        rerankear_resultados,
    )
    MEJORAS_DISPONIBLES = True
    gestor_errores = GestorErrores()
except ImportError:
    MEJORAS_DISPONIBLES = False
    gestor_errores = None

# =============================================================
# CONFIGURACION GLOBAL
# =============================================================
CARPETA_DB     = "../lexis_vectordb"
MODELO_NOMBRE  = "paraphrase-multilingual-mpnet-base-v2"
TOP_K_DEFAULT  = 30
HABILITAR_RERANKEO = True
K_RRF          = 60

# Peso relativo de cada motor (deben sumar 1.0)
# Sube PESO_SEMANTICO si las consultas son conceptuales/vagas
# Sube PESO_LEXICO    si las consultas usan terminos juridicos exactos
PESO_SEMANTICO = 0.05
PESO_LEXICO    = 0.95


# =============================================================
# PREPROCESAMIENTO
# =============================================================
STOPWORDS_ES = {
    "de", "la", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "no", "una", "su", "al", "lo", "como", "cómo", "mas", "más",
    "pero", "sus", "le", "ya", "o", "este", "si", "sí", "porque", "esta", "está",
    "entre", "cuando", "cuándo", "muy", "sin", "sobre", "ser", "tiene", "también",
    "me", "hasta", "hay", "donde", "dónde", "quien", "quién", "desde", "todo",
    "nos", "durante", "todos", "uno", "les", "ni", "contra", "otros", "ese",
    "eso", "ante", "ellos", "e", "esto", "mí", "mi", "antes", "algunos", "qué",
    "que", "unos", "yo", "otro", "otras", "otra", "él", "tanto", "esa", "estos",
    "cual", "cuál", "es", "son", "fue", "sea", "han", "ha",
}


def preprocesar_texto(texto: str) -> list[str]:
    """Minusculas + elimina puntuacion y stopwords vacías para el motor lexico (BM25)."""
    texto = texto.lower()
    puntuacion_ext = string.punctuation + "¿¡«»“”‘’—"
    texto = texto.translate(str.maketrans("", "", puntuacion_ext))
    tokens = [t for t in texto.split() if t not in STOPWORDS_ES and len(t) > 1]
    return tokens if tokens else texto.split()


# =============================================================
# MOTOR SEMÁNTICO LIGERO PARA DESPLIEGUE CLOUD (RAILWAY / SIN CHROMADB)
# =============================================================
MAPEO_LEY_ID_A_DOCUMENTO = {
    "ley:lft": "Ley Trabajo",
    "ley:cp_tlax": "Código Penal Tlaxcala",
    "ley:cc_tlax": "Codigo Civil Tlaxcala",
    "ley:cpc_tlax": "Procedimiento Civiles Tlaxcala",
    "ley:cpp_tlax": "Procedimiento Penal Tlaxcala",
    "ley:cpeum": "Constitucion",
}


class _VectorWrapper:
    """Empaqueta una matriz dispersa ofreciendo .tolist() e indexación compatible con ChromaDB y rerankeo."""

    def __init__(self, matriz):
        self.matriz = matriz

    def tolist(self):
        return self.matriz

    def __getitem__(self, idx):
        fila = self.matriz[idx]
        return fila.toarray().ravel() if hasattr(fila, "toarray") else fila

    def __len__(self):
        return self.matriz.shape[0]


class MotorSemanticoTFIDF:
    """
    Motor vectorial ligero basado en TF-IDF de n-gramas con escalado sublineal.
    Consume < 30 MB de RAM y arranca en ~1 segundo en contenedores Railway CPU.
    """

    def __init__(self, textos: list[str]):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizador = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=60000,
            lowercase=True,
            strip_accents="unicode",
            stop_words=list(STOPWORDS_ES),
        )
        self.matriz_docs = self.vectorizador.fit_transform(textos)

    def encode(self, consultas: list[str], **_kwargs) -> _VectorWrapper:
        vec = self.vectorizador.transform(consultas)
        return _VectorWrapper(vec)


class ColeccionLigeraTFIDF:
    """
    Emula la interfaz `coleccion.query(query_embeddings=..., n_results=...)` de ChromaDB
    utilizando similitud coseno directa sobre la matriz TF-IDF en memoria.
    """

    def __init__(self, ids_documentos: list[str], motor_tfidf: MotorSemanticoTFIDF):
        self.ids_documentos = ids_documentos
        self.motor_tfidf = motor_tfidf

    def query(self, query_embeddings, n_results: int = 30) -> dict:
        import numpy as np
        from sklearn.metrics.pairwise import linear_kernel

        q_vec = (
            query_embeddings.matriz
            if hasattr(query_embeddings, "matriz")
            else query_embeddings
        )
        similitudes = linear_kernel(q_vec, self.motor_tfidf.matriz_docs).ravel()
        k = min(n_results, len(self.ids_documentos))
        if k <= 0:
            return {"ids": [[]]}
        indices_top = np.argsort(similitudes)[::-1][:k]
        ids_ordenados = [self.ids_documentos[idx] for idx in indices_top]
        return {"ids": [ids_ordenados]}


def _cargar_corpus_desde_grafo_json() -> tuple[list[str], list[str], list[dict]]:
    """
    Carga los 7,221 artículos directamente desde `knowledge_graph/grafo_lexis.json`
    cuando `lexis_vectordb` no está presente en el contenedor de despliegue (ej. Railway).
    """
    ruta_grafo = Path(__file__).resolve().parent.parent / "knowledge_graph" / "grafo_lexis.json"
    if not ruta_grafo.exists():
        raise FileNotFoundError(
            f"No se encontró ni la base ChromaDB ni el grafo base en {ruta_grafo}"
        )

    with open(ruta_grafo, "r", encoding="utf-8") as f:
        datos_grafo = json.load(f)

    ids_documentos: list[str] = []
    textos_documentos: list[str] = []
    metadatos_lista: list[dict] = []

    for nodo in datos_grafo.get("nodos", []):
        if nodo.get("tipo_nodo") != "Articulo":
            continue
        if nodo.get("es_transitorio", False):
            continue

        doc_id = nodo["id"]
        ley_id = nodo.get("ley_id", "")
        documento = MAPEO_LEY_ID_A_DOCUMENTO.get(ley_id, ley_id)
        num_can = nodo.get("numero_canonico", "")
        etiqueta = (
            nodo.get("etiqueta")
            or nodo.get("etiqueta_original")
            or (f"Artículo {num_can}" if num_can else "")
        )
        if etiqueta and not etiqueta.endswith(".") and not etiqueta.endswith("-"):
            etiqueta_fmt = f"{etiqueta}.-"
        else:
            etiqueta_fmt = etiqueta
        jerarquia = nodo.get("jerarquia", "") or "General"
        texto_cuerpo = nodo.get("texto_completo", "")
        texto_busqueda = f"[{documento}] {etiqueta_fmt} - {jerarquia}: {texto_cuerpo}"

        ids_documentos.append(doc_id)
        textos_documentos.append(texto_busqueda)
        metadatos_lista.append(
            {
                "documento": documento,
                "articulo": etiqueta_fmt,
                "jerarquia": jerarquia,
                "nodo_articulo_id": doc_id,
                "articulo_id": doc_id,
                "cve_ley": ley_id.replace("ley:", ""),
            }
        )

    return ids_documentos, textos_documentos, metadatos_lista


# =============================================================
# INICIALIZACION DE MOTORES
# =============================================================
def inicializar_motores(ruta_db: str, modelo_nombre: str):
    """
    Conecta ChromaDB, carga el modelo semantico y construye el indice BM25.
    En entornos cloud como Railway (o cuando `lexis_vectordb` no está presente),
    activa automáticamente el motor híbrido ligero basado en `knowledge_graph/grafo_lexis.json`
    para reducir el consumo de RAM y evitar descargas pesadas en el arranque.
    """
    en_railway = bool(
        os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("RAILWAY_PROJECT_ID")
        or os.getenv("RAILWAY_SERVICE_ID")
    )
    forzar_ligero = os.getenv("LEXIS_MODO_LIGERO", "").strip().lower() in (
        "1",
        "true",
        "si",
        "yes",
    )
    forzar_chroma = os.getenv("LEXIS_FORZAR_CHROMA", "").strip().lower() in (
        "1",
        "true",
        "si",
        "yes",
    )

    usar_modo_ligero = forzar_ligero or (en_railway and not forzar_chroma)
    coleccion = None
    modelo = None
    ids_documentos = []
    textos_documentos = []
    metadatos_lista = []

    if not usar_modo_ligero:
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer

            print("Conectando con la base de datos vectorial de LEXIS...")
            cliente = chromadb.PersistentClient(path=ruta_db)
            coleccion = cliente.get_collection(name="lexis_leyes_mexico")

            print("Cargando el motor semantico...")
            modelo = SentenceTransformer(modelo_nombre)

            datos_db = coleccion.get(include=["documents", "metadatas"])
            ids_documentos = datos_db["ids"]
            textos_documentos = datos_db["documents"]
            metadatos_lista = datos_db["metadatas"]
        except Exception as err_chroma:
            print(
                f"  [INFO] ChromaDB local no disponible ({err_chroma}). "
                "Activando motor híbrido ligero desde knowledge_graph/grafo_lexis.json..."
            )
            usar_modo_ligero = True

    if usar_modo_ligero:
        print("Iniciando motor híbrido optimizado para Cloud/Railway desde el Grafo de Conocimiento...")
        ids_documentos, textos_documentos, metadatos_lista = _cargar_corpus_desde_grafo_json()
        modelo = MotorSemanticoTFIDF(textos_documentos)
        coleccion = ColeccionLigeraTFIDF(ids_documentos, modelo)

    print("Cargando índice BM25...")

    # Intentar cargar índice BM25 desde caché
    ruta_cache = Path(ruta_db) / "cache"
    ruta_cache.mkdir(parents=True, exist_ok=True)
    sufijo_cache = "cloud" if usar_modo_ligero else "chroma"
    ruta_bm25 = ruta_cache / f"bm25_index_{sufijo_cache}.pkl"
    
    datos_cache = cargar_indice_bm25(ruta_bm25) if MEJORAS_DISPONIBLES else None
    
    if datos_cache and len(datos_cache.get('corpus', [])) == len(textos_documentos):
        # Usar índice cacheado
        motor_bm25 = datos_cache['motor']
        corpus_tokenizado = datos_cache['corpus']
    else:
        # Construir nuevo índice
        print("Construyendo el índice léxico (BM25)...")
        corpus_tokenizado = [preprocesar_texto(doc) for doc in textos_documentos]
        motor_bm25 = BM25Okapi(corpus_tokenizado)
        
        # Guardar en caché
        if MEJORAS_DISPONIBLES:
            guardar_indice_bm25(motor_bm25, corpus_tokenizado, ruta_bm25)

    # Mapas id -> texto y id -> metadatos para recuperacion rapida
    diccionario_textos    = {i: t for i, t in zip(ids_documentos, textos_documentos)}
    diccionario_metadatos = {i: m for i, m in zip(ids_documentos, metadatos_lista)}

    # Catalogo de valores disponibles para los filtros
    documentos_disponibles = sorted({m.get("documento", "") for m in metadatos_lista if m.get("documento")})
    jerarquias_disponibles = sorted({m.get("jerarquia",  "") for m in metadatos_lista if m.get("jerarquia")})

    print(f"\nDocumentos indexados  : {len(ids_documentos)}")
    print(f"Leyes disponibles     : {len(documentos_disponibles)}")
    print(f"Jerarquias disponibles: {len(jerarquias_disponibles)}")

    return (
        coleccion,
        motor_bm25,
        modelo,
        diccionario_textos,
        diccionario_metadatos,
        documentos_disponibles,
        jerarquias_disponibles,
    )


# =============================================================
# FILTRADO POST-RECUPERACION
# =============================================================
def aplicar_filtros(
    ids_candidatos: list[str],
    diccionario_metadatos: dict,
    filtro_documento: str | None = None,
    filtro_jerarquia: str | None = None,
) -> list[str]:
    """
    Filtra una lista de IDs conservando solo los que cumplen
    los criterios de documento y/o jerarquia.
    La comparacion es insensible a mayusculas y acepta coincidencia parcial.
    """
    if not filtro_documento and not filtro_jerarquia:
        return ids_candidatos  # Sin filtros -> devuelve todo

    ids_filtrados = []
    fd = filtro_documento.lower().strip() if filtro_documento else None
    fj = filtro_jerarquia.lower().strip()  if filtro_jerarquia  else None

    for doc_id in ids_candidatos:
        meta = diccionario_metadatos.get(doc_id, {})
        doc_val = meta.get("documento", "").lower()
        jer_val = meta.get("jerarquia",  "").lower()

        # Matching por coincidencia exacta/subcadena o todas las palabras distintivas
        cumple_doc = True
        if fd:
            palabras_fd = [p for p in fd.split() if len(p) > 3 and p != "tlaxcala"]
            cumple_doc = (fd in doc_val) or (doc_val in fd) or (
                bool(palabras_fd) and all(palabra in doc_val for palabra in palabras_fd)
            )
        
        cumple_jer = True
        if fj:
            cumple_jer = (fj in jer_val) or (jer_val in fj)

        if cumple_doc and cumple_jer:
            ids_filtrados.append(doc_id)

    return ids_filtrados


# =============================================================
# BUSQUEDA HIBRIDA CON RRF PONDERADO
# =============================================================
def busqueda_hibrida(
    consulta: str,
    coleccion,
    motor_bm25: BM25Okapi,
    modelo,
    diccionario_textos: dict,
    diccionario_metadatos: dict,
    top_k: int          = TOP_K_DEFAULT,
    filtro_documento: str | None = None,
    filtro_jerarquia: str | None = None,
) -> list[dict]:
    """
    0. Pre-filtrado por documento (MEJORA: filtra ANTES de buscar)
    1. Busqueda semantica  (ChromaDB)
    2. Busqueda lexica     (BM25)
    3. Fusion RRF ponderada
    4. Filtrado final por jerarquia
    Resultados ordenados de MAYOR a MENOR puntuacion RRF.
    """
    inicio_tiempo = time.time()
    error_msg = None
    
    # MEJORA: Expansión de consulta con sinónimos
    if MEJORAS_DISPONIBLES:
        consulta_expandida = expandir_consulta(consulta)
    else:
        consulta_expandida = consulta
    
    # MEJORA: Análisis dinámico de pesos
    if MEJORAS_DISPONIBLES:
        info_pesos = analizar_tipo_consulta(consulta)
        peso_semantico = info_pesos['peso_semantico']
        peso_lexico = info_pesos['peso_lexico']
    else:
        peso_semantico = PESO_SEMANTICO
        peso_lexico = PESO_LEXICO

    # Ampliamos n_results internamente para compensar el filtrado posterior
    n_interno = top_k * 8  # Aumentado para asegurar suficientes resultados tras filtrado

    # ================================================================
    # 0. PRE-FILTRADO: Obtener IDs que cumplen el filtro de documento
    # ================================================================
    ids_permitidos = None
    if filtro_documento:
        fd = filtro_documento.lower().strip()
        
        # Mapeo de términos a documentos exactos
        mapeo_exacto = {
            'código penal': 'Código Penal Tlaxcala',
            'codigo penal': 'Código Penal Tlaxcala',
            'código penal tlaxcala': 'Código Penal Tlaxcala',
            'codigo penal tlaxcala': 'Código Penal Tlaxcala',
            'penal': 'Código Penal Tlaxcala',
            'ley trabajo': 'Ley Trabajo',
            'ley del trabajo': 'Ley Trabajo',
            'ley federal del trabajo': 'Ley Trabajo',
            'trabajo': 'Ley Trabajo',
            'laboral': 'Ley Trabajo',
            'código civil': 'Codigo Civil Tlaxcala',
            'codigo civil': 'Codigo Civil Tlaxcala',
            'código civil tlaxcala': 'Codigo Civil Tlaxcala',
            'codigo civil tlaxcala': 'Codigo Civil Tlaxcala',
            'civil': 'Codigo Civil Tlaxcala',
            'constitucion': 'Constitucion',
            'constitución': 'Constitucion',
            'constitucional': 'Constitucion',
            'procedimiento civil': 'Procedimiento Civiles Tlaxcala',
            'procedimientos civiles': 'Procedimiento Civiles Tlaxcala',
            'procedimiento civiles tlaxcala': 'Procedimiento Civiles Tlaxcala',
            'procedimientos civiles tlaxcala': 'Procedimiento Civiles Tlaxcala',
            'procedimiento penal': 'Procedimiento Penal Tlaxcala',
            'procedimientos penales': 'Procedimiento Penal Tlaxcala',
            'procedimiento penal tlaxcala': 'Procedimiento Penal Tlaxcala',
            'procedimientos penales tlaxcala': 'Procedimiento Penal Tlaxcala',
        }
        
        # Si hay coincidencia exacta, usar ese documento
        documento_exacto = mapeo_exacto.get(fd)
        if documento_exacto:
            ids_permitidos = set()
            for doc_id, meta in diccionario_metadatos.items():
                if meta.get("documento", "").lower() == documento_exacto.lower():
                    ids_permitidos.add(doc_id)
        else:
            # Fallback: búsqueda por palabras
            palabras_filtro = [p for p in fd.split() if len(p) > 2]
            palabras_clave = {'penal', 'civil', 'laboral', 'trabajo', 'constitucion', 'procedimiento'}
            
            ids_permitidos = set()
            for doc_id, meta in diccionario_metadatos.items():
                doc_val = meta.get("documento", "").lower()
                
                # Si hay palabras clave específicas, usarlas
                if any(p in palabras_clave for p in palabras_filtro):
                    if any(p in doc_val for p in palabras_filtro if p in palabras_clave):
                        ids_permitidos.add(doc_id)
                else:
                    # Matching normal
                    if all(p in doc_val for p in palabras_filtro):
                        ids_permitidos.add(doc_id)
        
        if not ids_permitidos:
            print(f"  [AVISO] No se encontraron documentos para filtro: {filtro_documento}")
            return []
    
    # ----------------------------------------------------------
    # 1. Busqueda Semantica (solo en documentos permitidos si hay filtro)
    # ----------------------------------------------------------
    vector_consulta = modelo.encode([consulta]).tolist()
    
    # Optimización: si hay filtro, buscar solo en documentos permitidos
    # ChromaDB no permite filtrado directo por metadata en query, así que
    # recuperamos más resultados y filtramos después
    resultados_semanticos = coleccion.query(
        query_embeddings=vector_consulta,
        n_results=min(n_interno * 2, len(diccionario_textos)),
    )
    
    ids_semanticos = resultados_semanticos["ids"][0]
    
    # FILTRAR: solo IDs permitidos (reordenados por relevancia original de ChromaDB)
    if ids_permitidos:
        # Preservar el orden original de relevancia de ChromaDB
        ids_semanticos = [id_ for id_ in ids_semanticos if id_ in ids_permitidos]
    else:
        ids_semanticos = list(ids_semanticos)

    # ----------------------------------------------------------
    # 2. Busqueda Lexica (BM25) - solo en documentos permitidos
    # ----------------------------------------------------------
    consulta_tokenizada  = preprocesar_texto(consulta_expandida)
    puntuaciones_bm25    = motor_bm25.get_scores(consulta_tokenizada)

    if ids_permitidos:
        # Filtrar solo IDs permitidos
        ids_ordenados_bm25 = [
            (doc_id, score) 
            for doc_id, score in zip(diccionario_textos.keys(), puntuaciones_bm25)
            if doc_id in ids_permitidos
        ]
    else:
        ids_ordenados_bm25 = list(zip(diccionario_textos.keys(), puntuaciones_bm25))
    
    ids_ordenados_bm25.sort(key=lambda x: x[1], reverse=True)
    ids_lexicos = [item[0] for item in ids_ordenados_bm25[:n_interno]]

    # ----------------------------------------------------------
    # 3. Fusion RRF Ponderada (con pesos dinámicos)
    # ----------------------------------------------------------
    puntuaciones_rrf: dict[str, float] = defaultdict(float)

    for rango, doc_id in enumerate(ids_semanticos):
        puntuaciones_rrf[doc_id] += peso_semantico / (K_RRF + rango + 1)

    for rango, doc_id in enumerate(ids_lexicos):
        puntuaciones_rrf[doc_id] += peso_lexico / (K_RRF + rango + 1)

    # Ordenar de MAYOR a MENOR puntuacion RRF (mas relevante primero)
    ids_por_relevancia = sorted(
        puntuaciones_rrf.keys(),
        key=lambda x: puntuaciones_rrf[x],
        reverse=True,
    )

    # ----------------------------------------------------------
    # 3.5. Boost para conceptos legales clave y citas exactas de artículos
    # ----------------------------------------------------------
    import re
    consulta_lower = consulta.lower()
    articulos_citados_query: set[str] = set()
    for m_art in re.finditer(
        r"\b(?:art[íi]culos?|arts?\.?)\s+([0-9]+(?:\s*(?:bis|ter|quater|quinquies|[a-g]))?(?:\s*(?:,|y|e|al|a)\s*[0-9]+(?:\s*(?:bis|ter|quater|quinquies|[a-g]))?)*)",
        consulta_lower,
    ):
        bloque_nums = m_art.group(1)
        for sub_m in re.finditer(r"([0-9]+(?:\s*(?:bis|ter|quater|quinquies|[a-g]))?)", bloque_nums):
            articulos_citados_query.add(re.sub(r"[\s\-]+", "_", sub_m.group(1).strip().upper()))

    if articulos_citados_query:
        universo_docs = ids_permitidos if ids_permitidos is not None else diccionario_metadatos.keys()
        for doc_id in universo_docs:
            meta_doc = diccionario_metadatos.get(doc_id, {})
            art_id_doc = str(meta_doc.get("articulo_id") or meta_doc.get("nodo_articulo_id") or doc_id)
            sufijo_id = art_id_doc.split(":")[-1].upper().replace("-", "_") if ":" in art_id_doc else ""
            if sufijo_id in articulos_citados_query:
                puntuaciones_rrf[doc_id] = max(puntuaciones_rrf.get(doc_id, 0.0), 0.025) * 3.5

    ids_por_relevancia = list(puntuaciones_rrf.keys())
    conceptos_boost = {
        'horas extras': 2.0,
        'hora extra': 2.0,
        'despido': 1.8,
        'despedir': 1.8,
        'renuncia': 1.5,
        'indemnización': 1.5,
        'liquidación': 1.5,
        'pago': 1.3,
        'salario': 1.3,
        'aguinaldo': 1.5,
        'vacaciones': 1.5,
        'prima': 1.3,
        'contrato': 1.2,
        'rescisión': 1.5,
        'reinstala': 1.5,
    }
    
    for doc_id in ids_por_relevancia:
        texto_doc = diccionario_textos.get(doc_id, '').lower()
        boost = 1.0
        for concepto, factor in conceptos_boost.items():
            if concepto in consulta_lower and concepto in texto_doc:
                boost *= factor
        puntuaciones_rrf[doc_id] *= boost
    
    # Reordenar con los boosts aplicados
    ids_por_relevancia = sorted(
        puntuaciones_rrf.keys(),
        key=lambda x: puntuaciones_rrf[x],
        reverse=True,
    )

    # ----------------------------------------------------------
    # 4. Filtrado final por jerarquia
    # ----------------------------------------------------------
    ids_filtrados = aplicar_filtros(
        ids_por_relevancia,
        diccionario_metadatos,
        filtro_documento=None,  # Ya aplicado
        filtro_jerarquia=filtro_jerarquia,
    )

    # Tomamos los primeros top_k
    ids_finales = ids_filtrados[:top_k]

    # ----------------------------------------------------------
    # 5. Construir resultado final
    # ----------------------------------------------------------
    resultados = []
    for doc_id in ids_finales:
        meta = diccionario_metadatos.get(doc_id, {})
        art_id_can = meta.get("articulo_id") or meta.get("nodo_articulo_id") or ""
        resultados.append({
            "id"               : doc_id,
            "articulo_id"      : art_id_can,
            "nodo_articulo_id" : art_id_can or doc_id,
            "cve_ley"          : meta.get("cve_ley", ""),
            "texto"            : diccionario_textos[doc_id],
            "puntuacion_rrf"   : puntuaciones_rrf.get(doc_id, 0),
            "documento"        : meta.get("documento", "N/D"),
            "articulo"         : meta.get("articulo",  "N/D"),
            "jerarquia"        : meta.get("jerarquia",  "N/D"),
            "metadatos"        : meta,
        })

    # MEJORA: Re-rankeo de resultados
    if HABILITAR_RERANKEO and MEJORAS_DISPONIBLES and resultados:
        try:
            p_rrf = 0.75 if articulos_citados_query else 0.3
            p_sem = 0.25 if articulos_citados_query else 0.7
            resultados = rerankear_resultados(
                resultados,
                consulta,
                modelo,
                top_n=top_k,
                peso_rrf=p_rrf,
                peso_semantico=p_sem
            )
        except Exception as e:
            print(f"  [INFO] Re-rankeo no disponible: {e}")

    # MEJORA: Logging de búsqueda
    tiempo_respuesta = time.time() - inicio_tiempo
    if MEJORAS_DISPONIBLES:
        guardar_log_busqueda(
            consulta=consulta,
            filtro_documento=filtro_documento,
            filtro_jerarquia=filtro_jerarquia,
            num_resultados=len(resultados),
            tiempo_respuesta=tiempo_respuesta,
            errores=error_msg
        )

    return resultados


# =============================================================
# INTERFAZ DE LINEA DE COMANDOS
# =============================================================
def mostrar_catalogo(documentos: list[str], jerarquias: list[str]):
    print("\n" + "="*60)
    print("LEYES DISPONIBLES PARA FILTRAR:")
    for i, d in enumerate(documentos, 1):
        print(f"  {i:>3}. {d}")
    print("\nJERARQUIAS DISPONIBLES:")
    for j in jerarquias:
        print(f"  - {j}")
    print("="*60 + "\n")


def parsear_filtros(entrada: str, documentos: list[str]) -> tuple[str | None, str | None]:
    """
    Interpreta comandos de filtro escritos por el usuario.
    Formatos aceptados:
      ley:<nombre o numero>      ->  filtra por documento
      jerarquia:<valor>          ->  filtra por jerarquia
    Ejemplo: "ley:constitucion jerarquia:capitulo"
    """
    filtro_doc = None
    filtro_jer = None
    partes     = entrada.lower().split()

    for parte in partes:
        if parte.startswith("ley:"):
            valor = parte[4:].strip()
            # Si es numero, buscar por indice en el catalogo
            if valor.isdigit():
                idx = int(valor) - 1
                if 0 <= idx < len(documentos):
                    filtro_doc = documentos[idx]
            else:
                filtro_doc = valor

        elif parte.startswith("jerarquia:"):
            filtro_jer = parte[10:].strip()

    return filtro_doc, filtro_jer


def main():
    try:
        (
            coleccion,
            motor_bm25,
            modelo,
            diccionario_textos,
            diccionario_metadatos,
            documentos_disponibles,
            jerarquias_disponibles,
        ) = inicializar_motores(CARPETA_DB, MODELO_NOMBRE)

        print("\n" + "="*60)
        print("  LEXIS  -  MOTOR DE BUSQUEDA HIBRIDO  v2.0")
        print("="*60)
        print("Comandos especiales:")
        print("  catalogo          -> muestra leyes y jerarquias disponibles")
        print("  ley:<nombre/num>  -> filtra por ley  (ej: ley:constitucion)")
        print("  jerarquia:<val>   -> filtra por jerarquia (ej: jerarquia:titulo)")
        print("  salir             -> cierra LEXIS")
        print("\nEjemplo con filtro:")
        print('  "derecho a la educacion ley:1 jerarquia:capitulo"\n')

        filtro_documento_activo = None
        filtro_jerarquia_activa = None

        while True:
            entrada = input("Ciudadano: ").strip()

            if not entrada:
                continue

            if entrada.lower() in ("salir", "exit", "quit"):
                print("\nCerrando LEXIS. Hasta pronto.")
                break

            if entrada.lower() == "catalogo":
                mostrar_catalogo(documentos_disponibles, jerarquias_disponibles)
                continue

            # Separar filtros del texto de consulta real
            filtro_documento_activo, filtro_jerarquia_activa = parsear_filtros(
                entrada, documentos_disponibles
            )

            # Limpiar los tokens de filtro para obtener solo la consulta
            consulta_limpia = " ".join(
                p for p in entrada.split()
                if not p.lower().startswith("ley:")
                and not p.lower().startswith("jerarquia:")
            ).strip()

            if not consulta_limpia:
                print("  [!] Escribe tambien una consulta, no solo filtros.\n")
                continue

            # DETECCIÓN AUTOMÁTICA si no hay filtro explícito
            if not filtro_documento_activo and ANALIZADOR_DISPONIBLE:
                documento_auto, info = detectar_normativa(consulta_limpia, documentos_disponibles)
                if documento_auto:
                    print(f"  🔍 Auto-detección: '{documento_auto}'")
                    filtro_documento_activo = documento_auto

            # Informar filtros activos
            if filtro_documento_activo or filtro_jerarquia_activa:
                print(f"  [Filtros activos]  "
                      f"ley='{filtro_documento_activo or 'todas'}'  "
                      f"jerarquia='{filtro_jerarquia_activa or 'todas'}'")

            print("  Ejecutando busqueda hibrida...")
            hits = busqueda_hibrida(
                consulta_limpia,
                coleccion,
                motor_bm25,
                modelo,
                diccionario_textos,
                diccionario_metadatos,
                top_k=TOP_K_DEFAULT,
                filtro_documento=filtro_documento_activo,
                filtro_jerarquia=filtro_jerarquia_activa,
            )

            if not hits:
                print("\n  [!] Sin resultados para los filtros aplicados.\n")
                continue

            print("\n" + "-"*60)
            print(f"  RESULTADOS  (menor -> mayor relevancia | total: {len(hits)})")
            print("-"*60)

            for i, hit in enumerate(hits, 1):
                print(
                    f"[{i:>2}] RRF: {hit['puntuacion_rrf']:.5f}  |  "
                    f"{hit['documento']}  |  {hit['articulo']}  |  "
                    f"Jerarquia: {hit['jerarquia']}"
                )
                # DESPUÉS
                print(f"      {hit['texto']}\n")

            print("-"*60 + "\n")

    except Exception as e:
        print(f"\nError al iniciar LEXIS: {e}")


if __name__ == "__main__":
    main()