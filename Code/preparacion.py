import os
import re
import json
import subprocess
from pathlib import Path
import docx
import pdfplumber

# ==========================================
# 1. LECTURA Y CONVERSIÓN DE ARCHIVOS
# ==========================================

def convertir_doc_a_docx(ruta_archivo):
    """Convierte .doc a .docx usando LibreOffice en modo invisible (headless)."""
    print(f"Convirtiendo {ruta_archivo.name} a .docx...")
    comando = [
        'libreoffice', '--headless', '--convert-to', 'docx', 
        str(ruta_archivo), '--outdir', str(ruta_archivo.parent)
    ]
    try:
        subprocess.run(comando, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        nueva_ruta = ruta_archivo.with_suffix('.docx')
        return nueva_ruta
    except subprocess.CalledProcessError:
        print(f"Error convirtiendo {ruta_archivo.name}")
        return None

def extraer_texto(ruta_archivo):
    """Extrae texto dependiendo de si es PDF o DOCX."""
    texto = ""
    extension = ruta_archivo.suffix.lower()
    
    if extension == '.pdf':
        with pdfplumber.open(ruta_archivo) as pdf:
            for pagina in pdf.pages:
                t = pagina.extract_text()
                if t: texto += t + '\n'
                
    elif extension == '.docx':
        doc = docx.Document(ruta_archivo)
        texto = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
        
    return texto

# ==========================================
# 2. LIMPIEZA Y EXTRACCIÓN (REGEX MEJORADO)
# ==========================================

def limpiar_texto_y_extraer_dof(texto):
    """Extrae las notas del DOF y limpia el texto principal."""
    # Reemplazamos \s al final por [ \t] para no consumir saltos de línea (\n)
    patron_dof = r'(?m)^\s*(?:Párrafo|Artículo|Fracción|Inciso)?\s*(?:reformado|adicionado|derogado)\s+DOF[ \t\d\-\,\.]+'
    notas_dof = [nota.strip() for nota in re.findall(patron_dof, texto, flags=re.IGNORECASE)]
    
    # Borramos la nota del texto para que no interfiera después
    texto_limpio = re.sub(patron_dof, '', texto, flags=re.IGNORECASE).strip()
    return texto_limpio, notas_dof

def extraer_incisos(texto):
    """Extrae incisos tipo a), b), c) tolerando tabuladores o falta de espacios."""
    patron_inciso = r'(?m)^\s*([a-z])\)(.*?)(?=(?:^\s*[a-z]\))|\Z)'
    incisos = re.findall(patron_inciso, texto, flags=re.DOTALL)
    
    return [{"inciso": match[0], "texto_general": match[1].strip()} for match in incisos]

def extraer_fracciones(texto_articulo):
    """Extrae fracciones, limpia su texto principal y extrae sus incisos."""
    patron_fraccion = r'(?m)^\s*([IVXLCDM]+)[\.\-]\s+(.*?)(?=(?:^\s*[IVXLCDM]+[\.\-])|\Z)'
    fracciones = re.findall(patron_fraccion, texto_articulo, flags=re.DOTALL)
    
    resultado = []
    for match in fracciones:
        texto_fraccion = match[1].strip()
        incisos = extraer_incisos(texto_fraccion)
        
        # Recortamos el texto de la fracción si contiene incisos para evitar duplicados
        texto_limpio_fraccion = texto_fraccion
        if incisos:
            texto_limpio_fraccion = re.split(r'(?m)^\s*[a-z]\)', texto_fraccion, maxsplit=1)[0].strip()
            
        resultado.append({
            "fraccion": match[0],
            "texto_general": texto_limpio_fraccion,
            "incisos": incisos
        })
    return resultado

def estructurar_ley(texto_crudo):
    """Función principal que desglosa todo el texto de la ley en un diccionario."""
    estructura = []
    
    # Expresión estricta para sufijos de la ley mexicana
    patron_articulo = r'(?m)^\s*((?:ART[ÍI]CULO|Art[íi]culo)\s+\d+(?:[oOaA]|\.)?(?:[\s\.\-]*(?:BIS|TER|QU[ÁA]TER|QUINQUIES|Bis|Ter|Qu[áa]ter|Quinquies))?[\.\-]*)\s*(.*?)(?=(?:^\s*(?:ART[ÍI]CULO|Art[íi]culo)\s+\d+)|\Z)'
    articulos = re.findall(patron_articulo, texto_crudo, flags=re.DOTALL)
    
    for match in articulos:
        titulo_articulo = match[0].strip()
        texto_articulo = match[1].strip()
        
        texto_limpio, notas_historicas = limpiar_texto_y_extraer_dof(texto_articulo)
        
        fracciones = extraer_fracciones(texto_limpio)
        incisos_directos = []
        texto_general_limpio = texto_limpio
        
        # Recortamos el texto general del artículo si contiene fracciones o incisos directos
        if fracciones:
            texto_general_limpio = re.split(r'(?m)^\s*[IVXLCDM]+[\.\-]\s+', texto_limpio, maxsplit=1)[0].strip()
        else:
            incisos_directos = extraer_incisos(texto_limpio)
            if incisos_directos:
                texto_general_limpio = re.split(r'(?m)^\s*[a-z]\)', texto_limpio, maxsplit=1)[0].strip()
                
        estructura.append({
            "articulo": titulo_articulo,
            "texto_general": texto_general_limpio, 
            "historial_dof": notas_historicas,
            "fracciones": fracciones,
            "incisos_directos": incisos_directos
        })
        
    return estructura

# ==========================================
# 3. PROCESAMIENTO POR LOTES
# ==========================================

def procesar_directorio(carpeta_entrada, carpeta_salida):
    """Itera sobre los documentos, los procesa y los guarda como JSON."""
    ruta_entrada = Path(carpeta_entrada)
    ruta_salida = Path(carpeta_salida)
    ruta_salida.mkdir(parents=True, exist_ok=True)
    
    archivos = list(ruta_entrada.glob('*.pdf')) + list(ruta_entrada.glob('*.docx')) + list(ruta_entrada.glob('*.doc'))
    print(f"Se encontraron {len(archivos)} archivos en {carpeta_entrada}")
    
    for archivo in archivos:
        print(f"\nProcesando: {archivo.name}")
        
        archivo_a_procesar = archivo
        if archivo.suffix.lower() == '.doc':
            archivo_a_procesar = convertir_doc_a_docx(archivo)
            if not archivo_a_procesar: continue
            
        texto = extraer_texto(archivo_a_procesar)
        if not texto:
            print(f"No se pudo extraer texto de {archivo_a_procesar.name}")
            continue
            
        datos_estructurados = estructurar_ley(texto)
        
        nombre_salida = archivo.stem + '_estructurado.json'
        ruta_archivo_salida = ruta_salida / nombre_salida
        
        with open(ruta_archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(datos_estructurados, f, ensure_ascii=False, indent=4)
            
        print(f"Guardado con exito en: {ruta_archivo_salida}")

# ==========================================
# EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    carpeta_conocimiento = "../knowledge"
    carpeta_resultados = "../knowledge_structured"
    
    procesar_directorio(carpeta_conocimiento, carpeta_resultados)
    print("\nProcesamiento finalizado.")