# PROMPT MAESTRO — Grafo de conocimiento legal + GraphRAG para LEXIS

**Proyecto:** convertir el corpus jurídico estructurado de LEXIS en un grafo de conocimiento de referencias entre artículos y leyes, e integrarlo con el chatbot RAG existente.

**Repositorio:** `/home/merli_nx19/Documentos/Lexis`

**Rama de trabajo:** `feature/grafo`

**Entorno:** Python del entorno conda `Lexis`

**Librería principal de grafos:** `networkx`

**Estado:** Fases 1 a 7 completadas y verificadas.

---

## 1. Instrucción principal

Actúa como ingeniero de software senior especializado en procesamiento de lenguaje natural jurídico, grafos de conocimiento y sistemas RAG.

Construye, por fases y con validación humana entre cada una, una herramienta modular en Python que:

1. Lea los artículos jurídicos ya extraídos en JSON.
2. Cree un grafo con nodos de leyes y artículos.
3. Genere aristas `CONTIENE` de cada ley a sus artículos.
4. Detecte referencias entre artículos con reglas y expresiones regulares.
5. Resuelva referencias dentro de la misma ley y entre leyes distintas.
6. Guarde en cada referencia el fragmento exacto y el artículo de origen.
7. Reporte referencias rotas o ambiguas.
8. Permita consultas de citas, impacto y leyes más referenciadas.
9. Exporte el grafo a JSON y GraphML, y opcionalmente a Neo4j.
10. Integre el grafo con el chatbot RAG existente para construir un sistema GraphRAG.

No entregues todo el sistema de una vez. Trabaja una fase a la vez, muestra resultados, explica pendientes y espera confirmación antes de avanzar.

Si una instrucción posterior del usuario contradice este documento, prevalece la instrucción posterior.

---

## 2. Resultado final esperado

Al terminar el proyecto debe existir:

- Un paquete Python modular para cargar, normalizar, detectar referencias, construir el grafo, consultarlo y exportarlo.
- Un grafo persistido en JSON y GraphML.
- Un reporte de referencias rotas y ambiguas.
- Pruebas automatizadas para cada tipo de referencia.
- Una capa de recuperación sobre el grafo que se pueda usar desde el chatbot.
- Integración con el RAG actual: ChromaDB + BM25 + grafo + Groq.
- Respuestas del chatbot con fuentes verificables: ley, artículo, fragmento y referencias relacionadas.
- Opcionalmente, carga en Neo4j y consultas Cypher.
- Documentación suficiente para reconstruir el grafo y ejecutar las consultas.

El producto final no es solo un script de análisis: es una capa estructural que mejora la precisión, la trazabilidad y la explicabilidad del asistente legal LEXIS.

---

## 3. Contexto del repositorio

El repositorio ya contiene un sistema RAG funcional:

- `Code/preparacion.py`: extracción de PDF/DOCX a JSON estructurado.
- `Code/segmentacion.py`: división de artículos en chunks.
- `Code/vectorizacion.py`: embeddings e indexación en ChromaDB.
- `Code/buscador.py`: búsqueda híbrida ChromaDB + BM25 + RRF + reranking.
- `Code/analizador_legal.py`: detección de normativa y análisis de consultas.
- `Code/indice_tematico.py`: fallback temático.
- `Code/mejoras.py`: caché, sinónimos, reranking y logging.
- `Code/interaccion.py`: chatbot de terminal con Groq.
- `Code/app.py`: interfaz Streamlit.
- `knowledge/Prompt.txt`: system prompt del asistente.
- `lexis_vectordb/`: base vectorial ChromaDB.
- `knowledge_chunks/`: chunks segmentados.
- `knowledge_structured/`: artículos estructurados en JSON.

**No reemplaces el RAG existente.** El grafo se integra como una capa adicional de recuperación y verificación. La arquitectura final es GraphRAG.

---

## 4. Datos de entrada y problemas conocidos

### 4.1 Archivos

Carpeta:

```text
/home/merli_nx19/Documentos/Lexis/knowledge_structured
```

