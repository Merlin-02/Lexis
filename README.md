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

## Estado del Proyecto — Noviembre 2026

| Componente | Avance | Estado |
|------------|:------:|--------|
| **Pipeline de datos** (extracción PDF → JSON jerárquico → chunking → vectorización) | 98% | ✅ Completado |
| **Corpus indexado** (6 leyes: 10,825 chunks en ChromaDB y 7,221 artículos en Grafo) | 95% | ✅ Completado |
| **Grafo de Conocimiento Legal y GraphRAG** (`Code/grafo_lexis/`, 7,239 nodos y 10,135 aristas) | 95% | ✅ Completado |
| **Búsqueda híbrida dual** (ChromaDB/MiniLM local + modo ligero TF-IDF Cloud + BM25 + RRF) | 90% | ✅ Completado |
| **Detección automática de área legal** (`analizador_legal.py`, 6 clasificadores) | 85% | 🔧 En refinamiento (saneamiento de vocabulario) |
| **Prompt Engineering** con restricciones éticas (`knowledge/Prompt.txt`) | 100% | ✅ Completado |
| **Generación de respuesta** vía Groq LLM (`openai/gpt-oss-20b` + contexto GraphRAG) | 85% | 🔧 Operativo (pendiente fix UTF-8 en `interaccion.py`) |
| **Memoria conversacional** y seguimiento de contexto | 100% | ✅ Completado |
| **Sistema de fallback** con índice temático (`indice_tematico.py`) | 80% | 🔧 En refinamiento (auditoría de artículos locales) |
| **Optimizaciones** (caché BM25, sinónimos, logging JSONL, pesos dinámicos) | 95% | ✅ Completado |
| **Pruebas unitarias** (`test_unidades.py` + 9 suites en `Code/tests/` para grafo y sesiones) | 95% | ✅ Completado |
| **Interfaz de usuario en terminal** (`interaccion.py` y `grafo_lexis/cli.py`) | 100% | ✅ Completado |
| **Interfaz visual/web en Streamlit** (`app.py` + login + visualizador de grafo estilo Obsidian) | 90% | ✅ Completado |
| **Infraestructura de evaluación de sesiones y usuarios** (`gestor_evaluacion.py`, `gestor_usuarios.py`) | 100% | ✅ Completado |
| **Despliegue Cloud** (`Dockerfile`, `railway.json`, `Procfile`, modo ligero sin GPU) | 90% | ✅ Completado |
| **Pruebas de usabilidad** con usuarios reales (`sesiones_evaluacion/`) | 20% | 🔄 En curso (captura piloto iniciada) |
| **Ground Truth** (dataset de evaluación cuantitativa) | 0% | ⬜ Pendiente |
| **Métricas RAG cuantitativas** (Precision@k, Recall@k, MRR, Faithfulness) | 0% | ⬜ Pendiente |

**Progreso general:** ≈84.5% del proyecto total ejecutado. El sistema cuenta con arquitectura Híbrida + GraphRAG operativa, interfaz web interactiva en Streamlit con visualización de grafo en HTML5 Canvas, sistema de captura de evaluaciones y configuración de despliegue ligero en Railway; actualmente se encuentra en **fase de estabilización pre-producción y evaluación cuantitativa**.

---

## Arquitectura del Sistema

