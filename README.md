# LEXIS — Sistema de Asistencia Legal Automatizada con RAG

<p align="center">
  <img src="image/LogoLexis2.png" alt="LexIS Logo" width="250">
</p>

> *"El derecho no debería ser un privilegio para quienes pueden pagarlo, sino una herramienta accesible para quienes lo necesitan. La tecnología no reemplaza al abogado, pero puede tender el puente entre la ignorancia de la ley y su comprensión."*

---

## Contexto y Motivación

En México, el acceso a la información jurídica representa un desafío estructural para la población general. El lenguaje técnico-legal, la dispersión normativa entre más de 30 códigos estatales y federales, los costos elevados de la asesoría profesional, y las barreras geográficas en zonas rurales generan una brecha profunda entre el ciudadano y sus derechos.

**LEXIS** nace como respuesta a esta problemática: un sistema de asistencia legal automatizada diseñado para proporcionar orientación jurídica de primer contacto, utilizando técnicas de Generación Aumentada por Recuperación (RAG), búsqueda híbrida y modelos de lenguaje de gran escala (LLMs). Su propósito no es reemplazar al profesional del derecho, sino democratizar el acceso a la información jurídica fundamental, reduciendo las brechas económicas, geográficas y de conocimiento que enfrenta la ciudadanía.

---

## Propósito y Finalidad

**Objetivo General**

Desarrollar un agente conversacional basado en Procesamiento de Lenguaje Natural (PLN) y Modelos Grandes de Lenguaje (LLM) mediante arquitectura RAG, para proporcionar orientación jurídica de primer contacto en materia penal, civil y laboral para el Estado de Tlaxcala y legislación federal mexicana.

**Objetivos Específicos**

1. **Corpus textual especializado:** Integrar leyes locales del Estado de Tlaxcala y federales, así como códigos de procedimientos vigentes en materia penal, civil y laboral, estructurando una base de conocimiento del sistema.
2. **Prompt Engineering:** Diseñar la estructura de instrucciones del modelo de lenguaje, definiendo parámetros de comportamiento, restricciones éticas y formato de respuesta para garantizar que la generación de texto se base estrictamente en el contexto jurídico recuperado.
3. **Agente conversacional:** Construir e integrar modelos de PLN, desarrollando la arquitectura para interpretar consultas en lenguaje cotidiano y generar respuestas fundamentadas en el corpus legal procesado.
4. **Evaluación:** Medir el desempeño del agente mediante métricas especializadas como Precisión del Contexto, Exhaustividad del Contexto y Fidelidad, buscando que la orientación jurídica generada sea coherente, congruente y precisa.

---

## Estado del Proyecto — Junio 2026

| Componente | Avance | Estado |
|------------|:------:|--------|
| **Pipeline de datos** (extracción → chunking → vectorización) | 100% | ✅ Completado |
| **Corpus indexado** (6 leyes, 10,825 chunks en ChromaDB) | 100% | ✅ Completado |
| **Búsqueda híbrida** (BM25 + semántica + RRF + reranking + boost) | 100% | ✅ Completado |
| **Detección automática de área legal** (6 clasificadores) | 100% | ✅ Completado |
| **Prompt Engineering** con restricciones éticas | 100% | ✅ Completado |
| **Generación de respuesta** vía Groq LLM | 100% | ✅ Completado |
| **Memoria conversacional** y seguimiento de contexto | 100% | ✅ Completado |
| **Sistema de fallback** con índice temático | 100% | ✅ Completado |
| **Optimizaciones** (caché BM25, sinónimos, logging, pesos dinámicos) | 100% | ✅ Completado |
| **Pruebas unitarias** (10 tests funcionales) | 100% | ✅ Completado |
| **Interfaz de usuario en terminal** | 100% | ✅ Completado |
| **Interfaz visual/web** | 0% | ⬜ Pendiente |
| **Ground Truth** (dataset de evaluación) | 0% | ⬜ Pendiente (fase final) |
| **Métricas RAG** (Precision@k, Recall@k, MRR, Faithfulness) | 0% | ⬜ Pendiente (fase final) |
| **Pruebas de usabilidad** con usuarios reales | 0% | ⬜ Pendiente (fase final) |
| **Despliegue** en entorno de producción | 0% | ⬜ Pendiente (fase final) |

**Progreso general:** ≈54% del cronograma total ejecutado. El núcleo del sistema RAG es completamente funcional y está listo para su uso en terminal interactiva.

---

## Arquitectura del Sistema

