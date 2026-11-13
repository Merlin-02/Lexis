# Reporte de Pruebas de Usabilidad y Validación Jurídica — LEXIS (Etapa 5)

**Fecha de corte:** `2026-11-12T18:21:51`

## 1. Resumen Ejecutivo de Participación y Desempeño

| Indicador | Valor |
| :--- | :--- |
| **Usuarios registrados totales** | 6 (4 área jurídica Tlaxcala / 2 usuarios generales) |
| **Sesiones registradas** | 6 (6 finalizadas / 0 en curso) |
| **Consultas jurídicas evaluadas** | 16 |
| **Tasa de aprobación (Like vs. Dislike)** | **93.75%** (15 Like / 1 Dislike) |
| **Calificación promedio por respuesta (0–5 estrellas)** | **4.69 / 5.00** (DE: ±0.58) |
| **Calificación global de experiencia al cierre (0–5 estrellas)** | **4.67 / 5.00** (DE: ±0.47) |
| **Tiempo promedio de respuesta (RAG + GraphRAG + LLM)** | **2.03 s** |
| **Promedio de nodos del grafo jurídico activados por consulta** | **3.69 nodos** |

## 2. Desglose por Perfil de Evaluador

| Perfil de Usuario | Consultas Evaluadas | Likes | Dislikes | % Aprobación | Promedio Estrellas (0–5) | Desv. Estándar |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Abogados / Estudiantes de Derecho o afín (Tlaxcala) | 10 | 10 | 0 | 100.0% | 4.8 / 5.0 | ±0.4 |
| Usuarios Generales / Ciudadanos | 6 | 5 | 1 | 83.33% | 4.5 / 5.0 | ±0.76 |

## 3. Desglose por Normativa / Materia Jurídica

| Normativa / Materia | Consultas | Likes | Dislikes | % Aprobación | Estrellas (0–5) | Tiempo Prom. (s) | Nodos Grafo Prom. |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Codigo Civil Tlaxcala** | 5 | 4 | 1 | 80.0% | 4.4 (±0.8) | 2.16 s | 3.6 |
| **Constitucion** | 1 | 1 | 0 | 100.0% | 5.0 (±0.0) | 1.87 s | 4.0 |
| **Código Penal Tlaxcala** | 3 | 3 | 0 | 100.0% | 5.0 (±0.0) | 2.01 s | 3.33 |
| **Ley Trabajo** | 3 | 3 | 0 | 100.0% | 5.0 (±0.0) | 2.07 s | 4.33 |
| **Procedimiento Civiles Tlaxcala** | 2 | 2 | 0 | 100.0% | 5.0 (±0.0) | 1.94 s | 4.0 |
| **Procedimiento Penal Tlaxcala** | 2 | 2 | 0 | 100.0% | 4.0 (±0.0) | 1.86 s | 3.0 |

## 4. Retroalimentación y Observaciones Jurídicas (Licenciados en Derecho y Evaluadores)

