# preparacion.py
import os
import re
import json
import logging
import subprocess
from pathlib import Path
import docx
import pdfplumber

# ==========================================
# CONFIGURACIÓN DE LOGGING
# ==========================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ==========================================
# CONSTANTES
# ==========================================

_ROMANOS = r'(?:M{0,3})(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})'

PATRON_FRACCION = re.compile(
    rf'(?m)^\s*({_ROMANOS})[\.\-]\s+(.*?)(?=(?:^\s*{_ROMANOS}[\.\-])|\Z)',
    flags=re.DOTALL
)

PATRON_ARTICULO = re.compile(
    r'(?m)^\s*((?:ART[ÍI]CULO|Art[íi]culo)\s+\d+(?:[oOaA]|\.)?'
    r'(?:[\s\.\-]*(?:BIS|TER|QU[ÁA]TER|QUINQUIES|Bis|Ter|Qu[áa]ter|Quinquies))?[\.\-]*)\s*'
    r'(.*?)(?=(?:^\s*(?:ART[ÍI]CULO|Art[íi]culo)\s+\d+)|\Z)',
    flags=re.DOTALL
)

PATRON_DOF = re.compile(
    r'(?m)^\s*(?:Párrafo|Artículo|Fracción|Inciso)?\s*'
    r'(?:reformado|adicionado|derogado)\s+DOF[\s\t\d\-\,\.]*',
    flags=re.IGNORECASE
)

PATRON_REFERENCIA = re.compile(
    r'\b(?:art[íi]culo|art\.)\s*(\d+\s*(?:[oOaA°]\.?)?'
    r'(?:\s*(?:BIS|TER|QU[ÁA]TER|QUINQUIES|Bis|Ter|Qu[áa]ter|Quinquies))?)',
    flags=re.IGNORECASE
)

# MEJORA: Detecta encabezados de jerarquía documental (Título, Capítulo, Sección, Libro)
# para asociar cada artículo con su posición en la estructura de la ley.
# Acepta numeración romana, arábiga y en palabras (PRIMERO, SEGUNDO...).
_ORDINALES_ES = (
    r'(?:PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SÉPTIMO|OCTAVO|NOVENO|DÉCIMO'
    r'|Primero|Segundo|Tercero|Cuarto|Quinto|Sexto|Séptimo|Octavo|Noveno|Décimo)'
)
_NUM_JERARQUIA = rf'(?:{_ROMANOS}|\d+|{_ORDINALES_ES})'

PATRON_JERARQUIA = re.compile(
    rf'(?m)^\s*(LIBRO|TÍTULO|TÍTULO|TITULO|CAPÍTULO|CAPITULO|SECCIÓN|SECCION'
    rf'|Libro|Título|Titulo|Capítulo|Capitulo|Sección|Seccion)'
    rf'\s+({_NUM_JERARQUIA})\b[^\n]*',
    flags=re.IGNORECASE
)


# ==========================================
# 1. LECTURA Y CONVERSIÓN DE ARCHIVOS
# ==========================================

def convertir_doc_a_docx(ruta_archivo: Path) -> Path | None:
    """Convierte .doc a .docx usando LibreOffice headless."""
    log.info("Convirtiendo %s a .docx...", ruta_archivo.name)
    comando = [
        'libreoffice', '--headless', '--convert-to', 'docx',
        str(ruta_archivo), '--outdir', str(ruta_archivo.parent)
    ]
    try:
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ruta_archivo.with_suffix('.docx')
    except subprocess.CalledProcessError as e:
        log.error("Error convirtiendo %s: %s", ruta_archivo.name, e)
        return None


def extraer_texto(ruta_archivo: Path) -> str:
    """
    Extrae texto según la extensión del archivo.
    Un archivo corrupto no detiene el proceso.
    """
    texto = ""
    extension = ruta_archivo.suffix.lower()
    try:
        if extension == '.pdf':
            with pdfplumber.open(ruta_archivo) as pdf:
                for pagina in pdf.pages:
                    t = pagina.extract_text()
                    if t:
                        texto += t + '\n'
        elif extension == '.docx':
            doc = docx.Document(ruta_archivo)
            texto = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        log.error("No se pudo extraer texto de %s: %s", ruta_archivo.name, e)
    return texto


# ==========================================
# 2. LIMPIEZA Y NORMALIZACIÓN
# ==========================================

def normalizar_texto(texto: str) -> str:
    """Colapsa saltos de línea y espacios múltiples en una sola línea."""
    if not texto:
        return ""
    texto = texto.replace('\n', ' ').replace('\t', ' ')
    return re.sub(r'\s+', ' ', texto).strip()


