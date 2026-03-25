import json
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer

def inicializar_base_vectorial(ruta_db):
    """
    Inicializa la conexion con ChromaDB y purga datos anteriores 
    para evitar fragmentos fantasma y duplicados.
    """
    cliente = chromadb.PersistentClient(path=ruta_db)
    
    # Intentamos borrar la coleccion si ya existe para empezar en limpio
    try:
        cliente.delete_collection(name="lexis_leyes_mexico")
        print("Coleccion anterior detectada y purgada con exito.")
    except Exception:
        pass # Si no existe, no pasa nada
        
    # Creamos una coleccion completamente nueva
    coleccion = cliente.create_collection(
        name="lexis_leyes_mexico",
        metadata={"hnsw:space": "cosine"}
    )
    return coleccion

def vectorizar_documentos(carpeta_chunks, coleccion, modelo_nombres):
    """
    Lee los chunks, genera los embeddings y los almacena en ChromaDB.
    """
    print("Cargando el modelo de embeddings (esto puede tardar la primera vez que se descarga)...")
    # Usamos un modelo multilingüe ligero y rápido, ideal para español
    modelo = SentenceTransformer(modelo_nombres)
    
    ruta_entrada = Path(carpeta_chunks)
    archivos_json = list(ruta_entrada.glob('*_chunks.json'))
    
    if not archivos_json:
        print("No se encontraron archivos de chunks en el directorio.")
        return

    print(f"Iniciando vectorizacion de {len(archivos_json)} archivos de chunks...")

    for archivo in archivos_json:
        print(f"Procesando: {archivo.name}")
        with open(archivo, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        textos = []
        metadatos = []
        ids = []
        
        for i, chunk in enumerate(chunks):
            # Preparar los datos que requiere ChromaDB
            texto = chunk.get("texto_busqueda", "")
            meta = chunk.get("metadatos", {})
            
            # Generar un ID unico para cada chunk
            doc_nombre = meta.get("documento", "doc")
            art_nombre = meta.get("articulo", f"art_{i}").replace(" ", "_")
            chunk_id = f"{doc_nombre}_{art_nombre}_{i}"
            
            textos.append(texto)
            metadatos.append(meta)
            ids.append(chunk_id)
            
        # Generar embeddings en lote (es mucho mas rapido que uno por uno)
        print(f"Generando embeddings para {len(textos)} fragmentos...")
        embeddings = modelo.encode(textos, show_progress_bar=True)
        
        # Insertar a la base de datos
        print("Guardando en ChromaDB...")
        coleccion.add(
            embeddings=embeddings.tolist(),
            documents=textos,
            metadatas=metadatos,
            ids=ids
        )
        
        print(f"Archivo {archivo.name} vectorizado y guardado con exito.\n")

if __name__ == "__main__":
    carpeta_chunks = "../knowledge_chunks"
    carpeta_db = "../lexis_vectordb" # Aqui vivira la base de datos de Chroma
    modelo_elegido = "paraphrase-multilingual-MiniLM-L12-v2"
    
    coleccion_lexis = inicializar_base_vectorial(carpeta_db)
    vectorizar_documentos(carpeta_chunks, coleccion_lexis, modelo_elegido)
    
    print("Proceso de vectorizacion completado. El motor de busqueda esta listo.")