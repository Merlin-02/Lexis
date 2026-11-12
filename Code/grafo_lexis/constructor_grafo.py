"""Constructor del grafo de conocimiento jurídico con NetworkX (MultiDiGraph)."""

from typing import Dict, List, Any, Optional
import networkx as nx

from .modelos import (
    NodoLey,
    NodoArticulo,
    NodoNormaExterna,
    AristaContiene,
    AristaRefiereA,
    AristaMencionaNorma,
    ReferenciaRota,
)
from .cargador import cargar_corpus_completo
from .detector_referencias import DetectorReferencias
from .config_leyes import RUTA_CONOCIMIENTO_ESTRUCTURADO
from pathlib import Path
from collections import Counter


class ConstructorGrafoLexis:
    """Construye y gestiona el MultiDiGraph de leyes y artículos de LEXIS."""

    def __init__(self) -> None:
        self.grafo: nx.MultiDiGraph = nx.MultiDiGraph()
        self.leyes: Dict[str, NodoLey] = {}
        self.articulos_por_ley: Dict[str, List[NodoArticulo]] = {}
        self.indice_articulos: Dict[str, NodoArticulo] = {}
        self.normas_externas: Dict[str, NodoNormaExterna] = {}
        self.aristas_refiere_a: List[AristaRefiereA] = []
        self.aristas_menciona_norma: List[AristaMencionaNorma] = []
        self.referencias_rotas: List[ReferenciaRota] = []

    def cargar_y_construir_estructura_base(
        self, directorio: Path = RUTA_CONOCIMIENTO_ESTRUCTURADO
    ) -> nx.MultiDiGraph:
        """
        Fase 2: Carga las leyes y artículos del corpus, agrega los nodos
        Ley y Articulo, y crea las aristas CONTIENE.
        """
        self.leyes, self.articulos_por_ley = cargar_corpus_completo(directorio=directorio)

        for slug, nodo_ley in self.leyes.items():
            self.grafo.add_node(nodo_ley.id, **nodo_ley.to_dict())

            for nodo_art in self.articulos_por_ley[slug]:
                self.grafo.add_node(nodo_art.id, **nodo_art.to_dict())
                self.indice_articulos[nodo_art.id] = nodo_art

                arista = AristaContiene(
                    origen_id=nodo_ley.id,
                    destino_id=nodo_art.id,
                    orden=nodo_art.orden,
                    jerarquia=nodo_art.jerarquia,
                )
                self.grafo.add_edge(
                    nodo_ley.id,
                    nodo_art.id,
                    key=f"CONTIENE:{nodo_art.orden}",
                    **arista.to_dict(),
                )

        return self.grafo

    def obtener_estadisticas_fase2(self) -> Dict[str, Any]:
        """
        Calcula estadísticas detalladas por ley y globales para validación de la Fase 2.
        Por defecto separa conteo de artículos ordinarios y transitorios.
        """
        por_ley: Dict[str, Dict[str, Any]] = {}
        total_registros = 0
        total_ordinarios = 0
        total_transitorios = 0
        total_con_sufijo = 0
        total_texto_vacio = 0
        total_reconstruidos = 0
        total_aristas_contiene = 0

        for slug, nodo_ley in self.leyes.items():
            arts = self.articulos_por_ley.get(slug, [])
            ordinarios = [a for a in arts if not a.es_transitorio]
            transitorios = [a for a in arts if a.es_transitorio]
            con_sufijo = [a for a in ordinarios if a.sufijo is not None]
            vacios = [a for a in arts if a.texto_vacio]
            reconstruidos = [
                a for a in arts
                if a.reconstruccion_aplicada
                and a.reconstruccion_aplicada != "limpieza_ordinal_texto"
            ]

            aristas_ley = [
                (u, v, d)
                for u, v, d in self.grafo.out_edges(nodo_ley.id, data=True)
                if d.get("tipo") == "CONTIENE"
            ]

            por_ley[nodo_ley.clave] = {
                "ley_id": nodo_ley.id,
                "nombre_oficial": nodo_ley.nombre_oficial,
                "fuente_json": nodo_ley.fuente_json,
                "total_registros": len(arts),
                "articulos_ordinarios": len(ordinarios),
                "transitorios_y_decretos": len(transitorios),
                "con_sufijo": len(con_sufijo),
                "texto_general_vacio": len(vacios),
                "etiquetas_reconstruidas": len(reconstruidos),
                "aristas_contiene": len(aristas_ley),
            }

            total_registros += len(arts)
            total_ordinarios += len(ordinarios)
            total_transitorios += len(transitorios)
            total_con_sufijo += len(con_sufijo)
            total_texto_vacio += len(vacios)
            total_reconstruidos += len(reconstruidos)
            total_aristas_contiene += len(aristas_ley)

        nodos_ley = [
            n for n, d in self.grafo.nodes(data=True) if d.get("tipo_nodo") == "Ley"
        ]
        nodos_art = [
            n for n, d in self.grafo.nodes(data=True) if d.get("tipo_nodo") == "Articulo"
        ]

        return {
            "global": {
                "nodos_ley": len(nodos_ley),
                "nodos_articulo_totales": len(nodos_art),
                "articulos_ordinarios_activos": total_ordinarios,
                "transitorios_excluidos_por_defecto": total_transitorios,
                "articulos_con_sufijo": total_con_sufijo,
                "articulos_texto_general_vacio": total_texto_vacio,
                "etiquetas_reconstruidas": total_reconstruidos,
                "aristas_contiene": total_aristas_contiene,
                "ids_unicos_verificados": len(nodos_art) == total_registros,
            },
            "por_ley": por_ley,
        }

    def detectar_y_agregar_referencias_fase3(
        self, incluir_transitorios: bool = False
    ) -> Dict[str, Any]:
        """
        Fase 3: Ejecuta DetectorReferencias para referencias directas y con ley explícita,
        agrega nodos NormaExterna y aristas REFIERE_A y MENCIONA_NORMA al grafo.
        """
        return self._ejecutar_deteccion_referencias(
            incluir_transitorios=incluir_transitorios,
            incluir_rangos_y_relativas=False,
        )

    def detectar_y_agregar_referencias_fase4(
        self, incluir_transitorios: bool = False
    ) -> Dict[str, Any]:
        """
        Fase 4: Ejecuta DetectorReferencias incluyendo rangos expandidos y referencias
        relativas (a artículos anteriores/siguientes y a la propia ley).
        """
        return self._ejecutar_deteccion_referencias(
            incluir_transitorios=incluir_transitorios,
            incluir_rangos_y_relativas=True,
        )

    def _ejecutar_deteccion_referencias(
        self,
        incluir_transitorios: bool = False,
        incluir_rangos_y_relativas: bool = False,
    ) -> Dict[str, Any]:
        """Limpia aristas de referencia previas (si existen) y ejecuta la detección solicitada."""
        # Limpiar posibles aristas de referencia previas para evitar duplicados al re-ejecutar
        aristas_a_remover = [
            (u, v, k)
            for u, v, k, d in self.grafo.edges(keys=True, data=True)
            if d.get("tipo") in {"REFIERE_A", "MENCIONA_NORMA"}
        ]
        for u, v, k in aristas_a_remover:
            self.grafo.remove_edge(u, v, key=k)

        detector = DetectorReferencias(self.leyes, self.articulos_por_ley)
        resultado = detector.detectar_en_corpus(
            incluir_transitorios=incluir_transitorios,
            incluir_rangos_y_relativas=incluir_rangos_y_relativas,
        )

        self.normas_externas = resultado["normas_externas"]
        self.aristas_refiere_a = resultado["aristas_refiere_a"]
        self.aristas_menciona_norma = resultado["aristas_menciona_norma"]
        self.referencias_rotas = resultado["referencias_rotas"]

        for ext_id, nodo_ext in self.normas_externas.items():
            self.grafo.add_node(ext_id, **nodo_ext.to_dict())

        for arista_ref in self.aristas_refiere_a:
            self.grafo.add_edge(
                arista_ref.origen_id,
                arista_ref.destino_id,
                key=arista_ref.id,
                **arista_ref.to_dict(),
            )

        for arista_m in self.aristas_menciona_norma:
            self.grafo.add_edge(
                arista_m.origen_id,
                arista_m.destino_id,
                key=arista_m.id,
                **arista_m.to_dict(),
            )

        return self.obtener_estadisticas_fase3()

    def obtener_estadisticas_fase3(self) -> Dict[str, Any]:
        """Devuelve estadísticas de cobertura y desglose de aristas creadas en Fase 3."""
        por_clase = Counter(a.clase for a in self.aristas_refiere_a)
        por_relacion = Counter(a.relacion for a in self.aristas_refiere_a)
        por_ley_origen = Counter(a.origen_ley_id for a in self.aristas_refiere_a)
        pares_entre_leyes = Counter(
            f"{a.origen_ley_id} -> {a.destino_ley_id}"
            for a in self.aristas_refiere_a
            if a.relacion == "entre_leyes"
        )
        motivos_rotas = Counter(r.motivo for r in self.referencias_rotas)

        return {
            "total_refiere_a": len(self.aristas_refiere_a),
            "total_menciona_norma": len(self.aristas_menciona_norma),
            "total_normas_externas": len(self.normas_externas),
            "total_referencias_rotas_o_externas": len(self.referencias_rotas),
            "por_clase": dict(por_clase),
            "por_relacion": dict(por_relacion),
            "por_ley_origen": dict(por_ley_origen),
            "entre_leyes_pares": dict(pares_entre_leyes.most_common()),
            "motivos_no_resueltas": dict(motivos_rotas),
        }

