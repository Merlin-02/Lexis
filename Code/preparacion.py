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

# FIX 3: Patrón de fracciones restringido a números romanos reales
# Evita que palabras como "DIM", "MIX", "CIVIL" activen la regex
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

# FIX 5: Patrón DOF ampliado — acepta sin espacio entre "DOF" y la fecha
# y captura también variantes con coma o sin separador
PATRON_DOF = re.compile(
    r'(?m)^\s*(?:Párrafo|Artículo|Fracción|Inciso)?\s*'
    r'(?:reformado|adicionado|derogado)\s+DOF[\s\t\d\-\,\.]*',
    flags=re.IGNORECASE
)

# NUEVO: Patrón de referencias a artículos dentro del texto
# Captura: "artículo 10", "artículos 3, 5 y 8", "Art. 20 Bis", "Art. 3o."
PATRON_REFERENCIA = re.compile(
    r'\b(?:art[íi]culo|art\.)\s*(\d+\s*(?:[oOaA°]\.?)?'
    r'(?:\s*(?:BIS|TER|QU[ÁA]TER|QUINQUIES|Bis|Ter|Qu[áa]ter|Quinquies))?)',
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
    FIX 1: Manejo de excepciones — un archivo corrupto no detiene el proceso.
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
    """
    Extrae fracciones en numeración romana.
    FIX 3: Usa PATRON_FRACCION con regex romana estricta para evitar falsos positivos.
    """
    resultado = []
    for match in PATRON_FRACCION.findall(texto_articulo):
        # PATRON_FRACCION puede capturar una fracción vacía si el grupo romano
        # no hace match — filtramos explícitamente
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
# NUEVO: EXTRACCIÓN DE REFERENCIAS
# ==========================================

def extraer_referencias_articulos(texto: str) -> list[str]:
    """
    Extrae y normaliza todas las referencias a otros artículos encontradas
    dentro del texto de un artículo dado.

    Ejemplos capturados:
      "artículo 10"        → "Artículo 10"
      "artículos 3 y 5"   → ["Artículo 3", "Artículo 5"]  (no aplica aquí,
                              cada número se captura por separado vía la regex)
      "Art. 20 Bis"        → "Artículo 20 Bis"
      "artículo 3o."       → "Artículo 3o."

    Devuelve una lista ordenada de strings únicos, sin el artículo actual
    (la eliminación del auto-referenciado se hace en el llamador).
    """
    matches = PATRON_REFERENCIA.findall(texto)
    referencias = set()
    for m in matches:
        # Normalizar capitalización: "Artículo <número>"
        ref = "Artículo " + re.sub(r'\s+', ' ', m).strip()
        referencias.add(ref)
    return sorted(referencias)

# ==========================================
# 3. ESTRUCTURACIÓN PRINCIPAL
# ==========================================

def estructurar_ley(texto_crudo: str) -> list[dict]:
    """
    Desglosa el texto de la ley en artículos con sus fracciones,
    incisos, notas DOF y referencias a otros artículos.

    FIX 2: Guarda sin procesar si el texto está vacío en lugar de lanzar error.
    """
    # FIX 2: Salida temprana si no hay texto
    if not texto_crudo or not texto_crudo.strip():
        log.warning("Se recibió texto vacío en estructurar_ley.")
        return []

    estructura = []
    articulos = PATRON_ARTICULO.findall(texto_crudo)

    for match in articulos:
        titulo_articulo = normalizar_texto(match[0])
        texto_articulo = match[1].strip()

        texto_limpio, notas_historicas = limpiar_texto_y_extraer_dof(texto_articulo)

        fracciones = extraer_fracciones(texto_limpio)
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

        # NUEVO: construir el texto completo del artículo para buscar referencias
        texto_completo_articulo = " ".join([
            texto_general_limpio,
            " ".join(f["texto_general"] for f in fracciones),
            " ".join(
                " ".join(inc["texto_general"] for inc in f["incisos"])
                for f in fracciones
            ),
            " ".join(inc["texto_general"] for inc in incisos_directos),
        ])

        referencias = extraer_referencias_articulos(texto_completo_articulo)

        # Eliminar auto-referencia (el artículo no se menciona a sí mismo)
        numero_propio = re.search(r'\d+', titulo_articulo)
        if numero_propio:
            patron_propio = re.compile(
                r'^Artículo\s+' + re.escape(numero_propio.group()) + r'\b',
                flags=re.IGNORECASE
            )
            referencias = [r for r in referencias if not patron_propio.match(r)]

        estructura.append({
            "articulo": titulo_articulo,
            "texto_general": normalizar_texto(texto_general_limpio),
            "historial_dof": notas_historicas,
            "fracciones": fracciones,
            "incisos_directos": incisos_directos,
            "referencias_articulos": referencias,   # ← NUEVO campo
        })

    return estructura

# ==========================================
# 4. PROCESAMIENTO POR LOTES
# ==========================================

def procesar_directorio(carpeta_entrada: str, carpeta_salida: str) -> None:
    """
    Itera sobre PDF/DOCX/DOC, estructura cada ley y guarda el resultado en JSON.
    FIX 4: Los archivos .docx temporales generados desde .doc se eliminan al terminar.
    """
    ruta_entrada = Path(carpeta_entrada)
    ruta_salida = Path(carpeta_salida)
    ruta_salida.mkdir(parents=True, exist_ok=True)

    archivos = (
        list(ruta_entrada.glob('*.pdf')) +
        list(ruta_entrada.glob('*.docx')) +
        list(ruta_entrada.glob('*.doc'))
    )
    log.info("Se encontraron %d archivos en %s", len(archivos), carpeta_entrada)

    for archivo in archivos:
        log.info("Procesando: %s", archivo.name)

        archivo_a_procesar = archivo
        docx_temporal = None   # FIX 4: rastrear archivo temporal

        if archivo.suffix.lower() == '.doc':
            archivo_a_procesar = convertir_doc_a_docx(archivo)
            if not archivo_a_procesar:
                continue
            docx_temporal = archivo_a_procesar   # FIX 4

        texto = extraer_texto(archivo_a_procesar)
        if not texto:
            log.warning("Sin texto extraído de %s, se omite.", archivo_a_procesar.name)
            # FIX 4: limpiar aunque no haya texto
            if docx_temporal and docx_temporal.exists():
                docx_temporal.unlink()
            continue

        datos_estructurados = estructurar_ley(texto)

        nombre_salida = archivo.stem + '_estructurado.json'
        ruta_archivo_salida = ruta_salida / nombre_salida

        with open(ruta_archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(datos_estructurados, f, ensure_ascii=False, indent=4)

        log.info("Guardado en: %s", ruta_archivo_salida)

        # FIX 4: Eliminar el .docx temporal generado desde el .doc original
        if docx_temporal and docx_temporal.exists():
            docx_temporal.unlink()
            log.info("Temporal eliminado: %s", docx_temporal.name)

# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    procesar_directorio("../knowledge", "../knowledge_structured")
    log.info("Procesamiento y normalización finalizados.")