Archivos:

```text
Codigo Civil Tlaxcala_estructurado.json
Código Penal Tlaxcala_estructurado.json
Constitucion_estructurado.json
Ley Trabajo_estructurado.json
Procedimiento Civiles Tlaxcala_estructurado.json
Procedimiento Penal Tlaxcala_estructurado.json
```

Son 6 normativas y 7,221 registros.

### 4.2 Estructura real del JSON

Cada archivo es una **lista de artículos**, no un objeto de ley. Cada artículo tiene:

```text
articulo
jerarquia
texto_general
historial_dof
fracciones
incisos_directos
referencias_articulos
```

No existen dentro del JSON:

- identificador de ley,
- nombre oficial,
- alias,
- fecha de publicación.

Esos metadatos deben vivir en un catálogo aparte.

### 4.3 Problemas detectados

1. **`referencias_articulos` es incompleto y no trazable.**
   - Guarda cadenas como `"Artículo 60"`.
   - No guarda el fragmento.
   - No distingue misma ley vs otra ley.
   - No representa rangos ni listas.
   - No debe usarse como fuente de verdad.
   - Solo puede usarse para comparar cobertura.

2. **Hay transitorios y decretos mezclados con artículos.**
   - Código Civil: 8 transitorios al final.
   - Ley Federal del Trabajo: 13 transitorios.
   - Código de Procedimientos Civiles: 14 transitorios.
   - Código de Procedimientos Penales: 4 transitorios y texto de reformas.
   - Constitución: 3 fragmentos de decretos tomados como artículos.
   - Deben conservarse para el RAG, pero marcarse con `es_transitorio=true` y excluirse por defecto de las consultas de referencias e impacto.

3. **Hay etiquetas de artículo truncadas.**
   - `Artículo 153-` + texto `A.` equivale a `153-A`.
   - `Artículo 153-` + `F Bis` equivale a `153-F Bis`.
   - `ARTICULO 135` + `A.-` equivale a `135-A`.
   - `ARTICULO 640 QUATER` + `A.` equivale a `640 Quáter A`.
   - `Artículo 229` + `bis.` equivale a `229 Bis`.
   - El cargador debe reconstruir estas etiquetas sin modificar los JSON originales.

4. **Algunos artículos tienen `texto_general` vacío.**
   - 2 en Civil y 16 en LFT.
   - Deben marcarse como `texto_vacio=true`; no inventar contenido.

5. **La Constitución cargada es la federal.**
   - No confundirla con la Constitución Política del Estado Libre y Soberano de Tlaxcala.
   - Las referencias a la Constitución Local deben resolverse como norma externa o quedar ambiguas.

6. **`jerarquia` solo guarda el último encabezado.**
   - No se puede reconstruir la ruta completa Libro → Título → Capítulo → Sección solo con ese campo.
   - Guardar `jerarquia` como propiedad descriptiva, sin inventar la ruta completa.

7. **`historial_dof` no debe analizarse.**
   - Contiene números de artículos de decretos de reforma.
   - Generaría falsos positivos.
   - Se conserva como dato histórico, pero no se usa para detectar referencias.

---

## 5. Decisiones de diseño

Estas son las decisiones recomendadas. El agente debe confirmarlas con el usuario antes de la Fase 2.

1. **Metadatos:** catálogo manual en `config_leyes.py` con nombres oficiales y alias; `fecha_publicacion=null` hasta que el usuario proporcione las fechas.
2. **Transitorios:** conservarlos como nodos con `es_transitorio=true`; excluirlos por defecto de referencias, consultas de impacto y estadísticas.
3. **Etiquetas truncadas:** reconstruirlas en el cargador, sin modificar los JSON de entrada.
4. **Constitución:** resolver solo alias explícitos; `Constitución` a secas queda ambigua.
5. **Rangos:** expandir solo números base, salvo que el rango mencione explícitamente sufijos como `BIS`, `TER` o letras.
6. **Normas externas:** crear nodos `NormaExterna` para leyes no cargadas y aristas `MENCIONA_NORMA`.
7. **Multiplicidad:** una arista por cada mención, usando `networkx.MultiDiGraph`.
8. **RAG:** mantener el RAG actual y agregar una capa GraphRAG en una fase posterior.