```
  USUARIO (Interfaz Web Streamlit app.py / Terminal CLI)
       │
       ▼
┌────────────────────────────────────────────────────────┐
│                    ANALIZADOR LEGAL                    │
│                  (analizador_legal.py)                 │
│                                                        │
│  • Normalización de texto y expansión de sinónimos     │
│  • Detección de área legal (laboral / penal / civil /  │
│    constitucional / proc. penal / proc. civil)         │
│  • Análisis de coherencia y filtro de ámbito geográfico│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│               MOTOR DE BÚSQUEDA HÍBRIDA                │
│                     (buscador.py)                      │
│                                                        │
│  ┌────────────────────────┐ ┌───────────────────────┐  │
│  │ Semántico / Vectorial  │ │     Léxico (BM25)     │  │
│  │ • Local: ChromaDB      │ │ • Exactitud de        │  │
│  │   (MiniLM-L12-v2)      │ │   términos y artículos│  │
│  │ • Cloud: TF-IDF char   │ │ • Caché persistente   │  │
│  └───────────┬────────────┘ └───────────┬───────────┘  │
│              └────────────┬─────────────┘              │
│                           ▼                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  FUSIÓN RRF PONDERADA + RERANKING + BOOST LEGAL  │  │
│  └────────────────────────┬─────────────────────────┘  │
│                           │                            │
│             Fallback: indice_tematico.py               │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│         EXPANSIÓN POR GRAFO DE CONOCIMIENTO            │
│      (Code/grafo_lexis/ — GraphRAG sobre NetworkX)     │
│                                                        │
│  • 7,239 nodos (6 Leyes, 7,221 Artículos, 12 Externas) │
│  • 10,135 aristas (CONTIENE, REFIERE_A, MENCIONA_NORMA)│
│  • Expansión 1-hop de artículos citados (salientes y   │
│    entrantes) e inyección de contexto normativo conexo │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           GENERACIÓN Y EXPERIENCIA DE USUARIO          │
│     (interaccion.py / app.py / gestor_evaluacion.py)   │
│                                                        │
│  • Síntesis jurídica con Groq API (openai/gpt-oss-20b) │
│  • Visualizador interactivo estilo Obsidian (Canvas)   │
│  • Gestión de sesiones, autenticación y evaluación     │
│    obligatoria por respuesta y encuesta final          │
└────────────────────────────────────────────────────────┘
```

---

## Normativas Indexadas

Actualmente el sistema integra **6 cuerpos normativos** tanto en formato de fragmentos vectoriales (**10,825 chunks** en ChromaDB) como en el Grafo de Conocimiento Legal (**7,221 nodos de artículos** —7,179 principales y 42 transitorios— y **2,900 relaciones de citación `REFIERE_A`**):

| Clave | Normativa | Chunks (ChromaDB) | Artículos (Grafo) | Ámbito | Cobertura |
|:-----:|-----------|:-----------------:|:-----------------:|:------:|-----------|
| **LFT** | Ley Federal del Trabajo | 3,191 | 1,098 (1,091 + 7 trans.) | Federal | Laboral |
| **CCT** | Código Civil para el Estado Libre y Soberano de Tlaxcala | 3,311 | 3,192 (3,191 + 1 trans.) | Estatal (Tlaxcala) | Civil |
| **CPT** | Código Penal para el Estado Libre y Soberano de Tlaxcala | 1,050 | 1,727 (1,722 + 5 trans.) | Estatal (Tlaxcala) | Penal |
| **CPEUM** | Constitución Política de los Estados Unidos Mexicanos | 997 | 156 (136 + 20 trans.) | Federal | Constitucional |
| **CFPC** | Código Federal de Procedimientos Civiles | 1,649 | 553 (549 + 4 trans.) | Federal | Procesal Civil |
| **CNPP** | Código Nacional de Procedimientos Penales | 627 | 495 (490 + 5 trans.) | Federal | Procesal Penal |

---

## Stack Tecnológico

