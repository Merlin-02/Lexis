"""Catálogo de configuración y metadatos de las normativas del corpus LEXIS."""

from pathlib import Path
from typing import Dict, Any, Optional, List
import unicodedata
import re

from .modelos import NodoLey

RUTA_CONOCIMIENTO_ESTRUCTURADO = (
    Path(__file__).resolve().parent.parent.parent / "knowledge_structured"
)

CATALOGO_LEYES: Dict[str, Dict[str, Any]] = {
    "cc_tlax": {
        "id": "ley:cc_tlax",
        "slug": "cc_tlax",
        "clave": "CC-TLAX",
        "nombre_oficial": "Código Civil para el Estado Libre y Soberano de Tlaxcala",
        "nombre_corto": "Código Civil de Tlaxcala",
        "alias": [
            "Código Civil para el Estado Libre y Soberano de Tlaxcala",
            "Código Civil del Estado Libre y Soberano de Tlaxcala",
            "Código Civil para el Estado de Tlaxcala",
            "Código Civil del Estado de Tlaxcala",
            "Código Civil de Tlaxcala",
            "Código Civil del Estado",
            "Código Civil Local",
            "Código Civil",
            "CC-TLAX",
        ],
        "tipo_norma": "codigo",
        "ambito": "estatal",
        "materia": "civil",
        "fecha_publicacion": None,
        "fuente_json": "Codigo Civil Tlaxcala_estructurado.json",
        "en_corpus": True,
    },
    "cp_tlax": {
        "id": "ley:cp_tlax",
        "slug": "cp_tlax",
        "clave": "CP-TLAX",
        "nombre_oficial": "Código Penal para el Estado Libre y Soberano de Tlaxcala",
        "nombre_corto": "Código Penal de Tlaxcala",
        "alias": [
            "Código Penal para el Estado Libre y Soberano de Tlaxcala",
            "Código Penal del Estado Libre y Soberano de Tlaxcala",
            "Código Penal para el Estado de Tlaxcala",
            "Código Penal del Estado de Tlaxcala",
            "Código Penal de Tlaxcala",
            "Código Penal del Estado",
            "Código Penal Local",
            "Código Penal",
            "CP-TLAX",
        ],
        "tipo_norma": "codigo",
        "ambito": "estatal",
        "materia": "penal",
        "fecha_publicacion": None,
        "fuente_json": "Código Penal Tlaxcala_estructurado.json",
        "en_corpus": True,
    },
    "cpeum": {
        "id": "ley:cpeum",
        "slug": "cpeum",
        "clave": "CPEUM",
        "nombre_oficial": "Constitución Política de los Estados Unidos Mexicanos",
        "nombre_corto": "Constitución Federal (CPEUM)",
        "alias": [
            "Constitución Política de los Estados Unidos Mexicanos",
            "Constitución de los Estados Unidos Mexicanos",
            "Constitución General de la República",
            "Constitución de la República Mexicana",
            "Constitución de la República",
            "Constitución Federal",
            "Carta Magna",
            "CPEUM",
        ],
        "tipo_norma": "constitucion",
        "ambito": "federal",
        "materia": "constitucional",
        "fecha_publicacion": None,
        "fuente_json": "Constitucion_estructurado.json",
        "en_corpus": True,
    },
    "lft": {
        "id": "ley:lft",
        "slug": "lft",
        "clave": "LFT",
        "nombre_oficial": "Ley Federal del Trabajo",
        "nombre_corto": "Ley Federal del Trabajo",
        "alias": [
            "Ley Federal del Trabajo",
            "LFT",
        ],
        "tipo_norma": "ley",
        "ambito": "federal",
        "materia": "laboral",
        "fecha_publicacion": None,
        "fuente_json": "Ley Trabajo_estructurado.json",
        "en_corpus": True,
    },
    "cpc_tlax": {
        "id": "ley:cpc_tlax",
        "slug": "cpc_tlax",
        "clave": "CPC-TLAX",
        "nombre_oficial": "Código de Procedimientos Civiles para el Estado Libre y Soberano de Tlaxcala",
        "nombre_corto": "Código de Procedimientos Civiles de Tlaxcala",
        "alias": [
            "Código de Procedimientos Civiles para el Estado Libre y Soberano de Tlaxcala",
            "Código de Procedimientos Civiles del Estado Libre y Soberano de Tlaxcala",
            "Código de Procedimientos Civiles para el Estado de Tlaxcala",
            "Código de Procedimientos Civiles del Estado de Tlaxcala",
            "Código de Procedimientos Civiles de Tlaxcala",
            "Código de Procedimientos Civiles del Estado",
            "Código de Procedimientos Civiles",
            "CPC-TLAX",
        ],
        "tipo_norma": "codigo",
        "ambito": "estatal",
        "materia": "procesal_civil",
        "fecha_publicacion": None,
        "fuente_json": "Procedimiento Civiles Tlaxcala_estructurado.json",
        "en_corpus": True,
    },
    "cpp_tlax": {
        "id": "ley:cpp_tlax",
        "slug": "cpp_tlax",
        "clave": "CPP-TLAX",
        "nombre_oficial": "Código de Procedimientos Penales para el Estado Libre y Soberano de Tlaxcala",
        "nombre_corto": "Código de Procedimientos Penales de Tlaxcala",
        "alias": [
            "Código de Procedimientos Penales para el Estado Libre y Soberano de Tlaxcala",
            "Código de Procedimientos Penales del Estado Libre y Soberano de Tlaxcala",
            "Código de Procedimientos Penales para el Estado de Tlaxcala",
            "Código de Procedimientos Penales del Estado de Tlaxcala",
            "Código de Procedimientos Penales de Tlaxcala",
            "Código de Procedimientos Penales del Estado",
            "Código de Procedimientos Penales",
            "CPP-TLAX",
        ],
        "tipo_norma": "codigo",
        "ambito": "estatal",
        "materia": "procesal_penal",
        "fecha_publicacion": None,
        "fuente_json": "Procedimiento Penal Tlaxcala_estructurado.json",
        "en_corpus": True,
    },
}