def limpiar_texto_y_extraer_dof(texto: str) -> tuple[str, list[str]]:
    """Separa las notas históricas del DOF del cuerpo legal."""
    notas_dof = [normalizar_texto(n) for n in PATRON_DOF.findall(texto)]
    texto_limpio = PATRON_DOF.sub('', texto).strip()
    return texto_limpio, notas_dof


def extraer_incisos(texto: str) -> list[dict]:
    """Extrae incisos tipo a), b), c) al inicio de línea."""
    patron = re.compile(
        r'(?m)^\s*([a-z])\)(.*?)(?=(?:^\s*[a-z]\))|\Z)',
        flags=re.DOTALL
    )
    return [
        {"inciso": m[0], "texto_general": normalizar_texto(m[1])}
        for m in patron.findall(texto)
    ]


def extraer_fracciones(texto_articulo: str) -> list[dict]:
    """Extrae fracciones en numeración romana."""
    resultado = []
    for match in PATRON_FRACCION.findall(texto_articulo):
        if not match[0]:
            continue
        texto_fraccion = match[1].strip()
        incisos = extraer_incisos(texto_fraccion)
        texto_limpio_fraccion = texto_fraccion
        if incisos:
            partes = re.split(r'(?m)^\s*[a-z]\)', texto_fraccion, maxsplit=1)
            texto_limpio_fraccion = partes[0].strip()
        resultado.append({
            "fraccion": match[0],
            "texto_general": normalizar_texto(texto_limpio_fraccion),
            "incisos": incisos
        })
    return resultado


# ==========================================
# EXTRACCIÓN DE REFERENCIAS
# ==========================================

def extraer_referencias_articulos(texto: str) -> list[str]:
    """
    Extrae y normaliza todas las referencias a otros artículos dentro del texto.
    Devuelve una lista ordenada de strings únicos.
    """
    matches = PATRON_REFERENCIA.findall(texto)
    referencias = set()
    for m in matches:
        ref = "Artículo " + re.sub(r'\s+', ' ', m).strip()
        referencias.add(ref)
    return sorted(referencias)


# ==========================================
# MEJORA: MAPA DE JERARQUÍAS DEL DOCUMENTO
# ==========================================

def construir_mapa_jerarquias(texto_crudo: str) -> list[tuple[int, str]]:
    """
    Escanea el texto completo y devuelve una lista ordenada de
    (posicion_char, etiqueta_jerarquia) para cada encabezado encontrado.

    Ejemplo de salida:
      [(0, ''), (1240, 'Título I'), (5800, 'Capítulo II'), ...]

    Con esto se puede asignar a cada artículo la jerarquía vigente
    en el momento en que aparece en el texto.
    """
    mapa = []
    for m in PATRON_JERARQUIA.finditer(texto_crudo):
        tipo  = m.group(1).capitalize()
        num   = m.group(2).strip()
        # Normalizar el tipo: quitar tildes para uniformidad en los filtros
        tipo_norm = (
            tipo
            .replace('Título', 'Titulo')
            .replace('Capítulo', 'Capitulo')
            .replace('Sección', 'Seccion')
        )
        etiqueta = f"{tipo_norm} {num}"
        mapa.append((m.start(), etiqueta))
    return mapa


def jerarquia_para_posicion(posicion: int, mapa: list[tuple[int, str]]) -> str:
    """
    Dado el offset del artículo en el texto, devuelve la etiqueta
    del último encabezado de jerarquía que apareció antes de él.
    Si no hay ninguno, devuelve cadena vacía.
    """
    jerarquia_actual = ""
    for pos, etiqueta in mapa:
        if pos <= posicion:
            jerarquia_actual = etiqueta
        else:
            break
    return jerarquia_actual


# ==========================================
# 3. ESTRUCTURACIÓN PRINCIPAL
# ==========================================

