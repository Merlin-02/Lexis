"""Exportación CSV, generación de scripts Cypher y carga opcional en Neo4j (Fase 6)."""

import csv
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import networkx as nx

from .reporte_rotas import RUTA_KNOWLEDGE_GRAPH_DEFECTO

CONSULTAS_CYPHER_REFERENCIA = """// =========================================================================
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
"""


class CargadorNeo4jLexis:
    """
    Prepara los artefactos para Neo4j (`nodos_leyes.csv`, `nodos_articulos.csv`,
    `nodos_normas_externas.csv`, `aristas_contiene.csv`, `aristas_refiere_a.csv`,
    `aristas_menciona_norma.csv` y `importar_y_consultar.cypher`), y permite cargar
    directamente en una instancia activa de Neo4j vía `neo4j` Python driver si está disponible.
    """

    def __init__(self, grafo: nx.MultiDiGraph) -> None:
        self.grafo = grafo

    def exportar_artefactos_neo4j(
        self, directorio_salida: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Genera los archivos CSV de nodos/aristas y el archivo `.cypher` en `knowledge_graph/neo4j/`.
        """
        if directorio_salida is None:
            directorio_salida = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "neo4j"
        else:
            directorio_salida = Path(directorio_salida)
        directorio_salida.mkdir(parents=True, exist_ok=True)

        ruta_leyes = directorio_salida / "nodos_leyes.csv"
        ruta_articulos = directorio_salida / "nodos_articulos.csv"
        ruta_externas = directorio_salida / "nodos_normas_externas.csv"
        ruta_contiene = directorio_salida / "aristas_contiene.csv"
        ruta_refiere = directorio_salida / "aristas_refiere_a.csv"
        ruta_menciona = directorio_salida / "aristas_menciona_norma.csv"
        ruta_cypher = directorio_salida / "importar_y_consultar.cypher"

        # 1. Nodos Ley, Articulo y NormaExterna
        with (
            open(ruta_leyes, "w", encoding="utf-8", newline="") as f_ley,
            open(ruta_articulos, "w", encoding="utf-8", newline="") as f_art,
            open(ruta_externas, "w", encoding="utf-8", newline="") as f_ext,
        ):
            w_ley = csv.writer(f_ley)
            w_art = csv.writer(f_art)
            w_ext = csv.writer(f_ext)

            w_ley.writerow(
                ["id", "clave", "nombre_oficial", "nombre_corto", "tipo_norma", "ambito", "materia"]
            )
            w_art.writerow(
                [
                    "id",
                    "ley_id",
                    "numero",
                    "numero_base",
                    "sufijo",
                    "etiqueta_normalizada",
                    "orden",
                    "jerarquia",
                    "es_transitorio",
                ]
            )
            w_ext.writerow(["id", "nombre", "en_corpus"])

            for node_id, data in self.grafo.nodes(data=True):
                tipo_nodo = data.get("tipo_nodo")
                if tipo_nodo == "Ley":
                    w_ley.writerow(
                        [
                            node_id,
                            data.get("clave", ""),
                            data.get("nombre_oficial", ""),
                            data.get("nombre_corto", ""),
                            data.get("tipo_norma", ""),
                            data.get("ambito", ""),
                            data.get("materia", ""),
                        ]
                    )
                elif tipo_nodo == "Articulo":
                    w_art.writerow(
                        [
                            node_id,
                            data.get("ley_id", ""),
                            data.get("numero", ""),
                            data.get("numero_base", 0),
                            data.get("sufijo") or "",
                            data.get("etiqueta_normalizada", ""),
                            data.get("orden", 0),
                            data.get("jerarquia", ""),
                            data.get("es_transitorio", False),
                        ]
                    )
                elif tipo_nodo == "NormaExterna":
                    w_ext.writerow(
                        [
                            node_id,
                            data.get("nombre", ""),
                            data.get("en_corpus", False),
                        ]
                    )

        # 2. Aristas CONTIENE, REFIERE_A y MENCIONA_NORMA
        with (
            open(ruta_contiene, "w", encoding="utf-8", newline="") as f_con,
            open(ruta_refiere, "w", encoding="utf-8", newline="") as f_ref,
            open(ruta_menciona, "w", encoding="utf-8", newline="") as f_men,
        ):
            w_con = csv.writer(f_con)
            w_ref = csv.writer(f_ref)
            w_men = csv.writer(f_men)

            w_con.writerow(["origen_id", "destino_id", "orden", "jerarquia"])
            w_ref.writerow(
                [
                    "id",
                    "origen_id",
                    "destino_id",
                    "origen_ley_id",
                    "destino_ley_id",
                    "clase",
                    "relacion",
                    "componente",
                    "rango",
                    "grupo_id",
                    "texto_referencia",
                    "snippet",
                    "confianza",
                    "metodo",
                ]
            )
            w_men.writerow(
                [
                    "id",
                    "origen_id",
                    "destino_id",
                    "articulo_mencionado",
                    "texto_referencia",
                    "snippet",
                    "confianza",
                ]
            )

            for u, v, k, data in self.grafo.edges(keys=True, data=True):
                tipo = data.get("tipo")
                if tipo == "CONTIENE":
                    w_con.writerow(
                        [u, v, data.get("orden", 0), data.get("jerarquia", "")]
                    )
                elif tipo == "REFIERE_A":
                    w_ref.writerow(
                        [
                            data.get("id", str(k)),
                            u,
                            v,
                            data.get("origen_ley_id", ""),
                            data.get("destino_ley_id", ""),
                            data.get("clase", ""),
                            data.get("relacion", ""),
                            data.get("componente") or "",
                            data.get("rango") or "",
                            data.get("grupo_id") or "",
                            data.get("texto_referencia", ""),
                            data.get("snippet", ""),
                            data.get("confianza", ""),
                            data.get("metodo", ""),
                        ]
                    )
                elif tipo == "MENCIONA_NORMA":
                    w_men.writerow(
                        [
                            data.get("id", str(k)),
                            u,
                            v,
                            data.get("articulo_mencionado") or "",
                            data.get("texto_referencia", ""),
                            data.get("snippet", ""),
                            data.get("confianza", ""),
                        ]
                    )

        # 3. Script Cypher con restricciones, carga CSV y consultas de referencia
        with open(ruta_cypher, "w", encoding="utf-8") as f_cyp:
            f_cyp.write(CONSULTAS_CYPHER_REFERENCIA)

        return {
            "nodos_leyes": ruta_leyes,
            "nodos_articulos": ruta_articulos,
            "nodos_normas_externas": ruta_externas,
            "aristas_contiene": ruta_contiene,
            "aristas_refiere_a": ruta_refiere,
            "aristas_menciona_norma": ruta_menciona,
            "script_cypher": ruta_cypher,
        }

    def cargar_en_neo4j(
        self,
        uri: Optional[str] = None,
        usuario: Optional[str] = None,
        password: Optional[str] = None,
        limpiar_previo: bool = False,
    ) -> Dict[str, int]:
        """
        Conecta con una instancia Neo4j mediante el driver oficial `neo4j` (si está instalado)
        e inserta por lotes los nodos y aristas del grafo.
        """
        try:
            from neo4j import GraphDatabase  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "El paquete 'neo4j' no está instalado en el entorno. "
                "Use 'exportar_artefactos_neo4j()' para obtener los CSV y el script Cypher, "
                "o instale el driver con: pip install neo4j"
            ) from exc

        uri_efectiva = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        usr_efectivo = usuario or os.environ.get("NEO4J_USER", "neo4j")
        pwd_efectivo = password or os.environ.get("NEO4J_PASSWORD", "")

        leyes_batch: List[Dict[str, Any]] = []
        arts_batch: List[Dict[str, Any]] = []
        ext_batch: List[Dict[str, Any]] = []

        for node_id, data in self.grafo.nodes(data=True):
            t = data.get("tipo_nodo")
            if t == "Ley":
                leyes_batch.append(
                    {
                        "id": node_id,
                        "clave": data.get("clave"),
                        "nombre_oficial": data.get("nombre_oficial"),
                        "nombre_corto": data.get("nombre_corto"),
                        "ambito": data.get("ambito"),
                        "materia": data.get("materia"),
                    }
                )
            elif t == "Articulo":
                arts_batch.append(
                    {
                        "id": node_id,
                        "ley_id": data.get("ley_id"),
                        "numero": data.get("numero"),
                        "numero_base": data.get("numero_base"),
                        "sufijo": data.get("sufijo"),
                        "etiqueta_normalizada": data.get("etiqueta_normalizada"),
                        "orden": data.get("orden"),
                        "jerarquia": data.get("jerarquia"),
                    }
                )
            elif t == "NormaExterna":
                ext_batch.append({"id": node_id, "nombre": data.get("nombre")})

        contiene_batch: List[Dict[str, Any]] = []
        refiere_batch: List[Dict[str, Any]] = []
        menciona_batch: List[Dict[str, Any]] = []

        for u, v, k, data in self.grafo.edges(keys=True, data=True):
            t = data.get("tipo")
            if t == "CONTIENE":
                contiene_batch.append(
                    {"origen_id": u, "destino_id": v, "orden": data.get("orden")}
                )
            elif t == "REFIERE_A":
                refiere_batch.append(
                    {
                        "id": data.get("id", str(k)),
                        "origen_id": u,
                        "destino_id": v,
                        "clase": data.get("clase"),
                        "relacion": data.get("relacion"),
                        "componente": data.get("componente"),
                        "rango": data.get("rango"),
                        "texto_referencia": data.get("texto_referencia"),
                        "snippet": data.get("snippet"),
                    }
                )
            elif t == "MENCIONA_NORMA":
                menciona_batch.append(
                    {
                        "id": data.get("id", str(k)),
                        "origen_id": u,
                        "destino_id": v,
                        "articulo_mencionado": data.get("articulo_mencionado"),
                        "texto_referencia": data.get("texto_referencia"),
                        "snippet": data.get("snippet"),
                    }
                )

        driver = GraphDatabase.driver(uri_efectiva, auth=(usr_efectivo, pwd_efectivo))
        with driver.session() as session:
            if limpiar_previo:
                session.run("MATCH (n) DETACH DELETE n")
            session.run(
                "UNWIND $rows AS row MERGE (l:Ley {id: row.id}) SET l += row",
                rows=leyes_batch,
            )
            session.run(
                "UNWIND $rows AS row MERGE (a:Articulo {id: row.id}) SET a += row",
                rows=arts_batch,
            )
            session.run(
                "UNWIND $rows AS row MERGE (n:NormaExterna {id: row.id}) SET n += row",
                rows=ext_batch,
            )
            session.run(
                "UNWIND $rows AS row MATCH (l:Ley {id: row.origen_id}), (a:Articulo {id: row.destino_id}) "
                "MERGE (l)-[r:CONTIENE]->(a) SET r.orden = row.orden",
                rows=contiene_batch,
            )
            session.run(
                "UNWIND $rows AS row MATCH (o {id: row.origen_id}), (d {id: row.destino_id}) "
                "MERGE (o)-[r:REFIERE_A {id: row.id}]->(d) SET r += row",
                rows=refiere_batch,
            )
            session.run(
                "UNWIND $rows AS row MATCH (o:Articulo {id: row.origen_id}), (d:NormaExterna {id: row.destino_id}) "
                "MERGE (o)-[r:MENCIONA_NORMA {id: row.id}]->(d) SET r += row",
                rows=menciona_batch,
            )
        driver.close()

        return {
            "nodos_ley": len(leyes_batch),
            "nodos_articulo": len(arts_batch),
            "nodos_norma_externa": len(ext_batch),
            "aristas_contiene": len(contiene_batch),
            "aristas_refiere_a": len(refiere_batch),
            "aristas_menciona_norma": len(menciona_batch),
        }
