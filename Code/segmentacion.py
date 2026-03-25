import json
from pathlib import Path

def crear_chunk(texto, documento, articulo, jerarquia=""):
    """Crea un diccionario estandarizado para un chunk de texto."""
    prefijo = f"{articulo}"
    if jerarquia:
        prefijo += f" - {jerarquia}"
        
    texto_enriquecido = f"[{documento}] {prefijo}: {texto}"
    
    return {
        "texto_busqueda": texto_enriquecido,
        "metadatos": {
            "documento": documento,
            "articulo": articulo,
            "jerarquia": jerarquia
        }
    }

def procesar_articulo_a_chunks(articulo_dict, nombre_doc):
    """
    Desglosa un articulo estructurado en multiples chunks,
    arrastrando el texto introductorio hacia las fracciones e incisos.
    """
    chunks = []
    nombre_art = articulo_dict.get("articulo", "Articulo Desconocido")
    
    texto_general = articulo_dict.get("texto_general", "").strip()
    
    # 1. Chunk del texto general solo (como referencia)
    if texto_general:
        chunks.append(crear_chunk(texto_general, nombre_doc, nombre_art))
        
    # 2. Fracciones
    for fraccion in articulo_dict.get("fracciones", []):
        nombre_fraccion = f"Fraccion {fraccion.get('fraccion')}"
        texto_fraccion = fraccion.get("texto_general", "").strip()
        
        # INYECCION DE CONTEXTO: Unimos la introduccion con la fraccion
        texto_combinado_fraccion = texto_fraccion
        if texto_general:
            texto_combinado_fraccion = f"{texto_general} {texto_fraccion}"
            
        if texto_combinado_fraccion:
            chunks.append(crear_chunk(texto_combinado_fraccion, nombre_doc, nombre_art, nombre_fraccion))
            
        # Incisos dentro de la fraccion
        for inciso in fraccion.get("incisos", []):
            nombre_inciso = f"{nombre_fraccion} - Inciso {inciso.get('inciso')})"
            texto_inciso = inciso.get("texto_general", "").strip()
            
            # INYECCION DE CONTEXTO: Unimos introduccion + fraccion + inciso
            texto_combinado_inciso = texto_inciso
            if texto_general or texto_fraccion:
                texto_combinado_inciso = f"{texto_general} {texto_fraccion} {texto_inciso}".strip()
                
            if texto_combinado_inciso:
                chunks.append(crear_chunk(texto_combinado_inciso, nombre_doc, nombre_art, nombre_inciso))
                
    # 3. Incisos directos
    for inciso in articulo_dict.get("incisos_directos", []):
        nombre_inciso = f"Inciso {inciso.get('inciso')})"
        texto_inciso = inciso.get("texto_general", "").strip()
        
        # INYECCION DE CONTEXTO: Unimos introduccion con inciso directo
        texto_combinado_inciso_dir = texto_inciso
        if texto_general:
            texto_combinado_inciso_dir = f"{texto_general} {texto_inciso}"
            
        if texto_combinado_inciso_dir:
            chunks.append(crear_chunk(texto_combinado_inciso_dir, nombre_doc, nombre_art, nombre_inciso))
            
    return chunks

def ejecutar_segmentacion(carpeta_entrada, carpeta_salida):
    """Lee todos los JSON estructurados y genera una lista plana de chunks."""
    ruta_entrada = Path(carpeta_entrada)
    ruta_salida = Path(carpeta_salida)
    ruta_salida.mkdir(parents=True, exist_ok=True)
    
    archivos_json = list(ruta_entrada.glob('*.json'))
    print(f"Iniciando segmentacion de {len(archivos_json)} documentos estructurados...")
    
    for archivo in archivos_json:
        nombre_doc = archivo.stem.replace('_estructurado', '')
        chunks_documento = []
        
        with open(archivo, 'r', encoding='utf-8') as f:
            datos_estructurados = json.load(f)
            
        for articulo in datos_estructurados:
            chunks_obtenidos = procesar_articulo_a_chunks(articulo, nombre_doc)
            chunks_documento.extend(chunks_obtenidos)
            
        archivo_salida = ruta_salida / f"{nombre_doc}_chunks.json"
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(chunks_documento, f, ensure_ascii=False, indent=4)
            
        print(f"Segmentado: {archivo.name} -> {len(chunks_documento)} chunks generados.")

if __name__ == "__main__":
    carpeta_estructurados = "../knowledge_structured"
    carpeta_chunks = "../knowledge_chunks"
    
    ejecutar_segmentacion(carpeta_estructurados, carpeta_chunks)
    print("\nSegmentacion finalizada. Los textos estan listos para vectorizar.")