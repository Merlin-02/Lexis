# LEXIS — Sistema de Asistencia Legal Automatizada con RAG

![Status](https://img.shields.io/badge/Status-En%20Desarrollo-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![RAG](https://img.shields.io/badge/Arquitectura-RAG-green)
![ChromaDB](https://img.shields.io/badge/Vector%20DB-ChromaDB-yellow)

## Descripción

**LEXIS** es un agente conversacional basado en arquitectura RAG (Retrieval-Augmented Generation) que proporciona orientación jurídica de primer contacto en materia **penal, civil y laboral** para el Estado de Tlaxcala y legislación federal mexicana. Utiliza búsqueda híbrida (BM25 + semántica con Sentence Transformers) acoplada a un LLM (Groq) para generar respuestas fundamentadas exclusivamente en el corpus legal indexado.

## Estado del Proyecto — Junio 2025

| Componente | % | Estado |
|------------|:-:|--------|
| Corpus indexado (6 leyes, 10,825 chunks) | 100% | Completado |
| Pipeline de datos (extracción → chunking → vectorización) | 100% | Completado |
| Búsqueda híbrida (BM25 + semántica + RRF + reranking) | 100% | Completado |
| Detección automática de área legal | 100% | Completado |
| Prompt Engineering con restricciones éticas | 100% | Completado |
| Generación de respuesta vía Groq LLM | 100% | Completado |
| Memoria conversacional y contexto entre turnos | 100% | Completado |
| Fallback con índice temático | 100% | Completado |
| Optimizaciones (caché, sinónimos, logging, boost) | 100% | Completado |
| Tests unitarios | 100% | Completado |
| Interfaz de usuario (terminal) | 100% | Completado |
| **Interfaz visual/web** | **0%** | **Pendiente** |
| Ground Truth para evaluación | 0% | Pendiente (fase final) |
| Evaluación de métricas RAG | 0% | Pendiente (fase final) |
| Pruebas de usabilidad | 0% | Pendiente (fase final) |
| Despliegue | 0% | Pendiente (fase final) |

**Progreso general del proyecto:** ~54% del cronograma total ejecutado. El núcleo RAG es completamente funcional.

## Arquitectura del Sistema

```
Usuario (lenguaje natural)
    │
    ▼
┌─────────────────────────────┐
│   analizador_legal.py        │  ← Detección de área legal (laboral/penal/civil/etc.)
│   • Normalización de texto   │
│   • Clasificación por keywords│
│   • Corrección de consultas  │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   buscador.py                │  ← Motor de búsqueda híbrida
│                              │
│   ┌──────────┐ ┌──────────┐  │
│   │ ChromaDB │ │  BM25    │  │
│   │(semántico)│ │ (léxico) │  │
│   └────┬─────┘ └────┬─────┘  │
│        └──────┬─────┘        │
│               ▼              │
│   ┌────────────────────┐     │
│   │  RRF + Reranking    │     │
│   │  + Boost conceptual │     │
│   └──────────┬─────────┘     │
│              │                │
│   Fallback: índice_tematico   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│   interaccion.py             │  ← Interfaz + Generación
│   • Arma prompt con leyes    │
│   • Llama a Groq API         │
│   • Gestiona historial       │
│   • Modelo: gpt-oss-20b      │
└─────────────────────────────┘
```

## Normativas Indexadas

| Normativa | Chunks | Formato | Ámbito |
|-----------|:------:|:-------:|--------|
| Ley Federal del Trabajo | 3,191 | DOCX | Federal |
| Código Civil para el Estado de Tlaxcala | 3,311 | DOCX | Estatal |
| Código Penal para el Estado de Tlaxcala | 1,050 | PDF | Estatal |
| Constitución Política de los Estados Unidos Mexicanos | 997 | PDF | Federal |
| Código de Procedimientos Civiles para el Estado de Tlaxcala | 1,649 | DOCX | Estatal |
| Código de Procedimientos Penales para el Estado de Tlaxcala | 627 | PDF | Estatal |
| **Total** | **10,825** | — | — |

## Stack Tecnológico

| Tecnología | Uso |
|------------|-----|
| Python 3.10 | Lenguaje base |
| ChromaDB 1.5.5 | Base de datos vectorial |
| Sentence Transformers | Embeddings multilingüe (paraphrase-multilingual-mpnet-base-v2, 768 dims) |
| rank_bm25 | Búsqueda léxica |
| Groq API | Inferencia LLM (openai/gpt-oss-20b) |
| pdfplumber | Extracción de PDF |
| python-docx | Lectura de DOCX |
| PyTorch (CUDA) | Backend de embeddings |

## Pipeline de Inicialización

```bash
cd Code
python preparacion.py       # Extraer artículos de PDF/DOCX → JSON
python segmentacion.py      # Segmentar en chunks → JSON
python vectorizacion.py     # Embeddings + ChromaDB
```

## Ejecución del Sistema

```bash
cd Code
python interaccion.py       # Iniciar asistente conversacional
```

### Comandos disponibles

| Comando | Descripción |
|---------|-------------|
| `/filtro ley:<nombre>` | Filtrar por normativa específica |
| `/filtro limpiar` | Eliminar filtro activo |
| `/salir` | Terminar sesión |

El sistema también detecta automáticamente la normativa aplicable basada en palabras clave de la consulta.

## Características Implementadas

- **Búsqueda híbrida**: BM25 (léxica) + ChromaDB (semántica) fusionados con RRF ponderado
- **Reranking**: Reordenamiento por similitud coseno para mejorar precisión
- **Boost conceptual**: Multiplicación de puntuación para términos clave (horas extra ×2.0, despido ×1.8, etc.)
- **Detección de área legal**: 6 áreas (laboral, penal, civil, constitucional, procesal penal, procesal civil)
- **Memoria conversacional**: Últimos 5 intercambios con seguimiento de tema y nombre del usuario
- **Fallback**: Índice temático manual cuando la búsqueda híbrida no encuentra resultados relevantes
- **Expansión de sinónimos**: Ej. "despedido" → "despido", "robaron" → "robo"
- **Cache de BM25**: Persistencia del índice léxico para carga rápida
- **Filtro de consultas no legales**: Detecta temas fuera del ámbito jurídico
- **Pesos dinámicos**: Ajuste automático entre búsqueda léxica y semántica según el tipo de consulta
- **Logging**: Registro de todas las búsquedas para análisis posterior
- **Manejo de errores**: Gestor centralizado con persistencia en archivo

## Archivos del Proyecto

### Código Fuente (`Code/`)

| Archivo | Líneas | Función |
|---------|:------:|---------|
| `preparacion.py` | 367 | Extracción y estructuración de leyes desde PDF/DOCX |
| `segmentacion.py` | 171 | Segmentación de artículos en chunks |
| `vectorizacion.py` | 220 | Embeddings e indexación en ChromaDB |
| `buscador.py` | 577 | Motor de búsqueda híbrida (BM25 + semántica + RRF) |
| `interaccion.py` | 487 | Interfaz conversacional con Groq |
| `analizador_legal.py` | 804 | Detección de área legal y análisis de coherencia |
| `indice_tematico.py` | 638 | Índice temático manual de fallback |
| `mejoras.py` | 521 | Caché, sinónimos, reranking, logging, errores |
| `test_unidades.py` | 237 | Tests unitarios |

### Datos

| Directorio | Contenido |
|------------|-----------|
| `knowledge/` | Documentos legales fuente (PDF, DOCX) + Prompt.txt |
| `knowledge_structured/` | Artículos extraídos en formato JSON (6 archivos) |
| `knowledge_chunks/` | Fragmentos segmentados con metadatos (6 archivos) |
| `lexis_vectordb/` | Base ChromaDB (~77 MB) + caché BM25 + logs |

## Configuración del Entorno

```bash
conda env create -f environment.yml
conda activate Lexis
```

Crear `Code/.env` con:
```
GROQ_API_KEY=tu_api_key
```

## Trabajo Futuro

- [ ] **Interfaz web**: Migrar a Streamlit o aplicación web moderna
- [ ] **Ground Truth**: Construir dataset de evaluación (QA pairs con artículos relevantes)
- [ ] **Métricas RAG**: Evaluación formal con Precision@k, Recall@k, MRR, Faithfulness
- [ ] **Pruebas de usabilidad**: Sesiones con usuarios reales y abogados
- [ ] **Despliegue**: API REST + entorno de pruebas
- [ ] **Evaluación TT II**: Validación final de hipótesis de investigación
- [ ] **Más normativas**: Ampliar cobertura a otras entidades federativas

## Aviso Legal

**LEXIS** es una herramienta de orientación jurídica de primer contacto. Las respuestas generadas **no sustituyen** el consejo, representación o diagnóstico de un profesional del derecho. Consulte a un abogado para casos concretos.
