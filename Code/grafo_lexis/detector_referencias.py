"""Detector de referencias jurídicas entre artículos y normativas mediante reglas y expresiones regulares."""

from typing import Dict, List, Tuple, Optional, Any, Set
import re
import uuid

from .modelos import (
    NodoLey,
    NodoArticulo,
    NodoNormaExterna,
    AristaRefiereA,
    AristaMencionaNorma,
    ReferenciaRota,
)
from .config_leyes import (
    CATALOGO_LEYES,
    normalizar_texto_comparacion,
    obtener_alias_ordenados,
)
from .cargador import SUFIJOS_LATINOS, normalizar_sufijo, formatear_numero_canonico

# Patrón para detectar dónde inicia el bloque de TRANSITORIOS incrustado al final del último artículo ordinario
PATRON_INICIO_TRANSITORIOS_INCRUSTADO = re.compile(
    r"\b(?:T\s*R\s*A\s*N\s*S\s*I\s*T\s*O\s*R\s*I\s*O\s*S|TRANSITORIOS|Art[ií]culos\s+Transitorios)\b"
)

# Patrón de notas editoriales de reforma (DOF / P.O.) incrustadas en texto para enmascararlas
PATRON_NOTA_REFORMA_INLINE = re.compile(
    r"(?:\((?:REFORMAD[OA]|ADICIONAD[OA]|DEROGAD[OA]|FE DE ERRATAS)[^)\n]{0,200}\))"
    r"|(?:\b(?:Fracci[oó]n|P[aá]rrafo|Inciso|Art[ií]culo|Apartado|Secci[oó]n|Cap[ií]tulo|T[ií]tulo)[ \t]+"
    r"(?:reformad[oa]|adicionad[oa]|derogad[oa]|recorrid[oa])[^.\n]{0,160}?\b(?:DOF|P\.O\.)[^.\n]{0,120})"
    r"|(?:\bReforma[ \t]+DOF[ \t]+[\d\-]+:[ \t]*Derog[oó][ \t]+[^.\n]{0,180})"
    r"|(?:\bFe[ \t]+de[ \t]+erratas[ \t]+al[ \t]+(?:art[ií]culo|p[aá]rrafo|inciso|fracci[oó]n)[ \t]+DOF[ \t]+[\d\-., \t]{0,80})",
    re.IGNORECASE,
)

# Expresión para un número de artículo individual con posible sufijo (ej. "12", "3o.", "153-F Bis", "640 Quáter A", "240 C")
TOKEN_NUM_ARTICULO = (
    rf"\d+(?:[ \t]*(?:[°º]\.?|o\.|o\.-|\.-))?(?:[ \t]*-[ \t]*(?-i:[A-ZÑ])\b(?:[ \t]+(?:{SUFIJOS_LATINOS})\b)?"
    rf"|[ \t]+(?:{SUFIJOS_LATINOS})\b(?:[ \t]+(?-i:[A-E])\b)?"
    rf"|[ \t]+(?-i:[A-E])\b(?=[ \t]*(?:,|;|\.|\by\b|\bo\b|\bdel\b|\bde\b|\bfracci[oó]n|$)))?"
)

# Componente previo al artículo: "la fracción II del artículo 12", "el párrafo tercero de la fracción I del artículo 5"
PATRON_COMPONENTE_PREVIO = re.compile(
    r"(?:(?:el|la|los|las)[ \t]+)?"
    r"((?:(?:primer|segundo|tercer|cuarto|quinto|sexto|s[eé]ptimo|octavo|noveno|d[eé]cimo|[uú]ltimo|pen[uú]ltimo)[ \t]+p[aá]rrafo"
    r"|p[aá]rrafos?[ \t]+(?:primero|segundo|tercero|cuarto|quinto|sexto|s[eé]ptimo|octavo|noveno|d[eé]cimo|[uú]ltimo|pen[uú]ltimo|[IVXLCDM]+|\d+)(?:[ \t]+y[ \t]+(?:primero|segundo|tercero|cuarto|quinto|sexto|[uú]ltimo))?"
    r"|fracci[oó]n(?:es)?[ \t]+(?:[IVXLCDM]+|\d+)(?:[ \t]*(?:,|y|a|al)[ \t]*(?:[IVXLCDM]+|\d+))*"
    r"|apartado[ \t]+[A-Z]"
    r"|incisos?[ \t]+[a-z]\))"
    r"(?:[ \t]+(?:de[ \t]+la|del)[ \t]+(?:fracci[oó]n[ \t]+[IVXLCDM]+|apartado[ \t]+[A-Z]|p[aá]rrafo[ \t]+\w+))?)"
    r"[ \t]+(?:del|de[ \t]+los)[ \t]+$",
    re.IGNORECASE,
)


def _enmascarar_notas_reforma(texto: str) -> str:
    """
    Reemplaza por espacios del mismo largo las notas editoriales DOF/P.O.
    y el bloque de TRANSITORIOS incrustado al final del último artículo,
    manteniendo intactos los offsets (span_inicio, span_fin) sobre texto_completo.
    """
    chars = list(texto)
    m_tr = PATRON_INICIO_TRANSITORIOS_INCRUSTADO.search(texto)
    if m_tr:
        for i in range(m_tr.start(), len(chars)):
            if chars[i] != "\n":
                chars[i] = " "

    texto_parcial = "".join(chars)
    for m in PATRON_NOTA_REFORMA_INLINE.finditer(texto_parcial):
        for i in range(m.start(), m.end()):
            if chars[i] != "\n":
                chars[i] = " "
    return "".join(chars)


def parsear_token_articulo(token: str) -> Optional[Tuple[int, Optional[str], str]]:
    """
    Convierte una cadena de número de artículo (ej. "140 Bis", "153-A", "3o.", "240 C")
    en (numero_base, sufijo_normalizado, slug_num).
    """
    limpio = token.strip()
    limpio = re.sub(r"^[.\-\s]+|[.\-\s]+$", "", limpio)
    m = re.match(r"^(\d+)\s*(?:[°ºo]\.?|\.-)?\s*(.*)$", limpio, re.IGNORECASE)
    if not m:
        return None
    num_base = int(m.group(1))
    resto = m.group(2).strip()
    resto = re.sub(r"^[\-.\s]+|[\-.\s]+$", "", resto)
    sufijo = normalizar_sufijo(resto) if resto else None
    _, slug_num = formatear_numero_canonico(num_base, sufijo, False)
    return num_base, sufijo, slug_num


