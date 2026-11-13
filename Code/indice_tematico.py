"""
Índice temático auditado para todas las normativas del sistema LEXIS.
Cada entrada incluye su identificador canónico en el grafo (`articulo_id`)
y corresponde exactamente a artículos reales y vigentes del corpus estructurado.
"""

# ============================================================
# LEY FEDERAL DEL TRABAJO (LFT)
# ============================================================
INDICE_LFT = {
    "horas_extras": {
        "sinonimos": ["hora extra", "horas extra", "horas extras", "tiempo extra", "sobretiempo", "jornada extendida"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:65", "articulo": "Artículo 65.-", "tema": "Prolongación de jornada por riesgo o siniestro"},
            {"articulo_id": "articulo:lft:66", "articulo": "Artículo 66.-", "tema": "Límite de horas extraordinarias"},
            {"articulo_id": "articulo:lft:67", "articulo": "Artículo 67.-", "tema": "Pago de horas extraordinarias al doble"},
            {"articulo_id": "articulo:lft:68", "articulo": "Artículo 68.-", "tema": "Pago de tiempo extraordinario excedente al triple"},
        ],
    },
    "despido": {
        "sinonimos": ["despedir", "despedido", "despido injustificado", "despido nulo", "despido verbal"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:47", "articulo": "Artículo 47.-", "tema": "Causas de rescisión sin responsabilidad para el patrón"},
            {"articulo_id": "articulo:lft:48", "articulo": "Artículo 48.-", "tema": "Reinstalación o indemnización constitucional por despido injustificado"},
            {"articulo_id": "articulo:lft:49", "articulo": "Artículo 49.-", "tema": "Casos de exención de reinstalación mediante indemnización"},
            {"articulo_id": "articulo:lft:50", "articulo": "Artículo 50.-", "tema": "Importe de las indemnizaciones laborales"},
        ],
    },
    "renuncia": {
        "sinonimos": ["renunciar", "renunció", "renuncia voluntaria", "renuncia forzada", "renuncia en blanco"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:33", "articulo": "Artículo 33.-", "tema": "Irrenunciabilidad de derechos y salarios devengados"},
            {"articulo_id": "articulo:lft:48-BIS", "articulo": "Artículo 48 Bis.-", "tema": "Actuaciones notoriamente improcedentes como hacer firmar renuncia en blanco"},
        ],
    },
    "indemnizacion": {
        "sinonimos": ["indemnización", "compensación", "liquidación", "prima de antigüedad", "finiquito"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:48", "articulo": "Artículo 48.-", "tema": "Indemnización por despido injustificado"},
            {"articulo_id": "articulo:lft:50", "articulo": "Artículo 50.-", "tema": "Cálculo de indemnizaciones"},
            {"articulo_id": "articulo:lft:162", "articulo": "Artículo 162.-", "tema": "Derecho y cálculo de la prima de antigüedad"},
        ],
    },
    "salario": {
        "sinonimos": ["sueldo", "pago", "remuneración", "nómina", "nomina"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:82", "articulo": "Artículo 82.-", "tema": "Definición de salario"},
            {"articulo_id": "articulo:lft:84", "articulo": "Artículo 84.-", "tema": "Integración del salario"},
            {"articulo_id": "articulo:lft:97", "articulo": "Artículo 97.-", "tema": "Protección del salario mínimo contra descuentos"},
            {"articulo_id": "articulo:lft:98", "articulo": "Artículo 98.-", "tema": "Libre disposición del salario"},
            {"articulo_id": "articulo:lft:99", "articulo": "Artículo 99.-", "tema": "Irrenunciabilidad del derecho a percibir salario"},
        ],
    },
    "jornada": {
        "sinonimos": ["jornada laboral", "horario", "horas de trabajo"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:58", "articulo": "Artículo 58.-", "tema": "Definición de jornada de trabajo"},
            {"articulo_id": "articulo:lft:59", "articulo": "Artículo 59.-", "tema": "Fijación y reparto de la jornada"},
            {"articulo_id": "articulo:lft:60", "articulo": "Artículo 60.-", "tema": "Jornada diurna, nocturna y mixta"},
            {"articulo_id": "articulo:lft:61", "articulo": "Artículo 61.-", "tema": "Duración máxima de la jornada"},
        ],
    },
    "vacaciones": {
        "sinonimos": ["vacación", "descanso anual", "período vacacional", "prima vacacional"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:76", "articulo": "Artículo 76.-", "tema": "Período anual de vacaciones pagadas (mínimo 12 días)"},
            {"articulo_id": "articulo:lft:80", "articulo": "Artículo 80.-", "tema": "Prima vacacional no menor del veinticinco por ciento"},
        ],
    },
    "aguinaldo": {
        "sinonimos": ["aguinaldo anual", "prestación de fin de año"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:87", "articulo": "Artículo 87.-", "tema": "Derecho a aguinaldo anual mínimo de quince días"},
            {"articulo_id": "articulo:lft:88", "articulo": "Artículo 88.-", "tema": "Plazos máximos para el pago del salario"},
        ],
    },
    "contrato": {
        "sinonimos": ["contrato de trabajo", "contrato individual", "relación laboral"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:20", "articulo": "Artículo 20.-", "tema": "Relación de trabajo y contrato individual"},
            {"articulo_id": "articulo:lft:21", "articulo": "Artículo 21.-", "tema": "Presunción de existencia del contrato y relación de trabajo"},
            {"articulo_id": "articulo:lft:25", "articulo": "Artículo 25.-", "tema": "Requisitos del escrito de condiciones de trabajo"},
        ],
    },
    "menores": {
        "sinonimos": ["menores de edad", "trabajo infantil", "trabajo de menores"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:173", "articulo": "Artículo 173.-", "tema": "Vigilancia y protección del trabajo de menores"},
            {"articulo_id": "articulo:lft:174", "articulo": "Artículo 174.-", "tema": "Certificado médico y requisitos para mayores de quince y menores de dieciocho años"},
            {"articulo_id": "articulo:lft:175", "articulo": "Artículo 175.-", "tema": "Prohibiciones de utilización del trabajo de menores"},
            {"articulo_id": "articulo:lft:177", "articulo": "Artículo 177.-", "tema": "Jornada máxima de menores de dieciséis años"},
            {"articulo_id": "articulo:lft:178", "articulo": "Artículo 178.-", "tema": "Prohibición de horas extraordinarias y trabajo nocturno para menores"},
        ],
    },
    "maternidad": {
        "sinonimos": ["embarazo", "maternidad", "trabajadora embarazada", "lactancia"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:170", "articulo": "Artículo 170.-", "tema": "Derechos de las madres trabajadoras en embarazo y lactancia"},
            {"articulo_id": "articulo:lft:171", "articulo": "Artículo 171.-", "tema": "Servicios de guardería infantil"},
        ],
    },
    "seguridad_social": {
        "sinonimos": ["imss", "seguridad social", "afiliación", "riesgo de trabajo"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:2", "articulo": "Artículo 2o.-", "tema": "Trabajo digno o decente con acceso a la seguridad social"},
            {"articulo_id": "articulo:lft:473", "articulo": "Artículo 473.-", "tema": "Definición de riesgos de trabajos"},
        ],
    },
    "inspeccion": {
        "sinonimos": ["inspección del trabajo", "autoridad laboral", "competencia federal"],
        "documento": "Ley Trabajo",
        "articulos": [
            {"articulo_id": "articulo:lft:527", "articulo": "Artículo 527.-", "tema": "Competencia de autoridades laborales"},
        ],
    },
}