- **[Ley Trabajo]** *Merlin (Usuario General)* — Calificación: `LIKE` (5/5 estrellas): "Explicación muy clara sobre el aviso de rescisión del artículo 47 de la LFT." *(Consulta: "hola que tal como puedo saber los motivos fundamentados de despido o de renuncia")*
- **[Código Penal Tlaxcala]** *Elena Rojas Rugerio (Usuario General)* — Calificación: `LIKE` (5/5 estrellas): "Identificó con precisión los artículos 321, 322 y 330 del Código Penal de Tlaxcala sobre robo de vehículo." *(Consulta: "que hago si me robaron mi carro")*
- **[Codigo Civil Tlaxcala]** *Elena Rojas Rugerio (Usuario General)* — Calificación: `LIKE` (5/5 estrellas): "Fundamentó adecuadamente la obligación alimentaria en los artículos 149, 156 y 387 del Código Civil de Tlaxcala." *(Consulta: "es necesario que yo le de pension alimenticia a mi hijo")*
- **[Codigo Civil Tlaxcala]** *Elena Rojas Rugerio (Usuario General)* — Calificación: `DISLIKE` (3/5 estrellas): "En la consulta corta sin contexto recuperó artículos de sucesiones antes de precisar la manutención." *(Consulta: "pero solo tiene mi apellido")*
- **[Codigo Civil Tlaxcala]** *Elena Rojas Rugerio (Usuario General)* — Calificación: `LIKE` (5/5 estrellas): "Con contexto adicional precisó el reconocimiento de hijos en el artículo 199 del Código Civil de Tlaxcala." *(Consulta: "pero ese niño del que me piden manutencion solo tiene mi apellido ")*
- **[Ley Trabajo]** *Lic. Alejandro Morales Xicohténcatl (Licenciado en Derecho / Abogado)* — Calificación: `LIKE` (5/5 estrellas): "Excelente recuperación del artículo 47 y 48 de la LFT y expansión por grafo hacia los artículos 43, 50 y 161. El desglose de los tres meses de salario e intereses moratorios es jurídicamente exacto." *(Consulta: "¿Cuáles son las causas de rescisión de la relación laboral sin responsabilidad para el patrón y cómo se calcula la indemnización del artículo 48 de la LFT?")*
- **[Procedimiento Civiles Tlaxcala]** *Lic. Alejandro Morales Xicohténcatl (Licenciado en Derecho / Abogado)* — Calificación: `LIKE` (5/5 estrellas): "Destacable precisión del GraphRAG: el nodo semilla articulo:cpc_tlax:1470 expandió automáticamente las citas inter-ley hacia articulo:cc_tlax:240-C y articulo:cc_tlax:240-D." *(Consulta: "¿Qué requisitos establece la legislación de Tlaxcala para tramitar la revocación de la adopción y qué artículos del Código Civil cita el artículo 1470 procesal?")*
- **[Procedimiento Civiles Tlaxcala]** *Lic. Alejandro Morales Xicohténcatl (Licenciado en Derecho / Abogado)* — Calificación: `LIKE` (5/5 estrellas): "Recuperación exacta de los artículos 567, 578 y 588 del Código de Procedimientos Civiles de Tlaxcala." *(Consulta: "¿Cuándo causan ejecutoria las sentencias definitivas en materia procesal civil en Tlaxcala y cómo procede el embargo en ejecución de sentencia?")*
- **[Código Penal Tlaxcala]** *Lic. Valeria Hernández Cuamatzi (Licenciado en Derecho / Abogado)* — Calificación: `LIKE` (5/5 estrellas): "Identifica correctamente el artículo 229 y 229 Bis del Código Penal de Tlaxcala y las razones de género." *(Consulta: "¿Cómo se tipifica y sanciona el delito de feminicidio en el Código Penal de Tlaxcala?")*
- **[Procedimiento Penal Tlaxcala]** *Lic. Valeria Hernández Cuamatzi (Licenciado en Derecho / Abogado)* — Calificación: `LIKE` (4/5 estrellas): "Citación puntual de los artículos 8 Bis, 91 y 92 del Código de Procedimientos Penales de Tlaxcala. El grafo detectó incluso la remisión al Código Penal." *(Consulta: "¿Qué delitos requieren querella de la víctima u ofendido en el procedimiento penal de Tlaxcala y cuándo procede la detención en flagrancia?")*
- **[Código Penal Tlaxcala]** *Lic. Valeria Hernández Cuamatzi (Licenciado en Derecho / Abogado)* — Calificación: `LIKE` (5/5 estrellas): "Los artículos 268 (extorsión) y 338-339 (fraude) del Código Penal de Tlaxcala fueron recuperados con fidelidad textual." *(Consulta: "¿Qué establece el Código Penal de Tlaxcala respecto al delito de fraude y la extorsión?")*
- **[Constitucion]** *Diego Fernando Tlapale (Estudiante de Derecho)* — Calificación: `LIKE` (5/5 estrellas): "Recuperación completa de los artículos 1o., 14, 16 y 123 de la CPEUM incluyendo fracciones e incisos." *(Consulta: "¿Qué garantías de legalidad y audiencia consagran los artículos 1, 14 y 16 de la Constitución Política y qué regula el artículo 123 sobre el derecho al trabajo?")*
- **[Ley Trabajo]** *Diego Fernando Tlapale (Estudiante de Derecho)* — Calificación: `LIKE` (5/5 estrellas): "Citación exacta de los artículos 76, 80 y 87 de la LFT." *(Consulta: "¿Cuántos días de vacaciones pagadas y qué porcentaje de prima vacacional y aguinaldo corresponden conforme a la Ley Federal del Trabajo?")*
- **[Codigo Civil Tlaxcala]** *Mariana Cortés Netzahual (Estudiante de Derecho)* — Calificación: `LIKE` (5/5 estrellas): "Citación precisa del artículo 2008 y correlativos del Código Civil de Tlaxcala sobre arrendamiento." *(Consulta: "¿Qué obligaciones tienen el arrendador y el arrendatario según el Código Civil de Tlaxcala en un contrato de arrendamiento?")*
- **[Codigo Civil Tlaxcala]** *Mariana Cortés Netzahual (Estudiante de Derecho)* — Calificación: `LIKE` (4/5 estrellas): "Recuperó correctamente los artículos 2596 y 2606 del Código Civil de Tlaxcala." *(Consulta: "¿Cómo se define el testamento y la herencia en el Código Civil de Tlaxcala?")*

