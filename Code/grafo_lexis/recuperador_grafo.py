"""Recuperador por expansión de subgrafo (GraphRAG) para enriquecer hits de búsqueda híbrida (Fase 7)."""

import re
from typing import Dict, List, Any, Optional, Set, Tuple
import networkx as nx

from .config_leyes import CATALOGO_LEYES, normalizar_texto_comparacion
from .consultas import ConsultasGrafoLexis
from .detector_referencias import parsear_token_articulo
from .exportador import ExportadorGrafoLexis
from .reporte_rotas import RUTA_KNOWLEDGE_GRAPH_DEFECTO


def _cargar_o_construir_grafo_defecto() -> nx.MultiDiGraph:
    ruta_json = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "grafo_lexis.json"
    if ruta_json.exists():
        return ExportadorGrafoLexis.cargar_desde_json(ruta_json)
    from .constructor_grafo import ConstructorGrafoLexis

    constructor = ConstructorGrafoLexis()
    constructor.cargar_y_construir_estructura_base()
    constructor.detectar_y_agregar_referencias_fase4()
    ExportadorGrafoLexis(constructor.grafo).exportar_json(ruta_json)
    return constructor.grafo


class RecuperadorGrafoLexis:
    """
    Conecta los resultados (`hits`) del buscador híbrido (ChromaDB + BM25) con el grafo
    de conocimiento jurídico (`MultiDiGraph`) para expandir cada artículo semilla con:
      1. Artículos citados directamente por los hits (`REFIERE_A` salientes), priorizando
         citas entre leyes distintas (`entre_leyes`), directas y listas.
      2. Artículos que citan o modifican a los hits (`REFIERE_A` entrantes / impacto).
      3. Normas externas mencionadas (`MENCIONA_NORMA`).
    """

    def __init__(self, grafo: Optional[nx.MultiDiGraph] = None) -> None:
        self.grafo = grafo if grafo is not None else _cargar_o_construir_grafo_defecto()
        self.consultas = ConsultasGrafoLexis(self.grafo)

        # Mapa inverso de nombres de documento en ChromaDB -> slug de ley
        self._mapa_doc_a_slug: Dict[str, str] = {}
        for slug, cfg in CATALOGO_LEYES.items():
            self._mapa_doc_a_slug[normalizar_texto_comparacion(cfg["nombre_corto"])] = slug
            self._mapa_doc_a_slug[normalizar_texto_comparacion(cfg["nombre_oficial"])] = slug
            self._mapa_doc_a_slug[normalizar_texto_comparacion(cfg["clave"])] = slug
            for alias in cfg["alias"]:
                self._mapa_doc_a_slug[normalizar_texto_comparacion(alias)] = slug

    def mapear_documento_a_ley_slug(self, documento_str: str) -> Optional[str]:
        """Convierte el campo `documento` de ChromaDB (ej. 'Ley Trabajo', 'Codigo Civil Tlaxcala') en el slug de ley."""
        if not documento_str:
            return None
        norm = normalizar_texto_comparacion(documento_str)
        if norm in self._mapa_doc_a_slug:
            return self._mapa_doc_a_slug[norm]

        # Coincidencia parcial por palabras clave de los nombres de archivos en ChromaDB
        if "procedimientos" in norm and "civiles" in norm:
            return "cpc_tlax"
        if "procedimientos" in norm and "penales" in norm:
            return "cpp_tlax"
        if "civil" in norm:
            return "cc_tlax"
        if "penal" in norm:
            return "cp_tlax"
        if "trabajo" in norm or "laboral" in norm:
            return "lft"
        if "constitucion" in norm:
            return "cpeum"
        return None

    def mapear_hit_a_nodo_articulo(self, hit: Dict[str, Any]) -> Optional[str]:
        """
        Resuelve un diccionario `hit` (con llaves `documento`, `articulo`, `texto`)
        al ID canónico del nodo `Articulo` en el grafo (`articulo:<ley_slug>:<num>`).
        """
        if "nodo_articulo_id" in hit and self.grafo.has_node(hit["nodo_articulo_id"]):
            return hit["nodo_articulo_id"]

        doc_str = str(hit.get("documento", ""))
        art_str = str(hit.get("articulo", ""))
        ley_slug = self.mapear_documento_a_ley_slug(doc_str)
        if not ley_slug:
            return None

        # Si la etiqueta en ChromaDB termina en guion (ej. "Artículo 153-"), está truncada;
        # no usar resolver_id_articulo directo porque quitaría el guion y devolvería 153 en vez de 153-A..X
        etiqueta_truncada = art_str.strip().endswith("-")
        if not etiqueta_truncada:
            nodo_id = self.consultas.resolver_id_articulo(art_str, ley=f"ley:{ley_slug}")
            if nodo_id:
                return nodo_id

        # Buscar por número base y prefijo/coincidencia de texto_completo
        m_num = re.search(r"(\d+)", art_str)
        if not m_num:
            return None
        num_base = int(m_num.group(1))
        texto_raw = str(hit.get("texto", "")).strip()
        # Verificar si el texto del hit comienza con el sufijo desbordado (ej. "A. Los patrones...")
        m_suf = re.match(r"^([A-ZÑ](?:\s+Bis)?)\s*[.\-]\s*(.*)$", texto_raw, re.IGNORECASE)
        if m_suf:
            suf_cand = m_suf.group(1).strip().upper().replace(" ", "-")
            cand_suf_id = f"articulo:{ley_slug}:{num_base}-{suf_cand}"
            if self.grafo.has_node(cand_suf_id):
                return cand_suf_id

        texto_hit = normalizar_texto_comparacion(texto_raw[:120])

        candidatos = [
            n
            for n, d in self.grafo.nodes(data=True)
            if d.get("tipo_nodo") == "Articulo"
            and d.get("ley_id") == f"ley:{ley_slug}"
            and d.get("numero_base") == num_base
        ]
        if len(candidatos) == 1:
            return candidatos[0]
        for cand_id in candidatos:
            txt_nodo = normalizar_texto_comparacion(
                str(self.grafo.nodes[cand_id].get("texto_completo", ""))[:140]
            )
            if texto_hit and (texto_hit[:45] in txt_nodo or txt_nodo[:45] in texto_hit):
                return cand_id
        return candidatos[0] if candidatos else None

    def expandir_contexto_hits(
        self,
        hits: List[Dict[str, Any]],
        max_semillas: int = 3,
        max_vecinos_total: int = 4,
    ) -> Dict[str, Any]:
        """
        Toma los `hits` recuperados por `buscador.py`, identifica los nodos semilla en el grafo
        y recupera los artículos vecinos conectados por `REFIERE_A` (salientes y entrantes),
        evitando duplicar artículos que ya están en los top hits.
        """
        nodos_semilla: List[str] = []
        semillas_set: Set[str] = set()

        for h in hits[:max_semillas]:
            nid = self.mapear_hit_a_nodo_articulo(h)
            if nid and nid not in semillas_set:
                nodos_semilla.append(nid)
                semillas_set.add(nid)

        vecinos_salientes: List[Dict[str, Any]] = []
        vecinos_entrantes: List[Dict[str, Any]] = []
        normas_externas: List[Dict[str, Any]] = []
        articulos_vecinos_vistos: Set[str] = set(semillas_set)

        # Prioridad de clases para ordenar vecinos salientes (primero citas cruzadas y directas, luego listas y relativas)
        prioridad_clase = {
            "explicita_otra_ley": 0,
            "directa": 1,
            "lista": 2,
            "relativa": 3,
            "rango": 4,
        }

        candidatos_salientes: List[Tuple[int, str, str, Dict[str, Any]]] = []
        for sem_id in nodos_semilla:
            for _, dest_id, _, edata in self.grafo.out_edges(sem_id, keys=True, data=True):
                tipo = edata.get("tipo")
                datos_dest = self.grafo.nodes.get(dest_id, {})
                if tipo == "REFIERE_A" and datos_dest.get("tipo_nodo") == "Articulo":
                    prio = prioridad_clase.get(str(edata.get("clase")), 5)
                    candidatos_salientes.append((prio, sem_id, dest_id, edata))
                elif tipo == "MENCIONA_NORMA":
                    normas_externas.append(
                        {
                            "origen_id": sem_id,
                            "norma_externa": datos_dest.get("nombre", dest_id),
                            "articulo_mencionado": edata.get("articulo_mencionado"),
                            "texto_referencia": edata.get("texto_referencia"),
                        }
                    )

        candidatos_salientes.sort(key=lambda x: x[0])

        for _, sem_id, dest_id, edata in candidatos_salientes:
            if dest_id in articulos_vecinos_vistos:
                continue
            if len(vecinos_salientes) >= max_vecinos_total:
                break
            articulos_vecinos_vistos.add(dest_id)
            datos_dest = self.grafo.nodes[dest_id]
            ley_dest_nodo = self.grafo.nodes.get(datos_dest.get("ley_id", ""), {})
            vecinos_salientes.append(
                {
                    "articulo_id": dest_id,
                    "desde_semilla_id": sem_id,
                    "etiqueta": datos_dest.get("etiqueta_normalizada"),
                    "ley_id": datos_dest.get("ley_id"),
                    "ley_nombre": ley_dest_nodo.get("nombre_corto", datos_dest.get("ley_id")),
                    "jerarquia": datos_dest.get("jerarquia"),
                    "clase": edata.get("clase"),
                    "relacion": edata.get("relacion"),
                    "componente": edata.get("componente"),
                    "texto_referencia": edata.get("texto_referencia"),
                    "texto_completo": datos_dest.get("texto_completo", ""),
                }
            )

        # Si aún queda espacio en max_vecinos_total, agregar artículos que citan a las semillas (impacto entrante)
        if len(vecinos_salientes) < max_vecinos_total:
            restantes = max_vecinos_total - len(vecinos_salientes)
            for sem_id in nodos_semilla:
                for orig_id, _, _, edata in self.grafo.in_edges(sem_id, keys=True, data=True):
                    if edata.get("tipo") != "REFIERE_A":
                        continue
                    datos_orig = self.grafo.nodes.get(orig_id, {})
                    if datos_orig.get("tipo_nodo") != "Articulo":
                        continue
                    if orig_id in articulos_vecinos_vistos:
                        continue
                    articulos_vecinos_vistos.add(orig_id)
                    ley_orig_nodo = self.grafo.nodes.get(datos_orig.get("ley_id", ""), {})
                    vecinos_entrantes.append(
                        {
                            "articulo_id": orig_id,
                            "hacia_semilla_id": sem_id,
                            "etiqueta": datos_orig.get("etiqueta_normalizada"),
                            "ley_id": datos_orig.get("ley_id"),
                            "ley_nombre": ley_orig_nodo.get("nombre_corto", datos_orig.get("ley_id")),
                            "jerarquia": datos_orig.get("jerarquia"),
                            "clase": edata.get("clase"),
                            "relacion": edata.get("relacion"),
                            "texto_referencia": edata.get("texto_referencia"),
                            "texto_completo": datos_orig.get("texto_completo", ""),
                        }
                    )
                    if len(vecinos_entrantes) >= restantes:
                        break
                if len(vecinos_entrantes) >= restantes:
                    break

        return {
            "nodos_semilla": nodos_semilla,
            "vecinos_citados_salientes": vecinos_salientes,
            "vecinos_afectados_entrantes": vecinos_entrantes,
            "normas_externas_mencionadas": normas_externas,
        }