# ============================================================
# CÓDIGO PENAL DE TLAXCALA
# ============================================================
INDICE_CP = {
    "robo": {
        "sinonimos": ["robar", "robo", "hurto", "asaltar", "asalto"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:321", "articulo": "Artículo 321.", "tema": "Tipo penal de robo y sanciones"},
            {"articulo_id": "articulo:cp_tlax:326", "articulo": "Artículo 326.", "tema": "Agravantes y robo con violencia"},
            {"articulo_id": "articulo:cp_tlax:327", "articulo": "Artículo 327.", "tema": "Robo calificado (casa habitación, vehículo)"},
        ],
    },
    "lesiones": {
        "sinonimos": ["lesionar", "lesiones", "herir", "agredir", "golpear"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:232", "articulo": "Artículo 232.", "tema": "Delito de lesiones y punibilidad según gravedad"},
            {"articulo_id": "articulo:cp_tlax:233", "articulo": "Artículo 233.", "tema": "Lesiones que dejan cicatriz o secuela"},
        ],
    },
    "feminicidio": {
        "sinonimos": ["feminicidio", "violencia de género", "femicidio"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:229", "articulo": "Artículo 229.", "tema": "Delito de feminicidio y razones de género"},
            {"articulo_id": "articulo:cp_tlax:229-BIS", "articulo": "Artículo 229 bis.", "tema": "Punibilidad agravada del feminicidio"},
        ],
    },
    "violencia_familiar": {
        "sinonimos": ["violencia familiar", "maltrato familiar", "abuso familiar", "deudor alimentario"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:371", "articulo": "Artículo 371.", "tema": "Incumplimiento de obligaciones alimentarias y violencia en el ámbito familiar"},
            {"articulo_id": "articulo:cp_tlax:45", "articulo": "Artículo 45.", "tema": "Reparación del daño integral"},
        ],
    },
    "secuestro": {
        "sinonimos": ["secuestrar", "secuestro", "privación ilegal", "privación de la libertad"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:258", "articulo": "Artículo 258.", "tema": "Privación ilegal de la libertad"},
            {"articulo_id": "articulo:cp_tlax:259", "articulo": "Artículo 259.", "tema": "Agravantes en la privación de la libertad"},
            {"articulo_id": "articulo:cp_tlax:260", "articulo": "Artículo 260.", "tema": "Privación de la libertad con fines de robo o extorsión"},
        ],
    },
    "extorsion": {
        "sinonimos": ["extorsión", "extorsionar", "amenazar para dinero"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:268", "articulo": "Artículo 268.", "tema": "Delito de extorsión"},
            {"articulo_id": "articulo:cp_tlax:269", "articulo": "Artículo 269.", "tema": "Extorsión agravada"},
        ],
    },
    "fraude": {
        "sinonimos": ["fraude", "engañar", "estafa", "engaño"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:338", "articulo": "Artículo 338.", "tema": "Delito de fraude genérico"},
            {"articulo_id": "articulo:cp_tlax:339", "articulo": "Artículo 339.", "tema": "Fraudes específicos"},
        ],
    },
    "denuncia": {
        "sinonimos": ["denunciar", "denuncia", "querella", "perdón del ofendido"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:105", "articulo": "Artículo 105.", "tema": "Causas de extinción de la pretensión punitiva"},
            {"articulo_id": "articulo:cp_tlax:111", "articulo": "Artículo 111.", "tema": "Requisitos en delitos perseguibles por querella y perdón de la víctima"},
        ],
    },
    "delito": {
        "sinonimos": ["delito", "crimen", "ilícito penal", "principio de legalidad"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:1", "articulo": "Artículo 1.", "tema": "Principio de legalidad penal"},
            {"articulo_id": "articulo:cp_tlax:2", "articulo": "Artículo 2.", "tema": "Principio de tipicidad y prohibición de retroactividad"},
        ],
    },
    "penal": {
        "sinonimos": ["sanción penal", "pena", "cárcel", "prisión"],
        "documento": "Código Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cp_tlax:34", "articulo": "Artículo 34.", "tema": "Catálogo de penas"},
            {"articulo_id": "articulo:cp_tlax:35", "articulo": "Artículo 35.", "tema": "Catálogo de medidas de seguridad"},
        ],
    },
}

