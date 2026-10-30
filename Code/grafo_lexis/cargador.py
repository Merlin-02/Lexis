"""Cargador y normalizador de artículos jurídicos desde los archivos JSON estructurados."""

from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
import copy
import re

from .modelos import NodoLey, NodoArticulo
from .config_leyes import (
    CATALOGO_LEYES,
    RUTA_CONOCIMIENTO_ESTRUCTURADO,
    obtener_nodos_ley,
)

# Sufijos latinos reconocidos en etiquetas de artículos
SUFIJOS_LATINOS = (
    r"BIS|TER|QU[AÁ]TER|QUINQUIES|SEX(?:T)?IES|SEPTIES|OCTIES|NONIES|DECIES"
)


def normalizar_sufijo(raw_sufijo: str) -> str:
    """
    Normaliza el formato de un sufijo de artículo a la convención canónica:
    - "A" -> "A"
    - "BIS" -> "BIS"
    - "F Bis" -> "F-BIS"
    - "QUATER A" -> "QUATER-A"
    - "SEXTIES" -> "SEXTIES"
    """
    if not raw_sufijo:
        return ""
    limpio = raw_sufijo.strip().upper()
    limpio = limpio.replace("Á", "A")
    limpio = re.sub(r"[.\-]+", " ", limpio)
    partes = [p for p in limpio.split() if p]
    return "-".join(partes)


def formatear_numero_canonico(
    numero_base: int, sufijo: Optional[str], es_transitorio: bool, orden_transitorio: int = 0
) -> Tuple[str, str]:
    """
    Devuelve (numero_canonico, slug_id) para el artículo.
    Ejemplos:
      (135, "A", False) -> ("135-A", "135-A")
      (229, "BIS", False) -> ("229 BIS", "229-BIS")
      (153, "F-BIS", False) -> ("153-F BIS", "153-F-BIS")
      (640, "QUATER-A", False) -> ("640 QUATER A", "640-QUATER-A")
    """
    if es_transitorio:
        if sufijo:
            num_str = f"TRANSITORIO-{orden_transitorio} ({numero_base}-{sufijo})"
            slug_id = f"TRANSITORIO-{orden_transitorio}"
        else:
            num_str = f"TRANSITORIO-{orden_transitorio}"
            slug_id = f"TRANSITORIO-{orden_transitorio}"
        return num_str, slug_id

    if not sufijo:
        return str(numero_base), str(numero_base)

    # Si empieza con letra única (A..Z o Ñ), va unido con guion al número base: 135-A, 153-F BIS
    partes = sufijo.split("-")
    if len(partes[0]) == 1 and partes[0].isalpha():
        if len(partes) == 1:
            num_str = f"{numero_base}-{partes[0]}"
        else:
            num_str = f"{numero_base}-{partes[0]} {' '.join(partes[1:])}"
    else:
        num_str = f"{numero_base} {' '.join(partes)}"

    slug_id = f"{numero_base}-{sufijo}"
    return num_str, slug_id


def construir_texto_completo(
    texto_general: str,
    fracciones: List[Dict[str, Any]],
    incisos_directos: List[Dict[str, Any]],
) -> str:
    """
    Consolida texto_general, fracciones (y sus incisos) e incisos_directos
    en un único texto preservando el contenido original para cálculo de spans.
    """
    bloques: List[str] = []
    if texto_general and texto_general.strip():
        bloques.append(texto_general.strip())

    for frac in fracciones:
        num_f = frac.get("fraccion", "").strip()
        txt_f = frac.get("texto_general", "").strip()
        if num_f or txt_f:
            bloques.append(f"Fracción {num_f}. {txt_f}".strip())
        for inc in frac.get("incisos", []):
            num_i = inc.get("inciso", "").strip()
            txt_i = inc.get("texto", "").strip()
            if num_i or txt_i:
                bloques.append(f"Inciso {num_i}) {txt_i}".strip())

    for inc in incisos_directos:
        num_i = inc.get("inciso", "").strip()
        txt_i = inc.get("texto", "").strip()
        if num_i or txt_i:
            bloques.append(f"Inciso {num_i}) {txt_i}".strip())

    return "\n".join(bloques)