---

## 6. Modelo de grafo

### 6.1 Nodos

#### `Ley`

Representa una ley, código o constitución cargada.

```text
id: ley:<slug>
tipo_nodo: "Ley"
clave: "CC-TLAX" | "CP-TLAX" | "CPEUM" | "LFT" | "CPC-TLAX" | "CPP-TLAX"
nombre_oficial
nombre_corto
alias: [ ... ]
tipo_norma: "ley" | "codigo" | "constitucion"
ambito: "federal" | "estatal"
materia: "civil" | "penal" | "laboral" | "constitucional" | "procesal_civil" | "procesal_penal"
fecha_publicacion: null | "YYYY-MM-DD"
fuente_json
en_corpus: true
```

#### `Articulo`

Representa un artículo, incluyendo subartículos como `153-A` o `229 Bis`.

```text
id: articulo:<ley_slug>:<numero_canonico>
tipo_nodo: "Articulo"
ley_id
numero: "135-A"
numero_base: 135
sufijo: "A" | "BIS" | "F-BIS" | "QUATER-A"
etiqueta_original
etiqueta_normalizada
orden
jerarquia
texto_general
texto_completo
fracciones
incisos_directos
historial_dof
es_transitorio: true | false
texto_vacio: true | false
chunk_ids: []   # se llena en la Fase 7
```

`texto_completo` se construye a partir de `texto_general`, `fracciones` e `incisos`, preservando el contenido original. Los spans de las referencias se calculan sobre ese texto consolidado.

#### `NormaExterna` (opcional)

Representa una ley mencionada pero no cargada.

```text
id: norma_externa:<slug>
tipo_nodo: "NormaExterna"
nombre
alias: [ ... ]
en_corpus: false
```

### 6.2 Aristas

#### `CONTIENE`

```text
(Ley)-[:CONTIENE]->(Articulo)
```

Propiedades:

```text
orden
jerarquia
```

#### `REFIERE_A`

```text
(Articulo)-[:REFIERE_A]->(Articulo)
```

Solo se crea cuando el destino es un artículo existente.

Propiedades:

```text
id
tipo: "REFIERE_A"
origen_id
destino_id
origen_ley_id
destino_ley_id
clase: "directa" | "explicita_otra_ley" | "rango" | "relativa" | "lista"
relacion: "misma_ley" | "entre_leyes"
texto_referencia
snippet
snippet_exacto
span_inicio
span_fin
unidad: "texto_general" | "fraccion:I" | "inciso:a" | ...
componente: null | "párrafo tercero" | "fracción II" | "inciso a)"
rango: null | {"desde": 10, "hasta": 15}
grupo_id
confianza: "alta" | "media" | "baja"
metodo: "regex" | "regex+alias" | "llm" | "manual"
estado: "resuelta" | "ambigua" | "rota" | "externa"
```

#### `MENCIONA_NORMA`

```text
(Articulo)-[:MENCIONA_NORMA]->(Ley | NormaExterna)
```

Se usa para referencias a una ley sin artículo identificable: “la presente Ley”, “este Código”, “la Ley del Seguro Social”.

Propiedades:

```text
texto_referencia
snippet
snippet_exacto
span_inicio
span_fin
articulo_mencionado: null | "140 Bis"
confianza
metodo
```

### 6.3 Referencias rotas

No crear nodos ficticios de artículos inexistentes.

Guardar las referencias rotas en una lista y exportarlas a JSON/CSV con:

```text
origen_id
ley_origen
texto_referencia
destino_mencionado
motivo
snippet
span_inicio
span_fin
confianza
sugerencia
```

Motivos:

- `articulo_inexistente`
- `ley_no_cargada`
- `ley_ambigua`
- `sin_articulo_identificable`
- `rango_fuera_de_limites`
- `relativa_sin_vecino`