# ============================================================
# CÓDIGO CIVIL DE TLAXCALA
# ============================================================
INDICE_CC = {
    "persona": {
        "sinonimos": ["persona", "personas", "capacidad", "capacidad jurídica"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:1", "articulo": "ARTICULO 1.-", "tema": "Ámbito de aplicación civil en el Estado de Tlaxcala"},
            {"articulo_id": "articulo:cc_tlax:31", "articulo": "ARTICULO 31.-", "tema": "Capacidad jurídica de las personas físicas"},
        ],
    },
    "matrimonio": {
        "sinonimos": ["matrimonio", "casarse", "boda", "unión legal", "sociedad conyugal"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:42", "articulo": "ARTICULO 42.", "tema": "Definición y naturaleza del matrimonio"},
            {"articulo_id": "articulo:cc_tlax:43", "articulo": "ARTICULO 43.-", "tema": "Requisitos de edad y consentimiento para contraer matrimonio"},
        ],
    },
    "divorcio": {
        "sinonimos": ["divorciar", "divorcio", "divorciarme", "separación legal", "divorcio incausado"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:106", "articulo": "ARTICULO 106.-", "tema": "Disolución del vínculo matrimonial por divorcio"},
            {"articulo_id": "articulo:cc_tlax:123", "articulo": "ARTICULO 123.-", "tema": "Divorcio incausado y convenio regulador"},
        ],
    },
    "paternidad": {
        "sinonimos": ["paternidad", "filiación", "hijo", "madre", "reconocimiento de hijos"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:170", "articulo": "ARTICULO 170.-", "tema": "Reglas generales de la filiación"},
            {"articulo_id": "articulo:cc_tlax:282", "articulo": "ARTICULO 282.-", "tema": "Administración de bienes bajo patria potestad"},
        ],
    },
    "adopcion": {
        "sinonimos": ["adopción", "adoptar", "hijo adoptivo", "parentesco civil"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:140", "articulo": "ARTICULO 140.-", "tema": "Parentesco civil nacido de la adopción"},
            {"articulo_id": "articulo:cc_tlax:240-C", "articulo": "ARTICULO 240 C.-", "tema": "Disposiciones sobre adopción en el Estado de Tlaxcala"},
        ],
    },
    "tutela": {
        "sinonimos": ["tutela", "tutor", "menor", "incapaz"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:291", "articulo": "ARTICULO 291.-", "tema": "Objeto de la tutela y guarda de la persona y bienes"},
        ],
    },
    "propiedad": {
        "sinonimos": ["propiedad", "dueño", "posesión", "bienes", "derecho real"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:750", "articulo": "ARTICULO 750.-", "tema": "Definición y función social del derecho de propiedad"},
        ],
    },
    "contrato": {
        "sinonimos": ["contrato", "convenio", "acuerdo", "obligación contractual"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:1272", "articulo": "ARTICULO 1272.-", "tema": "Definición de convenio"},
            {"articulo_id": "articulo:cc_tlax:1273", "articulo": "ARTICULO 1273.-", "tema": "Definición de contrato"},
        ],
    },
    "arrendamiento": {
        "sinonimos": ["arrendar", "arrendamiento", "renta", "inquilino", "arrendador"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:2008", "articulo": "ARTICULO 2008.-", "tema": "Contrato de arrendamiento"},
        ],
    },
    "testamento": {
        "sinonimos": ["testamento", "herencia", "legado", "heredar", "testador"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:2606", "articulo": "ARTICULO 2606.-", "tema": "Definición y naturaleza del testamento"},
        ],
    },
    "sucesion": {
        "sinonimos": ["sucesión", "heredar", "herencia", "sucesión legítima"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:2596", "articulo": "ARTICULO 2596.-", "tema": "Definición de herencia y sucesión"},
        ],
    },
    "obligaciones": {
        "sinonimos": ["obligación", "deuda", "pagar", "alimentos", "pensión alimenticia"],
        "documento": "Codigo Civil Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cc_tlax:54", "articulo": "ARTICULO 54.-", "tema": "Obligación alimentaria de los cónyuges hacia los hijos"},
            {"articulo_id": "articulo:cc_tlax:1630", "articulo": "ARTICULO 1630.-", "tema": "Tiempo y cumplimiento del pago de las obligaciones"},
        ],
    },
}