def normalizar_registro_articulo(
    registro: Dict[str, Any],
    ley_slug: str,
    ley_id: str,
    orden: int,
    en_seccion_transitorios: bool,
    contador_transitorios: int,
) -> NodoArticulo:
    """
    Normaliza un registro crudo del JSON sin mutar el diccionario de entrada.
    Reconstruye etiquetas truncadas o mal segmentadas y construye NodoArticulo.
    """
    etiqueta_original = registro.get("articulo", "").strip()
    tg_original = registro.get("texto_general", "")
    fracciones = copy.deepcopy(registro.get("fracciones", []))
    incisos_directos = copy.deepcopy(registro.get("incisos_directos", []))
    historial_dof = list(registro.get("historial_dof", []))
    jerarquia = registro.get("jerarquia", "").strip()

    # Marcar texto_vacio según el estado original de texto_general (2 en CC-TLAX y 16 en LFT)
    texto_vacio = len(tg_original.strip()) == 0

    tg_trabajo = tg_original.strip()
    reconstrucciones: List[str] = []

    # 1. Extraer número base y posible sufijo ya presente en etiqueta_original
    m_base = re.match(
        r"^(?:ART[IÍ]CULO|Art[ií]culo|Articulo)\s+(\d+)(.*)$",
        etiqueta_original,
    )
    if m_base:
        numero_base = int(m_base.group(1))
        resto_etiqueta = m_base.group(2).strip()
    else:
        numero_base = 0
        resto_etiqueta = ""

    # 2. Caso A: Falso "Ter" por corte de "Terminado / Terminada"
    # Ej: art="ARTICULO 1044.- Ter" + tg="minado el usufructo..."
    m_falso_ter = re.match(r"^\.-\s*(Ter)$", resto_etiqueta, re.IGNORECASE)
    if m_falso_ter and re.match(r"^minad[oa]s?\b", tg_trabajo, re.IGNORECASE):
        prefijo_ter = m_falso_ter.group(1)
        tg_trabajo = prefijo_ter + tg_trabajo
        resto_etiqueta = ".-"
        reconstrucciones.append("reconstruccion_palabra_terminado")

    # Limpiar puntuación ordinal o guiones sueltos en resto_etiqueta
    # Ej: "o.", "o.-", ".-", ".", "-"
    termina_en_guion = resto_etiqueta.endswith("-") and not resto_etiqueta.endswith(".-")
    resto_limpio = re.sub(r"^(?:o\.|o\.-|\.-|\.|-)+", "", resto_etiqueta, flags=re.IGNORECASE).strip()
    resto_limpio = re.sub(r"(?:\.-|\.|-)+$", "", resto_limpio).strip()

    partes_sufijo: List[str] = []
    if resto_limpio:
        partes_sufijo.append(normalizar_sufijo(resto_limpio))

    # 3. Limpiar prefijo ordinal en texto_general ("°.- ", "º.- ")
    m_ord = re.match(r"^[°º]\.-\s*", tg_trabajo)
    if m_ord:
        tg_trabajo = tg_trabajo[m_ord.end():].strip()
        reconstrucciones.append("limpieza_ordinal_texto")

    # 4. Detectar sufijo truncado al inicio de texto_general
    # Sólo si la etiqueta original no terminaba en punto/guion cerrado (ej. 'ARTICULO 135', 'Artículo 153-', 'ARTICULO 640 QUATER')
    etiqueta_abierta = (
        termina_en_guion
        or not etiqueta_original.endswith((".", ".-"))
    )

    if etiqueta_abierta and tg_trabajo:
        # 4a. Sufijo de letra + opcional Bis/Ter (ej. "A.-", "F Bis.", "D Ter.")
        m_letra = re.match(
            rf"^([A-ZÑ])(?:\s+({SUFIJOS_LATINOS}))?\s*(?:\.-|\.)\s*",
            tg_trabajo,
            re.IGNORECASE,
        )
        # 4b. Sufijo latino al inicio de texto_general (ej. "SEXIES.-", "bis.", "ter.")
        m_latino = re.match(
            rf"^({SUFIJOS_LATINOS})\s*(?:\.-|\.)\s*",
            tg_trabajo,
            re.IGNORECASE,
        )
        if m_letra:
            letra = m_letra.group(1).upper()
            sub_lat = m_letra.group(2)
            suf_extra = f"{letra}-{normalizar_sufijo(sub_lat)}" if sub_lat else letra
            partes_sufijo.append(suf_extra)
            tg_trabajo = tg_trabajo[m_letra.end():].strip()
            reconstrucciones.append(f"sufijo_desde_texto:{suf_extra}")
        elif m_latino:
            suf_extra = normalizar_sufijo(m_latino.group(1))
            partes_sufijo.append(suf_extra)
            tg_trabajo = tg_trabajo[m_latino.end():].strip()
            reconstrucciones.append(f"sufijo_latino_desde_texto:{suf_extra}")
        elif termina_en_guion and not partes_sufijo:
            # Ejemplo: "Artículo 890-" donde texto_general es "Se deroga."
            reconstrucciones.append("guion_final_sin_sufijo")

    # 5. Caso donde texto_general estaba vacío porque el sufijo C/D/I/L/V se fue a fracciones[0]
    if etiqueta_abierta and not tg_trabajo and fracciones:
        primera_frac = fracciones[0].get("fraccion", "").strip()
        if re.fullmatch(r"[A-ZÑ]", primera_frac):
            # Revisar si es un artículo con letra (C, D, I, L, V) cuyo encabezado cayó en fracciones[0]
            # En CC-TLAX (244-C, 244-D) y LFT (15-C, 15-D, 39-C, 39-D, 153-C, 153-D, 153-I, 153-L, 153-V, 343-C, 343-D, 512-D, 836-C, 836-D, 899-C, 899-D)
            partes_sufijo.append(primera_frac)
            tg_recuperado = fracciones[0].get("texto_general", "").strip()
            incisos_recuperados = fracciones[0].get("incisos", [])
            fracciones = fracciones[1:]
            tg_trabajo = tg_recuperado
            if incisos_recuperados and not incisos_directos:
                incisos_directos = incisos_recuperados
            reconstrucciones.append(f"sufijo_desde_fraccion:{primera_frac}")

    sufijo_final = "-".join(partes_sufijo) if partes_sufijo else None

    # Formatear número canónico e ID
    num_canonico, slug_num = formatear_numero_canonico(
        numero_base=numero_base,
        sufijo=sufijo_final,
        es_transitorio=en_seccion_transitorios,
        orden_transitorio=contador_transitorios,
    )

    if en_seccion_transitorios:
        etiqueta_normalizada = f"Artículo Transitorio {contador_transitorios} ({etiqueta_original})"
    else:
        etiqueta_normalizada = f"Artículo {num_canonico}"

    articulo_id = f"articulo:{ley_slug}:{slug_num}"
    texto_completo = construir_texto_completo(tg_trabajo, fracciones, incisos_directos)

    return NodoArticulo(
        id=articulo_id,
        ley_id=ley_id,
        numero=num_canonico,
        numero_base=numero_base,
        sufijo=sufijo_final,
        etiqueta_original=etiqueta_original,
        etiqueta_normalizada=etiqueta_normalizada,
        orden=orden,
        jerarquia=jerarquia,
        texto_general=tg_trabajo,
        texto_completo=texto_completo,
        fracciones=fracciones,
        incisos_directos=incisos_directos,
        historial_dof=historial_dof,
        es_transitorio=en_seccion_transitorios,
        texto_vacio=texto_vacio,
        reconstruccion_aplicada=";".join(reconstrucciones) if reconstrucciones else None,
    )