def slugificar_norma_externa(nombre: str) -> str:
    """Genera un slug estable para una NormaExterna a partir de su nombre."""
    norm = normalizar_texto_comparacion(nombre)
    partes = [p for p in norm.split() if p not in {"de", "del", "la", "el", "los", "las", "para", "en", "y"}]
    slug = "_".join(partes[:8])
    return slug or "norma_desconocida"


def obtener_snippet_contexto(texto: str, inicio: int, fin: int, ventana: int = 85) -> str:
    """Extrae un fragmento legible alrededor del span [inicio:fin]."""
    s_ini = max(0, inicio - ventana)
    s_fin = min(len(texto), fin + ventana)
    frag = texto[s_ini:s_fin].replace("\n", " ")
    frag = re.sub(r"\s+", " ", frag).strip()
    return frag


def determinar_unidad_span(nodo_art: NodoArticulo, span_inicio: int) -> str:
    """
    Determina en qué sección lógica del artículo (texto_general, fraccion:X, inciso:y)
    ocurre el span_inicio dentro de texto_completo.
    """
    lineas = nodo_art.texto_completo[:span_inicio].split("\n")
    unidad_actual = "texto_general"
    for linea in lineas:
        m_f = re.match(r"^Fracci[oó]n\s+([^\s.]+)\.", linea)
        if m_f:
            unidad_actual = f"fraccion:{m_f.group(1)}"
        else:
            m_i = re.match(r"^Inciso\s+([^\s)]+)\)", linea)
            if m_i:
                unidad_actual = f"inciso:{m_i.group(1)}"
    return unidad_actual


