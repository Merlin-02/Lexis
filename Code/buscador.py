#buscador.py
import string
import warnings
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from collections import defaultdict

warnings.filterwarnings("ignore")

# =============================================================
# CONFIGURACION GLOBAL
# =============================================================
CARPETA_DB     = "../lexis_vectordb"
MODELO_NOMBRE  = "paraphrase-multilingual-MiniLM-L12-v2"
TOP_K_DEFAULT  = 15
K_RRF          = 60

# Peso relativo de cada motor (deben sumar 1.0)
# Sube PESO_SEMANTICO si las consultas son conceptuales/vagas
# Sube PESO_LEXICO    si las consultas usan terminos juridicos exactos
PESO_SEMANTICO = 0.6
PESO_LEXICO    = 0.4


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

    print("Construyendo el indice lexico (BM25) en memoria...")
    # Incluimos metadatos para poder filtrar sin consulta extra
    datos_db          = coleccion.get(include=["documents", "metadatas"])
    ids_documentos    = datos_db["ids"]
    textos_documentos = datos_db["documents"]
    metadatos_lista   = datos_db["metadatas"]  # lista de dicts

    corpus_tokenizado = [preprocesar_texto(doc) for doc in textos_documentos]
    motor_bm25        = BM25Okapi(corpus_tokenizado)

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

        cumple_doc = (fd is None) or (fd in doc_val)
        cumple_jer = (fj is None) or (fj in jer_val)

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
    1. Busqueda semantica  (ChromaDB)
    2. Busqueda lexica     (BM25)
    3. Fusion RRF ponderada
    4. Filtrado por metadatos (documento / jerarquia)
    Resultados ordenados de MENOR a MAYOR puntuacion RRF.
    """
    # Ampliamos n_results internamente para compensar el filtrado posterior
    n_interno = top_k * 4

    # ----------------------------------------------------------
    # 1. Busqueda Semantica
    # ----------------------------------------------------------
    vector_consulta      = modelo.encode([consulta]).tolist()
    resultados_semanticos = coleccion.query(
        query_embeddings=vector_consulta,
        n_results=min(n_interno, len(diccionario_textos)),
    )
    ids_semanticos = resultados_semanticos["ids"][0]

    # ----------------------------------------------------------
    # 2. Busqueda Lexica (BM25)
    # ----------------------------------------------------------
    consulta_tokenizada  = preprocesar_texto(consulta)
    puntuaciones_bm25    = motor_bm25.get_scores(consulta_tokenizada)

    ids_ordenados_bm25 = sorted(
        zip(diccionario_textos.keys(), puntuaciones_bm25),
        key=lambda x: x[1],
        reverse=True,
    )
    ids_lexicos = [item[0] for item in ids_ordenados_bm25[:n_interno]]

    # ----------------------------------------------------------
    # 3. Fusion RRF Ponderada
    # ----------------------------------------------------------
    puntuaciones_rrf: dict[str, float] = defaultdict(float)

    for rango, doc_id in enumerate(ids_semanticos):
        puntuaciones_rrf[doc_id] += PESO_SEMANTICO / (K_RRF + rango + 1)

    for rango, doc_id in enumerate(ids_lexicos):
        puntuaciones_rrf[doc_id] += PESO_LEXICO / (K_RRF + rango + 1)

    # Ordenar de MENOR a MAYOR puntuacion RRF (menos relevante primero)
    ids_por_relevancia = sorted(
        puntuaciones_rrf.keys(),
        key=lambda x: puntuaciones_rrf[x],
        reverse=False,   # <-- MENOR a MAYOR
    )

    # ----------------------------------------------------------
    # 4. Filtrado por metadatos
    # ----------------------------------------------------------
    ids_filtrados = aplicar_filtros(
        ids_por_relevancia,
        diccionario_metadatos,
        filtro_documento,
        filtro_jerarquia,
    )

    # Tomamos los ultimos top_k (los de mayor puntuacion tras filtrar)
    ids_finales = ids_filtrados[-top_k:]

    # ----------------------------------------------------------
    # 5. Construir resultado final
    # ----------------------------------------------------------
    resultados = []
    for doc_id in ids_finales:
        meta = diccionario_metadatos.get(doc_id, {})
        resultados.append({
            "id"             : doc_id,
            "texto"          : diccionario_textos[doc_id],
            "puntuacion_rrf" : puntuaciones_rrf[doc_id],
            "documento"      : meta.get("documento", "N/D"),
            "articulo"       : meta.get("articulo",  "N/D"),
            "jerarquia"      : meta.get("jerarquia",  "N/D"),
        })

    return resultados  # orden: menor -> mayor puntuacion RRF


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