| Categoría | Tecnología | Versión | Propósito |
|-----------|------------|:-------:|-----------|
| Lenguaje | Python | 3.10+ | Lenguaje base del sistema |
| Interfaz Web | Streamlit | ≥1.32 | Aplicación web conversacional, login y panel de evaluación |
| Grafo Legal | NetworkX | ≥3.1 | Construcción, recorrido y análisis del Grafo de Conocimiento Legal |
| Exportación Grafo | GraphML / Neo4j Cypher / HTML5 Canvas | — | Interoperabilidad con Gephi/Neo4j y visualizador interactivo estilo Obsidian |
| Vector DB (Local) | ChromaDB | 1.5.5 | Almacenamiento y búsqueda vectorial densa |
| Embeddings (Local) | sentence-transformers | — | Embeddings multilingües (`paraphrase-multilingual-MiniLM-L12-v2` / mpnet) |
| Motor Ligero (Cloud) | scikit-learn (`TfidfVectorizer`) | ≥1.3 | Fallback semántico de bajo consumo RAM (<30 MB) para contenedores sin GPU |
| Búsqueda léxica | rank_bm25 | ≥0.2.2 | Búsqueda por términos exactos e identificadores de artículos |
| LLM | Groq API | ≥0.9.0 | Inferencia de lenguaje natural (`openai/gpt-oss-20b`) |
| Extracción PDF/DOCX | PyMuPDF (`fitz`) / pdfplumber / python-docx | — | Parseo estructural de documentos legislativos |
| Despliegue | Docker + Railway | — | Contenerización y despliegue continuo en la nube |

---

## Estructura del Repositorio

```
Lexis/
├── Code/                                # Código fuente principal
│   ├── app.py                           # Interfaz web en Streamlit (login, chat, grafo, evaluación)
│   ├── preparacion.py                   # Extracción PDF/DOCX → JSON jerárquico
│   ├── segmentacion.py                  # Segmentación en chunks con metadatos
│   ├── vectorizacion.py                 # Embeddings + indexación en ChromaDB
│   ├── buscador.py                      # Motor híbrido (ChromaDB / TF-IDF ligero + BM25 + RRF)
│   ├── interaccion.py                   # Agente conversacional en CLI + cliente Groq
│   ├── analizador_legal.py              # Clasificador de áreas legales y expansión de sinónimos
│   ├── indice_tematico.py               # Índice de respaldo temático por concepto
│   ├── mejoras.py                       # Caché LRU, historial, validador y logging JSONL
│   ├── gestor_usuarios.py               # Registro, autenticación y tokens de sesión persistentes
│   ├── gestor_evaluacion.py             # Telemetría y evaluación por respuesta y por sesión
│   ├── test_unidades.py                 # Pruebas unitarias del motor base
│   │
│   ├── grafo_lexis/                     # Subsistema de Grafo de Conocimiento Legal (GraphRAG)
│   │   ├── modelos.py                   # Dataclasses de nodos, aristas y referencias
│   │   ├── config_leyes.py              # Catálogo canónico de las 6 leyes y normas externas
│   │   ├── cargador.py                  # Saneamiento de etiquetas y carga desde JSON estructurado
│   │   ├── detector_referencias.py      # Motor regex de citas directas, rangos, inter-ley y relativas
│   │   ├── constructor_grafo.py         # Ensamblado del MultiDiGraph en NetworkX
│   │   ├── consultas.py                 # API de consultas estructurales sobre el grafo
│   │   ├── recuperador_grafo.py         # Mapeo chunk→nodo y expansión de vecindario (1-hop)
│   │   ├── integracion_rag.py           # Orquestador híbrido + GraphRAG para el prompt del LLM
│   │   ├── exportador.py                # Exportación a JSON, GraphML y CSVs + Cypher para Neo4j
│   │   ├── reporte_rotas.py             # Auditoría de referencias rotas, externas o ambiguas
│   │   ├── neo4j_loader.py              # Cargador directo a instancia Neo4j vía driver Bolt
│   │   ├── visualizador_obsidian.py     # Renderizador interactivo en HTML5 Canvas estilo Obsidian
│   │   ├── llm_groq.py                  # Cliente Groq para el CLI de GraphRAG
│   │   └── cli.py                       # Interfaz de línea de comandos del grafo legal
│   │
│   └── tests/                           # Suites de pruebas automatizadas (Grafo y Sesiones)
│       ├── test_cargador.py
│       ├── test_referencias_directas.py
│       ├── test_referencias_ley.py
│       ├── test_rangos.py
│       ├── test_referencias_relativas.py
│       ├── test_consultas.py
│       ├── test_exportador.py
│       ├── test_graphrag.py
│       └── test_evaluacion_sesiones.py
│
├── knowledge/                           # Documentos legales fuente (PDF) y Prompt.txt
├── knowledge_structured/                # 6 archivos JSON con la jerarquía normativa extraída
├── knowledge_chunks/                    # 6 archivos JSON con los 10,825 chunks segmentados
├── knowledge_graph/                     # Artefactos compilados del Grafo Legal
│   ├── grafo_lexis.json                 # Grafo serializado (7,239 nodos, 10,135 aristas)
│   ├── grafo_lexis.graphml              # Grafo para Gephi / Cytoscape
│   ├── estadisticas_grafo.json          # Métricas estructurales y top artículos citados
│   ├── reporte_referencias_rotas.json   # Registro auditable de 82 referencias no resueltas
│   └── neo4j/                           # CSVs de nodos/aristas y script import_neo4j.cypher
│
├── lexis_vectordb/                      # Base vectorial ChromaDB, caché BM25 y logs JSONL
├── sesiones_evaluacion/                 # Sesiones de usuarios y consolidado de evaluaciones
├── Dockerfile                           # Imagen optimizada para despliegue en contenedor
├── railway.json                         # Configuración de despliegue en Railway
├── Procfile                             # Comando de arranque para plataforma PaaS
├── requirements.txt                     # Dependencias para despliegue en producción
├── environment.yml                      # Entorno Conda para desarrollo local con GPU
├── PROMPT_GRAFO_LEGAL.md                # Especificación técnica de la arquitectura del grafo
└── README.md                            # Este documento
```