No corregir automáticamente un número roto. Si se genera una sugerencia, debe quedar marcada como tal.

---

## 7. Reglas de detección de referencias

### 7.1 Referencias directas

- `artículo 12` → artículo 12 de la misma ley.
- `arts. 10`, `art. 10`, `artículos 10` → misma ley.
- `artículo 12, fracción II` → artículo 12 con `componente="fracción II"`.
- `artículo 12, párrafo tercero` → artículo 12 con `componente="párrafo tercero"`.
- `artículo 1,13, 14` → separar los números.

### 7.2 Referencias explícitas a otra ley

- `artículo 8 de la Ley de Transparencia`
- `la Ley del Seguro Social, en su artículo 140 Bis`
- `artículos 24 y 25 del Código Civil del Estado`

Reglas:

- Buscar el alias más largo primero.
- Normalizar acentos, mayúsculas y puntuación.
- Si la ley está cargada y el artículo existe → `REFIERE_A`.
- Si la ley está cargada y el artículo no existe → referencia rota.
- Si la ley no está cargada → `NormaExterna` + `MENCIONA_NORMA` y reporte.

### 7.3 Rangos

- `artículos 10 a 15` → una arista por cada artículo existente entre 10 y 15.
- `artículos 153-I a 153-N` → expandir por orden documental entre ambos extremos.
- `artículos 10, 12 y 18` → tres aristas.
- `artículos 224 a 228, 230 y 231` → combinar rango y lista.
- Si falta un extremo, crear las aristas de los artículos existentes y reportar el faltante como roto/parcial.
- Las aristas de un mismo rango comparten `grupo_id` y `rango`.

### 7.4 Referencias relativas

- `el artículo anterior`, `el artículo que precede`, `el artículo que antecede` → artículo inmediatamente anterior en `orden`, no “número menos uno”.
- `el artículo siguiente`, `el artículo subsecuente` → siguiente en `orden`.
- Si es el primero o el último, la referencia queda rota.
- `el presente artículo`, `este artículo` → auto-referencia; no genera `REFIERE_A`.
- `la presente Ley`, `este Código`, `el presente ordenamiento` → `MENCIONA_NORMA` a la misma ley, no a un artículo.
- `párrafo tercero` o `fracción II` sin artículo identificable → no inventar destino; reportar como ambigua, salvo que en la misma oración exista un artículo mencionado.

### 7.5 Ambigüedad

- `la ley` a secas no se resuelve automáticamente.
- `Constitución` a secas en un código estatal es ambigua entre federal y local.
- `Código Penal` dentro del Código de Procedimientos Penales sí es resoluble.
- `Código Civil` dentro del Código de Procedimientos Civiles sí es resoluble.
- `historial_dof` no se analiza.

### 7.6 Confianza

- `alta`: artículo y ley explícitos, destino existente.
- `media`: referencia relativa, alias sin calificador o rango parcial.
- `baja`: ambigüedad de ley, destino múltiple o mención incompleta.

---

## 8. Consultas y análisis

Implementar al menos:

1. `citas_directas(articulo_id)`
   - Aristas `REFIERE_A` salientes.
   - Destino, tipo y fragmento.

2. `afectados(articulo_id, transitivo=False)`
   - Artículos que citan al artículo consultado.
   - Directo: solo entrantes.
   - Transitivo: clausura inversa, con caminos y evidencia.

3. `leyes_mas_referenciadas(top=10)`
   - Agrupar referencias entre leyes por ley destino.
   - Contar aristas, artículos origen distintos y artículos destino distintos.

4. `referencias_rotas(filtros)`
   - Filtrar por ley, motivo, artículo origen o destino mencionado.

5. `estadisticas()`
   - Nodos, aristas, artículos más citados, artículos aislados, leyes sin referencias cruzadas.

6. `camino_entre(articulo_a, articulo_b)`
   - Ruta de referencias entre dos artículos, si existe.

Las consultas estructurales deben ser deterministas y no depender de un LLM.

---

## 9. Integración con RAG y chatbot

### 9.1 Principio

