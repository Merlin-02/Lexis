# Plan de Acción — Cierre y Estabilización del Proyecto LEXIS

**Fecha de elaboración:** Noviembre 2026  
**Rama base:** `feature/grafo`  
**Avance actual estimado:** ~88%  
**Objetivo:** Llevar el sistema LEXIS del estado actual al **100% de completitud técnica, documental y experimental**, corrigiendo los defectos críticos detectados en la auditoría, sincronizando las bases de conocimiento (ChromaDB y Grafo Legal), consolidando los resultados de las **pruebas de usabilidad con usuarios reales** y blindando el despliegue en producción.

---

## Mapa de Dependencias y Orden de Ejecución

```
┌─────────────────────────────────────────────────────────────────────────┐
│ FASE 1: Hotfixes Críticos e Integridad del Grafo (Prioridad Inmediata)  │
│  1.1 Restaurar UTF-8 en interaccion.py (acentos y 'ñ' hacia Groq)       │
│  1.2 Reparar lectura de incisos en cargador.py y regenerar el Grafo     │
│  1.3 Corregir bugs en app.py (vecinos del grafo y fallback temático)    │
│  1.4 Blindar seguridad (LEXIS_ADMIN_KEY, MODELO_GROQ) y borrar prueba.py│
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FASE 2: Saneamiento de Reglas Jurídicas y Sincronización Vectorial      │
│  2.1 Limpiar vocabulario corrupto y prioridades en analizador_legal.py  │
│  2.2 Auditar y corregir artículos de Tlaxcala en indice_tematico.py     │
│  2.3 Inyectar articulo_id canónico en segmentacion.py y ChromaDB        │
│  2.4 Corregir tests con efectos secundarios en test_unidades.py         │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FASE 3: Pruebas de Usabilidad con Usuarios Reales y Análisis (Etapa 5)  │
│  3.1 Completar campaña de sesiones de evaluación con usuarios reales    │
│  3.2 Script de análisis y reporte de sesiones (sesiones_evaluacion/)    │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ FASE 4: Persistencia Concurrente, Mejoras UX y Cierre Documental        │
│  4.1 Bloqueo de concurrencia (filelock / escritura atómica) en sesiones │
│  4.2 Exportación de dictamen/consulta para el usuario final en app.py   │
│  4.3 Sincronizar DOCUMENTACION_COMPLETA.json, PROMPT_GRAFO y README.md  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## FASE 1: Hotfixes Críticos e Integridad del Grafo (Prioridad Crítica)

> **Por qué va primero:** Actualmente el LLM recibe textos mutilados sin acentos ni letras `ñ`, y los nodos del grafo legal (que también alimentan el buscador en Railway) tienen vacío el texto de todos los incisos. Ninguna métrica ni prueba con usuarios será fidedigna hasta corregir esto.

### Tarea 1.1 — Eliminar mutilación ASCII en `Code/interaccion.py`
- **Archivo:** `Code/interaccion.py` (líneas 170–171 y línea 294)
- **Problema:** Se fuerza `.encode('ascii', errors='ignore').decode('ascii')` sobre `user_prompt` y `system_prompt`, convirtiendo `"año"` en `"ao"`, `"niño"` en `"nio"`, `"daño"` en `"dao"`, `"cónyuge"` en `"cnyuge"` y `"artículo"` en `"artculo"`.
- **Acción:**
  1. En `llamar_groq()` (`Code/interaccion.py:169-171`), eliminar la conversión a ASCII o reemplazarla por normalización Unicode segura (`unicodedata.normalize("NFC", texto)`) que conserve íntegramente los caracteres en español (`á, é, í, ó, ú, ü, ñ, ¿, ¡`).
  2. En `Code/interaccion.py:294`, eliminar `.encode('ascii', errors='ignore').decode('ascii')` del mensaje de error de excepción.
- **Criterio de aceptación:** Al imprimir o inspeccionar el payload enviado a `client.chat.completions.create`, las palabras acentuadas y con `ñ` tanto de `Prompt.txt` como de los artículos recuperados se conservan intactas.

### Tarea 1.2 — Reparar pérdida de texto de incisos en `Code/grafo_lexis/cargador.py` y regenerar el Grafo
- **Archivo:** `Code/grafo_lexis/cargador.py` (líneas 94–104)
- **Problema:** `Code/preparacion.py` (línea 136) guarda el contenido de los incisos bajo la llave `"texto_general"`, pero `construir_texto_completo()` en `cargador.py` busca `inc.get("texto", "")`. Como resultado, todos los incisos aparecen vacíos (`"Inciso a)"`) en `knowledge_graph/grafo_lexis.json` y en el motor ligero de Railway (`buscador.py`).
- **Acción:**
  1. En `Code/grafo_lexis/cargador.py` (líneas 97 y 103), cambiar:
     ```python
     inc_texto = (inc.get("texto", "") or inc.get("texto_general", "")).strip()
     ```
  2. Añadir un test unitario en `Code/tests/test_cargador.py` que verifique que el `texto_completo` de un artículo con incisos (p. ej. `CPEUM:ART:123` o `LFT:ART:51`) incluya el texto íntegro de sus incisos.
  3. Reconstruir y re-exportar todos los artefactos del grafo ejecutando:
     ```bash
     cd Code
     python -m grafo_lexis.cli construir --exportar-todo
     ```
  4. Eliminar archivos de caché BM25 desfasados en `lexis_vectordb/cache/` para que se regeneren con el texto completo.
- **Criterio de aceptación:** `knowledge_graph/grafo_lexis.json` contiene el texto completo de todos los incisos y el número de referencias detectadas (`REFIERE_A`) se actualiza reflejando las citas presentes dentro de incisos.

### Tarea 1.3 — Corregir bugs de integración en `Code/app.py`
- **Archivo:** `Code/app.py` (líneas 971–982 y 1006–1010)
- **Problemas:**
  1. **Vecinos del grafo no registrados en sesiones (`L1007-L1008`):** Se lee `v.get("nodo_id")`, pero `expandir_contexto_hits()` en `Code/grafo_lexis/recuperador_grafo.py:191` devuelve la clave `"articulo_id"`.
  2. **Fallback temático sin texto normativo (`L971-L982`):** Cuando la búsqueda híbrida no supera el umbral y entra el respaldo de `indice_tematico.py`, `app.py` inyecta solo el título `'Fundamento legal temático sobre...'` sin buscar el texto real del artículo en `diccionario_textos`, impidiendo que el LLM cite o explique el artículo.
- **Acción:**
  1. En `Code/app.py:1007-1008`, cambiar `v.get("nodo_id")` por `v.get("articulo_id") or v.get("nodo_id")`.
  2. En `Code/app.py:971-982`, replicar la búsqueda en `diccionario_metadatos` y `diccionario_textos` (o consultar directamente el nodo en `grafo_lexis` vía `consultas.py`) para inyectar el texto real del artículo en `resultados_finales`.
- **Criterio de aceptación:** En `sesiones_evaluacion/`, el arreglo `nodos_grafo_usados` registra IDs reales (ej. `["LFT:ART:47", "LFT:ART:48"]`) y las consultas que activan el índice temático reciben el texto completo del artículo.

### Tarea 1.4 — Seguridad, parametrización de entorno y limpieza de archivos
- **Archivos:** `Code/app.py`, `Code/interaccion.py`, `Code/grafo_lexis/llm_groq.py`, `Code/.env.example`, `Code/prueba.py`
- **Acciones:**
  1. **Parametrizar modelo Groq:** En `Code/interaccion.py:51` y `Code/grafo_lexis/llm_groq.py:18`, cambiar a:
     ```python
     MODELO_GROQ = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
     ```
     y documentar `GROQ_MODEL` en `Code/.env.example`.
  2. **Proteger panel de administración (`Code/app.py:835`):** Eliminar la contraseña por defecto hardcodeada `"lexis_admin_2026"`. Leer `admin_pass = os.getenv("LEXIS_ADMIN_KEY")` y solo habilitar la validación si la variable de entorno está definida y no es vacía.
  3. **Eliminar archivo ajeno al proyecto:** Borrar `Code/prueba.py`.
- **Criterio de aceptación:** `Code/prueba.py` ya no existe en el repositorio; el panel de administración no expone datos de usuarios con una clave pública por defecto.

---

## FASE 2: Saneamiento de Reglas Jurídicas y Sincronización Vectorial (Prioridad Alta)

### Tarea 2.1 — Depurar `Code/analizador_legal.py`
- **Archivo:** `Code/analizador_legal.py`
- **Problemas detectados:**
  - Artefactos corruptos en `PALABRAS_CLAVE_POR_AREA`: `' innocence'` (L102), falta de coma entre `'servicios públicos'` y `'obligación alimentaria'` (L134), `'垂recautelar'` (L136), `'治外法権'` (L160), `'ley делега'` (L213), `'页码'` (L265), `'cosa慕容'` (L317), `'cosajoin'` y `'cosa join'` repetido 6 veces (L318–319), `'indicio'` repetido 7 veces (L328), `'por дело'` (L409–410).
  - `PRIORIDAD_AREAS` (L577–584) tiene todas las áreas con valor `6` (y `constitucional: 5`), contradiciendo el diseño de desempate.
  - `generar_consulta_corregida()` (L761–780) devuelve `return consulta` en ambas ramas sin hacer nada.
- **Acción:**
  1. Eliminar todas las cadenas corruptas, duplicados y palabras en otros idiomas en `PALABRAS_CLAVE_POR_AREA` y separar `'servicios públicos'`, `'obligación alimentaria'`.
  2. Calibrar `PRIORIDAD_AREAS` según el peso real esperado en orientación ciudadana (o documentar la decisión de pesos).
  3. Implementar la lógica real en `generar_consulta_corregida()` (por ejemplo, expandiendo abreviaturas legales comunes como `art.` → `artículo`, `fracc.` → `fracción`, `LFT` → `Ley Federal del Trabajo`) o simplificar su contrato.
- **Criterio de aceptación:** Ninguna lista en `analizador_legal.py` contiene caracteres no latinos ni elementos duplicados; todos los tests de clasificación en `Code/test_unidades.py` pasan al 100%.

### Tarea 2.2 — Auditar y corregir `Code/indice_tematico.py` contra el Grafo Legal
- **Archivo:** `Code/indice_tematico.py`
- **Problema:** Contiene `"Artículo atán."` en el tema `"denuncia"` (línea 213) y varios números de artículos asignados al Código Civil y Código Penal de Tlaxcala no coinciden con la numeración real de los PDFs procesados en `knowledge_structured/`.
- **Acción:**
  1. Crear un script de verificación (o test en `Code/tests/`) que cruce cada entrada de `INDICE_TEMATICO` contra los nodos reales de `knowledge_graph/grafo_lexis.json`.
  2. Reemplazar `"Artículo atán."` y actualizar los números de artículos desfasados por los identificadores y artículos vigentes reales en el corpus indexado, añadiendo además la llave opcional `"articulo_id"` (ej. `"CCT:ART:..."`) para enlace directo con el grafo.
- **Criterio de aceptación:** El 100% de las entradas en `INDICE_TEMATICO` resuelven a un nodo existente en `grafo_lexis.json`.

### Tarea 2.3 — Sincronizar `articulo_id` entre `knowledge_chunks/` (ChromaDB) y el Grafo Legal
- **Archivos:** `Code/segmentacion.py`, `Code/vectorizacion.py`, `Code/grafo_lexis/recuperador_grafo.py`
- **Problema:** Los 10,825 chunks en `knowledge_chunks/` fueron creados antes del grafo y carecen del metadato `articulo_id` (además de tener etiquetas crudas como `"Artículo 153-"`).
- **Acción:**
  1. En `Code/segmentacion.py`, reutilizar la función de normalización de `Code/grafo_lexis/cargador.py` para incluir `"articulo_id"` (ej. `"LFT:ART:153_A"`) y `"cve_ley"` dentro de `metadata` en cada chunk generado.
  2. Ejecutar `python Code/segmentacion.py` y `python Code/vectorizacion.py` para actualizar `knowledge_chunks/` y `lexis_vectordb/`.
  3. En `Code/grafo_lexis/recuperador_grafo.py:mapear_hit_a_nodo_articulo()`, priorizar la lectura directa de `metadata.get("articulo_id")` en $O(1)$ y dejar las expresiones regulares actuales como respaldo.
- **Criterio de aceptación:** El 100% de los chunks en `knowledge_chunks/*_chunks.json` cuentan con el campo `metadata.articulo_id` válido en `grafo_lexis.json`.

### Tarea 2.4 — Corregir pruebas unitarias en `Code/test_unidades.py`
- **Archivo:** `Code/test_unidades.py` (líneas 170–187 y 283–336)
- **Acción:**
  1. Hacer que `TestBuscador.test_preprocesar_texto` importe y evalúe la función real `preprocesar_texto` de `buscador.py`.
  2. Modificar `TestMejoras.test_historial_busquedas` y `TestGestorErrores` para que utilicen `tempfile.TemporaryDirectory()` en lugar de escribir en `lexis_vectordb/cache/historial.json` y `lexis_vectordb/logs/errores.jsonl`.
- **Criterio de aceptación:** Ejecutar `pytest Code/test_unidades.py Code/tests/ -v` pasa al 100% sin modificar ningún archivo rastreado ni ensuciar `lexis_vectordb/`.

---

## FASE 3: Evaluación mediante Pruebas de Usabilidad con Usuarios Reales (Prioridad Alta — Cierre Etapa 5)

> **Enfoque de evaluación adoptado:** En lugar de un dataset sintético (*Ground Truth*), la validación del desempeño, relevancia del contexto y fidelidad jurídica del sistema se realiza directamente mediante **pruebas de usabilidad estructuradas con usuarios reales y estudiantes/profesionales del derecho** a través del sistema de evaluación integrado en la interfaz web (`gestor_evaluacion.py` + `sesiones_evaluacion/`).

### Tarea 3.1 — Completar Campaña de Evaluación de Sesiones con Usuarios Reales
- **Archivos:** `Code/app.py`, `Code/gestor_evaluacion.py`, `sesiones_evaluacion/evaluaciones_consolidado.json`
- **Acción:**
  - Con los hotfixes de la Fase 1 y Fase 2 aplicados, ejecutar las sesiones de prueba con usuarios reales (ciudadanos, estudiantes de derecho y abogados) en la interfaz de Streamlit.
  - Recolectar en cada consulta:
    - Calificación binaria de utilidad (`👍 Sí me sirvió` / `👎 No fue útil`).
    - Calificación en escala de 0 a 5 estrellas.
    - Retroalimentación cualitativa y correcciones jurídicas sugeridas por los evaluadores.
    - Trazabilidad automática de artículos recuperados, relevancia híbrida, área detectada, tiempo de respuesta y nodos del grafo expandidos (`nodos_grafo_usados`).
  - Recolectar la encuesta global al finalizar cada sesión (calificación general, facilidad de uso, utilidad percibida del grafo legal, percepción de velocidad y recomendación).

### Tarea 3.2 — Script de Procesamiento Estadístico y Reporte de Usabilidad (`Code/reporte_evaluaciones.py`)
- **Archivo a crear:** `Code/reporte_evaluaciones.py`
- **Acción:**
  - Procesar automáticamente `sesiones_evaluacion/evaluaciones_consolidado.json` y `sesiones_evaluacion/usuarios.json` para generar un resumen estadístico listo para el documento terminal / reporte final:
    1. **Métricas por consulta:** Tasa de aprobación (% de respuestas útiles), promedio de estrellas (0–5) global y desglosado por área legal (`laboral`, `civil`, `penal`, `constitucional`, `procesal`), tiempo promedio de respuesta (`tiempo_respuesta_seg`) y promedio de relevancia de búsqueda híbrida.
    2. **Impacto del Grafo Legal:** Comparativa de calificación promedio en respuestas con expansión de nodos del grafo (`nodos_grafo_usados`) y valoración directa de los usuarios sobre la visualización del grafo.
    3. **Métricas de experiencia global:** Facilidad de uso, satisfacción por perfil de usuario (estudiante/abogado vs. ciudadano) y tasa de recomendación.
  - Exportar el resumen en `sesiones_evaluacion/resumen_metricas_usabilidad.json` y en una tabla Markdown lista para integrar en `README.md`.

---

## FASE 4: Persistencia Concurrente, Mejoras UX y Cierre Documental (Prioridad Media/Baja)

### Tarea 4.1 — Blindar Concurrencia en `gestor_usuarios.py` y `gestor_evaluacion.py`
- **Archivos:** `Code/gestor_usuarios.py`, `Code/gestor_evaluacion.py`
- **Problema:** Escrituras concurrentes de varios usuarios evaluando al mismo tiempo en Streamlit sobre `usuarios.json` y `evaluaciones_consolidado.json` pueden generar condiciones de carrera (*race conditions*) o pérdida de registros.
- **Acción:**
  - Implementar escritura atómica mediante archivo temporal + `os.replace()` protegido con un lock (`threading.RLock()` + `fcntl.flock` en Linux) en todas las operaciones de guardado de `gestor_usuarios.py` y `gestor_evaluacion.py`.

### Tarea 4.2 — Exportación de Consulta para el Usuario Final en `Code/app.py`
- **Archivo:** `Code/app.py`
- **Acción:**
  - Agregar en la interfaz de usuario un botón `"📄 Descargar orientación legal (.md / .txt)"` que permita al ciudadano descargar el historial de su consulta actual junto con los artículos citados y el aviso legal.

### Tarea 4.3 — Sincronización Documental Final
- **Archivos:** `DOCUMENTACION_COMPLETA.json`, `PROMPT_GRAFO_LEGAL.md`, `README.md`
- **Acción:**
  1. Actualizar `PROMPT_GRAFO_LEGAL.md` (líneas 13 y 801–803) cambiando el estado a *"Fases 1 a 7 completadas y verificadas"*.
  2. Actualizar `DOCUMENTACION_COMPLETA.json` con la arquitectura actual, las métricas de usabilidad obtenidas en la Fase 3 y los nuevos módulos (`app.py`, `gestor_evaluacion.py`, `gestor_usuarios.py`, `Code/grafo_lexis/`).
  3. Incorporar la tabla de resultados de las pruebas de usabilidad con usuarios reales en `README.md`.

---

## Checklist Rápido de Control de Avance

- [x] **1.1** Quitar filtro ASCII destructivo en `Code/interaccion.py`
- [x] **1.2** Corregir lectura de `texto_general` en `Code/grafo_lexis/cargador.py` y regenerar `knowledge_graph/`
- [x] **1.3** Corregir `articulo_id` de vecinos y texto de fallback temático en `Code/app.py`
- [x] **1.4** Parametrizar `GROQ_MODEL`, proteger `LEXIS_ADMIN_KEY` y eliminar `Code/prueba.py`
- [x] **2.1** Limpiar palabras corruptas y calibrar prioridades en `Code/analizador_legal.py`
- [x] **2.2** Auditar y corregir artículos de Tlaxcala en `Code/indice_tematico.py`
- [x] **2.3** Añadir `articulo_id` en `Code/segmentacion.py` y re-indexar `lexis_vectordb/`
- [x] **2.4** Aislar efectos secundarios en disco de `Code/test_unidades.py`
- [x] **3.1** Completar sesiones de evaluación de usabilidad con usuarios reales en `sesiones_evaluacion/`
- [x] **3.2** Crear script `Code/reporte_evaluaciones.py` para consolidar estadísticas y métricas de usabilidad
- [x] **4.1** Añadir escritura atómica y lock de concurrencia en `gestor_usuarios.py` y `gestor_evaluacion.py`
- [x] **4.2** Añadir botón de descarga de orientación legal para el usuario en `Code/app.py`
- [x] **4.3** Actualizar `DOCUMENTACION_COMPLETA.json`, `PROMPT_GRAFO_LEGAL.md` y métricas finales en `README.md`