---

## Instalación y Uso

### Prerrequisitos

- Python 3.10+
- CUDA (opcional, para aceleración GPU en modo ChromaDB completo)
- Cuenta en Groq con API key (`GROQ_API_KEY`)

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/Merlin-02/Lexis.git
cd Lexis

# Opción A: Crear entorno Conda (desarrollo completo)
conda env create -f environment.yml
conda activate Lexis

# Opción B: Instalar dependencias ligeras con pip
pip install -r requirements.txt

# Configurar variables de entorno
cp Code/.env.example Code/.env
# Editar Code/.env con tu GROQ_API_KEY (y opcionalmente LEXIS_ADMIN_KEY)
```

### Pipeline de datos y construcción del Grafo Legal (solo si se desea regenerar)

```bash
cd Code
python preparacion.py                                    # 1. Extraer PDFs → knowledge_structured/
python segmentacion.py                                   # 2. Segmentar en chunks → knowledge_chunks/
python vectorizacion.py                                  # 3. Vectorizar en ChromaDB → lexis_vectordb/
python -m grafo_lexis.cli construir --exportar-todo      # 4. Construir y exportar Grafo → knowledge_graph/
```

### Ejecutar la Interfaz Web (Streamlit)

```bash
streamlit run Code/app.py
```

> Para forzar el **modo ligero** (sin requerir GPU ni ChromaDB, cargando desde `knowledge_graph/grafo_lexis.json`):
> ```bash
> LEXIS_MODO_LIGERO=1 streamlit run Code/app.py
> ```

### Ejecutar en Terminal (CLI Conversacional y CLI del Grafo)

```bash
cd Code
# Asistente conversacional interactivo en consola
python interaccion.py

