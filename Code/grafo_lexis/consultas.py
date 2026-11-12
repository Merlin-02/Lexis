"""Motor de consultas deterministas sobre el grafo de conocimiento jurídico LEXIS (Fase 5)."""

from collections import Counter, deque
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import networkx as nx

from .config_leyes import CATALOGO_LEYES, normalizar_texto_comparacion
from .detector_referencias import parsear_token_articulo
from .reporte_rotas import RUTA_KNOWLEDGE_GRAPH_DEFECTO


class ConsultasGrafoLexis:
    """
    Ejecuta consultas de análisis jurídico sobre el `MultiDiGraph` de LEXIS:
      1. `citas_directas`: ¿qué artículos o normas cita directamente el artículo X?
      2. `afectados`: ¿qué artículos se ven afectados directa o indirectamente si modifico el artículo X?
      3. `leyes_mas_referenciadas`: ¿qué leyes se referencian más entre sí (y hacia normas externas)?
      4. `articulos_mas_citados`: ranking de artículos con mayor número de citas entrantes (in-degree).
      5. `camino_entre`: camino más corto entre dos artículos del grafo.
      6. `estadisticas`: métricas globales y por ley del grafo.
    """

    def __init__(self, grafo: nx.MultiDiGraph) -> None:
        self.grafo = grafo

    def resolver_id_ley(self, ley: str) -> Optional[str]:
        """
        Convierte una clave, slug o alias (ej. 'CC-TLAX', 'cc_tlax', 'Código Civil', 'ley:cc_tlax')
        en el ID canónico del nodo Ley ('ley:<slug>').
        """
        limpio = ley.strip()
        if limpio.startswith("ley:") and self.grafo.has_node(limpio):
            return limpio

        slug_cand = limpio.lower().replace("-", "_")
        if self.grafo.has_node(f"ley:{slug_cand}"):
            return f"ley:{slug_cand}"

        norm = normalizar_texto_comparacion(limpio)
        for slug, cfg in CATALOGO_LEYES.items():
            if norm == normalizar_texto_comparacion(cfg["clave"]) or norm == slug:
                return f"ley:{slug}"
            for alias in cfg["alias"]:
                if norm == normalizar_texto_comparacion(alias):
                    return f"ley:{slug}"
        return None

    def resolver_id_articulo(
        self, articulo_o_id: str, ley: Optional[str] = None
    ) -> Optional[str]:
        """
        Acepta tanto un ID canónico ('articulo:cc_tlax:1409-BIS') como un par
        (articulo='1409 Bis', ley='CC-TLAX') y devuelve el ID canónico en el grafo.
        """
        limpio = articulo_o_id.strip()
        if limpio.startswith("articulo:") and self.grafo.has_node(limpio):
            return limpio

        if ley is None:
            return None

        ley_id = self.resolver_id_ley(ley)
        if not ley_id:
            return None
        ley_slug = ley_id.split(":", 1)[1]

        # Quitar prefijo "Artículo" si el usuario lo incluyó
        limpio_num = limpio
        for pref in ("artículo", "articulo", "art."):
            if limpio_num.lower().startswith(pref):
                limpio_num = limpio_num[len(pref) :].strip()

        parsed = parsear_token_articulo(limpio_num)
        if parsed:
            _, _, slug_num = parsed
            cand_id = f"articulo:{ley_slug}:{slug_num}"
            if self.grafo.has_node(cand_id):
                return cand_id

        cand_directo = f"articulo:{ley_slug}:{limpio_num.upper().replace(' ', '-')}"
        if self.grafo.has_node(cand_directo):
            return cand_directo

        return None

    def citas_directas(
        self,
        articulo_id: str,
        ley: Optional[str] = None,
        incluir_referencias_a_ley: bool = False,
    ) -> Dict[str, Any]:
        """
        Responde: ¿Qué artículos (y normas externas) cita directamente el artículo X?
        Inspecciona las aristas salientes `REFIERE_A` y `MENCIONA_NORMA` desde `articulo_id`.
        """
        nodo_id = self.resolver_id_articulo(articulo_id, ley)
        if not nodo_id or not self.grafo.has_node(nodo_id):
            raise ValueError(f"No se encontró el artículo '{articulo_id}' (ley={ley}) en el grafo.")

        datos_origen = self.grafo.nodes[nodo_id]
        articulos_citados: List[Dict[str, Any]] = []
        leyes_propias_citadas: List[Dict[str, Any]] = []
        normas_externas_citadas: List[Dict[str, Any]] = []

        for _, dest_id, _, edge_data in self.grafo.out_edges(nodo_id, keys=True, data=True):
            tipo_arista = edge_data.get("tipo")
            datos_dest = self.grafo.nodes.get(dest_id, {})

            if tipo_arista == "REFIERE_A":
                if datos_dest.get("tipo_nodo") == "Ley":
                    if incluir_referencias_a_ley:
                        leyes_propias_citadas.append(
                            {
                                "destino_id": dest_id,
                                "nombre_corto": datos_dest.get("nombre_corto"),
                                "clase": edge_data.get("clase"),
                                "texto_referencia": edge_data.get("texto_referencia"),
                                "snippet": edge_data.get("snippet"),
                            }
                        )
                    continue

                articulos_citados.append(
                    {
                        "destino_id": dest_id,
                        "etiqueta": datos_dest.get("etiqueta_normalizada"),
                        "ley_destino": edge_data.get("destino_ley_id"),
                        "clase": edge_data.get("clase"),
                        "relacion": edge_data.get("relacion"),
                        "componente": edge_data.get("componente"),
                        "rango": edge_data.get("rango"),
                        "texto_referencia": edge_data.get("texto_referencia"),
                        "snippet": edge_data.get("snippet"),
                        "confianza": edge_data.get("confianza"),
                    }
                )
            elif tipo_arista == "MENCIONA_NORMA":
                normas_externas_citadas.append(
                    {
                        "destino_id": dest_id,
                        "norma_externa": datos_dest.get("nombre"),
                        "articulo_mencionado": edge_data.get("articulo_mencionado"),
                        "texto_referencia": edge_data.get("texto_referencia"),
                        "snippet": edge_data.get("snippet"),
                    }
                )

        return {
            "articulo_origen": {
                "id": nodo_id,
                "etiqueta": datos_origen.get("etiqueta_normalizada"),
                "ley_id": datos_origen.get("ley_id"),
                "jerarquia": datos_origen.get("jerarquia"),
            },
            "total_articulos_citados": len(articulos_citados),
            "total_normas_externas_citadas": len(normas_externas_citadas),
            "articulos_citados": articulos_citados,
            "normas_externas_citadas": normas_externas_citadas,
            "referencias_a_propia_ley": leyes_propias_citadas,
        }

    def afectados(
        self,
        articulo_id: str,
        ley: Optional[str] = None,
        profundidad: int = 1,
    ) -> Dict[str, Any]:
        """
        Responde: ¿Qué artículos se ven afectados si modifico o derogo el artículo X?
        Realiza una búsqueda en anchura inversa (BFS sobre aristas entrantes `REFIERE_A`)
        hasta `profundidad` saltos (1 = impacto directo, 2+ = impacto transitivo en cascada).
        """
        nodo_id = self.resolver_id_articulo(articulo_id, ley)
        if not nodo_id or not self.grafo.has_node(nodo_id):
            raise ValueError(f"No se encontró el artículo '{articulo_id}' (ley={ley}) en el grafo.")

        if profundidad < 1:
            raise ValueError("La profundidad debe ser al menos 1.")

        datos_objetivo = self.grafo.nodes[nodo_id]
        visitados: Set[str] = {nodo_id}
        cola: deque[Tuple[str, int, List[str]]] = deque([(nodo_id, 0, [nodo_id])])

        impactos_por_nivel: Dict[int, List[Dict[str, Any]]] = {}
        todos_afectados: List[Dict[str, Any]] = []

        while cola:
            actual_id, nivel_actual, ruta = cola.popleft()
            if nivel_actual >= profundidad:
                continue

            # Explorar quiénes citan a `actual_id` (in_edges con tipo == REFIERE_A)
            for orig_id, _, _, edge_data in self.grafo.in_edges(actual_id, keys=True, data=True):
                if edge_data.get("tipo") != "REFIERE_A":
                    continue
                datos_orig = self.grafo.nodes.get(orig_id, {})
                if datos_orig.get("tipo_nodo") != "Articulo":
                    continue

                nuevo_nivel = nivel_actual + 1
                nueva_ruta = [orig_id] + ruta
                registro_impacto = {
                    "articulo_afectado_id": orig_id,
                    "etiqueta": datos_orig.get("etiqueta_normalizada"),
                    "ley_id": datos_orig.get("ley_id"),
                    "distancia_saltos": nuevo_nivel,
                    "cita_a": actual_id,
                    "clase": edge_data.get("clase"),
                    "relacion": edge_data.get("relacion"),
                    "componente": edge_data.get("componente"),
                    "texto_referencia": edge_data.get("texto_referencia"),
                    "snippet": edge_data.get("snippet"),
                    "cadena_dependencia": " -> ".join(nueva_ruta),
                }
                impactos_por_nivel.setdefault(nuevo_nivel, []).append(registro_impacto)
                todos_afectados.append(registro_impacto)

                if orig_id not in visitados:
                    visitados.add(orig_id)
                    cola.append((orig_id, nuevo_nivel, nueva_ruta))

        articulos_unicos_afectados = {item["articulo_afectado_id"] for item in todos_afectados}
        por_ley_afectada = Counter(item["ley_id"] for item in todos_afectados)

        return {
            "articulo_modificado": {
                "id": nodo_id,
                "etiqueta": datos_objetivo.get("etiqueta_normalizada"),
                "ley_id": datos_objetivo.get("ley_id"),
                "jerarquia": datos_objetivo.get("jerarquia"),
            },
            "profundidad_maxima": profundidad,
            "total_aristas_impacto": len(todos_afectados),
            "total_articulos_unicos_afectados": len(articulos_unicos_afectados),
            "por_ley_afectada": dict(por_ley_afectada),
            "por_nivel": impactos_por_nivel,
            "afectados": todos_afectados,
        }

    def leyes_mas_referenciadas(self) -> Dict[str, Any]:
        """
        Responde: ¿Qué leyes se referencian más entre sí (y qué leyes reciben más citas)?
        Devuelve:
          - `pares_entre_leyes_distintas`: ranking de (ley_origen -> ley_destino) con `relacion == 'entre_leyes'`.
          - `citas_internas_por_ley`: total de referencias internas (`misma_ley` entre artículos) de cada ley.
          - `ranking_leyes_mas_citadas_externamente`: leyes del corpus que más referencias reciben desde otras leyes.
          - `normas_externas_mas_citadas`: leyes fuera del corpus más mencionadas (`MENCIONA_NORMA`).
        """
        pares_cruzados: Counter[Tuple[str, str]] = Counter()
        internas_art_a_art: Counter[str] = Counter()
        internas_art_a_ley: Counter[str] = Counter()
        recibidas_desde_otra_ley: Counter[str] = Counter()
        emitidas_hacia_otra_ley: Counter[str] = Counter()
        normas_externas_cnt: Counter[Tuple[str, str]] = Counter()

        for u, v, data in self.grafo.edges(data=True):
            tipo = data.get("tipo")
            if tipo == "REFIERE_A":
                orig_ley = data.get("origen_ley_id")
                dest_ley = data.get("destino_ley_id")
                relacion = data.get("relacion")
                if relacion == "entre_leyes" and orig_ley and dest_ley:
                    pares_cruzados[(orig_ley, dest_ley)] += 1
                    recibidas_desde_otra_ley[dest_ley] += 1
                    emitidas_hacia_otra_ley[orig_ley] += 1
                elif relacion == "misma_ley" and orig_ley:
                    if str(v).startswith("ley:"):
                        internas_art_a_ley[orig_ley] += 1
                    else:
                        internas_art_a_art[orig_ley] += 1
            elif tipo == "MENCIONA_NORMA":
                datos_ext = self.grafo.nodes.get(v, {})
                nombre_ext = datos_ext.get("nombre", v)
                normas_externas_cnt[(v, nombre_ext)] += 1

        lista_pares = [
            {
                "ley_origen_id": orig,
                "ley_origen_nombre": self.grafo.nodes.get(orig, {}).get("nombre_corto", orig),
                "ley_destino_id": dest,
                "ley_destino_nombre": self.grafo.nodes.get(dest, {}).get("nombre_corto", dest),
                "total_referencias": total,
            }
            for (orig, dest), total in pares_cruzados.most_common()
        ]

        ranking_recibidas = [
            {
                "ley_id": ley_id,
                "nombre_corto": self.grafo.nodes.get(ley_id, {}).get("nombre_corto", ley_id),
                "citas_recibidas_de_otras_leyes": total,
            }
            for ley_id, total in recibidas_desde_otra_ley.most_common()
        ]

        ranking_externas = [
            {
                "norma_externa_id": ext_id,
                "nombre": nombre,
                "total_menciones": total,
            }
            for (ext_id, nombre), total in normas_externas_cnt.most_common()
        ]

        return {
            "pares_entre_leyes_distintas": lista_pares,
            "ranking_leyes_mas_citadas_por_otras": ranking_recibidas,
            "citas_emitidas_hacia_otras_leyes": dict(emitidas_hacia_otra_ley.most_common()),
            "citas_internas_entre_articulos": dict(internas_art_a_art.most_common()),
            "citas_relativas_a_propia_ley": dict(internas_art_a_ley.most_common()),
            "normas_externas_mas_citadas": ranking_externas,
        }

    def articulos_mas_citados(
        self, top_n: int = 20, ley: Optional[str] = None, solo_entre_leyes: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Devuelve los `top_n` artículos que reciben más referencias `REFIERE_A` entrantes.
        """
        ley_filtro_id = self.resolver_id_ley(ley) if ley else None
        conteo_entrante: Counter[str] = Counter()
        conteo_otras_leyes: Counter[str] = Counter()

        for u, v, data in self.grafo.edges(data=True):
            if data.get("tipo") != "REFIERE_A":
                continue
            datos_v = self.grafo.nodes.get(v, {})
            if datos_v.get("tipo_nodo") != "Articulo":
                continue
            if ley_filtro_id and datos_v.get("ley_id") != ley_filtro_id:
                continue
            es_cruzada = data.get("relacion") == "entre_leyes"
            if solo_entre_leyes and not es_cruzada:
                continue
            conteo_entrante[v] += 1
            if es_cruzada:
                conteo_otras_leyes[v] += 1

        resultado: List[Dict[str, Any]] = []
        for art_id, total in conteo_entrante.most_common(top_n):
            datos = self.grafo.nodes[art_id]
            resultado.append(
                {
                    "articulo_id": art_id,
                    "etiqueta": datos.get("etiqueta_normalizada"),
                    "ley_id": datos.get("ley_id"),
                    "jerarquia": datos.get("jerarquia"),
                    "total_citas_recibidas": total,
                    "citas_desde_otras_leyes": conteo_otras_leyes[art_id],
                    "citas_misma_ley": total - conteo_otras_leyes[art_id],
                }
            )
        return resultado

    def camino_entre(
        self,
        origen_id: str,
        destino_id: str,
        ley_origen: Optional[str] = None,
        ley_destino: Optional[str] = None,
        dirigido: bool = True,
    ) -> Dict[str, Any]:
        """
        Encuentra el camino más corto de referencias jurídicas (`REFIERE_A`) entre dos artículos.
        Excluye las aristas estructurales `CONTIENE` y los nodos `Ley` para que el camino sea
        estrictamente doctrinal/normativo entre artículos.
        """
        u_id = self.resolver_id_articulo(origen_id, ley_origen)
        v_id = self.resolver_id_articulo(destino_id, ley_destino)
        if not u_id or not v_id:
            raise ValueError(f"No se pudieron resolver los artículos '{origen_id}' o '{destino_id}'.")

        # Crear vista filtrada solo con aristas REFIERE_A entre nodos Articulo
        aristas_art = [
            (u, v)
            for u, v, d in self.grafo.edges(data=True)
            if d.get("tipo") == "REFIERE_A"
            and self.grafo.nodes.get(u, {}).get("tipo_nodo") == "Articulo"
            and self.grafo.nodes.get(v, {}).get("tipo_nodo") == "Articulo"
        ]
        subgrafo = nx.DiGraph() if dirigido else nx.Graph()
        subgrafo.add_edges_from(aristas_art)

        try:
            nodos_camino = nx.shortest_path(subgrafo, source=u_id, target=v_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return {
                "origen_id": u_id,
                "destino_id": v_id,
                "dirigido": dirigido,
                "existe_camino": False,
                "saltos": None,
                "nodos": [],
                "pasos": [],
            }

        pasos: List[Dict[str, Any]] = []
        for i in range(len(nodos_camino) - 1):
            a_id = nodos_camino[i]
            b_id = nodos_camino[i + 1]
            edge_dict = self.grafo.get_edge_data(a_id, b_id) or {}
            ref_edges = [d for d in edge_dict.values() if d.get("tipo") == "REFIERE_A"]
            direccion = "->"
            if not ref_edges and not dirigido:
                edge_dict_inv = self.grafo.get_edge_data(b_id, a_id) or {}
                ref_edges = [d for d in edge_dict_inv.values() if d.get("tipo") == "REFIERE_A"]
                direccion = "<-"

            primera = ref_edges[0] if ref_edges else {}
            pasos.append(
                {
                    "desde": a_id,
                    "hacia": b_id,
                    "direccion": direccion,
                    "clase": primera.get("clase"),
                    "texto_referencia": primera.get("texto_referencia"),
                    "snippet": primera.get("snippet"),
                }
            )

        return {
            "origen_id": u_id,
            "destino_id": v_id,
            "dirigido": dirigido,
            "existe_camino": True,
            "saltos": len(nodos_camino) - 1,
            "nodos": nodos_camino,
            "pasos": pasos,
        }

    def estadisticas(self) -> Dict[str, Any]:
        """Calcula las métricas globales del grafo (nodos, aristas, densidad y rankings principales)."""
        nodos_por_tipo = Counter(
            d.get("tipo_nodo", "Desconocido") for _, d in self.grafo.nodes(data=True)
        )
        aristas_por_tipo = Counter(
            d.get("tipo", "Desconocida") for _, _, d in self.grafo.edges(data=True)
        )
        ref_por_clase = Counter(
            d.get("clase")
            for _, _, d in self.grafo.edges(data=True)
            if d.get("tipo") == "REFIERE_A"
        )
        ref_por_relacion = Counter(
            d.get("relacion")
            for _, _, d in self.grafo.edges(data=True)
            if d.get("tipo") == "REFIERE_A"
        )

        resumen_leyes = self.leyes_mas_referenciadas()
        top_citados = self.articulos_mas_citados(top_n=15)

        return {
            "nodos": {
                "total": self.grafo.number_of_nodes(),
                "por_tipo": dict(nodos_por_tipo),
            },
            "aristas": {
                "total": self.grafo.number_of_edges(),
                "por_tipo": dict(aristas_por_tipo),
                "refiere_a_por_clase": dict(ref_por_clase),
                "refiere_a_por_relacion": dict(ref_por_relacion),
            },
            "leyes_mas_referenciadas": resumen_leyes,
            "top_15_articulos_mas_citados": top_citados,
        }

    def guardar_estadisticas_json(
        self, ruta_salida: Optional[Path] = None
    ) -> Path:
        """Guarda las estadísticas completas del grafo en `knowledge_graph/estadisticas_grafo.json`."""
        if ruta_salida is None:
            RUTA_KNOWLEDGE_GRAPH_DEFECTO.mkdir(parents=True, exist_ok=True)
            ruta_salida = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "estadisticas_grafo.json"
        else:
            ruta_salida = Path(ruta_salida)
            ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        datos = self.estadisticas()
        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        return ruta_salida