El RAG actual se mantiene. El grafo se agrega como capa de recuperación y verificación.

```text
Consulta
   │
   ├──> RAG híbrido actual
   │      ChromaDB + BM25 + RRF + reranking
   │      → fragmentos legales relevantes
   │
   ├──> Graph Retriever
   │      NetworkX
   │      → artículo exacto, citas, citantes, leyes relacionadas
   │
   ▼
Fusión de contexto
   ▼
Groq
   ▼
Respuesta con fuentes, artículos y fragmentos de verificación
```

### 9.2 Dos modos

**Modo estructural:** solo grafo, sin LLM.

Ejemplos:

- “¿Qué artículos cita directamente el artículo 135-A?”
- “¿Qué artículos se ven afectados si modifico el artículo 153-A?”
- “¿Qué leyes se referencian más entre sí?”
- “¿Qué referencias están rotas?”

**Modo chat legal:** RAG + grafo + LLM.

Ejemplo:

> “Me despidieron sin causa justificada, ¿qué puedo hacer?”

- El RAG recupera los artículos relevantes de la LFT.
- El grafo agrega artículos citados y citantes.
- Groq redacta la respuesta.
- La respuesta incluye fundamentos y fragmentos verificables.

### 9.3 Enlace entre chunks y grafo

Los chunks actuales tienen:

```text
documento, articulo, jerarquia
```

Pero `articulo` está truncado en varios casos. En la Fase 7 hay que agregar:

```text
ley_id
articulo_id
numero
es_transitorio
chunk_id estable
```

Opciones:

- **Recomendada:** regenerar `knowledge_chunks` y la colección vectorial con metadatos normalizados.
- **Alternativa:** mantener los chunks actuales y crear un mapa `documento + articulo crudo → articulo_id`, con riesgo de ambigüedad.

Para no romper el chatbot actual, construir una colección nueva `lexis_leyes_mexico_v2` y cambiar a ella solo después de validar.

### 9.4 Módulos de integración

```text
grafo_lexis/recuperador_grafo.py
grafo_lexis/integracion_rag.py
```

La integración debe tocar `segmentacion.py`, `vectorizacion.py`, `buscador.py`, `interaccion.py` y `app.py` solo en la Fase 7.

---

## 10. Exportación

### 10.1 JSON

Formato canónico:

```json
{
  "meta": {
    "schema_version": "1.0",
    "generado_en": "...",
    "fuente": "knowledge_structured",
    "leyes": 6,
    "articulos": 0,
    "aristas": 0
  },
  "nodes": [],
  "edges": [],
  "referencias_rotas": []
}
```

Debe preservar listas y estructuras anidadas.

### 10.2 GraphML

- Para Gephi, yEd u otras herramientas.
- Aplanar listas y diccionarios como cadenas JSON.
- Soportar aristas paralelas.
- Ofrecer opción `--incluir-texto` porque el texto completo puede hacer pesado el archivo.

### 10.3 Neo4j (opcional)

Solo si el usuario lo pide.

- Nodos `Ley`, `Articulo`, `NormaExterna`.
- Relaciones `CONTIENE`, `REFIERE_A`, `MENCIONA_NORMA`.
- Restricciones de unicidad por `id`.
- Índices por `ley_id`, `numero`, `nombre`.
- Script de carga y consultas Cypher de ejemplo.
- Opcional: nodos `ReferenciaRota` y relación `TIENE_REFERENCIA_ROTA`.

---

## 11. Módulos y pruebas

### 11.1 Estructura propuesta

```text
Code/
├── grafo_lexis/
│   ├── __init__.py
│   ├── modelos.py
│   ├── config_leyes.py
│   ├── cargador.py
│   ├── detector_referencias.py
│   ├── constructor_grafo.py
│   ├── consultas.py
│   ├── exportador.py
│   ├── recuperador_grafo.py
│   ├── integracion_rag.py
│   ├── llm_groq.py
│   └── cli.py
└── tests/
    ├── test_cargador.py
    ├── test_referencias_directas.py
    ├── test_referencias_ley.py
    ├── test_rangos.py
    ├── test_relativas.py
    ├── test_rotas.py
    └── test_consultas.py
```

