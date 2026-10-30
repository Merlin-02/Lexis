"""Generador y exportador del reporte de referencias rotas, externas y ambiguas (Fase 5)."""

from collections import Counter
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from .modelos import ReferenciaRota

RUTA_KNOWLEDGE_GRAPH_DEFECTO = (
    Path(__file__).resolve().parent.parent.parent / "knowledge_graph"
)


class GeneradorReporteRotas:
    """
    Agrupa, clasifica y exporta las referencias no resueltas dentro del corpus:
      - `articulo_inexistente`: cita a una ley cargada en el corpus cuyo artículo no existe.
      - `ley_no_cargada`: cita a una ley o código externo fuera de las 6 leyes del corpus.
      - `ley_ambigua`: mención a una ley sin especificar cuál (ej. "Constitución" en ámbito estatal).
      - `relativa_ambigua`: referencia relativa plural sin cuantificador ("los artículos anteriores").
      - `relativa_sin_anterior`: referencia relativa que sale de los límites de la ley.
      - `rango_invalido`: rango cuyos límites están invertidos o mal formados.
    """

    def __init__(self, referencias_rotas: List[ReferenciaRota]) -> None:
        self.referencias_rotas = referencias_rotas

    def generar_reporte(self) -> Dict[str, Any]:
        """Construye el diccionario completo del reporte clasificado por motivo y por ley de origen."""
        por_motivo = Counter(r.motivo for r in self.referencias_rotas)
        por_ley = Counter(r.ley_origen for r in self.referencias_rotas)
        por_confianza = Counter(r.confianza for r in self.referencias_rotas)

        agrupadas_por_motivo: Dict[str, List[Dict[str, Any]]] = {}
        for ref in self.referencias_rotas:
            agrupadas_por_motivo.setdefault(ref.motivo, []).append(ref.to_dict())

        # Separar estrictamente las erratas/artículos inexistentes en leyes cargadas
        rotas_estrictas = [
            r.to_dict()
            for r in self.referencias_rotas
            if r.motivo in {"articulo_inexistente", "rango_invalido", "relativa_sin_anterior"}
        ]
        normas_externas_citadas = [
            r.to_dict()
            for r in self.referencias_rotas
            if r.motivo == "ley_no_cargada"
        ]
        ambiguas = [
            r.to_dict()
            for r in self.referencias_rotas
            if r.motivo in {"ley_ambigua", "relativa_ambigua"}
        ]

        return {
            "resumen": {
                "total_registradas": len(self.referencias_rotas),
                "total_rotas_estrictas_en_corpus": len(rotas_estrictas),
                "total_hacia_leyes_externas": len(normas_externas_citadas),
                "total_ambiguas_o_indeterminadas": len(ambiguas),
                "por_motivo": dict(por_motivo),
                "por_ley_origen": dict(por_ley),
                "por_confianza": dict(por_confianza),
            },
            "rotas_estrictas_en_corpus": rotas_estrictas,
            "hacia_leyes_externas": normas_externas_citadas,
            "ambiguas_o_indeterminadas": ambiguas,
            "agrupadas_por_motivo": agrupadas_por_motivo,
        }

    def filtrar(
        self,
        motivo: Optional[str] = None,
        ley_origen: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Filtra la lista de referencias rotas por motivo y/o ley de origen."""
        resultado: List[Dict[str, Any]] = []
        for r in self.referencias_rotas:
            if motivo and r.motivo != motivo:
                continue
            if ley_origen and r.ley_origen != ley_origen:
                continue
            resultado.append(r.to_dict())
        return resultado

    def guardar_json(
        self, ruta_salida: Optional[Path] = None
    ) -> Path:
        """Guarda el reporte estructurado en `knowledge_graph/reporte_referencias_rotas.json`."""
        if ruta_salida is None:
            RUTA_KNOWLEDGE_GRAPH_DEFECTO.mkdir(parents=True, exist_ok=True)
            ruta_salida = RUTA_KNOWLEDGE_GRAPH_DEFECTO / "reporte_referencias_rotas.json"
        else:
            ruta_salida = Path(ruta_salida)
            ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        reporte = self.generar_reporte()
        with open(ruta_salida, "w", encoding="utf-8") as f:
            json.dump(reporte, f, ensure_ascii=False, indent=2)
        return ruta_salida
