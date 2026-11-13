# segmentacion.py
import json
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from grafo_lexis.cargador import normalizar_registro_articulo, detectar_inicio_transitorios
    CARGADOR_GRAFO_DISPONIBLE = True
except ImportError:
    CARGADOR_GRAFO_DISPONIBLE = False

MAPA_DOCUMENTO_A_SLUG = {
    "Ley Trabajo": "lft",
    "Código Penal Tlaxcala": "cp_tlax",
    "Codigo Civil Tlaxcala": "cc_tlax",
    "Procedimiento Civiles Tlaxcala": "cpc_tlax",
    "Procedimiento Penal Tlaxcala": "cpp_tlax",
    "Constitucion": "cpeum",
}


# ==========================================
# HELPERS
# ==========================================

def _hash_texto(texto: str) -> str:
    """MD5 corto para deduplicar chunks con contenido idéntico."""
    return hashlib.md5(texto.encode('utf-8')).hexdigest()[:12]


def crear_chunk(
    texto: str,
    documento: str,
    articulo: str,
    jerarquia: str = "",
    articulo_id: str = "",
    cve_ley: str = "",
) -> dict:
    """Crea un diccionario estandarizado para un chunk de texto con ID canónico del grafo."""
    prefijo = articulo
    if jerarquia:
        prefijo += f" - {jerarquia}"

    texto_enriquecido = f"[{documento}] {prefijo}: {texto}"

    meta = {
        "documento": documento,
        "articulo" : articulo,
        "jerarquia": jerarquia,     # propagado desde preparacion.py
    }
    if articulo_id:
        meta["articulo_id"] = articulo_id
    if cve_ley:
        meta["cve_ley"] = cve_ley

    return {
        "texto_busqueda": texto_enriquecido,
        "metadatos": meta,
    }


def procesar_articulo_a_chunks(
    articulo_dict: dict,
    nombre_doc: str,
    articulo_id: str = "",
    cve_ley: str = "",
) -> list[dict]:
    """
    Desglosa un artículo estructurado en múltiples chunks,
    arrastrando el texto introductorio hacia las fracciones e incisos.

    MEJORA: usa el campo 'jerarquia' generado por preparacion.py
    e inyecta `articulo_id` y `cve_ley` canónicos del grafo.
    """
    chunks   = []
    nombre_art = articulo_dict.get("articulo", "Articulo Desconocido")

    # MEJORA: leer la jerarquía real del artículo (Titulo I, Capitulo II, etc.)
    jerarquia    = articulo_dict.get("jerarquia", "").strip()
    texto_general = articulo_dict.get("texto_general", "").strip()

    # 1. Chunk del texto general solo (como referencia)
    if texto_general:
        chunks.append(crear_chunk(texto_general, nombre_doc, nombre_art, jerarquia, articulo_id, cve_ley))

    # 2. Fracciones
    for fraccion in articulo_dict.get("fracciones", []):
        nombre_fraccion   = f"Fraccion {fraccion.get('fraccion')}"
        texto_fraccion    = fraccion.get("texto_general", "").strip()

        # Inyección de contexto: introducción + fracción
        texto_combinado_fraccion = (
            f"{texto_general} {texto_fraccion}".strip()
            if texto_general else texto_fraccion
        )

        if texto_combinado_fraccion:
            chunks.append(crear_chunk(
                texto_combinado_fraccion, nombre_doc, nombre_art,
                # MEJORA: jerarquía más específica para fracciones
                f"{jerarquia} - {nombre_fraccion}".strip(" -"),
                articulo_id, cve_ley
            ))

        # Incisos dentro de la fracción
        for inciso in fraccion.get("incisos", []):
            nombre_inciso   = f"{nombre_fraccion} - Inciso {inciso.get('inciso')})"
            texto_inciso    = (inciso.get("texto", "") or inciso.get("texto_general", "")).strip()

            # Inyección de contexto: introducción + fracción + inciso
            texto_combinado_inciso = " ".join(
                filter(None, [texto_general, texto_fraccion, texto_inciso])
            ).strip()

            if texto_combinado_inciso:
                chunks.append(crear_chunk(
                    texto_combinado_inciso, nombre_doc, nombre_art,
                    f"{jerarquia} - {nombre_inciso}".strip(" -"),
                    articulo_id, cve_ley
                ))

    # 3. Incisos directos
    for inciso in articulo_dict.get("incisos_directos", []):
        nombre_inciso  = f"Inciso {inciso.get('inciso')})"
        texto_inciso   = (inciso.get("texto", "") or inciso.get("texto_general", "")).strip()

        texto_combinado_inciso_dir = (
            f"{texto_general} {texto_inciso}".strip()
            if texto_general else texto_inciso
        )

        if texto_combinado_inciso_dir:
            chunks.append(crear_chunk(
                texto_combinado_inciso_dir, nombre_doc, nombre_art,
                f"{jerarquia} - {nombre_inciso}".strip(" -"),
                articulo_id, cve_ley
            ))

    return chunks