# ============================================================
# PROCEDIMIENTO CIVIL DE TLAXCALA
# ============================================================
INDICE_PC = {
    "demanda": {
        "sinonimos": ["demanda", "demandar", "juicio civil", "escrito de demanda"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpc_tlax:801", "articulo": "Artículo 801.-", "tema": "Documentos y requisitos que deben acompañar a la demanda"},
        ],
    },
    "citatorio": {
        "sinonimos": ["citatorio", "citar", "notificación", "emplazamiento"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpc_tlax:61", "articulo": "Artículo 61.-", "tema": "Validez de emplazamientos, citas y notificaciones"},
        ],
    },
    "prueba": {
        "sinonimos": ["prueba", "pruebas", "evidencia", "medios de prueba"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpc_tlax:251", "articulo": "Artículo 251.-", "tema": "Catálogo de medios de prueba reconocidos por la ley procesal civil"},
        ],
    },
    "sentencia": {
        "sinonimos": ["sentencia", "juicio", "fallo", "sentencia definitiva"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpc_tlax:87", "articulo": "Artículo 87.-", "tema": "Clasificación de sentencias definitivas e interlocutorias"},
        ],
    },
    "recurso": {
        "sinonimos": ["recurso", "apelación", "revisar", "segunda instancia"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpc_tlax:509", "articulo": "Artículo 509.-", "tema": "Apertura de la segunda instancia mediante recurso de apelación"},
        ],
    },
    "embargo": {
        "sinonimos": ["embargo", "embargar", "bienes embargados"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpc_tlax:578", "articulo": "Artículo 578.-", "tema": "Ejecución de sentencia y requerimiento de embargo"},
            {"articulo_id": "articulo:cpc_tlax:588", "articulo": "Artículo 588.-", "tema": "Remate de bienes embargados"},
        ],
    },
    "subasta": {
        "sinonimos": ["subasta", "subastar", "remate", "avalúo"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpc_tlax:664", "articulo": "Artículo 664.-", "tema": "Derechos de los acreedores en el procedimiento de remate"},
        ],
    },
    "ejecutoria": {
        "sinonimos": ["ejecutoria", "sentencia ejecutoriada", "cosa juzgada"],
        "documento": "Procedimiento Civiles Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpc_tlax:567", "articulo": "Artículo 567.-", "tema": "Resoluciones que causan ejecutoria"},
        ],
    },
}

