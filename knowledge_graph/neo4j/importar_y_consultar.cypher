// =========================================================================
// 1. RESTRICCIONES DE UNICIDAD E ÍNDICES EN NEO4J 5+
// =========================================================================
CREATE CONSTRAINT ley_id_unico IF NOT EXISTS
FOR (l:Ley) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT articulo_id_unico IF NOT EXISTS
FOR (a:Articulo) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT norma_externa_id_unico IF NOT EXISTS
FOR (n:NormaExterna) REQUIRE n.id IS UNIQUE;

CREATE INDEX articulo_numero_idx IF NOT EXISTS
FOR (a:Articulo) ON (a.ley_id, a.numero);

// =========================================================================
// 2. CONSULTAS DE ANÁLISIS JURÍDICO EN CYPHER
// =========================================================================

// Consulta A: ¿Qué artículos cita directamente un artículo específico? (ej. articulo:cpc_tlax:1470)
MATCH (origen:Articulo {id: $articulo_id})-[r:REFIERE_A]->(destino)
RETURN origen.id AS origen,
       destino.id AS destino,
       labels(destino) AS tipo_destino,
       r.clase AS clase,
       r.relacion AS relacion,
       r.componente AS componente,
       r.texto_referencia AS texto_referencia,
       r.snippet AS snippet;

// Consulta B: ¿Qué artículos se ven afectados si se modifica o deroga el artículo X? (1 a 2 saltos)
MATCH camino = (afectado:Articulo)-[r:REFIERE_A*1..2]->(objetivo:Articulo {id: $articulo_id})
RETURN afectado.id AS articulo_afectado,
       afectado.ley_id AS ley_afectada,
       length(camino) AS saltos_distancia,
       [n IN nodes(camino) | n.id] AS cadena_dependencia;

// Consulta C: ¿Qué leyes del corpus se referencian más entre sí?
MATCH (a1:Articulo)-[r:REFIERE_A {relacion: 'entre_leyes'}]->(a2:Articulo)
RETURN r.origen_ley_id AS ley_origen,
       r.destino_ley_id AS ley_destino,
       count(r) AS total_referencias
ORDER BY total_referencias DESC;

// Consulta D: Top 15 artículos más citados en todo el corpus
MATCH (origen:Articulo)-[r:REFIERE_A]->(destino:Articulo)
RETURN destino.id AS articulo_id,
       destino.etiqueta_normalizada AS etiqueta,
       destino.ley_id AS ley_id,
       count(r) AS total_citas_recibidas
ORDER BY total_citas_recibidas DESC
LIMIT 15;

// Consulta E: Normas externas (fuera del corpus) más mencionadas
MATCH (a:Articulo)-[m:MENCIONA_NORMA]->(ne:NormaExterna)
RETURN ne.id AS norma_externa_id,
       ne.nombre AS nombre_norma,
       count(m) AS total_menciones
ORDER BY total_menciones DESC;
