"""Modelos de datos para nodos, aristas y referencias del grafo jurídico LEXIS."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class NodoLey:
    """Representa una ley, código o constitución cargada en el corpus."""
    id: str                         # ley:<slug>
    clave: str                      # "CC-TLAX" | "CP-TLAX" | "CPEUM" | "LFT" | "CPC-TLAX" | "CPP-TLAX"
    nombre_oficial: str
    nombre_corto: str
    alias: List[str]
    tipo_norma: str                 # "ley" | "codigo" | "constitucion"
    ambito: str                     # "federal" | "estatal"
    materia: str                    # "civil" | "penal" | "laboral" | "constitucional" | "procesal_civil" | "procesal_penal"
    fuente_json: str
    fecha_publicacion: Optional[str] = None
    en_corpus: bool = True
    tipo_nodo: str = "Ley"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NodoArticulo:
    """Representa un artículo jurídico (incluyendo subartículos y transitorios)."""
    id: str                         # articulo:<ley_slug>:<numero_canonico>
    ley_id: str                     # ley:<slug>
    numero: str                     # "135-A", "229 BIS", "640 QUATER A", "TRANSITORIO-1"
    numero_base: int                # 135
    sufijo: Optional[str]           # "A" | "BIS" | "F-BIS" | "QUATER-A" | None
    etiqueta_original: str
    etiqueta_normalizada: str
    orden: int                      # Índice secuencial 1-based dentro de la ley
    jerarquia: str
    texto_general: str
    texto_completo: str
    fracciones: List[Dict[str, Any]] = field(default_factory=list)
    incisos_directos: List[Dict[str, Any]] = field(default_factory=list)
    historial_dof: List[str] = field(default_factory=list)
    es_transitorio: bool = False
    texto_vacio: bool = False
    reconstruccion_aplicada: Optional[str] = None
    chunk_ids: List[str] = field(default_factory=list)
    tipo_nodo: str = "Articulo"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NodoNormaExterna:
    """Representa una ley o código mencionado pero no cargado en el corpus."""
    id: str                         # norma_externa:<slug>
    nombre: str
    alias: List[str] = field(default_factory=list)
    en_corpus: bool = False
    tipo_nodo: str = "NormaExterna"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AristaContiene:
    """Arista (Ley)-[:CONTIENE]->(Articulo)."""
    origen_id: str
    destino_id: str
    orden: int
    jerarquia: str
    tipo: str = "CONTIENE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AristaRefiereA:
    """Arista (Articulo)-[:REFIERE_A]->(Articulo) cuando el destino existe."""
    id: str
    origen_id: str
    destino_id: str
    origen_ley_id: str
    destino_ley_id: str
    clase: str                      # "directa" | "explicita_otra_ley" | "rango" | "relativa" | "lista"
    relacion: str                   # "misma_ley" | "entre_leyes"
    texto_referencia: str
    snippet: str
    snippet_exacto: str
    span_inicio: int
    span_fin: int
    unidad: str = "texto_completo"
    componente: Optional[str] = None
    rango: Optional[Dict[str, Any]] = None
    grupo_id: Optional[str] = None
    confianza: str = "alta"         # "alta" | "media" | "baja"
    metodo: str = "regex"           # "regex" | "regex+alias" | "llm" | "manual"
    estado: str = "resuelta"        # "resuelta" | "ambigua" | "rota" | "externa"
    tipo: str = "REFIERE_A"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AristaMencionaNorma:
    """Arista (Articulo)-[:MENCIONA_NORMA]->(Ley | NormaExterna)."""
    id: str
    origen_id: str
    destino_id: str
    texto_referencia: str
    snippet: str
    snippet_exacto: str
    span_inicio: int
    span_fin: int
    articulo_mencionado: Optional[str] = None
    confianza: str = "alta"
    metodo: str = "regex"
    tipo: str = "MENCIONA_NORMA"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReferenciaRota:
    """Registro de referencia rota o ambigua que no genera arista REFIERE_A."""
    origen_id: str
    ley_origen: str
    texto_referencia: str
    destino_mencionado: str
    motivo: str                     # "articulo_inexistente" | "ley_no_cargada" | "ley_ambigua" | "sin_articulo_identificable" | "rango_fuera_de_limites" | "relativa_sin_vecino"
    snippet: str
    span_inicio: int
    span_fin: int
    confianza: str = "media"
    sugerencia: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