# ============================================================
# PROCEDIMIENTO PENAL DE TLAXCALA
# ============================================================
INDICE_PP = {
    "detencion": {
        "sinonimos": ["detención", "detener", "arrestar", "flagrancia"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpp_tlax:91", "articulo": "Artículo 91.-", "tema": "Detención en caso de delito flagrante o urgente"},
            {"articulo_id": "articulo:cpp_tlax:92", "articulo": "Artículo 92.-", "tema": "Definición legal de flagrancia"},
        ],
    },
    "imputado": {
        "sinonimos": ["imputado", "acusado", "procesado", "inculpado"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpp_tlax:26-BIS", "articulo": "Artículo 26 Bis.-", "tema": "Término constitucional y derechos del inculpado puesto a disposición judicial"},
        ],
    },
    "victima": {
        "sinonimos": ["víctima", "victima", "ofendido", "querellante"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpp_tlax:8-BIS", "articulo": "Artículo 8 Bis.-", "tema": "Delitos perseguibles por querella de la víctima u ofendido"},
        ],
    },
    "audiencia": {
        "sinonimos": ["audiencia", "juicio oral", "vista"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpp_tlax:248", "articulo": "Artículo 248.-", "tema": "Citación a la audiencia de vista del proceso"},
            {"articulo_id": "articulo:cpp_tlax:249", "articulo": "Artículo 249.-", "tema": "Interrogatorio y alegatos en la audiencia"},
        ],
    },
    "prision": {
        "sinonimos": ["prisión preventiva", "cárcel", "privación de libertad"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpp_tlax:97", "articulo": "Artículo 97.-", "tema": "Reglas sobre cumplimiento de prisión preventiva"},
        ],
    },
    "defensa": {
        "sinonimos": ["defensa", "defensor", "abogado defensor"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpp_tlax:42", "articulo": "Artículo 42.-", "tema": "Vista a las partes y derecho de defensa para ofrecer pruebas"},
        ],
    },
    "orden": {
        "sinonimos": ["orden de aprehensión", "aprehensión", "comparecencia"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpp_tlax:50", "articulo": "Artículo 50.-", "tema": "Efectos de la suspensión contra orden de aprehensión o comparecencia"},
        ],
    },
    "carga_prueba": {
        "sinonimos": ["carga de la prueba", "cuerpo del delito", "comprobación"],
        "documento": "Procedimiento Penal Tlaxcala",
        "articulos": [
            {"articulo_id": "articulo:cpp_tlax:62", "articulo": "Artículo 62.-", "tema": "Comprobación del cuerpo del delito"},
        ],
    },
}

