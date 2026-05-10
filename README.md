# LEXIS: Sistema de Asistencia Legal Automatizada con IA ⚖️🤖

![Status](https://img.shields.io/badge/Status-En%20Desarrollo-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![NLP](https://img.shields.io/badge/AI-Procesamiento_de_Lenguaje_Natural-green)

## 📖 Descripción del Proyecto

El presente proyecto, denominado **LEXIS**, propone el desarrollo de un sistema de asistencia legal automatizada impulsado por inteligencia artificial. Concebido bajo los principios de accesibilidad, versatilidad y eficiencia, el sistema está capacitado para abordar problemáticas jurídicas recurrentes en los ámbitos **penal, civil y laboral** del Estado de Tlaxcala y legislación federal mexicana.

La finalidad de LEXIS es democratizar el acceso a la información jurídica, reduciendo significativamente las brechas económicas, geográficas y de conocimiento, para dotar a la población de respuestas precisas, de fácil comprensión y en una etapa de primer contacto.

## 🎯 Objetivos

### Objetivo General
Desarrollar e implementar un sistema de asistencia legal automatizada basado en inteligencia artificial, con el propósito de proporcionar orientación jurídica accesible, precisa y de primer contacto, contribuyendo así a la reducción de las brechas en el acceso a la justicia.

### Objetivos Específicos
1. **Sistematización Legal:** Conformar un corpus legal especializado estructurando la normativa y jurisprudencia (con enfoque en la legislación mexicana vigente) para asegurar la precisión y actualización de la información.
2. **Desarrollo del Modelo:** Integrar un modelo de Inteligencia Artificial basado en algoritmos de Procesamiento de Lenguaje Natural (PLN), capaz de interpretar consultas en lenguaje cotidiano y generar respuestas jurídicas coherentes.
3. **Plataforma Accesible:** Implementar y validar una plataforma digital intuitiva, diseñada para mitigar las barreras de entrada técnicas y económicas para los usuarios.

## ⚙️ Arquitectura y Tecnologías

- **Lenguaje Core:** Python 3.8+
- **Base de Datos Vectorial:** ChromaDB (embeddings multilingual)
- **Búsqueda Híbrida:** BM25 + Similitud semántica (Sentence Transformers)
- **Modelo de Embeddings:** paraphrase-multilingual-mpnet-base-v2
- **Generación de Respuestas:** Groq API (modelos LLM)
- **Preprocesamiento:** spaCy, NLTK
- **Frontend:** Terminal interactiva / Streamlit (en desarrollo)

## 📂 Estructura del Repositorio

```text
LEXIS/
 │
 ├── Code/                      # Código fuente principal
 │   ├── preparacion.py        # 1️⃣ Preprocesamiento de documentos
 │   ├── segmentacion.py      # 2️⃣ Segmentación en chunks
 │   ├── vectorizacion.py     # 3️⃣ Indexación en ChromaDB
 │   ├── buscador.py          # Motor de búsqueda híbrida
 │   ├── interaccion.py       # Interfaz con Groq para respuestas
 │   ├── analizador_legal.py  # Detector de áreas legales
 │   ├── indice_tematico.py   # Índice temático manual (fallback)
 │   ├── mejoras.py          # Funciones adicionales (caching, re-rankeo)
 │   └── test_unidades.py    # Tests unitarios
 │
 ├── knowledge/               # Documentos legales fuente (PDF, DOCX)
 ├── knowledge_chunks/        # Documentos segmentados en chunks
 ├── knowledge_structured/     # Documentos estructurados en JSON
 ├── lexis_vectordb/         # Base de datos vectorial (ChromaDB)
 │   ├── cache/              # Cache del índice BM25
 │   └── logs/               # Logs de búsquedas
 │
 ├── Documentacion/           # Protocolos y documentación
 └── README.md                # Este archivo
```

## 🔄 Orden de Ejecución

### Pipeline de Preparación de Datos (solo una vez o al actualizar leyes):

```bash
cd Code
python preparacion.py      # 1️⃣ Extrae artículos de PDFs/DOCX → JSON estructurado
python segmentacion.py    # 2️⃣ Divide artículos en chunks manejables
python vectorizacion.py   # 3️⃣ Crea embeddings y guarda en ChromaDB
```

### Ejecución del Sistema:

```bash
cd Code
python interaccion.py     # Inicia el asistente interactivo
```

## 📝 Descripción de Archivos

### Fase de Preparación (Pipeline):

| Archivo | Descripción | Orden |
|---------|-------------|-------|
| **preparacion.py** | Extrae y estructura artículos de documentos legales (PDF/DOCX). Convierte textos en JSON con metadatos (artículo, capítulo, fracción). | 1º |
| **segmentacion.py** | Divide los artículos estructurados en chunks (fragmentos) de tamaño adecuado para búsqueda. Elimina duplicados. | 2º |
| **vectorizacion.py** | Convierte los chunks en embeddings usando Sentence Transformers y los almacena en ChromaDB. Crea el índice de búsqueda. | 3º |

### Fase de Búsqueda y Respuesta:

| Archivo | Descripción |
|---------|-------------|
| **buscador.py** | Motor de búsqueda híbrida que combina BM25 (búsqueda léxica) + similitud semántica (Sentence Transformers). Incluye rerankeo y filtros por normativa. |
| **interaccion.py** | Interfaz interactiva del sistema. Recibe consultas del usuario, busca leyes relevantes y genera respuestas usando Groq API. |
| **analizador_legal.py** | Detector de áreas legales (laboral, penal, civil, etc.). Analiza consultas para determinar qué normativa aplicar automáticamente. |
| **indice_tematico.py** | Índice temático manual con artículos clave de cada normativa. Funciona como fallback cuando la búsqueda híbrida no encuentra suficientes resultados. |
| **mejoras.py** | Módulo de optimizaciones: cacheo de BM25, sinónimos, logging de búsquedas, análisis de tipo de consulta. |
| **test_unidades.py** | Tests unitarios para validar el funcionamiento del sistema. |

### Otros:

| Archivo | Descripción |
|---------|-------------|
| **prueba.py** | Script de pruebas rápidas (no parte del pipeline principal). |

## 🚀 Instalación y Uso

### 1. Clona este repositorio:
```bash
git clone https://github.com/Merlin-02/Lexis.git
cd LEXIS
```

### 2. Crea y activa un entorno Conda:
```bash
conda env create -f environment.yml
conda activate Lexis
```

### 3. Configura las variables de entorno:
Crea un archivo `Code/.env` con:
```env
GROQ_API_KEY=tu_api_key_de_groq
```

### 4. Ejecuta el pipeline de preparación (solo una vez):
```bash
cd Code
python preparacion.py
python segmentacion.py
python vectorizacion.py
```

### 5. Inicia el sistema:
```bash
cd Code
python interaccion.py
```

## 🔍 Características del Sistema

### Detección Automática de Áreas
- **Laboral:** Despidos, salarios, contratos, discriminación laboral, horas extras
- **Penal:** Robos, delitos, amenazas, violencia, secuestro
- **Civil:** Deudas, divorcios, propiedades, contratos, herencia

### Búsqueda Híbrida
- **BM25:** Búsqueda léxica precisa para términos legales exactos
- **Semántica:** Búsqueda por significado usando Sentence Transformers
- **RRF Fusion:** Combina ambos métodos para mejores resultados
- **Rerankeo:** Reordena resultados usando similitud coseno

### Mejoras Implementadas
- ✅ Sistema de sinónimos (despido/despedido/despedir)
- ✅ Re-rankeo de resultados con similitud coseno
- ✅ Cacheo del índice BM25
- ✅ Logging de búsquedas
- ✅ Detección de consultas no legales
- ✅ Pesos dinámicos según tipo de consulta
- ✅ Índice temático como fallback
- ✅ Detección automática de normativa

## 📋 Normativas Indexadas

- **Ley Federal del Trabajo** (3191 chunks)
- **Código Penal Tlaxcala** (1050 chunks)
- **Código Civil Tlaxcala** (3311 chunks)
- **Constitución Política de los Estados Unidos Mexicanos** (997 chunks)
- **Procedimiento Civil Tlaxcala** (1649 chunks)
- **Procedimiento Penal Tlaxcala** (627 chunks)

**Total: 10,825 fragmentos indexados**

## ⚠️ Aviso Legal y Limitación de Alcance

**LEXIS** es una herramienta tecnológica diseñada exclusivamente para fines de orientación e información jurídica de primer contacto. **Bajo ninguna circunstancia las respuestas generadas por este sistema de inteligencia artificial sustituyen el consejo, la representación o el diagnóstico formal de un profesional del derecho (abogado) debidamente acreditado.** En caso de requerir iniciar un proceso judicial o enfrentar una situación legal crítica, el sistema recomendará al usuario buscar asesoría legal profesional.

## 📄 Licencia

Este proyecto es de uso educativo y de investigación.
