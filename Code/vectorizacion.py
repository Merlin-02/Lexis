# vectorizacion.py
import json
import logging
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer

# ==========================================
# CONFIGURACIÓN
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# MEJORA: tamaño de lote para la generación de embeddings.
# Reduce este valor si tienes poca RAM/VRAM (ej. 32 o 64).
BATCH_SIZE = 128


# ==========================================
# INICIALIZACIÓN DE LA BASE VECTORIAL
# ==========================================

def inicializar_base_vectorial(ruta_db: str):
    """
    Conecta con ChromaDB y purga la colección anterior para evitar
    fragmentos fantasma y duplicados.
    """
    cliente = chromadb.PersistentClient(path=ruta_db)

    try:
        cliente.delete_collection(name="lexis_leyes_mexico")
        log.info("Colección anterior detectada y purgada con éxito.")
    except Exception:
        pass  # No existe aún, no es un error

    coleccion = cliente.create_collection(
        name="lexis_leyes_mexico",
        metadata={"hnsw:space": "cosine"}
    )
    log.info("Colección nueva creada: lexis_leyes_mexico")
    return coleccion


# ==========================================
# PREPARACIÓN Y VALIDACIÓN DE CHUNKS
# ==========================================

def normalizar_metadatos(meta: dict) -> dict:
    """
    MEJORA: limpia los valores de metadatos (strip de espacios,
    asegura que sean cadenas no vacías) para evitar errores
    silenciosos al filtrar en ChromaDB.
    """
    return {
        k: str(v).strip() if v is not None else ""
        for k, v in meta.items()
    }


def preparar_lote(chunks: list[dict], offset: int, nombre_doc: str) -> tuple:
    """
    Valida y empaqueta un lote de chunks para insertar en ChromaDB.

    MEJORA:
    - Salta chunks con texto vacío.
    - Deduplica IDs dentro del mismo lote.
    - Normaliza metadatos antes de insertar.

    Retorna (textos, metadatos, ids, omitidos).
    """
    textos    = []
    metadatos = []
    ids       = []
    ids_vistos = set()
    omitidos  = 0

    for i, chunk in enumerate(chunks):
        texto = chunk.get("texto_busqueda", "").strip()
        meta  = chunk.get("metadatos", {})

        # MEJORA: omitir chunks vacíos
        if not texto:
            log.debug("Chunk vacío omitido (índice %d en %s)", offset + i, nombre_doc)
            omitidos += 1
            continue

        # Generar ID único y reproducible
        doc_nombre = meta.get("documento", "doc").replace(" ", "_")
        art_nombre = meta.get("articulo",  f"art_{offset+i}").replace(" ", "_")
        jer_nombre = meta.get("jerarquia", "").replace(" ", "_")[:30]  # limitar longitud
        chunk_id   = f"{doc_nombre}__{art_nombre}__{jer_nombre}__{offset + i}"

        # MEJORA: evitar IDs duplicados dentro del mismo archivo
        if chunk_id in ids_vistos:
            chunk_id = f"{chunk_id}__dup{i}"
        ids_vistos.add(chunk_id)

        textos.append(texto)
        metadatos.append(normalizar_metadatos(meta))
        ids.append(chunk_id)

    return textos, metadatos, ids, omitidos


# ==========================================
# VECTORIZACIÓN
# ==========================================

def vectorizar_documentos(
    carpeta_chunks: str,
    coleccion,
    modelo_nombre: str,
) -> None:
    """
    Lee los chunks, genera embeddings en lotes y los almacena en ChromaDB.

    MEJORAS:
    - Procesamiento en lotes de tamaño BATCH_SIZE para controlar memoria.
    - Validación de textos vacíos y deduplicación de IDs.
    - Manejo de errores por archivo sin detener el proceso completo.
    - Reporte final con totales.
    """
    log.info(
        "Cargando el modelo de embeddings '%s'  "
        "(esto puede tardar la primera vez)...", modelo_nombre
    )
    modelo = SentenceTransformer(modelo_nombre)

    ruta_entrada  = Path(carpeta_chunks)
    archivos_json = list(ruta_entrada.glob('*_chunks.json'))

    if not archivos_json:
        log.warning("No se encontraron archivos de chunks en %s", carpeta_chunks)
        return

    log.info("Iniciando vectorización de %d archivos de chunks...", len(archivos_json))

    total_vectorizados = 0
    total_omitidos     = 0

    for archivo in archivos_json:
        log.info("Procesando: %s", archivo.name)
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            log.error("No se pudo leer %s: %s  — se omite.", archivo.name, e)
            continue

        if not chunks:
            log.warning("Archivo vacío: %s  — se omite.", archivo.name)
            continue

        nombre_doc         = archivo.stem.replace('_chunks', '')
        vectorizados_arch  = 0
        omitidos_arch      = 0

        # MEJORA: procesar en lotes para controlar uso de memoria
        for inicio in range(0, len(chunks), BATCH_SIZE):
            lote = chunks[inicio: inicio + BATCH_SIZE]

            textos, metadatos, ids, omitidos = preparar_lote(lote, inicio, nombre_doc)
            omitidos_arch += omitidos

            if not textos:
                continue

            try:
                log.info(
                    "  Lote %d-%d: generando %d embeddings...",
                    inicio + 1, inicio + len(lote), len(textos)
                )
                embeddings = modelo.encode(textos, show_progress_bar=False)

                coleccion.add(
                    embeddings=embeddings.tolist(),
                    documents=textos,
                    metadatas=metadatos,
                    ids=ids,
                )
                vectorizados_arch += len(textos)

            except Exception as e:
                log.error(
                    "  Error al insertar lote %d-%d de %s: %s",
                    inicio + 1, inicio + len(lote), archivo.name, e
                )

        total_vectorizados += vectorizados_arch
        total_omitidos     += omitidos_arch
        log.info(
            "  Archivo '%s' finalizado: %d vectorizados, %d omitidos.",
            archivo.name, vectorizados_arch, omitidos_arch
        )

    log.info("=" * 50)
    log.info("Vectorización completada.")
    log.info("  Total insertados en ChromaDB : %d", total_vectorizados)
    log.info("  Total chunks omitidos        : %d", total_omitidos)
    log.info("=" * 50)


# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    carpeta_chunks = "../knowledge_chunks"
    carpeta_db     = "../lexis_vectordb"
    modelo_elegido = "paraphrase-multilingual-MiniLM-L12-v2"

    coleccion_lexis = inicializar_base_vectorial(carpeta_db)
    vectorizar_documentos(carpeta_chunks, coleccion_lexis, modelo_elegido)

    log.info("El motor de búsqueda LEXIS está listo.")