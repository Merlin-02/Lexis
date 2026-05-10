"""
Índice temático manual para todas las normativas del sistema LexIS.
Este índice proporciona un fallback cuando la búsqueda híbrida no encuentra resultados relevantes.
"""

# ============================================================
# LEY FEDERAL DEL TRABAJO (LFT)
# ============================================================
INDICE_LFT = {
    "horas_extras": {
        "sinonimos": ["hora extra", "horas extra", "tiempo extra", "sobretiempo", "jornada extendida"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 65.-", "tema": "Límite de horas extras"},
            {"articulo": "Artículo 66.-", "tema": "Circunstancias extraordinarias"},
            {"articulo": "Artículo 67.-", "tema": "Pago de horas extras"},
            {"articulo": "Artículo 68.-", "tema": "Prohibición de horas extras"},
        ],
    },
    
    "despido": {
        "sinonimos": ["despedir", "despedido", "despido injustificado", "despido nulo", "despido verbal"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 47.-", "tema": "Causas de rescisión sin responsabilidad del patrón"},
            {"articulo": "Artículo 48.-", "tema": "Reinstauración e indemnización por despido injustificado"},
            {"articulo": "Artículo 49.-", "tema": "Indemnización por despido"},
            {"articulo": "Artículo 436.-", "tema": "Suspensión por despido"},
        ],
    },
    
    "renuncia": {
        "sinonimos": ["renunciar", "renunció", "renuncia voluntaria", "renuncia forzada", "renuncia en blanco"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 33.-", "tema": "Nulidad de renuncia de salarios"},
            {"articulo": "Artículo 1537.-", "tema": "Renuncia de derechos"},
        ],
    },
    
    "indemnizacion": {
        "sinonimos": ["indemnización", "compensación", "liquidación", "prima de antigüedad"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 48.-", "tema": "Indemnización por despido"},
            {"articulo": "Artículo 49.-", "tema": "Monto de indemnización"},
            {"articulo": "Artículo 162.-", "tema": "Prima de antigüedad"},
            {"articulo": "Artículo 163.-", "tema": "Monto de prima de antigüedad"},
        ],
    },
    
    "salario": {
        "sinonimos": ["sueldo", "pago", "remuneración", "nomina"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 82.-", "tema": "Definición de salario"},
            {"articulo": "Artículo 84.-", "tema": "Integral del salario"},
            {"articulo": "Artículo 97.-", "tema": "Pago del salario"},
            {"articulo": "Artículo 98.-", "tema": "Lugar de pago"},
            {"articulo": "Artículo 99.-", "tema": "Tiempo de pago"},
        ],
    },
    
    "jornada": {
        "sinonimos": ["jornada laboral", "horario", "horas de trabajo"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 58.-", "tema": "Definición de jornada"},
            {"articulo": "Artículo 59.-", "tema": "Duración máxima"},
            {"articulo": "Artículo 60.-", "tema": "Jornada nocturna"},
            {"articulo": "Artículo 61.-", "tema": "Jornada diurna y mixta"},
        ],
    },
    
    "vacaciones": {
        "sinonimos": ["vacación", "descanso anual", "período vacacional"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 70.-", "tema": "Vacaciones"},
            {"articulo": "Artículo 71.-", "tema": "Prima vacacional"},
        ],
    },
    
    "aguinaldo": {
        "sinonimos": ["aguinaldo anual", "prestación de fin de año"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 87.-", "tema": "Aguinaldo"},
            {"articulo": "Artículo 88.-", "tema": "Monto mínimo"},
        ],
    },
    
    "contrato": {
        "sinonimos": ["contrato de trabajo", "contrato individual"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 20.-", "tema": "Relación de trabajo"},
            {"articulo": "Artículo 21.-", "tema": "Contrato individual"},
            {"articulo": "Artículo 23.-", "tema": "Período de prueba"},
            {"articulo": "Artículo 25.-", "tema": "Condiciones de trabajo"},
        ],
    },
    
    "menores": {
        "sinonimos": ["menores de edad", "trabajo infantil", "menores"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 173.-", "tema": "Trabajo de menores"},
            {"articulo": "Artículo 174.-", "tema": "Prohibición de trabajo a menores"},
            {"articulo": "Artículo 175.-", "tema": "Jornada de menores"},
            {"articulo": "Artículo 176.-", "tema": "Trabajo peligroso"},
            {"articulo": "Artículo 177.-", "tema": "Prohibición de horas extras"},
            {"articulo": "Artículo 178.-", "tema": "Prohibición de trabajo nocturno"},
        ],
    },
    
    "maternidad": {
        "sinonimos": ["embarazo", "maternidad", "trabajadora embarazada", "lactancia"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 170.-", "tema": "Protección de la maternidad"},
            {"articulo": "Artículo 171.-", "tema": "Prohibición de trabajo a mujeres"},
        ],
    },
    
    "seguridad_social": {
        "sinonimos": ["imss", "seguridad social", "afiliación"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 127.-", "tema": "Obligaciones del patrón en seguridad social"},
            {"articulo": "Artículo 128.-", "tema": "Registro de trabajadores"},
        ],
    },
    
    "inspeccion": {
        "sinonimos": ["inspección del trabajo", "autoridad laboral"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo": "Artículo 527.-", "tema": "Inspección del trabajo"},
        ],
    },
}