# ============================================================
# CONSTITUCIÓN POLÍTICA DE LOS ESTADOS UNIDOS MEXICANOS
# ============================================================
INDICE_CONST = {
    "derechos": {
        "sinonimos": ["derechos humanos", "derechos fundamentales", "pro persona"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo_id": "articulo:cpeum:1", "articulo": "Artículo 1o.", "tema": "Reconocimiento de derechos humanos y principio pro persona"},
        ],
    },
    "garantias": {
        "sinonimos": ["garantías", "amparo", "debido proceso", "legalidad"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo_id": "articulo:cpeum:14", "articulo": "Artículo 14.", "tema": "Irretroactividad de la ley y garantía de audiencia"},
            {"articulo_id": "articulo:cpeum:16", "articulo": "Artículo 16.", "tema": "Garantía de legalidad y actos de molestia fundados y motivados"},
        ],
    },
    "trabajo": {
        "sinonimos": ["derecho al trabajo", "libertad de trabajo", "profesión"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo_id": "articulo:cpeum:5", "articulo": "Artículo 5o.", "tema": "Libertad de profesión, industria, comercio o trabajo lícito"},
            {"articulo_id": "articulo:cpeum:123", "articulo": "Artículo 123.", "tema": "Derecho al trabajo digno y bases constitucionales laborales"},
        ],
    },
    "educacion": {
        "sinonimos": ["educación", "escuela", "enseñanza"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo_id": "articulo:cpeum:3", "articulo": "Artículo 3o.", "tema": "Derecho a la educación"},
        ],
    },
    "propiedad": {
        "sinonimos": ["propiedad privada", "tierras y aguas", "expropiación"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo_id": "articulo:cpeum:27", "articulo": "Artículo 27.", "tema": "Propiedad originaria de la Nación y régimen de propiedad privada"},
        ],
    },
    "estado": {
        "sinonimos": ["estado", "gobierno", "división de poderes", "república"],
        "documento": "Constitucion",
        "articulos": [
            {"articulo_id": "articulo:cpeum:40", "articulo": "Artículo 40.", "tema": "República representativa, democrática, laica y federal"},
            {"articulo_id": "articulo:cpeum:50", "articulo": "Artículo 50.", "tema": "Depósito del Poder Legislativo en un Congreso General"},
        ],
    },
}

# ============================================================
# ÍNDICE UNIFICADO (sin colisión de claves entre normativas)
# ============================================================
INDICE_TEMATICO = {}

for prefijo, ind in [
    ("lft", INDICE_LFT),
    ("cp", INDICE_CP),
    ("cc", INDICE_CC),
    ("pc", INDICE_PC),
    ("pp", INDICE_PP),
    ("const", INDICE_CONST),
]:
    for key, value in ind.items():
        value["concepto"] = key
        clave_unificada = key if key not in INDICE_TEMATICO else f"{prefijo}_{key}"
        INDICE_TEMATICO[clave_unificada] = value


def buscar_por_concepto(query: str, documento_filtro: str = None) -> list[dict]:
    """
    Busca artículos relacionados con los conceptos de la query.

    Args:
        query: Consulta del usuario
        documento_filtro: Filtrar por documento específico (opcional)

    Returns:
        Lista de artículos encontrados con su temática e identificador canónico `articulo_id`
    """
    query_lower = query.lower()
    resultados = []

    for clave, datos in INDICE_TEMATICO.items():
        concepto = datos.get("concepto", clave)
        if documento_filtro:
            doc_norm = datos.get("documento", "").lower()
            if documento_filtro.lower() not in doc_norm and doc_norm not in documento_filtro.lower():
                continue

        encontrado = False
        sinonimos = datos.get("sinonimos", [])

        for sinonimo in sinonimos:
            if sinonimo.lower() in query_lower:
                encontrado = True
                break

        if not encontrado and concepto.replace("_", " ") in query_lower:
            encontrado = True

        if encontrado:
            for art in datos["articulos"]:
                resultados.append({
                    "concepto": concepto,
                    "documento": datos.get("documento", ""),
                    "articulo": art["articulo"],
                    "articulo_id": art.get("articulo_id", ""),
                    "tema": art["tema"],
                })

    return resultados


def detectar_documento(query: str) -> str:
    """
    Detecta qué normativa corresponde a la query basándose en palabras clave.
    """
    query_lower = query.lower()

    mapeo = [
        ("procedimiento penal", ["detención", "detenido", "detener", "imputado", "audiencia", "prisión preventiva", "defensa", "orden de aprehensión", "juicio oral", "fiscal", "agente"]),
        ("código penal", ["robo", "robar", "robandome", "lesión", "lesionar", "violencia", "feminicidio", "secuestro", "extorsión", "fraude", "delito", "crimen", "cárcel", "pena", "víctima", "asesinato", "violación"]),
        ("procedimiento civil", ["demanda", "juicio civil", "sentencia", "embargo", "subasta", "ejecutoria"]),
        ("código civil", ["matrimonio", "divorciarme", "divorcio", "herencia", "heredar", "propiedad", "testamento", "adopción", "adoptar", "tutela", "persona", "civil"]),
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
            print(f"  [{r['documento']}] {r['articulo']} ({r['articulo_id']}): {r['tema']}")
        print()