def deduplicar_chunks(chunks: list[dict]) -> list[dict]:
    """
    MEJORA: elimina chunks cuyo texto_busqueda sea idéntico.
    Conserva la primera aparición y descarta las repetidas.
    Devuelve la lista limpia y el conteo de duplicados eliminados.
    """
    vistos    = set()
    resultado = []
    for chunk in chunks:
        h = _hash_texto(chunk["texto_busqueda"])
        if h not in vistos:
            vistos.add(h)
            resultado.append(chunk)
    return resultado, len(chunks) - len(resultado)


# ==========================================
# PROCESAMIENTO POR LOTES
# ==========================================

def ejecutar_segmentacion(carpeta_entrada: str, carpeta_salida: str) -> None:
    """Lee todos los JSON estructurados y genera una lista plana de chunks."""
    ruta_entrada = Path(carpeta_entrada)
    ruta_salida  = Path(carpeta_salida)
    ruta_salida.mkdir(parents=True, exist_ok=True)

    archivos_json = list(ruta_entrada.glob('*.json'))
    print(f"Iniciando segmentación de {len(archivos_json)} documentos estructurados...")

    total_chunks    = 0
    total_duplicados = 0

    for archivo in archivos_json:
        nombre_doc     = archivo.stem.replace('_estructurado', '')
        cve_ley        = MAPA_DOCUMENTO_A_SLUG.get(nombre_doc, "")
        chunks_doc     = []

        with open(archivo, 'r', encoding='utf-8') as f:
            datos_estructurados = json.load(f)

        en_transitorios = False
        contador_trans = 0
        for idx, articulo in enumerate(datos_estructurados, start=1):
            articulo_id = ""
            art_Para_Chunk = dict(articulo)
            if CARGADOR_GRAFO_DISPONIBLE and cve_ley:
                if not en_transitorios and detectar_inicio_transitorios(articulo, cve_ley):
                    en_transitorios = True
                if en_transitorios:
                    contador_trans += 1
                nodo_norm = normalizar_registro_articulo(
                    articulo, cve_ley, f"ley:{cve_ley}", idx, en_transitorios, contador_trans
                )
                articulo_id = nodo_norm.id
                if nodo_norm.etiqueta_reconstruida:
                    art_Para_Chunk["articulo"] = f"Artículo {nodo_norm.numero}"
                    art_Para_Chunk["texto_general"] = nodo_norm.texto_general

            chunks_obtenidos = procesar_articulo_a_chunks(
                art_Para_Chunk, nombre_doc, articulo_id=articulo_id, cve_ley=cve_ley
            )
            chunks_doc.extend(chunks_obtenidos)

        # MEJORA: deduplicar antes de guardar
        chunks_doc, duplicados = deduplicar_chunks(chunks_doc)
        total_duplicados += duplicados

        archivo_salida = ruta_salida / f"{nombre_doc}_chunks.json"
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(chunks_doc, f, ensure_ascii=False, indent=4)

        total_chunks += len(chunks_doc)
        msg_dup = f" ({duplicados} duplicados eliminados)" if duplicados else ""
        print(f"  Segmentado: {archivo.name} -> {len(chunks_doc)} chunks{msg_dup}")

    print(f"\nSegmentación finalizada.")
    print(f"  Total chunks generados : {total_chunks}")
    print(f"  Duplicados eliminados  : {total_duplicados}")
    print("  Los textos están listos para vectorizar.")


if __name__ == "__main__":
    carpeta_estructurados = "../knowledge_structured"
    carpeta_chunks        = "../knowledge_chunks"

    ejecutar_segmentacion(carpeta_estructurados, carpeta_chunks)