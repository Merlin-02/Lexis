"""Interfaz de línea de comandos (CLI) para construir, exportar y consultar el grafo LEXIS."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional
import networkx as nx

from .constructor_grafo import ConstructorGrafoLexis
from .consultas import ConsultasGrafoLexis
from .exportador import ExportadorGrafoLexis
from .neo4j_loader import CargadorNeo4jLexis
from .reporte_rotas import GeneradorReporteRotas, RUTA_KNOWLEDGE_GRAPH_DEFECTO
from .visualizador_obsidian import exportar_html_cerebro_obsidian


def obtener_o_construir_grafo(forzar_reconstruccion: bool = False) -> nx.MultiDiGraph:
    """
    Si ya existe `knowledge_graph/grafo_lexis.json` y no se fuerza reconstrucción,
    lo carga en <0.2s; de lo contrario, construye el grafo completo y lo exporta.
    """
    ruta_json = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "grafo_lexis.json"
    if ruta_json.exists() and not forzar_reconstruccion:
        return ExportadorGrafoLexis.cargar_desde_json(ruta_json)

    constructor = ConstructorGrafoLexis()
    constructor.cargar_y_construir_estructura_base()
    constructor.detectar_y_agregar_referencias_fase4()
    ExportadorGrafoLexis(constructor.grafo).exportar_json(ruta_json)
    GeneradorReporteRotas(constructor.referencias_rotas).guardar_json()
    ConsultasGrafoLexis(constructor.grafo).guardar_estadisticas_json()
    return constructor.grafo


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="grafo_lexis.cli",
        description="CLI del Grafo de Conocimiento Jurídico LEXIS",
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # 1. construir
    p_const = subparsers.add_parser(
        "construir",
        help="Construye el grafo completo desde knowledge_structured/ y guarda todos los artefactos en knowledge_graph/",
    )
    p_const.add_argument(
        "--incluir-transitorios",
        action="store_true",
        help="Incluir también referencias salientes desde artículos transitorios",
    )

    # 2. estadisticas
    subparsers.add_parser(
        "estadisticas",
        help="Muestra las estadísticas globales del grafo y el ranking de leyes y artículos más citados",
    )

    # 3. citas
    p_citas = subparsers.add_parser(
        "citas",
        help="Muestra qué artículos y normas externas cita directamente un artículo",
    )
    p_citas.add_argument("--articulo", required=True, help="Número o ID del artículo (ej. '1470' o 'articulo:cpc_tlax:1470')")
    p_citas.add_argument("--ley", default=None, help="Clave o alias de la ley (ej. 'CPC-TLAX', 'LFT', 'CPEUM')")

    # 4. afectados
    p_afec = subparsers.add_parser(
        "afectados",
        help="Muestra qué artículos se ven afectados si se modifica el artículo indicado",
    )
    p_afec.add_argument("--articulo", required=True, help="Número o ID del artículo (ej. '123' o 'articulo:cpeum:123')")
    p_afec.add_argument("--ley", default=None, help="Clave o alias de la ley (ej. 'CPEUM', 'CC-TLAX')")
    p_afec.add_argument("--profundidad", type=int, default=1, help="Profundidad de saltos (default: 1)")

    # 5. leyes-mas-referenciadas
    subparsers.add_parser(
        "leyes-mas-referenciadas",
        help="Muestra los pares de leyes que más se referencian entre sí",
    )

    # 6. camino
    p_cam = subparsers.add_parser(
        "camino",
        help="Busca el camino más corto entre dos artículos",
    )
    p_cam.add_argument("--origen", required=True, help="ID o número del artículo origen")
    p_cam.add_argument("--destino", required=True, help="ID o número del artículo destino")
    p_cam.add_argument("--ley-origen", default=None, help="Ley del artículo origen")
    p_cam.add_argument("--ley-destino", default=None, help="Ley del artículo destino")
    p_cam.add_argument("--no-dirigido", action="store_true", help="Ignorar dirección de las flechas")

    # 7. reporte-rotas
    p_rotas = subparsers.add_parser(
        "reporte-rotas",
        help="Muestra y guarda el reporte de referencias rotas, externas y ambiguas",
    )
    p_rotas.add_argument("--motivo", default=None, help="Filtrar por motivo (ej. articulo_inexistente, ley_no_cargada)")

    # 8. exportar
    p_exp = subparsers.add_parser(
        "exportar",
        help="Exporta el grafo a JSON, GraphML y/o CSV+Cypher para Neo4j",
    )
    p_exp.add_argument(
        "--formato",
        choices=["todos", "json", "graphml", "neo4j"],
        default="todos",
        help="Formato de exportación (default: todos)",
    )

    # 9. visualizar
    p_vis = subparsers.add_parser(
        "visualizar",
        help="Genera el visualizador interactivo HTML tipo Cerebro de Obsidian en knowledge_graph/visualizador_cerebro_lexis.html",
    )
    p_vis.add_argument(
        "--max-nodos",
        type=int,
        default=200,
        help="Número máximo de nodos en el cerebro interactivo (default: 200)",
    )

    args = parser.parse_args(argv)

    if args.comando == "construir":
        constructor = ConstructorGrafoLexis()
        constructor.cargar_y_construir_estructura_base()
        est_base = constructor.obtener_estadisticas_fase2()
        est_ref = constructor.detectar_y_agregar_referencias_fase4(
            incluir_transitorios=args.incluir_transitorios
        )
        exp = ExportadorGrafoLexis(constructor.grafo)
        r_json = exp.exportar_json()
        r_gml = exp.exportar_graphml()
        r_neo = CargadorNeo4jLexis(constructor.grafo).exportar_artefactos_neo4j()
        r_rotas = GeneradorReporteRotas(constructor.referencias_rotas).guardar_json()
        r_est = ConsultasGrafoLexis(constructor.grafo).guardar_estadisticas_json()
        r_vis = exportar_html_cerebro_obsidian(constructor.grafo)

        salida = {
            "estado": "ok",
            "estructura_base": est_base["global"],
            "referencias": est_ref,
            "archivos_generados": {
                "grafo_json": str(r_json),
                "grafo_graphml": str(r_gml),
                "visualizador_obsidian_html": str(r_vis),
                "reporte_rotas_json": str(r_rotas),
                "estadisticas_json": str(r_est),
                "neo4j_dir": str(r_neo["script_cypher"].parent),
            },
        }
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return 0

    if args.comando == "reporte-rotas":
        constructor = ConstructorGrafoLexis()
        constructor.cargar_y_construir_estructura_base()
        constructor.detectar_y_agregar_referencias_fase4()
        gen = GeneradorReporteRotas(constructor.referencias_rotas)
        gen.guardar_json()
        if args.motivo:
            print(json.dumps(gen.filtrar(motivo=args.motivo), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(gen.generar_reporte()["resumen"], ensure_ascii=False, indent=2))
        return 0

    grafo = obtener_o_construir_grafo()
    consultas = ConsultasGrafoLexis(grafo)

    if args.comando == "estadisticas":
        print(json.dumps(consultas.estadisticas(), ensure_ascii=False, indent=2))
    elif args.comando == "citas":
        print(
            json.dumps(
                consultas.citas_directas(args.articulo, ley=args.ley),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.comando == "afectados":
        print(
            json.dumps(
                consultas.afectados(
                    args.articulo, ley=args.ley, profundidad=args.profundidad
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.comando == "leyes-mas-referenciadas":
        print(json.dumps(consultas.leyes_mas_referenciadas(), ensure_ascii=False, indent=2))
    elif args.comando == "camino":
        print(
            json.dumps(
                consultas.camino_entre(
                    args.origen,
                    args.destino,
                    ley_origen=args.ley_origen,
                    ley_destino=args.ley_destino,
                    dirigido=not args.no_dirigido,
                ),
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.comando == "exportar":
        exp = ExportadorGrafoLexis(grafo)
        generados = {}
        if args.formato in ("todos", "json"):
            generados["json"] = str(exp.exportar_json())
        if args.formato in ("todos", "graphml"):
            generados["graphml"] = str(exp.exportar_graphml())
        if args.formato in ("todos", "neo4j"):
            artefactos = CargadorNeo4jLexis(grafo).exportar_artefactos_neo4j()
            generados["neo4j"] = {k: str(v) for k, v in artefactos.items()}
        print(json.dumps(generados, ensure_ascii=False, indent=2))
    elif args.comando == "visualizar":
        r_html = exportar_html_cerebro_obsidian(grafo, max_nodos=args.max_nodos)
        print(
            json.dumps(
                {
                    "estado": "ok",
                    "visualizador_obsidian_html": str(r_html),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