# ============================================================
# CÓDIGO PENAL DE TLAXCALA
# ============================================================
INDICE_CP = {
    "robo": {
        "sinonimos": ["robar", "robo", "hurto", "asaltar"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 198.-", "tema": "Robo"},
            {"articulo": "Artículo 199.-", "tema": "Robo con violencia"},
            {"articulo": "Artículo 200.-", "tema": "Robo a casa habitación"},
        ],
    },
    
    "lesiones": {
        "sinonimos": ["lesionar", "lesiones", "herir", "agredir"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 130.-", "tema": "Lesiones"},
            {"articulo": "Artículo 131.-", "tema": "Lesiones graves"},
            {"articulo": "Artículo 132.-", "tema": "Lesiones dolosas"},
        ],
    },
    
    "feminicidio": {
        "sinonimos": ["feminicidio", "violencia de género", "femicidio"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 165 Bis.-", "tema": "Feminicidio"},
        ],
    },
    
    "violencia_familiar": {
        "sinonimos": ["violencia familiar", "maltrato familiar", "abuso familiar"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 187.-", "tema": "Violencia familiar"},
        ],
    },
    
    "secuestro": {
        "sinonimos": ["secuestrar", "secuestro", "privación ilegal"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 207.-", "tema": "Secuestro"},
            {"articulo": "Artículo 208.-", "tema": "Secuestro express"},
        ],
    },
    
    "extorsion": {
        "sinonimos": ["extorsión", "extorsionar", "amenazar para dinero"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 214.-", "tema": "Extorsión"},
        ],
    },
    
    "fraude": {
        "sinonimos": ["fraude", "engañar", "estafa", "engaño"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 216.-", "tema": "Fraude"},
        ],
    },
    
    "denuncia": {
        "sinonimos": ["denunciar", "denuncia", "querella"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo atán.", "tema": "Denuncia"},
        ],
    },
    
    "delito": {
        "sinonimos": ["delito", "crimen", "ilícito penal"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 1o.-", "tema": "Delito y responsabilidad"},
            {"articulo": "Artículo 2o.-", "tema": "Sujetos del delito"},
        ],
    },
    
    "penal": {
        "sinonimos": ["sanción penal", "pena", "cárcel", "prisión"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 24.-", "tema": "Penas"},
            {"articulo": "Artículo 25.-", "tema": "Prisión"},
        ],
    },
}

# ============================================================
# CÓDIGO CIVIL DE TLAXCALA
# ============================================================
INDICE_CC = {
    "persona": {
        "sinonimos": ["persona", "personas", "capacidad"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 1o.-", "tema": "Persona y capacidad"},
            {"articulo": "ARTICULO 2o.-", "tema": "Mayoría de edad"},
        ],
    },
    
    "matrimonio": {
        "sinonimos": ["matrimonio", "casarse", "boda", "unión legal"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 90.-", "tema": "Matrimonio"},
            {"articulo": "ARTICULO 91.-", "tema": "Requisitos del matrimonio"},
            {"articulo": "ARTICULO 140.-", "tema": "Divorcio"},
        ],
    },
    
    "divorcio": {
        "sinonimos": ["divorciar", "divorcio", "separación legal"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 140.-", "tema": "Divorcio"},
            {"articulo": "ARTICULO 141.-", "tema": "Causas de divorcio"},
        ],
    },
    
    "paternidad": {
        "sinonimos": ["paternidad", "filiación", "hijo", "madre"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 282.-", "tema": "Paternidad y filiación"},
            {"articulo": "ARTICULO 283.-", "tema": "Reconocimiento de hijos"},
        ],
    },
    
    "adopcion": {
        "sinonimos": ["adopción", "adoptar", "hijo adoptivo"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 390.-", "tema": "Adopción"},
        ],
    },
    
    "tutela": {
        "sinonimos": ["tutela", "tutor", "menor", "incapaz"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 410.-", "tema": "Tutela"},
        ],
    },
    
    "propiedad": {
        "sinonimos": ["propiedad", "dueño", "posesión", "bienes"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 780.-", "tema": "Propiedad"},
            {"articulo": "ARTICULO 781.-", "tema": "Bienes muebles e inmuebles"},
        ],
    },
    
    "contrato": {
        "sinonimos": ["contrato", "acuerdo", "obligación"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 1630.-", "tema": "Contratos"},
            {"articulo": "ARTICULO 1631.-", "tema": "Obligaciones contractuales"},
        ],
    },
    
    "arrendamiento": {
        "sinonimos": ["arrendar", "arrendamiento", "renta", "inquilino"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 2200.-", "tema": "Arrendamiento"},
        ],
    },
    
    "testamento": {
        "sinonimos": ["testamento", "herencia", "legado", "heredar"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 1300.-", "tema": "Testamento"},
            {"articulo": "ARTICULO 1301.-", "tema": "Tipos de testamento"},
        ],
    },
    
    "sucesion": {
        "sinonimos": ["sucesión", "heredar", "herencia", "legítimo"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 1400.-", "tema": "Sucesión"},
        ],
    },
    
    "obligaciones": {
        "sinonimos": ["obligación", "deuda", "pagar"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo": "ARTICULO 1600.-", "tema": "Obligaciones"},
        ],
    },
}

