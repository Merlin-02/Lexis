"""Integración GraphRAG con el sistema RAG de LEXIS (`interaccion.py` y `app.py`) (Fase 7)."""

from typing import Dict, List, Any, Optional
import networkx as nx

from .recuperador_grafo import RecuperadorGrafoLexis

_RECUPERADOR_SINGLETON: Optional[RecuperadorGrafoLexis] = None


def obtener_recuperador_grafo() -> RecuperadorGrafoLexis:
    """Devuelve una instancia cacheada en memoria de `RecuperadorGrafoLexis`."""
    global _RECUPERADOR_SINGLETON
    if _RECUPERADOR_SINGLETON is None:
        _RECUPERADOR_SINGLETON = RecuperadorGrafoLexis()
    return _RECUPERADOR_SINGLETON


def construir_contexto_graphrag(
    hits: List[Dict[str, Any]],
    max_fragmentos_base: int = 3,
    max_vecinos_grafo: int = 3,
    max_len_fragmento: int = 800,
    recuperador: Optional[RecuperadorGrafoLexis] = None,
) -> Dict[str, Any]:
    """
    Construye el bloque enriquecido de leyes para el prompt del LLM combinando:
      1. Los `max_fragmentos_base` fragmentos recuperados por búsqueda vectorial/BM25 (`hits`).
      2. Hasta `max_vecinos_grafo` artículos adicionales conectados en el Grafo de Conocimiento
         (`REFIERE_A` salientes y entrantes), junto con un resumen legible en Markdown para la UI.
    """
    if not hits:
        return {
            "bloque_prompt": "No se encontraron fragmentos legales relevantes para esta consulta.",
            "resumen_grafo_md": "",
            "expansion": {
                "nodos_semilla": [],
                "vecinos_citados_salientes": [],
                "vecinos_afectados_entrantes": [],
                "normas_externas_mencionadas": [],
            },
        }

    rec = recuperador or obtener_recuperador_grafo()
    hits_top = hits[:max_fragmentos_base]

    partes_prompt: List[str] = []
    for i, hit in enumerate(hits_top, 1):
        fuente = f"{hit.get('documento', 'N/D')} - {hit.get('articulo', 'N/D')} (Jerarquía: {hit.get('jerarquia', 'N/D')})"
        if hit.get("origen") == "tematico":
            fuente += f" [Tema: {hit.get('tema', 'General')}]"
        texto = str(hit.get("texto", ""))[:max_len_fragmento]
        texto = texto.encode("utf-8", errors="replace").decode("utf-8")
        partes_prompt.append(f"--- Fragmento {i} (Recuperación Directa) ---\nFuente: {fuente}\n{texto}")

    expansion = rec.expandir_contexto_hits(
        hits_top,
        max_semillas=max_fragmentos_base,
        max_vecinos_total=max_vecinos_grafo,
    )

    salientes = expansion["vecinos_citados_salientes"]
    entrantes = expansion["vecinos_afectados_entrantes"]
    externas = expansion["normas_externas_mencionadas"]

    lineas_md: List[str] = []

    if salientes or entrantes:
        partes_prompt.append("\n[ARTÍCULOS RELACIONADOS EN EL GRAFO DE CONOCIMIENTO JURÍDICO]")

    for j, vec in enumerate(salientes, 1):
        comp_str = f" ({vec['componente']})" if vec.get("componente") else ""
        encabezado = (
            f"--- Referencia del Grafo {j}: {vec['ley_nombre']} - {vec['etiqueta']}{comp_str} "
            f"[Citado por {vec['desde_semilla_id']} vía '{vec['texto_referencia']}'] ---"
        )
        txt_vec = str(vec.get("texto_completo", ""))[: max_len_fragmento - 150]
        partes_prompt.append(f"{encabezado}\n{txt_vec}")
        lineas_md.append(
            f"* **Cita saliente (`{vec['clase']}`)**: `{vec['desde_semilla_id']}` -> "
            f"**{vec['ley_nombre']} — {vec['etiqueta']}** *(ref: \"{vec['texto_referencia']}\")*"
        )

    for k, vec_in in enumerate(entrantes, 1):
        encabezado = (
            f"--- Impacto en el Grafo {k}: {vec_in['ley_nombre']} - {vec_in['etiqueta']} "
            f"[Remite a {vec_in['hacia_semilla_id']} vía '{vec_in['texto_referencia']}'] ---"
        )
        txt_vec = str(vec_in.get("texto_completo", ""))[: max_len_fragmento - 150]
        partes_prompt.append(f"{encabezado}\n{txt_vec}")
        lineas_md.append(
            f"* **Artículo que remite aquí (`{vec_in['clase']}`)**: **{vec_in['ley_nombre']} — {vec_in['etiqueta']}** "
            f"-> `{vec_in['hacia_semilla_id']}` *(ref: \"{vec_in['texto_referencia']}\")*"
        )

    for ext in externas[:3]:
        lineas_md.append(
            f"* **Norma externa mencionada**: *{ext['norma_externa']}* "
            f"(Art. {ext.get('articulo_mencionado', 'N/D')})"
        )

    return {
        "bloque_prompt": "\n\n".join(partes_prompt).strip(),
        "resumen_grafo_md": "\n".join(lineas_md).strip(),
        "expansion": expansion,
    }