def cargar_ley_desde_json(
    ley_slug: str, directorio: Path = RUTA_CONOCIMIENTO_ESTRUCTURADO
) -> Tuple[NodoLey, List[NodoArticulo]]:
    """
    Carga un archivo JSON estructurado y devuelve su NodoLey y la lista de NodoArticulo.
    Detecta automáticamente el bloque final de transitorios/decretos cuando la
    numeración de artículos se reinicia o cae abruptamente al final del documento.
    """
    if ley_slug not in CATALOGO_LEYES:
        raise ValueError(f"Ley desconocida: {ley_slug}")

    nodos_ley = obtener_nodos_ley()
    nodo_ley = nodos_ley[ley_slug]
    ruta_archivo = directorio / nodo_ley.fuente_json

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        registros_crudos = json.load(f)

    articulos: List[NodoArticulo] = []
    max_numero_visto = 0
    en_transitorios = False
    contador_transitorios = 0

    for idx, reg in enumerate(registros_crudos):
        etiqueta = reg.get("articulo", "").strip()
        m_num = re.search(r"(\d+)", etiqueta)
        num_actual = int(m_num.group(1)) if m_num else 0

        # Si aún no estamos en transitorios y el número cae abruptamente tras haber
        # avanzado en la ley, a partir de aquí son artículos transitorios o decretos finales
        if not en_transitorios and max_numero_visto > 50 and num_actual < max_numero_visto:
            en_transitorios = True

        if not en_transitorios and num_actual > max_numero_visto:
            max_numero_visto = num_actual

        if en_transitorios:
            contador_transitorios += 1

        nodo_art = normalizar_registro_articulo(
            registro=reg,
            ley_slug=ley_slug,
            ley_id=nodo_ley.id,
            orden=idx + 1,
            en_seccion_transitorios=en_transitorios,
            contador_transitorios=contador_transitorios,
        )
        articulos.append(nodo_art)

    return nodo_ley, articulos


def cargar_corpus_completo(
    directorio: Path = RUTA_CONOCIMIENTO_ESTRUCTURADO,
) -> Tuple[Dict[str, NodoLey], Dict[str, List[NodoArticulo]]]:
    """
    Carga las 6 leyes configuradas y devuelve:
      - leyes: {ley_slug: NodoLey}
      - articulos_por_ley: {ley_slug: [NodoArticulo, ...]}
    """
    leyes: Dict[str, NodoLey] = {}
    articulos_por_ley: Dict[str, List[NodoArticulo]] = {}

    for slug in CATALOGO_LEYES:
        nodo_ley, lista_articulos = cargar_ley_desde_json(slug, directorio=directorio)
        leyes[slug] = nodo_ley
        articulos_por_ley[slug] = lista_articulos

    return leyes, articulos_por_ley