```
  USUARIO (lenguaje natural)
       │
       ▼
┌────────────────────────────────────┐
│        ANALIZADOR LEGAL            │
│      (analizador_legal.py)         │
│                                    │
│  • Normalización de texto          │
│  • Detección de área legal         │
│    (laboral / penal / civil /      │
│     constitucional / proc. penal   │
│     / proc. civil)                 │
│  • Análisis de coherencia          │
│  • Corrección de consultas         │
└───────────────┬────────────────────┘
                │
                ▼
┌────────────────────────────────────┐
│       MOTOR DE BÚSQUEDA HÍBRIDA     │
│         (buscador.py)              │
│                                    │
│  ┌────────────┐ ┌──────────────┐   │
│  │  ChromaDB  │ │     BM25     │   │
│  │ (semántico)│ │  (léxico)    │   │
│  │  768 dims  │ │  exactitud   │   │
│  └─────┬──────┘ └──────┬───────┘   │
│        └───────┬───────┘           │
│                ▼                   │
│  ┌────────────────────────────┐    │
│  │  FUSIÓN RRF PONDERADA      │    │
│  │  + Boost conceptual        │    │
│  │  + Reranking por coseno    │    │
│  │  + Verificación relevancia │    │
│  └──────────────┬─────────────┘    │
│                 │                   │
│  Fallback: índice_tematico.py      │
└────────────────┬───────────────────┘
                 │
                 ▼
┌────────────────────────────────────┐
│     GENERACIÓN DE RESPUESTA        │
│       (interaccion.py)             │
│                                    │
│  • Construcción de prompt          │
│    con leyes recuperadas           │
│  • Llamada a Groq API              │
│    (openai/gpt-oss-20b)            │
│  • Gestión de historial            │
│    (últimos 5 turnos)              │
│  • Detección de nombre y tema      │
│  • Formato de respuesta            │
└────────────────────────────────────┘
```

---

## Normativas Indexadas

Actualmente el sistema cuenta con **10,825 fragmentos legales** indexados provenientes de 6 normativas:

| Normativa | Chunks | Formato | Ámbito | Cobertura |
|-----------|:------:|:-------:|:------:|-----------|
| Ley Federal del Trabajo | 3,191 | DOCX | Federal | Laboral |
| Código Civil del Estado de Tlaxcala | 3,311 | DOCX | Estatal | Civil |
| Código Penal del Estado de Tlaxcala | 1,050 | PDF | Estatal | Penal |
| Constitución Política de los Estados Unidos Mexicanos | 997 | PDF | Federal | Constitucional |
| Código de Procedimientos Civiles del Estado de Tlaxcala | 1,649 | DOCX | Estatal | Procesal Civil |
| Código de Procedimientos Penales del Estado de Tlaxcala | 627 | PDF | Estatal | Procesal Penal |

---

## Stack Tecnológico

| Categoría | Tecnología | Versión | Propósito |
|-----------|------------|:-------:|-----------|
| Lenguaje | Python | 3.10 | Lenguaje base del sistema |
| Vector DB | ChromaDB | 1.5.5 | Almacenamiento y búsqueda vectorial |
| Embeddings | sentence-transformers | — | Modelo multilingüe (768 dimensiones) |
| Modelo | paraphrase-multilingual-mpnet-base-v2 | — | Embeddings para español jurídico |
| Búsqueda léxica | rank_bm25 | — | Búsqueda por términos exactos |
| LLM | Groq API | — | Inferencia (openai/gpt-oss-20b) |
| Extracción PDF | pdfplumber | — | Parseo de documentos PDF |
| Lectura DOCX | python-docx | — | Parseo de documentos Word |
| Backend | PyTorch (CUDA) | 2.x | Cómputo de embeddings |

---

## Estructura del Repositorio

```
Lexis/
├── Code/                            # Código fuente del sistema
│   ├── preparacion.py              # Extracción PDF/DOCX → JSON estructurado
│   ├── segmentacion.py             # Segmentación en chunks con metadatos
│   ├── vectorizacion.py            # Embeddings + indexación ChromaDB
│   ├── buscador.py                 # Motor de búsqueda híbrida
│   ├── interaccion.py              # Interfaz conversacional + Groq
│   ├── analizador_legal.py         # Detección de área legal
│   ├── indice_tematico.py          # Índice de fallback por concepto
│   ├── mejoras.py                  # Caché, sinónimos, reranking, logging
│   ├── test_unidades.py            # Tests unitarios
│   └── prueba.py                   # Script de pruebas rápidas
│
├── knowledge/                       # Documentos legales fuente
│   ├── Ley Trabajo.docx             # Ley Federal del Trabajo
│   ├── Codigo Civil Tlaxcala.docx   # Código Civil Tlaxcala
│   ├── Código Penal Tlaxcala.pdf    # Código Penal Tlaxcala
│   ├── Constitucion.pdf             # Constitución Mexicana
│   ├── Procedimiento Civiles Tlaxcala.docx
│   ├── Procedimiento Penal Tlaxcala.pdf
│   └── Prompt.txt                   # System prompt del LLM
│
├── knowledge_structured/            # Artículos extraídos en JSON
│   └── 6 archivos (uno por normativa)
│
├── knowledge_chunks/                # Fragmentos segmentados con metadatos
│   └── 6 archivos (uno por normativa)
│
├── lexis_vectordb/                  # Base de datos vectorial
│   ├── chroma.sqlite3              # Datos vectoriales (~77 MB)
│   ├── cache/bm25_index.pkl        # Índice BM25 persistido
│   └── logs/                       # Registro de búsquedas
│
└── README.md                        # Este documento
```

