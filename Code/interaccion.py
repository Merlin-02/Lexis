#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interaccion.py - Asistente legal LexIA con RAG + Ollama.
Versión con keep_alive=0, reintentos, sanitización de entrada y lenguaje amigable.
"""

import sys
import os
import requests
import json
import time
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from buscador import (
    inicializar_motores,
    busqueda_hibrida,
    TOP_K_DEFAULT,
    CARPETA_DB,
    MODELO_NOMBRE,
)

# ============================================================
# CONFIGURACIÓN DE OLLAMA
# ============================================================
OLLAMA_URL = "http://localhost:11434/api/generate"
# Cambia por el modelo que tengas (ej. "llama3.1:8b", "phi3:mini", "tinyllama")
MODELO_LLM = "llama3.1:8b"

TEMPERATURA = 0.2            # Un poco más alta para respuestas naturales
TOP_P = 0.9
REPEAT_PENALTY = 1.1
MAX_TOKENS = 800             # Respuestas más completas
NUM_CTX = 4096               # Ventana de contexto
TIMEOUT = 600
KEEP_ALIVE = 0               # Descarga el modelo después de cada respuesta (libera memoria)

# Límites de caracteres
MAX_SYSTEM_CHARS = 4000      # Suficiente para el nuevo prompt amigable
MAX_USER_CHARS = 3500
MAX_FRAGMENTOS = 1
MAX_LEN_FRAGMENTO = 900

# ============================================================
# CARGA DEL SYSTEM PROMPT
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
# CONSTRUCCIÓN DEL BLOQUE DE LEYES (LIMITADO Y LIMPIO)
# ============================================================
def construir_bloque_leyes(hits: List[Dict[str, Any]]) -> str:
    if not hits:
        return "No se encontraron fragmentos legales relevantes para esta consulta."
    
    # hits viene ordenado de menor a mayor relevancia; tomamos los últimos (más relevantes)
    hits_top = hits[-MAX_FRAGMENTOS:] if len(hits) > MAX_FRAGMENTOS else hits
    
    bloque = ""
    for i, hit in enumerate(hits_top, 1):
        fuente = f"{hit['documento']} - {hit['articulo']}"
        texto = hit['texto'][:MAX_LEN_FRAGMENTO]
        # Limpiar caracteres extraños
        texto = texto.encode('utf-8', errors='replace').decode('utf-8')
        bloque += f"--- Fragmento {i} ---\nFuente: {fuente}\n{texto}\n\n"
    return bloque.strip()

# ============================================================
# LLAMADA A OLLAMA CON REINTENTOS Y KEEP_ALIVE=0
# ============================================================
def llamar_ollama(system_prompt: str, user_prompt: str) -> str:
    # Sanitizar entradas
    user_prompt = user_prompt.encode('ascii', errors='ignore').decode('ascii')
    system_prompt = system_prompt.encode('ascii', errors='ignore').decode('ascii')
    
    # Truncar por seguridad
    if len(system_prompt) > MAX_SYSTEM_CHARS:
        system_prompt = system_prompt[:MAX_SYSTEM_CHARS]
    if len(user_prompt) > MAX_USER_CHARS:
        user_prompt = user_prompt[:MAX_USER_CHARS]
    
    payload = {
        "model": "llama3.1:8b",
        "system": system_prompt,
        "prompt": user_prompt,
        "temperature": TEMPERATURA,
        "top_p": TOP_P,
        "repeat_penalty": REPEAT_PENALTY,
        "num_predict": MAX_TOKENS,
        "num_ctx": NUM_CTX,
        "keep_alive": KEEP_ALIVE,   # CLAVE: evita acumulación de memoria
        "stream": False,
    }
    
    print(f"📊 Tamaño system: {len(system_prompt)} chars | user: {len(user_prompt)} chars")
    
    for intento in range(3):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json().get("response", "Sin respuesta del modelo.")
            else:
                # Si es 500, reintentamos
                if response.status_code == 500 and intento < 2:
                    print(f"  [Reintento {intento+1}/3 por error 500]")
                    time.sleep(2 ** intento)  # espera exponencial
                    continue
                else:
                    return f"Error HTTP {response.status_code}: {response.text[:200]}"
        except requests.exceptions.Timeout:
            if intento < 2:
                print(f"  [Timeout, reintento {intento+1}/3]")
                time.sleep(2)
                continue
            return "Error: Tiempo de espera agotado."
        except requests.exceptions.RequestException as e:
            if intento < 2:
                print(f"  [Error de conexión, reintento {intento+1}/3]")
                time.sleep(2)
                continue
            return f"Error de conexión: {e}"
    
    return "No se pudo obtener respuesta tras varios intentos."

# ============================================================
# BUCLE PRINCIPAL
# ============================================================
def main():
    print("=" * 70)
    print("LexIA - Tu abogado amable (con lenguaje sencillo)")
    print("Escribe '/salir' para terminar")
    print("=" * 70)

    # Cargar system prompt
    system_prompt = cargar_system_prompt()
    print(f"[OK] System prompt cargado ({len(system_prompt)} caracteres)")

    # Inicializar buscador
    print("Inicializando base de datos legal...")
    try:
        (coleccion,
         motor_bm25,
         modelo,
         diccionario_textos,
         diccionario_metadatos,
         documentos_disponibles,
         jerarquias_disponibles) = inicializar_motores(CARPETA_DB, MODELO_NOMBRE)
        print("[OK] Base de datos conectada")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\nConsejo: puedes filtrar por ley escribiendo '/filtro ley:nombre'")
    print("Ejemplo: /filtro ley:trabajo")
    print("-" * 70)

    filtro_doc_actual = None
    filtro_jer_actual = None

    while True:
        consulta_raw = input("\n📝 Tu consulta: ").strip()
        if not consulta_raw:
            continue
        
        # Comandos
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
        
        # Sanitizar consulta
        consulta_limpia = consulta_raw.encode('ascii', errors='ignore').decode('ascii')
        
        # Búsqueda
        print("\n🔍 Buscando leyes que apliquen a tu caso...")
        try:
            hits = busqueda_hibrida(
                consulta=consulta_limpia,
                coleccion=coleccion,
                motor_bm25=motor_bm25,
                modelo=modelo,
                diccionario_textos=diccionario_textos,
                diccionario_metadatos=diccionario_metadatos,
                top_k=MAX_FRAGMENTOS * 2,
                filtro_documento=filtro_doc_actual,
                filtro_jerarquia=filtro_jer_actual,
            )
        except Exception as e:
            print(f"Error en búsqueda: {e}")
            continue
        
        if not hits:
            print("  No encontré leyes relacionadas. ¿Podrías darme más detalles?")
            continue
        
        # Construir bloque de leyes
        leyes_bloque = construir_bloque_leyes(hits)
        print(f"  Encontré {len(hits)} fragmento(s). Usando el más relevante.")
        
        user_prompt = f"""[CONSULTA DEL USUARIO]
{consulta_limpia}

[LEYES RECUPERADAS]
{leyes_bloque}"""
        
        print("🤖 Pensando en la mejor respuesta para ti...")
        respuesta = llamar_ollama(system_prompt, user_prompt)
        print("\n" + respuesta)
        print("\n" + "-" * 70)

if __name__ == "__main__":
    main()