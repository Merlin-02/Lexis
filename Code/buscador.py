#buscador.py
import string
import warnings
import time
import chromadb
from sentence_transformers import SentenceTransformer
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
MODELO_NOMBRE  = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K_DEFAULT  = 30
HABILITAR_RERANKEO = True
K_RRF          = 60

# Peso relativo de cada motor (deben sumar 1.0)
# Sube PESO_SEMANTICO si las consultas son conceptuales/vagas
# Sube PESO_LEXICO    si las consultas usan terminos juridicos exactos
PESO_SEMANTICO = 0.2
PESO_LEXICO    = 0.8


# =============================================================
# PREPROCESAMIENTO
# =============================================================
def preprocesar_texto(texto: str) -> list[str]:
    """Minusculas + elimina puntuacion para el motor lexico (BM25)."""
    texto = texto.lower()
    texto = texto.translate(str.maketrans("", "", string.punctuation))
    return texto.split()


# =============================================================
# INICIALIZACION DE MOTORES
# =============================================================
def inicializar_motores(ruta_db: str, modelo_nombre: str):
    """
    Conecta ChromaDB, carga el modelo semantico y construye el indice BM25.
    Retorna: (coleccion, motor_bm25, modelo, diccionario_textos, diccionario_metadatos)
    """
    print("Conectando con la base de datos vectorial de LEXIS...")
    cliente   = chromadb.PersistentClient(path=ruta_db)

    try:
        coleccion = cliente.get_collection(name="lexis_leyes_mexico")
    except ValueError:
        raise Exception(
            "No se encontro la coleccion. Ejecuta vectorizacion.py primero."
        )

    print("Cargando el motor semantico...")
    modelo = SentenceTransformer(modelo_nombre)

    print("Cargando índice BM25...")
    
    # Incluimos metadatos para poder filtrar sin consulta extra
    datos_db          = coleccion.get(include=["documents", "metadatas"])
    ids_documentos    = datos_db["ids"]
    textos_documentos = datos_db["documents"]
    metadatos_lista   = datos_db["metadatas"]

    # Intentar cargar índice BM25 desde caché
    ruta_cache = Path(ruta_db) / "cache"
    ruta_cache.mkdir(exist_ok=True)
    ruta_bm25 = ruta_cache / "bm25_index.pkl"
    
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

        # Matching más flexible: bidireccional
        cumple_doc = True
        if fd:
            # Buscar si el filtro está en el documento O viceversa
            cumple_doc = (fd in doc_val) or (doc_val in fd) or (
                any(palabra in doc_val for palabra in fd.split() if len(palabra) > 3)
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
            'penal': 'Código Penal Tlaxcala',
            'ley trabajo': 'Ley Trabajo',
            'ley del trabajo': 'Ley Trabajo',
            'trabajo': 'Ley Trabajo',
            'laboral': 'Ley Trabajo',
            'código civil': 'Codigo Civil Tlaxcala',
            'codigo civil': 'Codigo Civil Tlaxcala',
            'civil': 'Codigo Civil Tlaxcala',
            'constitucion': 'Constitucion',
            'constitucional': 'Constitucion',
            'procedimiento civil': 'Procedimiento Civiles Tlaxcala',
            'procedimiento penal': 'Procedimiento Penal Tlaxcala',
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
    # 1. Busqueda Semantica (luego filtraremos por IDs)
    # ----------------------------------------------------------
    vector_consulta = modelo.encode([consulta]).tolist()
    
    # Buscar en todos los documentos, filtraremos después
    resultados_semanticos = coleccion.query(
        query_embeddings=vector_consulta,
        n_results=min(n_interno, len(diccionario_textos)),
    )
    
    ids_semanticos = resultados_semanticos["ids"][0]
    
    # FILTRAR: solo IDs permitidos
    if ids_permitidos:
        ids_semanticos = [id_ for id_ in ids_semanticos if id_ in ids_permitidos]

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
        resultados.append({
            "id"             : doc_id,
            "texto"          : diccionario_textos[doc_id],
            "puntuacion_rrf" : puntuaciones_rrf.get(doc_id, 0),
            "documento"      : meta.get("documento", "N/D"),
            "articulo"       : meta.get("articulo",  "N/D"),
            "jerarquia"      : meta.get("jerarquia",  "N/D"),
        })

    # MEJORA: Re-rankeo de resultados
    if HABILITAR_RERANKEO and MEJORAS_DISPONIBLES and resultados:
        try:
            resultados = rerankear_resultados(
                resultados,
                consulta,
                modelo,
                top_n=top_k,
                peso_rrf=0.3,
                peso_semantico=0.7
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