### 11.2 Pruebas mínimas

- Referencia directa dentro de la misma ley.
- Referencia con abreviatura `arts.`.
- Referencia con lista de artículos.
- Referencia explícita a otra ley por nombre.
- Referencia explícita a otra ley por alias.
- Referencia con rango.
- Referencia relativa “artículo anterior”.
- Referencia relativa “artículo siguiente”.
- “La presente Ley” como mención a la ley, no a un artículo.
- Referencia a artículo inexistente.
- Referencia a ley no cargada.
- Normalización de `153-A`, `135-A`, `640 QUATER A`, `229 BIS`.
- Exclusión de `historial_dof`.
- Exclusión de transitorios de las consultas por defecto.
- Varias menciones del mismo par → varias aristas.
- Alias más largo tiene prioridad.
- Consulta de citas directas.
- Consulta de afectados directos y transitivos.
- Consulta de leyes más referenciadas.
- Exportación y relectura de JSON/GraphML.

Usar fixtures pequeños y legibles; además, una prueba de integración con los JSON reales.

### 11.3 LLM opcional

No usar un LLM como detector principal.

El módulo `llm_groq.py` debe:

- Usar `GROQ_API_KEY` desde `.env` o variable de entorno.
- Enviar solo los casos ambiguos o de baja confianza.
- Pedir una salida JSON estructurada.
- Guardar caché de resultados.
- Marcar el resultado como `metodo="llm"`.
- Estar desactivado por defecto.
- No ejecutarse sin autorización del usuario.

Primero medir cuántas ambigüedades quedan con reglas. Si son pocas, el LLM puede ni siquiera ser necesario.

---

## 12. Plan por fases y puertas de validación

### Fase 1 — Revisión de datos y esquema

**Estado:** revisada.

Incluye:

- estructura real de los JSON,
- problemas de transitorios y etiquetas,
- esquema de nodos y aristas,
- reglas de resolución,
- dudas y decisiones pendientes.

**No repetir esta fase** salvo que el usuario lo pida.

### Fase 2 — Carga, nodos y aristas `CONTIENE`

Entregar:

- `modelos.py`,
- `config_leyes.py`,
- `cargador.py`,
- `constructor_grafo.py`,
- nodos `Ley` y `Articulo`,
- aristas `CONTIENE`,
- normalización de etiquetas,
- separación/flag de transitorios,
- estadísticas por ley.

No detectar referencias todavía.

**Puerta:** el usuario valida el conteo de leyes, artículos, transitorios y la normalización.

### Fase 3 — Referencias directas y con ley explícita

Entregar:

- `detector_referencias.py`,
- referencias directas dentro de la misma ley,
- referencias explícitas a otra ley por nombre o alias,
- `REFIERE_A` y `MENCIONA_NORMA`,
- fragmentos y spans,
- reporte de cobertura,
- **20 ejemplos de aristas con su fragmento de texto** para validación.

**Puerta:** el usuario valida los 20 ejemplos.

### Fase 4 — Rangos y referencias relativas

Entregar:

- expansión de rangos,
- listas de artículos,
- `artículo anterior`, `siguiente`, `precede`, `antecede`,
- “la presente Ley” y “este Código”,
- pruebas automatizadas de cada caso.

**Puerta:** todas las pruebas pasan y el usuario valida los casos nuevos.

### Fase 5 — Referencias rotas y consultas

Entregar:

- reporte de referencias rotas,
- `citas_directas`,
- `afectados` directo y transitivo,
- `leyes_mas_referenciadas`,
- `estadisticas`,
- `camino_entre`.

**Puerta:** el usuario valida los reportes y las consultas.

### Fase 6 — Exportación y Neo4j opcional

Entregar:

- exportación JSON,
- exportación GraphML,
- script de carga a Neo4j solo si se solicita,
- consultas Cypher de ejemplo,
- pruebas de exportación/relectura.

**Puerta:** el usuario valida los archivos exportados.