# Consultas al Grafo de Conocimiento Legal y GraphRAG desde CLI
python -m grafo_lexis.cli stats
python -m grafo_lexis.cli articulo LFT:ART:47
python -m grafo_lexis.cli graphrag "me despidieron sin justificación" --llm
```

---

## Características Implementadas

### Búsqueda Híbrida Dual (Local + Cloud)
- **Fusión RRF ponderada**: combina recuperación semántica y léxica (BM25) con ajuste dinámico según el tipo de consulta
- **Doble motor de ejecución**:
  - *Modo Completo*: `ChromaDB` + `sentence-transformers` en GPU/CPU
  - *Modo Ligero (`LEXIS_MODO_LIGERO=1`)*: `MotorSemanticoTFIDF` en memoria sobre los 7,179 artículos del grafo (<30 MB de RAM) para despliegue económico en la nube
- **Reranking por similitud coseno** y **boost conceptual** para conceptos jurídicos prioritarios
- **Expansión de sinónimos** de lenguaje ciudadano a terminología técnico-jurídica
- **Caché de índice BM25** en disco y caché LRU de consultas frecuentes

### Grafo de Conocimiento Legal (GraphRAG)
- **7,239 nodos tipados**: 6 nodos `Ley`, 7,221 nodos `Articulo` (principales y transitorios) y 12 nodos `NormaExterna`
- **10,135 aristas dirigidas**: 7,221 relaciones jerárquicas `CONTIENE`, 2,900 relaciones de citación artículo-a-artículo `REFIERE_A` y 14 menciones a normas externas `MENCIONA_NORMA`
- **Detección determinista de referencias**: soporta citas simples, listas, rangos (`del artículo X al Y`), referencias inter-ley y referencias relativas (`artículo anterior`, `artículo siguiente`)
- **Expansión contextual 1-hop**: al recuperar artículos por búsqueda híbrida, el sistema incorpora automáticamente los artículos citados de forma saliente y entrante antes de construir el prompt para el LLM
- **Exportación multi-formato**: JSON, GraphML, CSVs + script Cypher para Neo4j y reporte auditable de referencias rotas

### Interfaz Web Interactiva y Evaluación de Usabilidad
- **Aplicación en Streamlit (`Code/app.py`)** con soporte de tema claro/oscuro y filtro de ámbito geográfico (`General`, `Tlaxcala`, `Federal`)
- **Visualizador de Grafo estilo Obsidian (`visualizador_obsidian.py`)**: lienzo interactivo en HTML5 Canvas con simulación física de fuerzas, zoom, filtros por ley y lector de artículos al hacer clic en cualquier nodo (tanto para el subgrafo de cada respuesta como para el grafo global)
- **Gestión de usuarios y sesiones (`gestor_usuarios.py` y `gestor_evaluacion.py`)**: registro de perfil, persistencia por token en URL, calificación obligatoria por turno (útil/no útil, 0–5 estrellas, corrección jurídica sugerida), encuesta de cierre de sesión y panel administrativo de exportación JSON

### Detección de Área Legal y Generación Controlada
- **6 clasificadores de área jurídica** (`laboral`, `penal`, `civil`, `constitucional`, `procesal_civil`, `procesal_penal`) con filtro antialucinación para consultas ajenas al ámbito legal
- **Prompt Engineering estricto** (`knowledge/Prompt.txt`) con temperatura baja (`0.2`) y prohibición expresa de inventar artículos fuera del contexto recuperado

---

## Pruebas Automatizadas

El proyecto cuenta con pruebas unitarias tanto para el motor de búsqueda base como para el subsistema de Grafo Legal y el gestor de sesiones:

| Suite de Pruebas | Archivo | Cobertura Principal | Estado |
|------------------|---------|---------------------|:------:|
| Motor Base y Mejoras | `Code/test_unidades.py` | Clasificador legal, normalización, coherencia, sinónimos, caché y errores | ✅ |
| Cargador del Grafo | `Code/tests/test_cargador.py` | Saneamiento de etiquetas (`153-` → `153_A`), transitorios y unicidad de IDs | ✅ |
| Citas Internas Directas | `Code/tests/test_referencias_directas.py` | Detección regex de artículos simples, listas, `bis`/`ter` y fracciones | ✅ |
| Referencias Inter-Ley | `Code/tests/test_referencias_ley.py` | Resolución de citas hacia otras leyes del corpus y normas externas | ✅ |
| Expansión de Rangos | `Code/tests/test_rangos.py` | Expansión controlada de rangos (`del artículo X al Y`) y límites de seguridad | ✅ |
| Referencias Relativas | `Code/tests/test_referencias_relativas.py` | Resolución contextual de `artículo anterior`, `siguiente` y `este artículo` | ✅ |
| Consultas de Grafo | `Code/tests/test_consultas.py` | Vecindarios, caminos más cortos, citas entrantes/salientes y ranking | ✅ |
| Exportación y Reportes | `Code/tests/test_exportador.py` | Generación de JSON, GraphML, CSVs Neo4j y reporte de referencias rotas | ✅ |
| Integración GraphRAG | `Code/tests/test_graphrag.py` | Mapeo de hits híbridos a nodos del grafo y expansión de contexto para LLM | ✅ |
| Evaluación de Sesiones | `Code/tests/test_evaluacion_sesiones.py` | Ciclo de vida de sesiones, bloqueo por evaluación pendiente y consolidado | ✅ |

Ejecutar todas las suites con:
```bash
pytest Code/test_unidades.py Code/tests/ -v
```

---

## Hoja de Ruta y Siguientes Pasos

### Completado
- [x] **Pipeline de extracción, segmentación y vectorización** de las 6 leyes (ChromaDB)
- [x] **Grafo de Conocimiento Legal y GraphRAG** completo en 7 fases (`Code/grafo_lexis/` y `knowledge_graph/`)
- [x] **Interfaz web en Streamlit** con autenticación, historial, selector de ámbito y visualizador interactivo estilo Obsidian (`Code/app.py`)
- [x] **Infraestructura de telemetría y evaluación de sesiones** (`gestor_evaluacion.py` y `gestor_usuarios.py`)
- [x] **Configuración de despliegue Cloud en Railway** con motor ligero TF-IDF (`Dockerfile`, `railway.json`, `Procfile`)

### Pendiente (Próximas Prioridades)
- [ ] **Prioridad 1 — Hotfixes de estabilización**:
  - Preservar codificación UTF-8 completa (acentos y `ñ`) al enviar prompts a Groq en `Code/interaccion.py`
  - Incorporar la clave `texto_general` de los incisos en `Code/grafo_lexis/cargador.py` y regenerar `knowledge_graph/`
  - Corregir clave `articulo_id` en el registro de vecinos del grafo y el texto del respaldo temático en `Code/app.py`
  - Parametrizar `MODELO_GROQ` por variable de entorno y reforzar validación de `LEXIS_ADMIN_KEY`
- [ ] **Prioridad 2 — Saneamiento de datos y sincronización vectorial**:
  - Limpiar términos corruptos en `Code/analizador_legal.py` y auditar artículos locales en `Code/indice_tematico.py`
  - Incluir `articulo_id` canónico en los metadatos de `knowledge_chunks/` y re-indexar `lexis_vectordb/`
- [ ] **Prioridad 3 — Evaluación cuantitativa RAG y pruebas de usabilidad**:
  - Construir dataset **Ground Truth** con pares pregunta–artículos relevantes validados por juristas
  - Implementar script automatizado de métricas (**Precision@k, Recall@k, MRR, Faithfulness**) comparando Vectorial vs. Híbrido vs. Híbrido + GraphRAG
  - Completar sesiones de evaluación de usabilidad con usuarios reales y profesionales del derecho
- [ ] **Prioridad 4 — Persistencia concurrente y exportación de usuario**:
  - Añadir bloqueo de archivos (`filelock`) o persistencia SQLite para sesiones concurrentes y exportación de consultas a PDF/Word para el usuario final

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