# ============================================================
# PROCEDIMIENTO CIVIL DE TLAXCALA
# ============================================================
INDICE_PC = {
    "demanda": {
        "sinonimos": ["demanda", "demandar", "juicio civil"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 1.-", "tema": "Demanda"},
        ],
    },
    
    "citatorio": {
        "sinonimos": ["citatorio", "citar", "notificación"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 68.-", "tema": "Citatorios"},
        ],
    },
    
    "prueba": {
        "sinonimos": ["prueba", "pruebas", "evidencia"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 180.-", "tema": "Medios de prueba"},
        ],
    },
    
    "sentencia": {
        "sinonimos": ["sentencia", "juicio", "fallo"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 280.-", "tema": "Sentencia"},
        ],
    },
    
    "recurso": {
        "sinonimos": ["recurso", "apelación", "revisar"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 300.-", "tema": "Recursos"},
        ],
    },
    
    "embargo": {
        "sinonimos": ["embargo", "embargar", "bienes"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 400.-", "tema": "Embargo"},
        ],
    },
    
    "subasta": {
        "sinonimos": ["subasta", "subastar", "adjudicación"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 500.-", "tema": "Subasta"},
        ],
    },
    
    "ejecutoria": {
        "sinonimos": ["ejecutoria", "sentencia ejecutoriada"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 280.-", "tema": "Ejecutoria"},
        ],
    },
}

# ============================================================
# PROCEDIMIENTO PENAL DE TLAXCALA
# ============================================================
INDICE_PP = {
    "detencion": {
        "sinonimos": ["detención", "detener", "arrestar", "prisión"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 140.-", "tema": "Detención"},
        ],
    },
    
    "imputado": {
        "sinonimos": ["imputado", "acusado", "procesado"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 100.-", "tema": "Imputado"},
        ],
    },
    
    "victima": {
        "sinonimos": ["víctima", "victima", "ofendido"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 105.-", "tema": "Víctima"},
        ],
    },
    
    "audiencia": {
        "sinonimos": ["audiencia", "juicio oral", "juicio"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 200.-", "tema": "Audiencia"},
        ],
    },
    
    "prision": {
        "sinonimos": ["prisión", "cárcel", "privación de libertad"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 150.-", "tema": "Prisión preventiva"},
        ],
    },
    
    "defensa": {
        "sinonimos": ["defensa", "defensor", "abogado"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 110.-", "tema": "Derecho de defensa"},
        ],
    },
    
    "orden": {
        "sinonimos": ["orden de aprehensión", "judicial", "juez"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 130.-", "tema": "Orden de aprehensión"},
        ],
    },
    
    "carga_prueba": {
        "sinonimos": ["carga de la prueba", "prueba", "responsabilidad"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo": "Artículo 180.-", "tema": "Carga de la prueba"},
        ],
    },
}

