#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interaccion.py - Asistente legal LexIA con Groq + RAG
- Busca fragmentos legales con ChromaDB + BM25
- Usa Groq (openai/gpt-oss-20b) para generar respuestas amables y precisas
- Lee el system prompt desde ../knowledge/Prompt.txt
"""

import sys
import os
import time
import threading
from dotenv import load_dotenv
from groq import Groq
from typing import List, Dict, Any

# Cargar variables de entorno desde Code/.env
load_dotenv()

# Añadir directorio actual al path para importar buscador
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from buscador import (
    inicializar_motores,
    busqueda_hibrida,
    TOP_K_DEFAULT,
    CARPETA_DB,
    MODELO_NOMBRE,
)
from indice_tematico import buscar_por_concepto, detectar_documento

try:
    from analizador_legal import (
        detectar_normativa,
        analizar_coherencia_consulta,
        generar_consulta_corregida,
    )
    ANALIZADOR_DISPONIBLE = True
except ImportError:
    ANALIZADOR_DISPONIBLE = False
    print("[AVISO] Módulo analizador_legal no disponible, usando detección básica")

# ============================================================
# CONFIGURACIÓN DE GROQ
# ============================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Error: No se encontró GROQ_API_KEY en el archivo .env")
    sys.exit(1)

MODELO_GROQ = "openai/gpt-oss-20b"   # verificar disponibilidad en Groq
TEMPERATURA = 0.2
MAX_TOKENS = 800
TOP_P = 0.9
TIMEOUT_SEGUNDOS = 120

# Límites de tamaño de prompt (Groq soporta mucho, pero por seguridad)
MAX_SYSTEM_CHARS = 4000
MAX_USER_CHARS = 8000
MAX_FRAGMENTOS = 3          # Usamos 3 fragmentos para más contexto
MAX_LEN_FRAGMENTO = 800

# ============================================================
# CARGA DEL SYSTEM PROMPT (desde archivo)
# ============================================================
def cargar_system_prompt(ruta: str = "../knowledge/Prompt.txt") -> str:
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read().strip()
            if not contenido:
                raise ValueError("El archivo Prompt.txt está vacío.")
            if len(contenido) > MAX_SYSTEM_CHARS:
                print(f"⚠️ System prompt muy largo ({len(contenido)} chars). Truncando a {MAX_SYSTEM_CHARS}.")
                contenido = contenido[:MAX_SYSTEM_CHARS]
            return contenido
    except FileNotFoundError:
        print(f"Error: No se encontró {ruta}")
        sys.exit(1)
    except Exception as e:
        print(f"Error al leer {ruta}: {e}")
        sys.exit(1)

# ============================================================
# CONSTRUCCIÓN DEL BLOQUE DE LEYES RECUPERADAS
# ============================================================
def construir_bloque_leyes(hits: List[Dict[str, Any]]) -> str:
    """Toma los hits más relevantes (ordenados de mayor a menor puntuación) y construye el bloque."""
    if not hits:
        return "No se encontraron fragmentos legales relevantes para esta consulta."
    
    # hits ya viene ordenado de mayor a menor relevancia (tras arreglo en buscador.py)
    hits_top = hits[:MAX_FRAGMENTOS] if len(hits) > MAX_FRAGMENTOS else hits
    
    bloque = ""
    for i, hit in enumerate(hits_top, 1):
        fuente = f"{hit['documento']} - {hit['articulo']} (Jerarquía: {hit['jerarquia']})"
        if hit.get('origen') == 'tematico':
            fuente += f" [Tema: {hit.get('tema', 'General')}]"
        texto = hit['texto'][:MAX_LEN_FRAGMENTO]
        texto = texto.encode('utf-8', errors='replace').decode('utf-8')
        bloque += f"--- Fragmento {i} ---\nFuente: {fuente}\n{texto}\n\n"
    return bloque.strip()

# ============================================================
# DETECCIÓN AUTOMÁTICA DE LEY (para filtrar sin que el usuario lo pida)
# ============================================================
def detectar_ley_sugerida(consulta: str, documentos_disponibles: List[str]) -> str | None:
    """Según palabras clave, sugiere un filtro de ley."""
    if ANALIZADOR_DISPONIBLE:
        documento, info = detectar_normativa(consulta, documentos_disponibles)
        return documento
    
    consulta_lower = consulta.lower()
    mapa = {
        "trabajo": ["Ley Trabajo", "Trabajo"],
        "laboral": ["Ley Trabajo"],
        "despido": ["Ley Trabajo"],
        "salario": ["Ley Trabajo"],
        "penal": ["Código Penal Tlaxcala", "Penal"],
        "delito": ["Código Penal Tlaxcala"],
        "robo": ["Código Penal Tlaxcala"],
        "civil": ["Codigo Civil Tlaxcala", "Civil"],
        "contrato": ["Codigo Civil Tlaxcala"],
        "constitucion": ["Constitucion"],
        "procedimiento civil": ["Procedimiento Civiles Tlaxcala"],
        "procedimiento penal": ["Procedimiento Penal Tlaxcala"],
    }
    for palabra, posibles in mapa.items():
        if palabra in consulta_lower:
            for doc in documentos_disponibles:
                for posible in posibles:
                    if posible.lower() in doc.lower():
                        return doc
    return None

# ============================================================
# ANIMACIÓN DE ESPERA (hilo independiente)
# ============================================================
def animar_mensaje(parar_evento):
    while not parar_evento.is_set():
        for puntos in [".", "..", "...", ""]:
            sys.stdout.write(f"\r⏳ Lexis está consultando la ley{puntos}   ")
            sys.stdout.flush()
            time.sleep(0.6)
            if parar_evento.is_set():
                break
    sys.stdout.write("\r✓ Respuesta lista\n")

# ============================================================
# LLAMADA A GROQ (con animación y timeout)
# ============================================================
def llamar_groq(system_prompt: str, user_prompt: str) -> str:
    # Sanitizar entradas
    user_prompt = user_prompt.encode('ascii', errors='ignore').decode('ascii')
    system_prompt = system_prompt.encode('ascii', errors='ignore').decode('ascii')
    
    # Truncar si exceden límites
    if len(system_prompt) > MAX_SYSTEM_CHARS:
        system_prompt = system_prompt[:MAX_SYSTEM_CHARS]
    if len(user_prompt) > MAX_USER_CHARS:
        user_prompt = user_prompt[:MAX_USER_CHARS]
    
    print(f"📊 Tamaño system: {len(system_prompt)} chars | user: {len(user_prompt)} chars")
    
    cliente = Groq(api_key=GROQ_API_KEY)
    
    # Iniciar animación
    parar = threading.Event()
    hilo = threading.Thread(target=animar_mensaje, args=(parar,))
    hilo.start()
    
    try:
        respuesta = cliente.chat.completions.create(
            model=MODELO_GROQ,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=TEMPERATURA,
            max_tokens=MAX_TOKENS,
            top_p=TOP_P,
            timeout=TIMEOUT_SEGUNDOS
        )
        parar.set()
        hilo.join()
        return respuesta.choices[0].message.content
    except Exception as e:
        parar.set()
        hilo.join()
        return f"Error al llamar a Groq: {e}"

# ============================================================
# BUCLE PRINCIPAL DE INTERACCIÓN
# ============================================================
def main():
    print("=" * 70)
    print("LexIA - Tu abogado amable (con Groq + RAG)")
    print(f"Modelo: {MODELO_GROQ}")
    print("Escribe '/salir' para terminar")
    print("=" * 70)

    # Cargar system prompt desde archivo
    system_prompt = cargar_system_prompt()
    print(f"[OK] System prompt cargado ({len(system_prompt)} caracteres)")

    # Inicializar motores de búsqueda (ChromaDB, BM25, modelo semántico)
    print("Inicializando base de datos legal...")
    try:
        (coleccion,
         motor_bm25,
         modelo_semantico,
         diccionario_textos,
         diccionario_metadatos,
         documentos_disponibles,
         jerarquias_disponibles) = inicializar_motores(CARPETA_DB, MODELO_NOMBRE)
        print("[OK] Base de datos conectada")
    except Exception as e:
        print(f"Error al inicializar buscador: {e}")
        sys.exit(1)

    print("\nConsejos:")
    print("  - Puedes filtrar manualmente por ley: /filtro ley:trabajo")
    print("  - O usar /filtro limpiar para quitar filtros")
    print("  - Lexis también intentará detectar automáticamente la ley que necesitas")
    print("-" * 70)

    filtro_doc_actual = None
    filtro_jer_actual = None
    
    # Historial de conversación
    historial_conversacion = []
    info_usuario = {"nombre": None}
    
    # Contexto de la conversación
    contexto_conversacion = {
        "tema_legal": None,
        "situacion_usuario": None,
        "documento_actual": None,
    }

    while True:
        consulta_raw = input("\n📝 Tu consulta: ").strip()
        if not consulta_raw:
            continue
        
        # Comandos del sistema
        if consulta_raw.lower() == "/salir":
            print("¡Hasta luego! Espero haberte ayudado.")
            break
        
        if consulta_raw.lower().startswith("/filtro"):
            partes = consulta_raw.split()
            if len(partes) < 2:
                print("  Uso: /filtro ley:nombre  o  /filtro limpiar")
                continue
            comando = partes[1].lower()
            if comando == "limpiar":
                filtro_doc_actual = None
                filtro_jer_actual = None
                print("  [Filtros eliminados]")
            elif comando.startswith("ley:"):
                valor = comando[4:]
                encontrado = None
                for doc in documentos_disponibles:
                    if valor.lower() in doc.lower():
                        encontrado = doc
                        break
                if encontrado:
                    filtro_doc_actual = encontrado
                    print(f"  [Filtro activo: solo {filtro_doc_actual}]")
                else:
                    print(f"  Ley '{valor}' no encontrada. Opciones: {', '.join(documentos_disponibles)}")
            else:
                print("  Formato no reconocido.")
            continue
        
        # Sanitizar consulta (eliminar caracteres raros)
        consulta_limpia = consulta_raw.encode('ascii', errors='ignore').decode('ascii')
        
        # Detectar nombre del usuario en la consulta
        import re
        patrones_nombre = [
            r'me llamo\s+(\w+)',
            r'mi nombre es\s+(\w+)',
            r'soy\s+(\w+)',
            r'^hola\s+soy\s+(\w+)',
        ]
        for patron in patrones_nombre:
            match = re.search(patron, consulta_limpia.lower())
            if match:
                info_usuario["nombre"] = match.group(1).capitalize()
                print(f"  [INFO] Encantado de conocerte, {info_usuario['nombre']}!")
        
        # --- ANÁLISIS DE COHERENCIA DE LA CONSULTA ---
        if ANALIZADOR_DISPONIBLE:
            es_coherente, sugerencias = analizar_coherencia_consulta(consulta_limpia)
            if not es_coherente:
                print(f"  ⚠️ {sugerencias[0]}")
                consulta_corregida = generar_consulta_corregida(consulta_limpia)
                if consulta_corregida != consulta_limpia:
                    consulta_limpia = consulta_corregida
                    print(f"  📝 Consulta interpretada como: \"{consulta_limpia}\"")
            elif any('vaga' in s.lower() for s in sugerencias):
                print(f"  💡 {sugerencias[0]}")
        
        # --- DETECCIÓN AUTOMÁTICA DE FILTRO (si no hay filtro manual) ---
        filtro_a_usar = filtro_doc_actual
        if filtro_a_usar is None:
            sugerida = detectar_ley_sugerida(consulta_limpia, documentos_disponibles)
            if sugerida:
                print(f"  🔍 Detecté que tu consulta se relaciona con '{sugerida}'. Aplicando filtro automático.")
                filtro_a_usar = sugerida
        
        # Búsqueda RAG
        print("\n🔍 Buscando leyes que apliquen a tu caso...")
        try:
            hits = busqueda_hibrida(
                consulta=consulta_limpia,
                coleccion=coleccion,
                motor_bm25=motor_bm25,
                modelo=modelo_semantico,
                diccionario_textos=diccionario_textos,
                diccionario_metadatos=diccionario_metadatos,
                top_k=TOP_K_DEFAULT,          # Recuperamos muchos (15) y luego seleccionamos los mejores
                filtro_documento=filtro_a_usar,
                filtro_jerarquia=filtro_jer_actual,
            )
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            continue
        
        # Fallback: verificar si los resultados son relevantes
        def verificar_relevancia(hits, consulta):
            """Verifica si los primeros resultados contienen conceptos legales relevantes."""
            if not hits:
                return False
            
            consulta_lower = consulta.lower()
            
            # Extraer conceptos clave de la consulta
            conceptos_clave = []
            if any(p in consulta_lower for p in ['hora extra', 'horas extra', 'tiempo extra']):
                conceptos_clave.extend(['hora', 'extra', 'pago', 'retribu'])
            if any(p in consulta_lower for p in ['despido', 'despedir', 'despedirme', 'despidieron']):
                conceptos_clave.extend(['despido', 'despido', 'rescisión', 'indemniz'])
            if any(p in consulta_lower for p in ['renuncia', 'renunciar', 'renuncie']):
                conceptos_clave.extend(['renuncia', 'renunci', 'nul'])
            
            if not conceptos_clave:
                return True  # No hay conceptos claros, asumir OK
            
            # Verificar si AL MENOS UNO de los top 3 contiene un concepto clave
            for h in hits[:3]:
                texto = h['texto'].lower()
                if any(c in texto for c in conceptos_clave):
                    return True
            
            return False  # Ningún resultado relevante
        
        # Usar fallback si no hay resultados o no son relevantes
        if not hits or len(hits) < 3 or not verificar_relevancia(hits, consulta_limpia):
            print("  [INFO] Buscando en índice temático...")
            
            # Detectar qué normativa buscar
            documento_detectado = detectar_documento(consulta_limpia)
            if documento_detectado:
                print(f"  [INFO] Documento detectado: {documento_detectado}")
            
            resultados_tematicos = buscar_por_concepto(consulta_limpia, documento_detectado)
            
            if resultados_tematicos:
                print(f"  [INFO] Encontré {len(resultados_tematicos)} artículos relacionados en el índice temático.")
                # Obtener artículos de ChromaDB basados en el índice temático
                hits_fallback = []
                articulos_buscados = set()
                doc_buscado = documento_detectado or filtro_a_usar
                
                for rt in resultados_tematicos[:15]:
                    art_num = rt['articulo'].replace('.-', '-').replace('.', '').replace('ARTICULO ', 'Artículo ')
                    art_normalizado = art_num.lower().replace(' ', '').replace('artículo', 'articulo')
                    
                    if art_num in articulos_buscados:
                        continue
                    
                    # Buscar en los diccionarios locales
                    for doc_id, meta in diccionario_metadatos.items():
                        # Filtrar por documento si hay uno detectado
                        if doc_buscado:
                            doc_norm = meta.get('documento', '').lower()
                            if doc_buscado.lower() not in doc_norm and doc_norm not in doc_buscado.lower():
                                continue
                        
                        art_meta = meta.get('articulo', '').replace('.-', '-').replace('.', '')
                        art_meta_norm = art_meta.lower().replace(' ', '').replace('artículo', 'articulo')
                        
                        if art_normalizado in art_meta_norm or art_meta_norm in art_normalizado:
                            hits_fallback.append({
                                'id': doc_id,
                                'texto': diccionario_textos.get(doc_id, ''),
                                'articulo': meta.get('articulo', ''),
                                'documento': meta.get('documento', ''),
                                'jerarquia': meta.get('jerarquia', ''),
                                'score': 1.0,
                                'origen': 'tematico',
                                'tema': rt.get('tema', '')
                            })
                            articulos_buscados.add(art_num)
                            break
                if hits_fallback:
                    hits = hits_fallback
        
        if not hits:
            print("  No encontré leyes relacionadas. ¿Podrías darme más detalles?")
            continue
        
        # Actualizar contexto de la conversación
        contexto_conversacion["documento_actual"] = filtro_a_usar
        
        # Extraer tema legal de la consulta para mantener contexto
        consulta_lower = consulta_limpia.lower()
        temas_legales = {
            "horas extras": "horas extras y pago overtime",
            "despido": "despido y terminación laboral",
            "renuncia": "renuncia y rescisión",
            "salario": "salario y pago",
            "vacaciones": "vacaciones y prima vacacional",
            "aguinaldo": "aguinaldo",
            "contrato": "contrato laboral",
            "indemnización": "indemnización",
            "robo": "robo y hurto",
            "lesión": "lesiones",
            "violencia": "violencia",
            "divorcio": "divorcio",
            "matrimonio": "matrimonio",
            "herencia": "herencia",
            "propiedad": "propiedad",
        }
        for palabra, tema in temas_legales.items():
            if palabra in consulta_lower:
                contexto_conversacion["tema_legal"] = tema
                break
        
        # Construimos bloque con los primeros MAX_FRAGMENTOS
        leyes_bloque = construir_bloque_leyes(hits)
        print(f"  Encontré {len(hits)} fragmento(s). Usando los {MAX_FRAGMENTOS} más relevantes.")
        
        # Armar el prompt del usuario en el formato esperado
        contexto_historico = ""
        if historial_conversacion:
            contexto_historico = "[HISTORIAL DE LA CONVERSACIÓN]\n"
            for i, (pregunta, contexto_info) in enumerate(historial_conversacion[-3:], 1):
                contexto_historico += f"Interacción {i}:\nUsuario: {pregunta}\nContexto: {contexto_info}\n"
            contexto_historico += "\n"
        
        # Construir contexto actual
        contexto_actual = ""
        if info_usuario["nombre"]:
            contexto_actual += f"El usuario se llama {info_usuario['nombre']}. "
        if contexto_conversacion["tema_legal"]:
            contexto_actual += f"Actualmente estamos hablando sobre: {contexto_conversacion['tema_legal']}. "
        if contexto_conversacion["documento_actual"]:
            contexto_actual += f"La normativa aplicable es: {contexto_conversacion['documento_actual']}. "
        
        user_prompt = f"""{contexto_actual}{contexto_historico}[CONSULTA ACTUAL DEL USUARIO]
{consulta_limpia}

[NOTA: Esta es una continuación de la conversación. Considera el contexto anterior.]

[LEYES RECUPERADAS]
{leyes_bloque}"""
        
        print("🤖 Lexis está preparando su respuesta...")
        respuesta = llamar_groq(system_prompt, user_prompt)
        
        # Guardar en historial con contexto
        contexto_info = f"Tema: {contexto_conversacion.get('tema_legal', 'general')} | Ley: {filtro_a_usar or 'automático'}"
        historial_conversacion.append((consulta_limpia, contexto_info))
        
        # Limitar historial a últimos 5 intercambios
        if len(historial_conversacion) > 5:
            historial_conversacion = historial_conversacion[-5:]
        
        print("\n" + respuesta)
        print("\n" + "-" * 70)

if __name__ == "__main__":
    main()