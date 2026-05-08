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

* **Lenguaje Core:** Python 3.8+
* **Base de Datos Vectorial:** ChromaDB (embeddings multilingual)
* **Búsqueda Híbrida:** BM25 + Similitud semántica (Sentence Transformers)
* **Modelo de Embeddings:** paraphrase-multilingual-MiniLM-L12-v2
* **Generación de Respuestas:** Groq API (modelos LLM)
* **Preprocesamiento:** spaCy, NLTK
* **Frontend:** Terminal interactiva / Streamlit (en desarrollo)

## 📂 Estructura del Repositorio

```text
LEXIS/
 │
 ├── Code/                      # Código fuente principal
 │   ├── buscador.py           # Motor de búsqueda híbrida
 │   ├── interaccion.py       # Interfaz con Groq para respuestas
 │   ├── analizador_legal.py  # Detector de áreas legales
 │   ├── mejoras.py          # Funciones adicionales (caching, re-rankeo)
 │   ├── vectorizacion.py    # Indexación de documentos
 │   ├── segmentacion.py     # Segmentación de textos legales
 │   ├── preparacion.py      # Preprocesamiento de documentos
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

## 🚀 Instalación y Uso

### 1. Clona este repositorio:
```bash
git clone https://github.com/Merlin-02/Lexis.git
cd LEXIS
```

### 2. Crea y activa un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

### 4. Configura las variables de entorno:
Crea un archivo `Code/.env` con:
```env
GROQ_API_KEY=tu_api_key_de_groq
```

### 5. Ejecuta el sistema:

**Modo búsqueda básica (terminal):**
```bash
cd Code
python buscador.py
```

**Modo interactivo con Groq:**
```bash
cd Code
python interaccion.py
```

## 🔍 Características del Sistema

### Detección Automática de Áreas
- **Laboral:** Despidos, salarios, contratos, discriminación laboral
- **Penal:** Robos, delitos, amenazas, violencia
- **Civil:** Deudas, divorcios, propiedades, contratos

### Mejoras Implementadas
- ✅ Sistema de sinónimos (despido/despedido/despedir)
- ✅ Re-rankeo de resultados con similitud coseno
- ✅ Cacheo del índice BM25
- ✅ Logging de búsquedas
- ✅ Detección de consultas no legales
- ✅ Pesos dinámicos según tipo de consulta

## 📋 Normativas Indexadas

- **Ley Federal del Trabajo**
- **Código Penal Tlaxcala**
- **Código Civil Tlaxcala**
- **Constitución Política de los Estados Unidos Mexicanos**
- **Procedimiento Civil Tlaxcala**
- **Procedimiento Penal Tlaxcala**

## ⚠️ Aviso Legal y Limitación de Alcance

**LEXIS** es una herramienta tecnológica diseñada exclusivamente para fines de orientación e información jurídica de primer contacto. **Bajo ninguna circunstancia las respuestas generadas por este sistema de inteligencia artificial sustituyen el consejo, la representación o el diagnóstico formal de un profesional del derecho (abogado) debidamente acreditado.** En caso de requerir iniciar un proceso judicial o enfrentar una situación legal crítica, el sistema recomendará al usuario buscar asesoría legal profesional.

## 📄 Licencia

Este proyecto es de uso educativo y de investigación.