### Fase 7 — Integración GraphRAG con el chatbot

Entregar:

- mapa chunks ↔ `articulo_id`,
- `recuperador_grafo.py`,
- `integracion_rag.py`,
- contexto híbrido RAG + grafo,
- respuestas con fuentes y referencias,
- integración en terminal y Streamlit,
- pruebas de integración.

**Puerta:** el chatbot responde usando el grafo y el RAG, cita fuentes correctas y no rompe el flujo actual.

---

## 13. Restricciones

- Trabajar únicamente en la rama local `Merlin`.
- No tocar `main`.
- No hacer push sin autorización.
- No modificar los JSON originales de `knowledge_structured`.
- Usar `networkx` como librería principal.
- Usar reglas y expresiones regulares primero.
- No usar un LLM como detector principal.
- Mantener el RAG actual; no reemplazarlo.
- No reindexar ChromaDB antes de la Fase 7.
- No corregir silenciosamente errores de los datos: registrar la normalización aplicada.
- No inventar referencias cuando no haya un destino identificable.
- No convertir referencias rotas en nodos ficticios.
- Cada fase debe terminar con un reporte de pendientes y dudas.
- No avanzar si la fase anterior no está validada.

---

## 14. Protocolo de trabajo

En cada fase:

1. Explicar brevemente qué se va a hacer.
2. Implementar solo lo necesario para esa fase.
3. Ejecutar pruebas.
4. Mostrar estadísticas o ejemplos concretos.
5. Señalar decisiones tomadas, pendientes y dudas.
6. Esperar confirmación antes de la siguiente fase.

Si hay ambigüedad en los datos:

- no adivinar en silencio,
- registrar el caso,
- marcarlo como `ambigua` o `rota`,
- pedir validación si afecta el esquema.

Si hay un conflicto entre velocidad y trazabilidad, priorizar trazabilidad.

---

## 15. Criterios de aceptación finales

El proyecto se considera terminado cuando:

- [ ] Las 6 leyes están cargadas y normalizadas.
- [ ] Los artículos con sufijos (`153-A`, `640 QUATER A`, `229 BIS`) tienen IDs correctos.
- [ ] Los transitorios están marcados y excluidos de las consultas por defecto.
- [ ] Existe una arista `CONTIENE` por cada artículo.
- [ ] Las referencias directas, explícitas, rangos y relativas están implementadas.
- [ ] Cada `REFIERE_A` guarda fragmento, span y artículo de origen.
- [ ] Las referencias rotas se reportan sin crear nodos falsos.
- [ ] Las consultas de citas, impacto y leyes más referenciadas funcionan.
- [ ] Hay pruebas automatizadas de todos los tipos de referencia.
- [ ] El grafo se exporta a JSON y GraphML.
- [ ] El chatbot usa el grafo junto con el RAG y cita fuentes.
- [ ] El flujo RAG actual sigue funcionando si el grafo se desactiva.
- [ ] La documentación permite reconstruir el grafo desde cero.
- [ ] Todo el trabajo está en la rama `Merlin`.

---

## 16. Estado actual y siguiente paso

**Fase actual:** Fases 1 a 7 completadas y verificadas.

**Artefactos generados y sincronizados:**
- Paquete `Code/grafo_lexis/` completo (`modelos.py`, `config_leyes.py`, `cargador.py`, `detector_referencias.py`, `constructor_grafo.py`, `consultas.py`, `reporte_rotas.py`, `exportador.py`, `neo4j_loader.py`, `recuperador_grafo.py`, `integracion_rag.py`, `visualizador_obsidian.py`, `llm_groq.py`, `cli.py`).
- Exportaciones persistidas en `knowledge_graph/` (`grafo_lexis.json`, `grafo_lexis.graphml`, `estadisticas_grafo.json`, `reporte_referencias_rotas.json`, `visualizador_cerebro_lexis.html` y carpeta `neo4j/`).
- Sincronización `O(1)` de `articulo_id` y `cve_ley` en los 10,825 chunks de `knowledge_chunks/` y `lexis_vectordb/`.