## 5. Comentarios de Experiencia Final y Sugerencias de Mejora

- **Merlin** (*Usuario General*, `5/5 estrellas`): "Me ayudó a entender que el patrón está obligado a darme aviso por escrito si me despide."
- **Elena Rojas Rugerio** (*Usuario General*, `4/5 estrellas`): "Resolvió mis dudas tanto del robo de vehículo como de pensión alimenticia en Tlaxcala."
- **Lic. Alejandro Morales Xicohténcatl** (*Licenciado en Derecho / Abogado*, `5/5 estrellas`): "El enlace entre los artículos sustantivos y procesales a través del grafo jurídico agiliza notablemente la verificación de remisiones entre el Código Civil y el Código de Procedimientos Civiles de Tlaxcala."
- **Lic. Valeria Hernández Cuamatzi** (*Licenciado en Derecho / Abogado*, `5/5 estrellas`): "Muy útil para validar tipos penales locales del Código Penal de Tlaxcala y verificar delitos perseguibles por querella en el artículo 8 Bis procesal."
- **Diego Fernando Tlapale** (*Estudiante de Derecho*, `5/5 estrellas`): "El texto completo de las fracciones e incisos del artículo 123 constitucional y de la LFT ahora se muestra íntegro y facilita mucho el estudio de derecho constitucional y laboral."
- **Mariana Cortés Netzahual** (*Estudiante de Derecho*, `4/5 estrellas`): "El visualizador interactivo tipo Obsidian ayuda mucho a identificar cómo se relacionan los artículos de arrendamiento, contratos y sucesiones en el Código Civil de Tlaxcala."

### Sugerencias para trabajo futuro registradas al cierre:
- **Merlin** (*Usuario General*): "Incluir formato ejemplo de solicitud ante el Centro de Conciliación."
- **Elena Rojas Rugerio** (*Usuario General*): "Mantener el hilo del tema familiar cuando se hacen preguntas breves de seguimiento."
- **Lic. Alejandro Morales Xicohténcatl** (*Licenciado en Derecho / Abogado*): "Incorporar jurisprudencia del Vigésimo Octavo Circuito aplicable al Estado de Tlaxcala."
- **Lic. Valeria Hernández Cuamatzi** (*Licenciado en Derecho / Abogado*): "Añadir comparativa directa con el Código Nacional de Procedimientos Penales (CNPP)."
- **Diego Fernando Tlapale** (*Estudiante de Derecho*): "Agregar modo de cuestionario de autoevaluación para estudiantes de Derecho."
- **Mariana Cortés Netzahual** (*Estudiante de Derecho*): "Permitir exportar directamente el subgrafo de la consulta como imagen PNG."
