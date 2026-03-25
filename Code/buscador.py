import string
import warnings
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# Ignorar advertencias menores
warnings.filterwarnings("ignore")

def preprocesar_texto(texto):
    """Convierte a minusculas y elimina puntuacion para el motor lexico."""
    texto = texto.lower()
    texto = texto.translate(str.maketrans('', '', string.punctuation))
    return texto.split()

def inicializar_motores(ruta_db, modelo_nombres):
    """Inicia ChromaDB (Semantico) y BM25 (Lexico)."""
    print("Conectando con la base de datos vectorial de LEXIS...")
    cliente = chromadb.PersistentClient(path=ruta_db)
    
    try:
        coleccion = cliente.get_collection(name="lexis_leyes_mexico")
    except ValueError:
        raise Exception("No se encontro la coleccion. Ejecuta vectorizacion.py primero.")
        
    print("Cargando el motor semantico...")
    modelo = SentenceTransformer(modelo_nombres)
    
    print("Construyendo el indice lexico (BM25) en memoria...")
    # Extraemos todos los documentos de ChromaDB para asegurar sincronizacion perfecta
    datos_db = coleccion.get()
    ids_documentos = datos_db['ids']
    textos_documentos = datos_db['documents']
    
    # Preparamos el corpus para BM25
    corpus_tokenizado = [preprocesar_texto(doc) for doc in textos_documentos]
    motor_bm25 = BM25Okapi(corpus_tokenizado)
    
    # Diccionario para recuperar el texto final usando el ID
    diccionario_textos = {id_doc: texto for id_doc, texto in zip(ids_documentos, textos_documentos)}
    
    return coleccion, motor_bm25, modelo, diccionario_textos

def busqueda_hibrida(consulta, coleccion, motor_bm25, modelo, diccionario_textos, top_k=5):
    """
    Ejecuta ambas busquedas y fusiona los resultados usando Reciprocal Rank Fusion (RRF).
    """
    # ---------------------------------------------------------
    # 1. Busqueda Semantica (ChromaDB)
    # ---------------------------------------------------------
    vector_consulta = modelo.encode([consulta]).tolist()
    resultados_semanticos = coleccion.query(
        query_embeddings=vector_consulta,
        n_results=top_k
    )
    ids_semanticos = resultados_semanticos['ids'][0]
    
    # ---------------------------------------------------------
    # 2. Busqueda Lexica (BM25)
    # ---------------------------------------------------------
    consulta_tokenizada = preprocesar_texto(consulta)
    puntuaciones_bm25 = motor_bm25.get_scores(consulta_tokenizada)
    
    # Emparejamos los IDs con sus puntuaciones y ordenamos de mayor a menor
    ids_con_puntuacion = list(zip(list(diccionario_textos.keys()), puntuaciones_bm25))
    ids_con_puntuacion.sort(key=lambda x: x[1], reverse=True)
    ids_lexicos = [item[0] for item in ids_con_puntuacion[:top_k]]
    
    # ---------------------------------------------------------
    # 3. Fusion de Resultados (RRF)
    # ---------------------------------------------------------
    # RRF penaliza rangos bajos y premia documentos que aparecen en ambas listas
    k_rrf = 60
    puntuaciones_rrf = {}
    
    for rango, doc_id in enumerate(ids_semanticos):
        puntuaciones_rrf[doc_id] = puntuaciones_rrf.get(doc_id, 0) + 1 / (k_rrf + rango + 1)
        
    for rango, doc_id in enumerate(ids_lexicos):
        puntuaciones_rrf[doc_id] = puntuaciones_rrf.get(doc_id, 0) + 1 / (k_rrf + rango + 1)
        
    # Ordenamos los IDs finales basados en la puntuacion RRF combinada
    ids_finales = sorted(puntuaciones_rrf.keys(), key=lambda x: puntuaciones_rrf[x], reverse=True)[:top_k]
    
    # Construimos la lista de resultados para mostrar
    resultados_finales = []
    for doc_id in ids_finales:
        resultados_finales.append({
            "id": doc_id,
            "texto": diccionario_textos[doc_id],
            "puntuacion_rrf": puntuaciones_rrf[doc_id]
        })
        
    return resultados_finales

if __name__ == "__main__":
    carpeta_db = "../lexis_vectordb"
    modelo_elegido = "paraphrase-multilingual-MiniLM-L12-v2"
    
    try:
        col_lexis, bm25_lexis, mod_lexis, dicc_textos = inicializar_motores(carpeta_db, modelo_elegido)
        
        print("\n" + "="*60)
        print("LEXIS MOTOR DE BUSQUEDA HIBRIDO ACTIVO")
        print("="*60)
        print("Escribe tu consulta. Escribe 'salir' para terminar.\n")
        
        while True:
            pregunta = input("Ciudadano: ")
            
            if pregunta.lower() in ['salir', 'exit', 'quit']:
                print("\nCerrando LEXIS. Hasta pronto.")
                break
                
            if not pregunta.strip():
                continue
                
            print("Ejecutando busqueda semantica y lexica...")
            hits = busqueda_hibrida(pregunta, col_lexis, bm25_lexis, mod_lexis, dicc_textos, top_k=15)
            
            print("\n" + "-"*60)
            print("ARTICULOS RECUPERADOS (Ordenados por relevancia hibrida):")
            print("-" * 60)
            
            for i, hit in enumerate(hits):
                print(f"[{i+1}] (Puntuacion RRF: {hit['puntuacion_rrf']:.4f})")
                print(f"{hit['texto']}\n")
                
            print("-" * 60 + "\n")
            
    except Exception as e:
        print(f"\nError al iniciar LEXIS: {e}")