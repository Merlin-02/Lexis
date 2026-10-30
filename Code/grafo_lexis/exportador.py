"""Exportación e importación del grafo jurídico LEXIS a JSON y GraphML (Fase 6)."""

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import networkx as nx

from .reporte_rotas import RUTA_KNOWLEDGE_GRAPH_DEFECTO


class ExportadorGrafoLexis:
    """
    Gestiona la persistencia del grafo `MultiDiGraph`:
      1. `exportar_json` / `cargar_desde_json`: serialización completa de nodos y aristas en
         `knowledge_graph/grafo_lexis.json` para carga instantánea (< 0.2s) desde CLI o GraphRAG.
      2. `exportar_graphml`: exportación compatible con el estándar XML GraphML
         (`knowledge_graph/grafo_lexis.graphml`) convirtiendo listas/diccionarios/None a escalares
         para que Gephi, Cytoscape o yEd lo abran sin errores.
    """

    def __init__(self, grafo: nx.MultiDiGraph) -> None:
        self.grafo = grafo

    def exportar_json(
        self,
        ruta_salida: Optional[Path] = None,
        incluir_texto_completo: bool = True,
    ) -> Path:
        """
        Guarda el grafo completo (nodos y aristas con todas sus propiedades) en formato JSON.
        """
        if ruta_salida is None:
            RUTA_KNOWLEDGE_GRAPH_DEFECTO.mkdir(parents=True, exist_ok=True)
            ruta_salida = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "grafo_lexis.json"
        else:
            ruta_salida = Path(ruta_salida)
            ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        nodos_serializados: List[Dict[str, Any]] = []
        for node_id, data in self.grafo.nodes(data=True):
            copia = dict(data)
            copia["id"] = node_id
            if not incluir_texto_completo and "texto_completo" in copia:
                copia.pop("texto_completo", None)
            nodos_serializados.append(copia)

        aristas_serializadas: List[Dict[str, Any]] = []
        for u, v, k, data in self.grafo.edges(keys=True, data=True):
            copia_e = dict(data)
            copia_e["origen_id"] = u
            copia_e["destino_id"] = v
            copia_e["key"] = str(k)
            aristas_serializadas.append(copia_e)

        documento = {
            "metadata": {
                "proyecto": "LEXIS - Grafo de Conocimiento Jurídico",
                "fecha_exportacion": datetime.now().isoformat(timespec="seconds"),
                "total_nodos": len(nodos_serializados),
                "total_aristas": len(aristas_serializadas),
                "tipo_grafo": "MultiDiGraph",
            },
            "nodos": nodos_serializados,
            "aristas": aristas_serializadas,
        }

        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(documento, f, ensure_ascii=False, indent=2)

        return ruta_salida

    @staticmethod
    def cargar_desde_json(ruta_entrada: Optional[Path] = None) -> nx.MultiDiGraph:
        """
        Reconstruye el `nx.MultiDiGraph` directamente desde `knowledge_graph/grafo_lexis.json`.
        """
        if ruta_entrada is None:
            ruta_entrada = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "grafo_lexis.json"
        else:
            ruta_entrada = Path(ruta_entrada)

        if not ruta_entrada.exists():
            raise FileNotFoundError(
                f"No existe el archivo de grafo en '{ruta_entrada}'. Ejecute primero el comando 'construir'."
            )

        with open(ruta_entrada, "r", encoding="utf-8") as f:
            documento = json.load(f)

        grafo = nx.MultiDiGraph()
        for nodo in documento.get("nodos", []):
            node_id = nodo["id"]
            grafo.add_node(node_id, **nodo)

        for arista in documento.get("aristas", []):
            copia = dict(arista)
            u = copia.get("origen_id")
            v = copia.get("destino_id")
            k = copia.pop("key", copia.get("id"))
            grafo.add_edge(u, v, key=k, **copia)

        return grafo

    def exportar_graphml(
        self,
        ruta_salida: Optional[Path] = None,
        incluir_texto_completo: bool = False,
    ) -> Path:
        """
        Exporta el grafo en formato XML GraphML (`knowledge_graph/grafo_lexis.graphml`).
        Por defecto `incluir_texto_completo=False` para mantener el archivo ligero y ágil en
        Gephi / Cytoscape, conservando etiquetas, jerarquías, snippets y metadatos de aristas.
        """
        if ruta_salida is None:
            RUTA_KNOWLEDGE_GRAPH_DEFECTO.mkdir(parents=True, exist_ok=True)
            ruta_salida = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "grafo_lexis.graphml"
        else:
            ruta_salida = Path(ruta_salida)
            ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        grafo_limpio = nx.MultiDiGraph()

        for node_id, data in self.grafo.nodes(data=True):
            atributos_nodo: Dict[str, Any] = {}
            for k, val in data.items():
                if not incluir_texto_completo and k in {
                    "texto_completo",
                    "texto_general",
                    "fracciones",
                    "incisos_directos",
                }:
                    continue
                atributos_nodo[k] = self._sanitizar_valor_graphml(val)
            # Añadir atributo 'label' estándar para visualizadores como Gephi/Cytoscape
            atributos_nodo["label"] = str(
                data.get("etiqueta_normalizada")
                or data.get("nombre_corto")
                or data.get("nombre")
                or node_id
            )
            grafo_limpio.add_node(node_id, **atributos_nodo)

        for u, v, k, data in self.grafo.edges(keys=True, data=True):
            atributos_arista: Dict[str, Any] = {}
            for prop, val in data.items():
                atributos_arista[prop] = self._sanitizar_valor_graphml(val)
            atributos_arista["label"] = str(data.get("tipo", "RELACION"))
            grafo_limpio.add_edge(u, v, key=str(k), **atributos_arista)

        nx.write_graphml(grafo_limpio, str(ruta_salida), encoding="utf-8")
        return ruta_salida

    @staticmethod
    def _sanitizar_valor_graphml(valor: Any) -> Any:
        """Convierte None, listas y diccionarios en tipos escalares admitidos por GraphML."""
        if valor is None:
            return ""
        if isinstance(valor, (bool, int, float, str)):
            return valor
        if isinstance(valor, list):
            if all(isinstance(x, str) for x in valor):
                return " | ".join(valor)
            return json.dumps(valor, ensure_ascii=False)
        if isinstance(valor, dict):
            return json.dumps(valor, ensure_ascii=False)
        return str(valor)