# Mapa inverso por nombre de archivo JSON
ARCHIVO_A_SLUG: Dict[str, str] = {
    cfg["fuente_json"]: slug for slug, cfg in CATALOGO_LEYES.items()
}


def normalizar_texto_comparacion(texto: str) -> str:
    """Elimina acentos, convierte a minúsculas y colapsa espacios."""
    texto_nfd = unicodedata.normalize("NFD", texto)
    sin_acentos = "".join(
        c for c in texto_nfd if unicodedata.category(c) != "Mn"
    )
    limpio = re.sub(r"[^\w\s-]", " ", sin_acentos.lower())
    return re.sub(r"\s+", " ", limpio).strip()


def obtener_nodos_ley() -> Dict[str, NodoLey]:
    """Devuelve un diccionario {ley_slug: NodoLey} para todas las leyes configuradas."""
    resultado: Dict[str, NodoLey] = {}
    for slug, cfg in CATALOGO_LEYES.items():
        resultado[slug] = NodoLey(
            id=cfg["id"],
            clave=cfg["clave"],
            nombre_oficial=cfg["nombre_oficial"],
            nombre_corto=cfg["nombre_corto"],
            alias=list(cfg["alias"]),
            tipo_norma=cfg["tipo_norma"],
            ambito=cfg["ambito"],
            materia=cfg["materia"],
            fecha_publicacion=cfg["fecha_publicacion"],
            fuente_json=cfg["fuente_json"],
            en_corpus=cfg["en_corpus"],
        )
    return resultado


def obtener_alias_ordenados() -> List[tuple]:
    """
    Devuelve una lista de tuplas (alias_normalizado, alias_original, ley_slug)
    ordenada de mayor a menor longitud para priorizar el alias más largo.
    """
    pares = []
    for slug, cfg in CATALOGO_LEYES.items():
        for alias in cfg["alias"]:
            norm = normalizar_texto_comparacion(alias)
            pares.append((norm, alias, slug))
    pares.sort(key=lambda x: len(x[0]), reverse=True)
    return pares