def estructurar_ley(texto_crudo: str) -> list[dict]:
    """
    Desglosa el texto de la ley en artículos con sus fracciones,
    incisos, notas DOF, referencias y — MEJORA — jerarquía documental.

    Salida temprana si el texto está vacío.
    """
    if not texto_crudo or not texto_crudo.strip():
        log.warning("Se recibió texto vacío en estructurar_ley.")
        return []

    # MEJORA: construir mapa de jerarquías una sola vez
    mapa_jerarquias = construir_mapa_jerarquias(texto_crudo)
    if mapa_jerarquias:
        log.info("Encabezados de jerarquía detectados: %d", len(mapa_jerarquias))

    estructura = []

    for match in PATRON_ARTICULO.finditer(texto_crudo):
        titulo_articulo = normalizar_texto(match.group(1))
        texto_articulo  = match.group(2).strip()

        texto_limpio, notas_historicas = limpiar_texto_y_extraer_dof(texto_articulo)

        fracciones       = extraer_fracciones(texto_limpio)
        incisos_directos = []
        texto_general_limpio = texto_limpio

        if fracciones:
            partes = re.split(r'(?m)^\s*' + _ROMANOS + r'[\.\-]\s+', texto_limpio, maxsplit=1)
            texto_general_limpio = partes[0].strip()
        else:
            incisos_directos = extraer_incisos(texto_limpio)
            if incisos_directos:
                partes = re.split(r'(?m)^\s*[a-z]\)', texto_limpio, maxsplit=1)
                texto_general_limpio = partes[0].strip()

        # Texto completo del artículo para buscar referencias
        texto_completo = " ".join([
            texto_general_limpio,
            " ".join(f["texto_general"] for f in fracciones),
            " ".join(
                " ".join(inc["texto_general"] for inc in f["incisos"])
                for f in fracciones
            ),
            " ".join(inc["texto_general"] for inc in incisos_directos),
        ])

        referencias = extraer_referencias_articulos(texto_completo)

        # Eliminar auto-referencia
        numero_propio = re.search(r'\d+', titulo_articulo)
        if numero_propio:
            patron_propio = re.compile(
                r'^Artículo\s+' + re.escape(numero_propio.group()) + r'\b',
                flags=re.IGNORECASE
            )
            referencias = [r for r in referencias if not patron_propio.match(r)]

        # MEJORA: asignar jerarquía según posición del artículo en el texto
        jerarquia = jerarquia_para_posicion(match.start(), mapa_jerarquias)

        estructura.append({
            "articulo"            : titulo_articulo,
            "jerarquia"           : jerarquia,          # <-- NUEVO campo
            "texto_general"       : normalizar_texto(texto_general_limpio),
            "historial_dof"       : notas_historicas,
            "fracciones"          : fracciones,
            "incisos_directos"    : incisos_directos,
            "referencias_articulos": referencias,
        })

    return estructura


# ==========================================
# 4. PROCESAMIENTO POR LOTES
# ==========================================

def procesar_directorio(carpeta_entrada: str, carpeta_salida: str) -> None:
    """
    Itera sobre PDF/DOCX/DOC, estructura cada ley y guarda el resultado en JSON.
    Los archivos .docx temporales generados desde .doc se eliminan al terminar.
    """
    ruta_entrada = Path(carpeta_entrada)
    ruta_salida  = Path(carpeta_salida)
    ruta_salida.mkdir(parents=True, exist_ok=True)

    archivos = (
        list(ruta_entrada.glob('*.pdf'))  +
        list(ruta_entrada.glob('*.docx')) +
        list(ruta_entrada.glob('*.doc'))
    )
    log.info("Se encontraron %d archivos en %s", len(archivos), carpeta_entrada)

    for archivo in archivos:
        log.info("Procesando: %s", archivo.name)

        archivo_a_procesar = archivo
        docx_temporal      = None

        if archivo.suffix.lower() == '.doc':
            archivo_a_procesar = convertir_doc_a_docx(archivo)
            if not archivo_a_procesar:
                continue
            docx_temporal = archivo_a_procesar

        texto = extraer_texto(archivo_a_procesar)
        if not texto:
            log.warning("Sin texto extraído de %s, se omite.", archivo_a_procesar.name)
            if docx_temporal and docx_temporal.exists():
                docx_temporal.unlink()
            continue

        datos_estructurados = estructurar_ley(texto)
        log.info(
            "  -> %d artículos extraídos de %s",
            len(datos_estructurados), archivo.name
        )

        nombre_salida       = archivo.stem + '_estructurado.json'
        ruta_archivo_salida = ruta_salida / nombre_salida

        with open(ruta_archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(datos_estructurados, f, ensure_ascii=False, indent=4)

        log.info("Guardado en: %s", ruta_archivo_salida)

        if docx_temporal and docx_temporal.exists():
            docx_temporal.unlink()
            log.info("Temporal eliminado: %s", docx_temporal.name)


# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    procesar_directorio("../knowledge", "../knowledge_structured")
    log.info("Procesamiento y normalización finalizados.")