# ============================================================
# CONSTITUCIÓN POLÍTICA DE TLAXCALA
# ============================================================
INDICE_CONST = {
    "derechos": {
        "sinonimos": ["derechos", "garantías", "libertad"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo": "Artículo 1o.", "tema": "Derechos humanos"},
        ],
    },
    
    "garantias": {
        "sinonimos": ["garantías", "amparo", "protección"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo": "Artículo 14.-", "tema": "Garantías individuales"},
            {"articulo": "Artículo 16.-", "tema": "Garantías de audiencia"},
        ],
    },
    
    "trabajo": {
        "sinonimos": ["derecho al trabajo", "empleo"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo": "Artículo 5o.", "tema": "Libertad de trabajo"},
        ],
    },
    
    "educacion": {
        "sinonimos": ["educación", "escuela", "enseñanza"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo": "Artículo 3o.", "tema": "Educación"},
        ],
    },
    
    "propiedad": {
        "sinonimos": ["propiedad privada", "bienes"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo": "Artículo 27.-", "tema": "Propiedad privada"},
        ],
    },
    
    "estado": {
        "sinonimos": ["estado", "gobierno", "poderes"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo": "Artículo 40.-", "tema": "Forma de gobierno"},
            {"articulo": "Artículo 50.-", "tema": "Poderes del estado"},
        ],
    },
}

# ============================================================
# ÍNDICE UNIFICADO
# ============================================================
INDICE_TEMATICO = {}

for ind in [INDICE_LFT, INDICE_CP, INDICE_CC, INDICE_PC, INDICE_PP, INDICE_CONST]:
    for key, value in ind.items():
        value["concepto"] = key
        INDICE_TEMATICO[key] = value


def buscar_por_concepto(query: str, documento_filtro: str = None) -> list[dict]:
    """
    Busca artículos relacionados con los conceptos de la query.
    
    Args:
        query: Consulta del usuario
        documento_filtro: Filtrar por documento específico (opcional)
        
    Returns:
        Lista de artículos encontrados con su temática
    """
    query_lower = query.lower()
    resultados = []
    
    for concepto, datos in INDICE_TEMATICO.items():
        # Verificar si el documento coincide (si hay filtro)
        if documento_filtro:
            doc_norm = datos.get("documento", "").lower()
            if documento_filtro.lower() not in doc_norm and doc_norm not in documento_filtro.lower():
                continue
        
        # Verificar si algún sinónimo está en la query
        encontrado = False
        sinonimos = datos.get("sinonimos", [])
        
        for sinonimo in sinonimos:
            if sinonimo.lower() in query_lower:
                encontrado = True
                break
        
        # También buscar el nombre del concepto
        if not encontrado and concepto.replace("_", " ") in query_lower:
            encontrado = True
        
        if encontrado:
            for art in datos["articulos"]:
                resultados.append({
                    "concepto": concepto,
                    "documento": datos.get("documento", ""),
                    "articulo": art["articulo"],
                    "tema": art["tema"],
                })
    
    return resultados


def detectar_documento(query: str) -> str:
    """
    Detecta qué normativa corresponde a la query basándose en palabras clave.
    """
    query_lower = query.lower()
    
    # Palabras clave por normativa (ordenadas por prioridad - las más específicas primero)
    mapeo = [
        ("procedimiento penal", ["detención", "detenido", "detener", "imputado", "audiencia", "prisión", "defensa", "orden de aprehensión", "juicio oral", "fiscal", "agente"]),
        ("código penal", ["robo", "robar", "robandome", "lesión", "lesionar", "violencia", "feminicidio", "secuestro", "extorsión", "fraude", "delito", "crimen", "cárcel", "pena", "víctima", "asesinato", "violación"]),
        ("procedimiento civil", ["demanda", "juicio civil", "sentencia", "embargo", "subasta", "ejecutoria"]),
        ("código civil", ["matrimonio", "divorciarme", "herencia", "heredar", "propiedad", "testamento", "adopción", "tutela", "persona", "civil"]),
        ("ley trabajo", ["trabajo", "empleador", "empleado", "patrón", "patron", "salario", "jornada", "vacaciones", "aguinaldo", "despido", "despedirme", "contrato", "horas extras", "indemnización", "renuncia"]),
        ("constitución", ["derecho", "garantía", "libertad", "constitucional"]),
    ]
    
    for doc, palabras in mapeo:
        coincidencias = sum(1 for p in palabras if p in query_lower)
        if coincidencias >= 1:
            return doc
    
    return None


if __name__ == "__main__":
    print("=== Prueba del Índice Temático ===\n")
    
    pruebas = [
        "me deben horas extras y quiero saber mis derechos",
        "me robaron en la calle qué puedo hacer",
        "quiero divorciarme de mi esposa",
        "mi hijo fue detenido sin motivo",
        "me deben dinero por un contrato",
    ]
    
    for q in pruebas:
        print(f"Consulta: {q}")
        doc = detectar_documento(q)
        print(f"Documento detectado: {doc}")
        resultados = buscar_por_concepto(q, doc)
        print(f"Resultados: {len(resultados)}")
        for r in resultados[:3]:
            print(f"  [{r['documento']}] {r['articulo']}: {r['tema']}")
        print()