class DetectorReferencias:
    """
    Motor de detección basada en reglas y expresiones regulares para citas jurídicas.
    Fase 3: Referencias directas dentro de la misma ley y explícitas a otra ley
            (tanto en orden Artículo->Ley como Ley->Artículo).
    """

    def __init__(
        self,
        leyes: Dict[str, NodoLey],
        articulos_por_ley: Dict[str, List[NodoArticulo]],
    ) -> None:
        self.leyes = leyes
        self.articulos_por_ley = articulos_por_ley
        self.alias_ordenados = obtener_alias_ordenados()

        # Índice rápido: (ley_slug, slug_num) -> NodoArticulo (excluyendo transitorios)
        self.indice_destino: Dict[Tuple[str, str], NodoArticulo] = {}
        # Índice por número base: (ley_slug, numero_base) -> List[NodoArticulo]
        self.indice_base: Dict[Tuple[str, int], List[NodoArticulo]] = {}
        # Lista de artículos ordinarios ordenados secuencialmente por ley: ley_slug -> List[NodoArticulo]
        self.ordinarios_por_ley: Dict[str, List[NodoArticulo]] = {}
        # Mapa de posición 0-based en ordinarios_por_ley: art.id -> int
        self.posicion_en_ley: Dict[str, int] = {}

        for slug, lista_arts in articulos_por_ley.items():
            ordinarios: List[NodoArticulo] = []
            for art in lista_arts:
                if art.es_transitorio:
                    continue
                partes_id = art.id.split(":")
                slug_num = partes_id[-1]
                self.indice_destino[(slug, slug_num)] = art
                self.indice_base.setdefault((slug, art.numero_base), []).append(art)
                self.posicion_en_ley[art.id] = len(ordinarios)
                ordinarios.append(art)
            self.ordinarios_por_ley[slug] = ordinarios

        self._compilar_patrones()

    def _compilar_patrones(self) -> None:
        """Compila las expresiones regulares ancladas en 'artículo(s)/arts.' para ejecución en <1s."""
        sub_comp_post = (
            r"(?:[ \t]*,?[ \t]*(?:en[ \t]+su[ \t]+|en[ \t]+sus[ \t]+)?"
            r"(?:fracci[oó]n(?:es)?[ \t]+(?-i:[IVXLCDM\d]+)(?:[ \t]*(?:,|\by\b(?![ \t]+\d)|\ba\b(?![ \t]+\d))[ \t]*(?-i:[IVXLCDM\d]+))*"
            r"|apartado[ \t]+[\"“]?[A-Z][\"”]?"
            r"|p[aá]rrafos?[ \t]+[a-záéíóúñ\d]+"
            r"|(?:primer|segundo|tercer|cuarto|quinto|sexto|[uú]ltimo|pen[uú]ltimo)[ \t]+p[aá]rrafo"
            r"|inciso[ \t]+[a-z]\)))?"
            r"(?:[ \t]*,?[ \t]*(?:fracci[oó]n(?:es)?[ \t]+(?-i:[IVXLCDM\d]+)"
            r"|apartado[ \t]+[\"“]?[A-Z][\"”]?"
            r"|p[aá]rrafos?[ \t]+[a-záéíóúñ\d]+"
            r"|(?:primer|segundo|tercer|cuarto|quinto|sexto|[uú]ltimo|pen[uú]ltimo)[ \t]+p[aá]rrafo))?"
        )

        cola_ley = (
            r"(?:[ \t]*,?[ \t]*(?:de[ \t]+la[ \t]+|del[ \t]+|de[ \t]+este[ \t]+|de[ \t]+esta[ \t]+|de[ \t]+[eé]sta[ \t]+|del[ \t]+presente[ \t]+|de[ \t]+la[ \t]+presente[ \t]+|de[ \t]+la[ \t]+misma[ \t]+|del[ \t]+mismo[ \t]+)"
            r"(?:Ley|C[oó]digo|Constituci[oó]n|Reglamento|Estatuto|Ordenamiento)"
            r"(?:[ \t]*,?[ \t]+(?:"
            r"(?-i:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)\b"
            r"|civil\b|penal\b|civiles\b|penales\b|trabajo\b|soberano\b|libre\b|unidos\b|mexicanos\b"
            r"|(?:de|del|la|el|los|las|para|en|sobre|y|o|a)\b(?=[ \t]+(?:(?-i:[A-ZÁÉÍÓÚÑ])|(?:los|las|el|la)\b)))){0,16}"
            r"|[ \t]+constitucional(?:es)?\b"
            r"|[ \t]+de[ \t]+[eé]st[ea]\b)?"
        )

        # Un bloque numérico puede ser un artículo individual o un par de rango "X a Y" / "X al Y"
        token_num_o_rango = (
            rf"(?:(?:del[ \t]+)?{TOKEN_NUM_ARTICULO}{sub_comp_post}"
            rf"(?:[ \t]+(?:a|al)[ \t]+(?:el[ \t]+)?{TOKEN_NUM_ARTICULO}{sub_comp_post})?)"
        )

        # Patrón 1: Anclado directamente en \b(artículos?|arts\.)
        self.patron_principal = re.compile(
            rf"\b(?P<palabra_art>art[íi]culos?|arts?\.)[ \t]+"
            rf"(?P<lista_nums>{token_num_o_rango}"
            rf"(?:[ \t]*(?:,|\by\b|\bo\b)[ \t]*(?:en[ \t]+el[ \t]+)?"
            rf"(?!el\b|la\b|los\b|las\b|en\b|se\b|que\b|para\b|por\b|con\b|sin\b|cuando\b|si\b|no\b|deber|podr|ser|est[aá]|son\b|del\b|de\b|\ba\b|\bal\b)"
            rf"{token_num_o_rango})*)"
            rf"(?P<cola_ley>{cola_ley})",
            re.IGNORECASE,
        )

        # Patrón 2 (Orden invertido): anclado en ", en su(s) artículo(s) X"
        self.patron_ley_primero = re.compile(
            r"\b(?P<ley_inv>(?:(?:esta|este|la[ \t]+presente|el[ \t]+presente)[ \t]+(?:Ley|C[oó]digo|Constituci[oó]n|Ordenamiento))"
            r"|(?:(?:Ley|C[oó]digo|Constituci[oó]n)(?:[ \t]+(?:(?-i:[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)|de|del|la|el|los|las|para|en|y)){1,12}))"
            r"[ \t]*,?[ \t]+en[ \t]+(?:su|sus)[ \t]+(?:(?P<comp_inv>p[aá]rrafo[ \t]+\w+|fracci[oó]n[ \t]+[IVXLCDM]+)[ \t]+del[ \t]+)?"
            r"(?P<palabra_art>art[íi]culos?|arts?\.)[ \t]+"
            rf"(?P<lista_nums>{TOKEN_NUM_ARTICULO}{sub_comp_post})",
            re.IGNORECASE,
        )

        # Patrón 3 (Fase 4 - Referencias relativas entre artículos: "el artículo anterior", "los dos artículos anteriores", etc.)
        self.patron_relativa_articulo = re.compile(
            r"\b(?:(?P<prep>el|los|al|del|en[ \t]+el|en[ \t]+los)[ \t]+)?"
            r"(?:(?P<cant>dos|tres|cuatro|cinco)[ \t]+)?"
            r"(?P<palabra_art>art[íi]culos?)[ \t]+"
            r"(?P<dir>inmediato(?:s)?[ \t]+anterior(?:es)?|inmediato(?:s)?[ \t]+siguiente(?:s)?"
            r"|anterior(?:es)?|siguiente(?:s)?|precedente(?:s)?"
            r"|que[ \t]+precede(?:n)?|que[ \t]+antecede(?:n)?)\b",
            re.IGNORECASE,
        )

        # Patrón 4 (Fase 4 - Referencias relativas a la propia ley: "la presente Ley", "este Código", "esta Constitución")
        self.patron_relativa_ley = re.compile(
            r"\b(?:la[ \t]+presente|el[ \t]+presente|esta|este)[ \t]+"
            r"(?:Ley|C[oó]digo|Constituci[oó]n|Ordenamiento)\b",
            re.IGNORECASE,
        )

    def _clasificar_destino_ley(
        self,
        cola_ley_raw: str,
        ley_origen_slug: str,
        ultima_ley_contexto: Optional[str] = None,
    ) -> Tuple[str, Optional[str], Optional[str], str]:
        """
        Analiza la mención de ley asociada a una referencia y devuelve:
          (tipo_resolucion, destino_ley_slug, nombre_norma_externa, confianza)
        donde tipo_resolucion es:
          - "misma_ley"
          - "otra_ley_corpus"
          - "norma_externa"
          - "ley_ambigua"
        """
        if not cola_ley_raw or not cola_ley_raw.strip():
            return "misma_ley", ley_origen_slug, None, "alta"

        limpio = cola_ley_raw.strip()
        limpio_norm = normalizar_texto_comparacion(limpio)

        # 1a. Anáforas "del mismo Código", "de la misma Ley", "de la misma Constitución"
        if re.search(r"\bmism[oa]\s+(?:ley|codigo|constitucion|ordenamiento)\b", limpio_norm):
            if ultima_ley_contexto and ultima_ley_contexto != ley_origen_slug:
                return "otra_ley_corpus", ultima_ley_contexto, None, "media"
            return "misma_ley", ley_origen_slug, None, "alta"

        # 1b. Referencias explícitas a la misma ley ("de esta Ley", "de este Código", "del presente Código", "de ésta")
        if re.search(
            r"\b(?:est[ea]\s+(?:ley|codigo|constitucion|ordenamiento)|presente\s+(?:ley|codigo|constitucion|ordenamiento)|de\s+est[ea]$)",
            limpio_norm,
        ):
            return "misma_ley", ley_origen_slug, None, "alta"

        # 2. "de la Ley" en LFT se refiere a la propia LFT
        if re.fullmatch(r"de\s+la\s+ley(?:\s+[yo])?", limpio_norm):
            if ley_origen_slug == "lft":
                return "misma_ley", "lft", None, "media"
            return "ley_ambigua", None, "la Ley", "baja"

        # 3. Adjetivo "constitucional" / "constitucionales"
        if re.fullmatch(r"constitucional(?:es)?", limpio_norm):
            return "otra_ley_corpus", "cpeum", None, "alta"

        # 4. Constitución Local de Tlaxcala explícita -> NormaExterna
        if "constitucion" in limpio_norm and "tlaxcala" in limpio_norm:
            return (
                "norma_externa",
                None,
                "Constitución Política del Estado Libre y Soberano de Tlaxcala",
                "alta",
            )

        # 5. Código Civil para el Distrito Federal -> NormaExterna (no confundir con CC-TLAX)
        if "codigo civil" in limpio_norm and (
            "distrito federal" in limpio_norm or "ciudad de mexico" in limpio_norm or "federal" in limpio_norm
        ):
            return (
                "norma_externa",
                None,
                "Código Civil para el Distrito Federal",
                "alta",
            )

        # 6. Código Nacional de Procedimientos Penales -> NormaExterna (no confundir con CPP-TLAX)
        if "codigo nacional de procedimientos penales" in limpio_norm:
            return (
                "norma_externa",
                None,
                "Código Nacional de Procedimientos Penales",
                "alta",
            )

        # 7. Buscar el alias más largo en CATALOGO_LEYES
        for alias_norm, alias_orig, slug_candidato in self.alias_ordenados:
            # Evitar que un alias corto ("ley", "codigo") coincida dentro de otra ley
            if re.search(rf"\b{re.escape(alias_norm)}\b", limpio_norm):
                # Verificar que si coincidió "codigo civil", no venga seguido de "federal" o "del distrito"
                return (
                    "misma_ley" if slug_candidato == ley_origen_slug else "otra_ley_corpus",
                    slug_candidato,
                    None,
                    "alta",
                )

        # 8. "Constitución" a secas:
        # En leyes federales (CPEUM, LFT) es CPEUM; en leyes estatales queda ambigua (Decisión 4 y Sección 7.5)
        if re.search(r"\bconstitucion\b", limpio_norm):
            if self.leyes[ley_origen_slug].ambito == "federal":
                return (
                    "misma_ley" if ley_origen_slug == "cpeum" else "otra_ley_corpus",
                    "cpeum",
                    None,
                    "media",
                )
            return "ley_ambigua", None, "Constitución (ambigua Federal vs Local)", "baja"

        # 9. Otra Ley, Código o Reglamento explícito no cargado en el corpus
        m_ext = re.search(
            r"((?:Ley|C[oó]digo|Reglamento|Estatuto)\s+[^\n.;:]+)",
            limpio,
            re.IGNORECASE,
        )
        if m_ext:
            nombre_ext = m_ext.group(1).strip().rstrip(",.;:")
            nombre_ext = re.sub(
                r"\s*,?\s+(?:as[ií]|para\s+su\b|que\s+se\b|publicad[oa]|vigente|en\s+vigor|ser[aá]n|mism[oa]s?|en\s+los\s+t[eé]rminos|en\s+el\s+supuesto|en\s*$).*$",
                "",
                nombre_ext,
                flags=re.IGNORECASE,
            ).strip().rstrip(",.;:")
            return "norma_externa", None, nombre_ext, "alta"

        return "misma_ley", ley_origen_slug, None, "alta"

    def _extraer_items_y_rangos(
        self, lista_nums_str: str, comp_prev: Optional[str]
    ) -> Tuple[List[Tuple[str, Optional[str]]], List[Tuple[str, str, str]]]:
        """
        Extrae de `lista_nums_str` tanto los artículos individuales como los pares de rango.
        Devuelve:
          - items_individuales: List[(num_raw, comp_final)]
          - rangos_detectados: List[(num_inicio_raw, num_fin_raw, texto_rango)]
        """
        patron_rango_par = re.compile(
            rf"(?P<rango_txt>(?:del[ \t]+)?(?P<ini>{TOKEN_NUM_ARTICULO})[ \t]+(?:a|al)[ \t]+(?:el[ \t]+)?(?P<fin>{TOKEN_NUM_ARTICULO}))",
            re.IGNORECASE,
        )
        rangos: List[Tuple[str, str, str]] = []
        chars = list(lista_nums_str)
        for mr in patron_rango_par.finditer(lista_nums_str):
            rangos.append(
                (
                    mr.group("ini").strip(),
                    mr.group("fin").strip(),
                    mr.group("rango_txt").strip(),
                )
            )
            for idx in range(mr.start(), mr.end()):
                chars[idx] = " "

        resto_str = "".join(chars)
        patron_item = re.compile(
            rf"(?P<num>{TOKEN_NUM_ARTICULO})"
            r"(?:\s*,?\s*(?:en\s+su\s+|en\s+sus\s+)?"
            r"(?P<comp>(?:fracci[oó]n(?:es)?\s+(?-i:[IVXLCDM\d]+)(?:\s*(?:,|\by\b(?![ \t]+\d)|\ba\b(?![ \t]+\d))\s*(?-i:[IVXLCDM\d]+))*"
            r"|apartado\s+[A-Z]|p[aá]rrafo\s+\w+|inciso\s+[a-z]\))"
            r"(?:\s*,?\s*(?:fracci[oó]n(?:es)?\s+(?-i:[IVXLCDM\d]+)|apartado\s+[A-Z]|p[aá]rrafo\s+\w+|pen[uú]ltimo\s+p[aá]rrafo|[uú]ltimo\s+p[aá]rrafo))*))?",
            re.IGNORECASE,
        )
        items: List[Tuple[str, Optional[str]]] = []
        comp_prev_limpio = comp_prev.strip() if comp_prev else None

        for m in patron_item.finditer(resto_str):
            num_raw = m.group("num").strip()
            comp_post = m.group("comp").strip() if m.group("comp") else None
            comp_final = comp_post or comp_prev_limpio
            items.append((num_raw, comp_final))

        return items, rangos

    def expandir_rango_articulos(
        self, dest_ley_slug: str, ini_raw: str, fin_raw: str
    ) -> Tuple[Optional[List[NodoArticulo]], Optional[str]]:
        """
        Expande un rango (ini_raw, fin_raw) siguiendo el orden secuencial real de `dest_ley_slug`.
        Incluye subartículos intermedios (Bis, Ter, -A..-N).
        Devuelve (lista_nodos, motivo_error).
        """
        p_ini = parsear_token_articulo(ini_raw)
        p_fin = parsear_token_articulo(fin_raw)
        if not p_ini or not p_fin:
            return None, "rango_invalido"

        _, _, slug_ini = p_ini
        _, _, slug_fin = p_fin

        nodo_ini = self.indice_destino.get((dest_ley_slug, slug_ini))
        nodo_fin = self.indice_destino.get((dest_ley_slug, slug_fin))
        if nodo_ini is None or nodo_fin is None:
            return None, "articulo_inexistente"

        pos_ini = self.posicion_en_ley.get(nodo_ini.id)
        pos_fin = self.posicion_en_ley.get(nodo_fin.id)
        if pos_ini is None or pos_fin is None or pos_ini > pos_fin:
            return None, "rango_invalido"

        ordinarios = self.ordinarios_por_ley.get(dest_ley_slug, [])
        # Si el artículo final tiene subartículos (ej. "artículos 10 a 15" y existe "15 Bis"),
        # incluir únicamente hasta nodo_fin exacto (pos_fin inclusive), que ya incluye todos los intermedios.
        return ordinarios[pos_ini : pos_fin + 1], None

    def detectar_en_corpus(
        self,
        incluir_transitorios: bool = False,
        incluir_rangos_y_relativas: bool = False,
    ) -> Dict[str, Any]:
        """
        Ejecuta la detección de referencias en todo el corpus.
        - Si `incluir_rangos_y_relativas=False` (Fase 3): solo directas, listas y explícitas a otra ley.
        - Si `incluir_rangos_y_relativas=True` (Fase 4): añade expansión de rangos y referencias relativas
          (a artículos anteriores/siguientes y a la propia ley).
        Devuelve un diccionario con:
          - aristas_refiere_a: List[AristaRefiereA]
          - aristas_menciona_norma: List[AristaMencionaNorma]
          - normas_externas: Dict[str, NodoNormaExterna]
          - referencias_rotas: List[ReferenciaRota]
        """
        aristas_refiere_a: List[AristaRefiereA] = []
        aristas_menciona_norma: List[AristaMencionaNorma] = []
        normas_externas: Dict[str, NodoNormaExterna] = {}
        referencias_rotas: List[ReferenciaRota] = []

        for ley_slug, lista_articulos in self.articulos_por_ley.items():
            nodo_ley_origen = self.leyes[ley_slug]
            # Contexto persistente de última ley externa/cruzada citada en artículos recientes de la misma ley
            contexto_ley_reciente: List[Optional[str]] = [None]
            orden_ultimo_contexto: List[int] = [-10]

            for nodo_art in lista_articulos:
                if nodo_art.es_transitorio and not incluir_transitorios:
                    continue

                texto_original = nodo_art.texto_completo
                if not texto_original:
                    continue

                texto_limpio = _enmascarar_notas_reforma(texto_original)
                spans_ocupados: List[Tuple[int, int]] = []
                # Si el artículo inmediatamente anterior citó otra ley (ej. cpc_tlax:1269 -> cc_tlax),
                # conservarla como contexto inicial para anáforas como "del mismo Código" en cpc_tlax:1270
                if nodo_art.orden - orden_ultimo_contexto[0] <= 2:
                    contexto_ley: List[Optional[str]] = [contexto_ley_reciente[0]]
                else:
                    contexto_ley = [None]

                tiene_palabra_art = bool(
                    re.search(r"\b(?:art[íi]culos?|arts?\.)", texto_limpio, re.IGNORECASE)
                )

                if tiene_palabra_art:
                    # 1. Primero evaluar patrón de orden invertido ("la Ley X, en su artículo Y")
                    if (
                        "en su" in texto_limpio.lower()
                        or "en el art" in texto_limpio.lower()
                        or "en los art" in texto_limpio.lower()
                    ):
                        for m_inv in self.patron_ley_primero.finditer(texto_limpio):
                            ini, fin = m_inv.span()
                            spans_ocupados.append((ini, fin))
                            ley_inv = m_inv.group("ley_inv")
                            comp_inv = m_inv.group("comp_inv")
                            lista_nums = m_inv.group("lista_nums")

                            self._procesar_coincidencia(
                                nodo_art=nodo_art,
                                ley_origen_slug=ley_slug,
                                ley_origen_id=nodo_ley_origen.id,
                                texto_original=texto_original,
                                ini=ini,
                                fin=fin,
                                lista_nums_str=lista_nums,
                                comp_prev=comp_inv,
                                cola_ley_raw=f"de la {ley_inv}",
                                aristas_refiere_a=aristas_refiere_a,
                                aristas_menciona_norma=aristas_menciona_norma,
                                normas_externas=normas_externas,
                                referencias_rotas=referencias_rotas,
                                contexto_ley=contexto_ley,
                                incluir_rangos=incluir_rangos_y_relativas,
                            )

                    # 2. Evaluar patrón principal ("artículo X [a Y] [de la Ley Z]")
                    for m_prin in self.patron_principal.finditer(texto_limpio):
                        ini, fin = m_prin.span()
                        if any(
                            not (fin <= o_ini or ini >= o_fin)
                            for o_ini, o_fin in spans_ocupados
                        ):
                            continue

                        lista_nums = m_prin.group("lista_nums")
                        spans_ocupados.append((ini, fin))

                        ventana_prev = texto_limpio[max(0, ini - 90) : ini]
                        m_prev = PATRON_COMPONENTE_PREVIO.search(ventana_prev)
                        if m_prev:
                            comp_prev = m_prev.group(1).strip()
                            ini = max(0, ini - 90) + m_prev.start()
                        else:
                            comp_prev = None

                        cola_ley = m_prin.group("cola_ley") or ""

                        self._procesar_coincidencia(
                            nodo_art=nodo_art,
                            ley_origen_slug=ley_slug,
                            ley_origen_id=nodo_ley_origen.id,
                            texto_original=texto_original,
                            ini=ini,
                            fin=fin,
                            lista_nums_str=lista_nums,
                            comp_prev=comp_prev,
                            cola_ley_raw=cola_ley,
                            aristas_refiere_a=aristas_refiere_a,
                            aristas_menciona_norma=aristas_menciona_norma,
                            normas_externas=normas_externas,
                            referencias_rotas=referencias_rotas,
                            contexto_ley=contexto_ley,
                            incluir_rangos=incluir_rangos_y_relativas,
                        )

                    # 3. Fase 4: Referencias relativas a artículos ("el artículo anterior", "el artículo siguiente", etc.)
                    if incluir_rangos_y_relativas:
                        for m_rel in self.patron_relativa_articulo.finditer(texto_limpio):
                            ini, fin = m_rel.span()
                            if any(
                                not (fin <= o_ini or ini >= o_fin)
                                for o_ini, o_fin in spans_ocupados
                            ):
                                continue
                            spans_ocupados.append((ini, fin))

                            ventana_prev = texto_limpio[max(0, ini - 90) : ini]
                            m_prev = PATRON_COMPONENTE_PREVIO.search(ventana_prev)
                            if m_prev:
                                comp_prev = m_prev.group(1).strip()
                                ini = max(0, ini - 90) + m_prev.start()
                            else:
                                comp_prev = None

                            self._procesar_relativa_articulo(
                                nodo_art=nodo_art,
                                ley_origen_slug=ley_slug,
                                ley_origen_id=nodo_ley_origen.id,
                                texto_original=texto_original,
                                ini=ini,
                                fin=fin,
                                m_rel=m_rel,
                                comp_prev=comp_prev,
                                aristas_refiere_a=aristas_refiere_a,
                                referencias_rotas=referencias_rotas,
                            )

                # 4. Fase 4: Referencias relativas a la propia ley ("la presente Ley", "este Código", "esta Constitución")
                if incluir_rangos_y_relativas:
                    for m_ley in self.patron_relativa_ley.finditer(texto_limpio):
                        ini, fin = m_ley.span()
                        # Si ya fue parte de una cita a artículo ("artículo 80 de este Código"), se omite
                        if any(
                            not (fin <= o_ini or ini >= o_fin)
                            for o_ini, o_fin in spans_ocupados
                        ):
                            continue
                        spans_ocupados.append((ini, fin))
                        texto_ref = texto_original[ini:fin].strip()
                        snippet = obtener_snippet_contexto(texto_original, ini, fin)
                        unidad = determinar_unidad_span(nodo_art, ini)

                        arista_rel_ley = AristaRefiereA(
                            id=f"ref:{len(aristas_refiere_a) + 1}",
                            origen_id=nodo_art.id,
                            destino_id=nodo_ley_origen.id,
                            origen_ley_id=nodo_ley_origen.id,
                            destino_ley_id=nodo_ley_origen.id,
                            clase="relativa",
                            relacion="misma_ley",
                            texto_referencia=texto_ref,
                            snippet=snippet,
                            snippet_exacto=texto_ref,
                            span_inicio=ini,
                            span_fin=fin,
                            unidad=unidad,
                            componente=None,
                            rango=None,
                            grupo_id=None,
                            confianza="alta",
                            metodo="contexto",
                            estado="resuelta",
                        )
                        aristas_refiere_a.append(arista_rel_ley)

                if contexto_ley[0] is not None and contexto_ley[0] != ley_slug:
                    contexto_ley_reciente[0] = contexto_ley[0]
                    orden_ultimo_contexto[0] = nodo_art.orden

        return {
            "aristas_refiere_a": aristas_refiere_a,
            "aristas_menciona_norma": aristas_menciona_norma,
            "normas_externas": normas_externas,
            "referencias_rotas": referencias_rotas,
        }

    def _procesar_coincidencia(
        self,
        nodo_art: NodoArticulo,
        ley_origen_slug: str,
        ley_origen_id: str,
        texto_original: str,
        ini: int,
        fin: int,
        lista_nums_str: str,
        comp_prev: Optional[str],
        cola_ley_raw: str,
        aristas_refiere_a: List[AristaRefiereA],
        aristas_menciona_norma: List[AristaMencionaNorma],
        normas_externas: Dict[str, NodoNormaExterna],
        referencias_rotas: List[ReferenciaRota],
        contexto_ley: Optional[List[Optional[str]]] = None,
        incluir_rangos: bool = False,
    ) -> None:
        """Resuelve cada artículo individual y cada rango en una coincidencia y crea las aristas o reportes."""
        texto_referencia = texto_original[ini:fin].strip()
        snippet = obtener_snippet_contexto(texto_original, ini, fin)
        unidad = determinar_unidad_span(nodo_art, ini)

        # Detectar si unos renglones antes en el mismo párrafo se nombró una ley externa y se dice "del referido ordenamiento"
        cola_efectiva = cola_ley_raw
        if not cola_efectiva.strip():
            cola_inmediata = texto_original[fin : fin + 55]
            if re.match(
                r"^\s+del\s+referido\s+ordenamiento", cola_inmediata, re.IGNORECASE
            ):
                ventana_ant = texto_original[max(0, ini - 280) : ini]
                m_ley_ant = re.search(
                    r"\b((?:Ley|C[oó]digo|Reglamento)\s+(?:General|Federal|Nacional|del|de\s+la)\s+[^\n,.;:]{3,70}?)(?=\s+(?:y\s+que|que\s+se|en\s+su|con\s+las|,|;|\.))",
                    ventana_ant,
                )
                if m_ley_ant:
                    cola_efectiva = f"de la {m_ley_ant.group(1).strip()}"

        ultima_ley = contexto_ley[0] if contexto_ley else None
        tipo_res, dest_ley_slug, nombre_ext, confianza = self._clasificar_destino_ley(
            cola_efectiva, ley_origen_slug, ultima_ley_contexto=ultima_ley
        )
        if (
            contexto_ley is not None
            and dest_ley_slug is not None
            and cola_efectiva.strip()
        ):
            contexto_ley[0] = dest_ley_slug

        items, rangos = self._extraer_items_y_rangos(lista_nums_str, comp_prev)

        # 1. Procesar artículos individuales (si los hay)
        es_lista = (len(items) + len(rangos)) > 1
        grupo_id = f"grp:{uuid.uuid4().hex[:8]}" if es_lista else None

        for num_raw, comp_item in items:
            parsed = parsear_token_articulo(num_raw)
            if not parsed:
                continue
            num_base, sufijo, slug_num = parsed

            if tipo_res == "ley_ambigua":
                referencias_rotas.append(
                    ReferenciaRota(
                        origen_id=nodo_art.id,
                        ley_origen=ley_origen_id,
                        texto_referencia=texto_referencia,
                        destino_mencionado=f"Artículo {num_raw} ({nombre_ext})",
                        motivo="ley_ambigua",
                        snippet=snippet,
                        span_inicio=ini,
                        span_fin=fin,
                        confianza="baja",
                        sugerencia="Especificar si se refiere a CPEUM o a la Constitución Local de Tlaxcala",
                    )
                )
                continue

            if tipo_res == "norma_externa" and nombre_ext:
                ext_slug = slugificar_norma_externa(nombre_ext)
                ext_id = f"norma_externa:{ext_slug}"
                if ext_id not in normas_externas:
                    normas_externas[ext_id] = NodoNormaExterna(
                        id=ext_id,
                        nombre=nombre_ext,
                        alias=[nombre_ext],
                    )
                arista_m = AristaMencionaNorma(
                    id=f"menciona:{len(aristas_menciona_norma) + 1}",
                    origen_id=nodo_art.id,
                    destino_id=ext_id,
                    texto_referencia=texto_referencia,
                    snippet=snippet,
                    snippet_exacto=texto_referencia,
                    span_inicio=ini,
                    span_fin=fin,
                    articulo_mencionado=num_raw,
                    confianza=confianza,
                    metodo="regex+alias",
                )
                aristas_menciona_norma.append(arista_m)
                referencias_rotas.append(
                    ReferenciaRota(
                        origen_id=nodo_art.id,
                        ley_origen=ley_origen_id,
                        texto_referencia=texto_referencia,
                        destino_mencionado=f"Artículo {num_raw} de {nombre_ext}",
                        motivo="ley_no_cargada",
                        snippet=snippet,
                        span_inicio=ini,
                        span_fin=fin,
                        confianza=confianza,
                        sugerencia=f"Norma externa registrada como {ext_id}",
                    )
                )
                continue

            assert dest_ley_slug is not None
            nodo_dest = self.indice_destino.get((dest_ley_slug, slug_num))

            if nodo_dest is None:
                candidatos = self.indice_base.get((dest_ley_slug, num_base), [])
                sug = (
                    f"Existen subartículos: {', '.join(c.id for c in candidatos[:4])}"
                    if candidatos
                    else None
                )
                referencias_rotas.append(
                    ReferenciaRota(
                        origen_id=nodo_art.id,
                        ley_origen=ley_origen_id,
                        texto_referencia=texto_referencia,
                        destino_mencionado=f"articulo:{dest_ley_slug}:{slug_num}",
                        motivo="articulo_inexistente",
                        snippet=snippet,
                        span_inicio=ini,
                        span_fin=fin,
                        confianza=confianza,
                        sugerencia=sug,
                    )
                )
                continue

            if nodo_dest.id == nodo_art.id and tipo_res == "misma_ley":
                continue

            es_otra_ley = dest_ley_slug != ley_origen_slug
            clase = (
                "explicita_otra_ley"
                if es_otra_ley
                else ("lista" if es_lista else "directa")
            )
            relacion = "entre_leyes" if es_otra_ley else "misma_ley"
            metodo = "regex+alias" if cola_efectiva.strip() else "regex"

            arista_ref = AristaRefiereA(
                id=f"ref:{len(aristas_refiere_a) + 1}",
                origen_id=nodo_art.id,
                destino_id=nodo_dest.id,
                origen_ley_id=ley_origen_id,
                destino_ley_id=self.leyes[dest_ley_slug].id,
                clase=clase,
                relacion=relacion,
                texto_referencia=texto_referencia,
                snippet=snippet,
                snippet_exacto=texto_referencia,
                span_inicio=ini,
                span_fin=fin,
                unidad=unidad,
                componente=comp_item,
                rango=None,
                grupo_id=grupo_id,
                confianza=confianza,
                metodo=metodo,
                estado="resuelta",
            )
            aristas_refiere_a.append(arista_ref)

        # 2. Fase 4: Procesar rangos ("artículos 10 a 15", "897-A al 897-G")
        if not incluir_rangos or not rangos:
            return

        for ini_raw, fin_raw, rango_txt in rangos:
            etiqueta_rango = f"{ini_raw}..{fin_raw}"
            grp_rango = grupo_id or f"grp:{uuid.uuid4().hex[:8]}"

            if tipo_res == "norma_externa" and nombre_ext:
                ext_slug = slugificar_norma_externa(nombre_ext)
                ext_id = f"norma_externa:{ext_slug}"
                if ext_id not in normas_externas:
                    normas_externas[ext_id] = NodoNormaExterna(
                        id=ext_id,
                        nombre=nombre_ext,
                        alias=[nombre_ext],
                    )
                arista_m = AristaMencionaNorma(
                    id=f"menciona:{len(aristas_menciona_norma) + 1}",
                    origen_id=nodo_art.id,
                    destino_id=ext_id,
                    texto_referencia=texto_referencia,
                    snippet=snippet,
                    snippet_exacto=texto_referencia,
                    span_inicio=ini,
                    span_fin=fin,
                    articulo_mencionado=etiqueta_rango,
                    confianza=confianza,
                    metodo="regex+alias",
                )
                aristas_menciona_norma.append(arista_m)
                referencias_rotas.append(
                    ReferenciaRota(
                        origen_id=nodo_art.id,
                        ley_origen=ley_origen_id,
                        texto_referencia=texto_referencia,
                        destino_mencionado=f"Artículos {etiqueta_rango} de {nombre_ext}",
                        motivo="ley_no_cargada",
                        snippet=snippet,
                        span_inicio=ini,
                        span_fin=fin,
                        confianza=confianza,
                        sugerencia=f"Norma externa registrada como {ext_id}",
                    )
                )
                continue

            if tipo_res == "ley_ambigua" or dest_ley_slug is None:
                referencias_rotas.append(
                    ReferenciaRota(
                        origen_id=nodo_art.id,
                        ley_origen=ley_origen_id,
                        texto_referencia=texto_referencia,
                        destino_mencionado=f"Artículos {etiqueta_rango}",
                        motivo="ley_ambigua",
                        snippet=snippet,
                        span_inicio=ini,
                        span_fin=fin,
                        confianza="baja",
                        sugerencia="Especificar la ley destino del rango",
                    )
                )
                continue

            nodos_expandidos, error_rango = self.expandir_rango_articulos(
                dest_ley_slug, ini_raw, fin_raw
            )
            if error_rango or not nodos_expandidos:
                referencias_rotas.append(
                    ReferenciaRota(
                        origen_id=nodo_art.id,
                        ley_origen=ley_origen_id,
                        texto_referencia=texto_referencia,
                        destino_mencionado=f"articulo:{dest_ley_slug}:{etiqueta_rango}",
                        motivo=error_rango or "rango_invalido",
                        snippet=snippet,
                        span_inicio=ini,
                        span_fin=fin,
                        confianza="baja",
                        sugerencia=f"Revisar límites del rango {etiqueta_rango} en {dest_ley_slug}",
                    )
                )
                continue

            es_otra_ley = dest_ley_slug != ley_origen_slug
            relacion = "entre_leyes" if es_otra_ley else "misma_ley"
            metodo = "rango+alias" if cola_efectiva.strip() else "rango"

            for nodo_dest in nodos_expandidos:
                if nodo_dest.id == nodo_art.id and not es_otra_ley:
                    continue
                arista_rango = AristaRefiereA(
                    id=f"ref:{len(aristas_refiere_a) + 1}",
                    origen_id=nodo_art.id,
                    destino_id=nodo_dest.id,
                    origen_ley_id=ley_origen_id,
                    destino_ley_id=self.leyes[dest_ley_slug].id,
                    clase="rango",
                    relacion=relacion,
                    texto_referencia=texto_referencia,
                    snippet=snippet,
                    snippet_exacto=texto_referencia,
                    span_inicio=ini,
                    span_fin=fin,
                    unidad=unidad,
                    componente=comp_prev,
                    rango=etiqueta_rango,
                    grupo_id=grp_rango,
                    confianza=confianza,
                    metodo=metodo,
                    estado="resuelta",
                )
                aristas_refiere_a.append(arista_rango)

    def _procesar_relativa_articulo(
        self,
        nodo_art: NodoArticulo,
        ley_origen_slug: str,
        ley_origen_id: str,
        texto_original: str,
        ini: int,
        fin: int,
        m_rel: re.Match,
        comp_prev: Optional[str],
        aristas_refiere_a: List[AristaRefiereA],
        referencias_rotas: List[ReferenciaRota],
    ) -> None:
        """
        Resuelve referencias relativas entre artículos ("el artículo anterior",
        "el artículo siguiente", "los dos artículos anteriores", etc.) usando el orden
        secuencial real de `ordinarios_por_ley`.
        """
        texto_referencia = texto_original[ini:fin].strip()
        snippet = obtener_snippet_contexto(texto_original, ini, fin)
        unidad = determinar_unidad_span(nodo_art, ini)

        palabra_art = m_rel.group("palabra_art").lower()
        cant_str = (m_rel.group("cant") or "").lower().strip()
        dir_str = m_rel.group("dir").lower()

        es_plural = palabra_art.endswith("s")
        mapa_cant = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5}

        # Si es plural sin cuantificador ("los artículos anteriores", "los artículos siguientes"),
        # es una referencia indeterminada y se reporta con confianza baja sin inventar aristas.
        if es_plural and not cant_str:
            referencias_rotas.append(
                ReferenciaRota(
                    origen_id=nodo_art.id,
                    ley_origen=ley_origen_id,
                    texto_referencia=texto_referencia,
                    destino_mencionado=texto_referencia,
                    motivo="relativa_ambigua",
                    snippet=snippet,
                    span_inicio=ini,
                    span_fin=fin,
                    confianza="baja",
                    sugerencia="Plural relativo sin cantidad explícita ('los artículos anteriores/siguientes')",
                )
            )
            return

        cantidad = mapa_cant.get(cant_str, 1)
        hacia_adelante = "siguiente" in dir_str
        pos_actual = self.posicion_en_ley.get(nodo_art.id)
        ordinarios = self.ordinarios_por_ley.get(ley_origen_slug, [])

        if pos_actual is None:
            return

        destinos: List[NodoArticulo] = []
        for paso in range(1, cantidad + 1):
            idx_dest = pos_actual + paso if hacia_adelante else pos_actual - paso
            if 0 <= idx_dest < len(ordinarios):
                destinos.append(ordinarios[idx_dest])
            else:
                referencias_rotas.append(
                    ReferenciaRota(
                        origen_id=nodo_art.id,
                        ley_origen=ley_origen_id,
                        texto_referencia=texto_referencia,
                        destino_mencionado=f"Posición fuera de límites ({idx_dest})",
                        motivo="relativa_sin_anterior",
                        snippet=snippet,
                        span_inicio=ini,
                        span_fin=fin,
                        confianza="baja",
                        sugerencia="No existe artículo previo/siguiente en la secuencia de la ley",
                    )
                )

        grp_id = f"grp:{uuid.uuid4().hex[:8]}" if len(destinos) > 1 else None
        for nodo_dest in destinos:
            arista_rel = AristaRefiereA(
                id=f"ref:{len(aristas_refiere_a) + 1}",
                origen_id=nodo_art.id,
                destino_id=nodo_dest.id,
                origen_ley_id=ley_origen_id,
                destino_ley_id=ley_origen_id,
                clase="relativa",
                relacion="misma_ley",
                texto_referencia=texto_referencia,
                snippet=snippet,
                snippet_exacto=texto_referencia,
                span_inicio=ini,
                span_fin=fin,
                unidad=unidad,
                componente=comp_prev,
                rango=None,
                grupo_id=grp_id,
                confianza="alta" if cantidad == 1 else "media",
                metodo="contexto",
                estado="resuelta",
            )
            aristas_refiere_a.append(arista_rel)