---

## Instalación y Uso

### Prerrequisitos

- Python 3.8+
- CUDA (opcional, para aceleración GPU)
- Cuenta en Groq con API key

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Merlin-02/Lexis.git
cd Lexis

# Crear entorno Conda
conda env create -f environment.yml
conda activate Lexis

# Configurar API key
echo "GROQ_API_KEY=tu_api_key" > Code/.env
```

### Pipeline de inicialización (solo una vez)

```bash
cd Code
python preparacion.py       # Extraer artículos → JSON
python segmentacion.py      # Segmentar en chunks
python vectorizacion.py     # Generar embeddings → ChromaDB
```

### Ejecutar el asistente

```bash
cd Code
python interaccion.py
```

---

## Características Implementadas

### Búsqueda Inteligente
- **Búsqueda híbrida** con fusión RRF ponderada (BM25 95% + semántica 5% ajustable dinámicamente)
- **Reranking** por similitud coseno entre consulta y documentos recuperados
- **Boost conceptual**: multiplicación de puntuación para 14 conceptos clave legales
- **Pesos dinámicos**: el sistema ajusta automáticamente el equilibrio léxico/semántico según el tipo de consulta
- **Expansión de sinónimos**: 17 familias semánticas con normalización a forma canónica
- **Caché de índice BM25** con persistencia en disco

### Detección de Área Legal
- **6 clasificadores** con más de 400 palabras clave en total
- **Prioridades ponderadas**: laboral (20), civil (8), penal (5), constitucional (5), procesal (1)
- **Palabras excluyentes** para evitar falsos positivos entre áreas
- **Filtro antialucinación**: detecta consultas no legales (cocina, deportes, tecnología, etc.)
- **Análisis de coherencia**: verifica longitud mínima, palabras significativas y términos jurídicos

### Experiencia de Usuario
- **Memoria conversacional**: último 5 intercambios con seguimiento de tema legal
- **Detección de nombre del usuario** mediante expresiones regulares
- **Filtros manuales**: `/filtro ley:<nombre>` y `/filtro limpiar`
- **Sistema de fallback**: índice temático con más de 50 conceptos mapeados a artículos específicos
- **Logging completo** de búsquedas para auditoría y análisis

### Generación de Respuestas
- **Prompt Engineering** con 6 reglas éticas fundamentales
- **Restricción antialucinación**: el LLM solo puede usar texto de los fragmentos recuperados
- **Citas legales** con fuente, artículo y jerarquía
- **Temperatura baja** (0.2) para respuestas deterministas

---

## Pruebas Unitarias

10 tests que cubren:

| Test | Descripción | Estado |
|------|-------------|:------:|
| Detección laboral | "me despidieron del trabajo" → laboral | ✅ |
| Detección penal | "me robaron" → penal | ✅ |
| Detección civil | "divorcio" → civil | ✅ |
| Detección normativa | Mapeo área → documento legal correcto | ✅ |
| Normalización | Acentos, puntuación, mayúsculas | ✅ |
| Coherencia | Consultas cortas vs válidas | ✅ |
| Expansión sinónimos | "despedido" → incluye "despido" | ✅ |
| Análisis tipo consulta | Léxica vs semántica | ✅ |
| Historial de búsquedas | FIFO con límite configurable | ✅ |
| Gestión de errores | Registro y estadísticas | ✅ |

Ejecutar con:
```bash
cd Code
python -m pytest test_unidades.py -v
```

---

## Hoja de Ruta (Trabajo Futuro)

- [ ] **Interfaz web**: Migrar de terminal a Streamlit o aplicación web moderna con experiencia de usuario mejorada
- [ ] **Ground Truth**: Construir dataset de evaluación con pares pregunta-artículos relevantes-respuesta ideal
- [ ] **Métricas RAG**: Evaluación formal con Precision@k, Recall@k, MRR, Faithfulness para validar hipótesis
- [ ] **Pruebas de usabilidad**: Sesiones estructuradas con usuarios reales y profesionales del derecho
- [ ] **Despliegue**: API REST + entorno de pruebas para acceso público controlado
- [ ] **Evaluación TT II**: Validación final de hipótesis de investigación y comparación contra LLM base
- [ ] **Ampliación de cobertura**: Incorporar normativas de otras entidades federativas

---

## Aviso Legal

**LEXIS** es una herramienta tecnológica diseñada exclusivamente para fines de orientación e información jurídica de primer contacto. **Bajo ninguna circunstancia las respuestas generadas por este sistema de inteligencia artificial sustituyen el consejo, la representación o el diagnóstico formal de un profesional del derecho debidamente acreditado.** En caso de requerir iniciar un proceso judicial o enfrentar una situación legal crítica, consulte a un abogado con todos sus documentos.

---

## Equipo de Desarrollo

- Kevin Merlin Cabrera Coyotzi
- Dulce Anahí Luna García

---

## Licencia

Proyecto de uso educativo y de investigación.
