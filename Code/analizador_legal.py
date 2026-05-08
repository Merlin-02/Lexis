#!/usr/bin/env python3
# analizador_legal.py
# Modulo de analisis lexico para deteccion de normativa y correccion de consultas

import os
import json
import re
import string
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
from pathlib import Path

STOPWORDS = {
    'de', 'la', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para',
    'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'mas', 'pero', 'sus', 'le', 'ya',
    'o', 'este', 'si', 'porque', 'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre',
    'ser', 'tiene', 'también', 'me', 'hasta', 'hay', 'donde', 'quien', 'desde', 'todo',
    'nos', 'durante', 'todos', 'uno', 'les', 'ni', 'contra', 'otros', 'ese', 'eso',
    'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos', 'qué', 'unos', 'yo',
    'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho', 'quienes', 'nada',
    'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo', 'nosotros',
    'mi', 'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros',
    'vosotras', 'os', 'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas',
    'suyo', 'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras',
    'es', 'son', 'era', 'eran', 'fue', 'fueron', 'sea', 'sean', 'será', 'serán',
    'sido', 'siendo', 'siendo', 'hay', 'han', 'había', 'habían', 'haber', 'habrá',
    'tener', 'tiene', 'tienen', 'tenía', 'tenían', 'tuve', 'tuvo', 'tuvieron',
    'poder', 'puede', 'pueden', 'podía', 'podían', 'podrá', 'podrán', 'podido',
    'hacer', 'hace', 'hacen', 'hacía', 'hacían', 'hizo', 'hicieron', 'haré', 'harán',
    'decir', 'dice', 'dicen', 'decía', 'decían', 'dijo', 'dijeron', 'diré', 'dirán',
    'ver', 've', 'ven', 'veía', 'veían', 'vio', 'vieron', 'veré', 'verán', 'visto',
    'dar', 'da', 'dan', 'daba', 'daban', 'dio', 'dieron', 'daré', 'darán',
    'saber', 'sabe', 'saben', 'sabía', 'sabían', 'supo', 'supieron', 'sabré', 'sabrán',
    'cada', 'cómo', 'cual', 'cuál', 'cuáles', 'cuándo', 'dónde', 'es', 'eso',
    'está', 'este', 'esto', 'estos', 'estoy', 'están', 'ha', 'han', 'he', 'hemos',
    'hice', 'hoy', 'huyo', 'ir', 'junto', 'más', 'mismo', 'nada', 'ni', 'nunca',
    'solo', 'sólo', 'tan', 'todo', 'tras', 'vez', 'ya'
}

RUTA_STRUCTURED = Path(__file__).parent.parent / "knowledge_structured"

PALABRAS_CLAVE_POR_AREA = {
    'laboral': {
        'alta_prioridad': [
            'trabajo', 'laboral', 'empleo', 'empleador', 'patrón', 'patron', 'trabajador',
            'trabajadora',             'despido', 'despedido', 'despedida', 'despedir', 'despedirme', 'despidieron', 'despidido',
            'trabajado', 'trabajadora', 'trabajando', 'laborado', 'laborando', 'antigüedad', 'antiguedad',
            'transferencia', 'transferir', 'traslado', 'trasladar', 'cambio de plaza', 'cambio de área',
            'indemnización', 'indemnizacion', 'contrato', 'contrato de trabajo', 'vacaciones',
            'prima', 'aguinaldo', 'infonavit', 'imss', 'seguridad social', 'afiliación',
            'liquidación', 'liquidacion', 'finiquito', 'huelga', 'sindicato', 'contratación',
            'jornada', 'horario', 'remuneración', 'remuneracion', 'pago', 'nómina', 'nomina',
            'bono', 'utilidades', 'cesantía', 'cesantia', 'subcontratación', 'outsourcing',
            'protección', 'violencia laboral', 'hostigamiento', 'acoso', 'acoso sexual',
            'discriminación', 'discriminacion laboral', 'igualdad', 'capacitación', 'capacitacion',
            'treceavo', 'domingo', 'descanso', 'semana', 'festivo', 'prima dominical',
            'tiempo extra', 'sobretiempo', '形成', 'prestaciones', 'beneficio', 'regimen',
            'ley federal del trabajo', 'lft', 'ctm', 'cmg', 'servicio', 'prestador',
            'dependencia', 'subordinación', 'subordinacion', 'dirección', 'organización',
            'inspección', 'vistoria', 'multa', 'sanción', 'infracción', 'amparo', 'reclamación',
            'queja', 'demanda', 'juicio', 'laudo', 'tribunal', 'juez', 'conciliación',
            'audiencia', 'procedimiento', 'recurso', 'revocación', 'apelación', 'laborando',
            'laboraba', 'empleo', 'empleando', 'renuncia', 'renunciar', 'renuncie', 'vacante', 'jefe',
            'gerente', 'supervisor', 'encargado', 'dueño', 'dueno', 'patronal', 'empresa',
            'salario', 'sueldo', 'pago', 'pagar', 'remuneración', 'discriminación', 'discriminar',
            'discriminado', 'género', 'genero', 'mujer', 'hombre', 'embarazada', 'embarazo',
            'discapacidad', 'discapacitado', 'edad', 'religión', 'religion', 'origen',
            'hostigamiento', 'hostigar', 'hostigado', 'acoso', 'acosar', 'acosado',
            'ambiente', 'laboral', 'clima', 'mobbing', 'violencia', 'vg'
        ],
        'palabras_excluyentes': ['penal', 'delito', 'robo', 'asalto', 'homicidio', 'asesinato',
            'cívil', 'matrimonio', 'herencia', 'testamento', 'divorcio', 'custodia']
    },
    'penal': {
        'alta_prioridad': [
            'penal', 'delito', 'crimen', 'robo', 'robado', 'robaron', 'asalto', 'asaltado',
            'asaltar', 'assalto', 'assaltar', 'assaltado', 'assaltaron', 'asaltaron',
            'assaultaron', 'asaultar', 'homicidio', 'asesinato', 'asesinado', 'matar', 'mató', 'mataron',
            'violación', 'violado', 'abuso', 'abusado', 'extorsión', 'extorsionado',
            'fraude', 'secuestro', 'secuestrado', 'tráfico', 'narcotráfico', 'droga',
            'lesiones', 'lesionado', 'amenazas', 'amenazado', 'estafa', 'estafado',
            'daño', 'perjuicio', 'falsificación', 'cohecho', 'corrupción', 'soborno', 'peculado',
            'detención', 'detenido', 'arresto', 'arrestado', 'prisión', 'cárcel', 'reos', 'sentencia', 'condena',
            'tribunal', 'juez', 'fiscal', 'ministerio público', 'agencia', 'denuncia',
            'denunciar', 'denunciado', 'querella', 'víctima', 'imputado', 'acusado', 'procesado', 'defensor',
            'abogado', 'prueba', 'testigo', 'indicio', 'evidencia', 'código penal',
            'ley penal', 'delito', 'falta', 'infracción', 'sanción', 'pena', 'multa',
            'cárcel', 'reclusión', 'prisión preventiva', 'libertad', 'bajo',
            'caución', 'fianza', 'cumpimiento', 'suspensión', 'condicional', 'beneficio',
            'remisión', 'perdón', 'gracia', 'indulto', 'amnistía', 'excarcelación',
            'parole', 'libertad condicional', 'régimen', 'semiabierto', 'abierto',
            'victimario', 'agresor', 'denunciante', 'demanda', 'querella', 'actuación',
            'investigación', 'averiguación', 'proceso', 'juicio', 'procedimiento',
            'recurso', 'apelación', 'amparo', 'revisión', 'circunstancia', 'atenuante',
            'agravante', 'calificación', 'tipicidad', 'culpabilidad', 'dolo', 'culpa',
            'tentativa', 'conato', 'consumación', 'participación', 'cómplice', 'autor',
            'instigador', 'eximente', 'exculpante', 'justificación', 'legítima defensa',
            'estado de necesidad', 'cumplimiento del deber', 'orden de autoridad',
            'consentimiento', 'error', 'inimputabilidad', 'menor', 'incapaz', 'adicción',
            'alcoholemia', 'drogadicción', 'psiquiátrico', 'forense', 'peritaje',
            'autopsia', 'inspector', 'levantamiento', 'cadáver', 'restos', 'escena',
            'huella', 'dactilar', 'genético', 'adn', 'testimonio', 'declaración',
            'careo', 'interrogatorio', 'contrainterrogatorio', 'coartada', 'presunción',
            ' innocence', 'dubio', 'in dubio pro reo', 'non bis in idem', 'cosa juzgada',
            'legalidad', 'proporcionalidad', 'necesidad', 'racionalidad', 'finalidad',
            'violencia', 'golpe', 'golpes', 'pegar', 'pega', 'pego', 'agredir', 'agredido',
            'agresión', 'agresiva', 'agresor', 'lesionar', 'lesionado', 'lesion',
            'herir', 'herido', 'herida', 'amenaza', 'amenazar', 'amenazo', 'amenazado',
            'maltrato', 'maltratar', 'maltrato', 'abuso', 'abusar', 'abusado',
            'físico', 'fisico', 'verbal', 'cuchillo', 'arma', 'golpear', 'golpeado',
            'puño', 'puñetazo', 'patada', 'matar', 'mató', 'matado'
        ],
        'palabras_excluyentes': ['trabajo', 'laboral', 'empleo', 'salario', 'civil',
            'matrimonio', 'herencia', 'testamento', 'divorcio', 'contrato']
    },
    'civil': {
        'alta_prioridad': [
            'civil', 'código civil', 'codigo civil', 'persona', 'física', 'moral', 'derecho civil',
            'patrimonio', 'bienes', 'posesión', 'propiedad', 'usufructo', 'servidumbre',
            'obligación', 'obligacion', 'contrato', 'contrato civil', 'contrato mercantil',
            'obligar', 'deber', 'derecho', 'acreedor', 'deudor', 'deuda', 'deudas',
            'prestación', 'cumplimiento', 'incumplimiento', 'resolución', 'rescisión',
            'novación', 'compensación', 'conjunción', 'subrogación', 'prescripción',
            'caducidad', 'ténrmino', 'plazo', 'condición', 'modalidad', 'carga',
            'onus', 'prueba', 'presunción', 'ficción', 'excepción', 'defensa', 'acción',
            'juicio', 'proceso', 'procedimiento', 'sentencia', 'laudo', 'litis',
            'parte', 'demandante', 'demandado', 'tercero', 'interesado', 'legítimo',
            'representante', 'apoderado', 'mandatario', 'tutor', 'curador', 'albacea',
            'heredero', 'legatario', 'testador', 'testamento', 'sucesión', 'herencia',
            'legítima', 'mejora', 'donación', 'entre vivos', 'mortis causa', 'codicilo',
            'matrimonio', 'divorcio', 'divorciarme', 'divorciar', 'concubinato', 'unión', 'pareja', 'filiación',
            'paternidad', 'maternidad', 'adopción', 'tutela', 'patria potestad',
            'casa', 'vivienda', 'inmueble', 'departamento', 'departamento', 'terreno', 'lote',
            'propiedad', 'posesión', 'usufructo', 'servidumbre', 'derecho de paso', 'medidor',
            'luz', 'agua', 'servicios', 'servicio público', 'servicios públicos'
            'obligación alimentaria', 'pensión', 'menor', 'incapaz', 'interdicción',
            'embargo', '垂recautelar', 'medida', 'cautelar', 'provisional', 'precautelar',
            'anexión', 'anexo', 'documento', 'escritura', 'pública', 'protocolo',
            'notario', 'registro', 'inscripción', 'matrícula', 'folio', 'real',
            'hipoteca', 'gravamen', 'carga', 'liminación', 'cancelación', 'inscripción',
            'usucapión', 'prescripción acquisitiva', 'dominio', 'posesión', 'tenencia',
            'arrendamiento', 'renta', 'inquilino', 'arrendador', 'subarrendamiento',
            'comodato', 'préstamo', 'prestamo', 'mutuo', 'depósito', 'deposito', 'mandato',
            'gestión', 'representación', 'sociedad', 'asociación', 'fundación',
            'corporación', 'moral', 'civil', 'comercio', 'mercantil', 'letra', 'cambio',
            'cheque', 'pagaré', 'pagare', 'factura', 'conciliación', 'transacción',
            'renuncia', 'remisión', 'compromiso', 'arbitraje', 'jurisdicción', 'voluntad',
            'autonomía', 'privada', 'orden público', 'buenas costumbres', 'moralidad',
            'ilegal', 'ilícito', 'inmoral', 'contravención', 'infracción', 'sanción',
            'indemnización', 'indemnizar', 'daño', 'perjuicio', 'lucro', 'cesante', 'daño moral',
            'responsabilidad', 'civil', 'contractual', 'extracontractual', 'objetiva',
            'subjetiva', 'directo', 'indirecto', 'consecuencial', 'eximente', 'exculpante',
            'culpa', 'negligencia', 'impericia', 'imprudencia', 'dolo', 'caso fortuito',
            'fuerza mayor', 'hecho', 'propio', 'ajeno', 'tercero', 'causa', 'efecto',
            'relación', 'causal', 'imputación', 'atribución', 'imputabilidad',
            'capacidad', 'derecho', 'capacidad de goce', 'capacidad de ejercicio',
            'mayoría', 'edad', 'emancipación', 'menor', 'interdicto', 'sonámbulo',
            'borracho', 'drogadicto', 'locura', 'demencia', 'enfermedad', 'mental',
            'incapacidad', 'inhabilitación', 'suspensión', 'quiebra', 'concurso',
            'acreedor', 'deudor', 'insolvencia', 'beneficio', 'limitación', 'excarcelación',
            'prisión', '治外法権', 'exención', 'privilegio', 'prerrogativa', 'inmunidad',
            'domicilio', 'residencia', 'vecindad', 'nacionalidad', 'ciudadanía', 'extranjero',
            'apátrida', 'refugiado', 'migrante', 'indocumentado', 'visado', 'visa',
            'pasaporte', 'identificación', 'documento', 'identidad', 'nombre', 'pseudónimo',
            'alias', 'seudónimo', 'renombre', 'firma', 'rúbrica', 'signo', 'marca',
            'logo', 'embblema', 'distintivo', 'denominación', 'razón social', 'denominación',
            'social', 'objeto', 'social', 'domicilio', 'sede', 'representante', 'legal',
            'poder', 'facultad', 'atribución', 'competencia', 'atribución', 'función',
            'cargo', 'empleo', 'puesto', 'oficio', 'profesión', 'ocupación', 'actividad',
            'industria', 'comercio', 'servicio', 'empresa', 'establecimiento', 'local',
            'negocio', 'oficina', 'despacho', 'consultorio', 'taller', 'fábrica',
            'náquina', 'herramienta', 'instrumento', 'utensilio', 'materia', 'prima',
            'producto', 'elaboración', 'fabricación', 'manufactura', 'producción',
            'distribución', 'comercialización', 'venta', 'compra', 'adquisición',
            'enajenación', 'transferencia', 'transmisión', 'cesión', 'adjudicación',
            'asignación', 'dación', 'pago', 'prestación', 'entrega', 'recepción',
            'aceptación', 'rechazo', 'observación', 'objecion', 'reclamación', 'impugnación',
            'recurso', 'revocación', 'anulación', 'nulidad', 'inexistencia', 'invalidez',
            'ilegalidad', 'inconstitucionalidad', 'ilegitimidad', 'indebido', 'improcedente',
            'inadmisible', 'infundado', 'fundado', 'procedente', 'legal', 'legítimo',
            'válido', 'eficaz', 'subsistente', 'vigente', 'actual', 'presente', 'futuro',
            'pasado', 'antiguo', 'nuevo', 'reciente', 'moderno', 'antiguo', 'clásico',
            'tradicional', 'costumbre', 'práctica', 'uso', 'estilo', 'moda', 'tendencia',
            'demanda', 'demandar', 'demando', 'reclamar', 'reclamo', 'exigir', 'exijo',
            'pagar', 'pago', 'adeudo', 'adeudar', 'cobrar', 'cobro', 'cobranza'
        ],
        'palabras_excluyentes': ['trabajo', 'laboral', 'empleo', 'penal', 'delito', 'robo']
    },
    'constitucional': {
        'alta_prioridad': [
            'constitución', 'constitucional', 'carta', 'magna', 'fundamental', 'derecho',
            'garantía', 'amnistía', 'indulto', 'gracia', 'amnistía', 'veto', 'ley',
            'decreto', 'reglamento', 'circular', 'acuerdo', 'disposición', 'norma',
            'ordenamiento', 'codificación', 'legislación', 'estatuto', 'bylaw', 'charter',
            'federal', 'estatal', 'municipal', 'local', 'regional', 'nacional', 'internacional',
            'soberanía', 'independencia', 'autonomía', 'federalismo', 'centralización',
            'descentralización', 'democracia', 'república', 'monarquía', 'dictadura',
            'gobierno', 'poder', 'ejecutivo', 'legislativo', 'judicial', 'tribunal',
            'corte', 'suprema', 'corte suprema', 'corte constitucional', 'tribunal constitucional',
            'senado', 'cámara', 'congreso', 'asamblea', 'legislatura', 'diputado',
            'representante', 'senador', 'governor', 'prefect', 'alcalde', 'regidor',
            'síndico', 'tesorero', 'contralor', 'auditor', 'funcionario', 'empleado',
            'servidor', 'público', 'autoridad', 'jurisdiccional', 'administrativo',
            'civil', 'penal', 'militar', 'eclesiástico', 'jurisdicción', 'competencia',
            'rango', 'jerarquía', 'pirámide', 'kelsen', 'fuente', 'formal', 'material',
            'ley', 'tratado', 'costumbre', 'principio', 'general', 'sentido', 'justicia',
            'equidad', 'legalidad', 'seguridad', 'jurídica', 'stabilitas', 'jurisprudencia',
            'precedente', 'stare decisis', 'doctrina', 'principio', 'teoría', 'escuela',
            'interpretación', 'literal', 'teleológica', 'histórica', 'sistemática',
            'analógica', 'restrictiva', 'extensiva', 'auténtica', 'usual', 'común',
            'vigencia', 'entrada', 'vigencia', 'publicación', 'promulgación', 'sanción',
            'vetar', 'orden jerárquico', 'superioridad', 'inferioridad', 'rango',
            'ley fundamental', 'ley suprema', 'ley marco', 'ley orgánica', 'ley ordinal',
            'ley делега', 'ley habilitante', 'decreto ley', 'decreto legislativo',
            'decreto gubernamental', 'reglamento', 'reglamentario', 'circular', 'oficio',
            'instructivo', 'directriz', 'guía', 'protocolo', 'procedimiento', 'norma',
            'técnica', 'estándar', 'specification', 'requisito', 'condición', 'elemento',
            'factor', 'aspecto', 'particular', 'general', 'universal', 'absoluto', 'relativo',
            'pleno', 'parcial', 'total', 'global', 'integral', 'completo', 'exhaustivo',
            'exclusivo', 'incluyente', 'excluyente', 'abierto', 'cerrado', 'limitado',
            'ilimitado', 'finito', 'infinito', 'permanente', 'temporal', 'transitorio',
            'provisional', 'definitivo', 'irrevocable', 'revocable', 'renunciable',
            'indisponible', 'disponible', 'transferible', 'intransferible', 'cesible',
            'incesible', 'transmisible', 'intransmisible', 'dividible', 'indivisible',
            'divisible', ' separable', 'inseparable', 'accesible', 'inaccesible', 'abordable',
            'inabordable', 'lícito', 'ilícito', 'legal', 'ilegal', 'legítimo', 'ilegítimo',
            'constitucional', 'inconstitucional', 'convencional', 'inconvencional',
            'legal', 'ilegal', 'reglamentario', 'irregular', 'anormal', 'típico',
            'atípico', 'regular', 'estándar', 'anexo', 'adicional', 'complementario',
            'modificatorio', 'derogatorio', 'abrogatorio', 'refundido', 'compilado'
        ],
        'palabras_excluyentes': []
    },
    'procesal_civil': {
        'alta_prioridad': [
            'procesal', 'procedimiento', 'proceso', 'juicio', 'tramite', 'diligencia',
            'actuación', 'actuación judicial', 'órgano', 'jurisdiccional', 'tribunal',
            'juzgado', 'juez', 'magistrado', 'secretario', 'actuario', 'oficial',
            'notificador', 'perito', 'testigo', 'parte', 'demandante', 'demandado',
            'tercero', 'interviniente', 'coadyuvante', 'fiscal', 'ministerio', 'público',
            'actor', 'reo', 'imputado', 'acusado', 'procesado', 'sentenciado', 'condenado',
            'absuelto', 'exculpado', 'inculpado', 'querellante', 'denunciante', 'víctima',
            'ofendido', 'agraviado', 'perjudicado', 'interesado', 'legitimado', 'capacidad',
            'legitimación', 'personería', 'representación', 'apoderado', 'mandatario',
            'tutor', 'curador', 'defensor', 'abogado', 'patrón', 'sindicato', 'asociación',
            'institución', 'entidad', 'persona', 'moral', 'física', 'demanda', 'contestación',
            'reconvención', 'excepción', 'defensa', 'objeciones', 'impugnación', 'recurso',
            'apelación', 'revisión', 'amparo', 'queja', 'denuncia', 'querella', 'denuncia',
            'acusación', 'cargo', 'imputación', 'atribución', 'tipificación', 'calificación',
            'delito', 'falta', 'infracción', 'sanción', 'pena', 'multa', 'cárcel',
            'prisión', 'reclusión', 'arresto', 'detención', 'custodia', 'arraigo',
            'medida', 'cautelar', 'provisional', 'precautoria', 'aseguramiento', 'embargo',
            'secuestro', 'incautación', 'decomiso', 'confiscación', 'exhibición',
            'presentación', 'intimación', 'citación', 'notificación', 'emplazamiento',
            'convocatoria', 'llamamiento', 'invitación', 'requerimiento', 'exhorto',
            'comisión', 'despacho', 'orden', 'mandamiento', 'auto', 'sentencia', 'laudo',
            'lazo', 'fallo', 'veredicto', 'resolución', 'decreto', 'proveído', 'dictamen',
            'voto', 'mayoría', 'disidencia', 'opinión', 'razón', 'considerando',
            'resultando', 'antecedente', 'hecho', 'fundamento', 'derecho', 'motivos',
            'fallo', 'parte', 'dispositivo', 'sentencia', 'definitiva', 'interlocutoria',
            'provisional', 'parcial', 'total', 'absoluta', 'condenatoria', 'absolutoria',
            'mixta', 'incidente', 'cuestión', 'incidente', 'tema', 'punto', 'objeto',
            'pretensión', 'reclamación', 'petitum', 'pedimento', 'solicitud', 'petición',
            'gestión', 'instancia', 'expediente', 'expediente judicial', 'carpeta',
            'legajo', 'tomo', 'folio', '页码', 'documento', 'acta', 'constancia',
            'certificación', 'testimonio', 'copia', 'original', 'traslado', 'vista',
            'audiencia', 'vista', 'conciliación', 'medición', 'arbitraje', 'negociación',
            'mediador', 'conciliador', 'árbitro', 'compromisario', 'componedor', 'amigable',
            'componedor', 'transacción', 'convenio', 'acuerdo', 'conciliatorio', 'arreglo',
            'desistimiento', 'renuncia', 'abandono', 'caducidad', 'prescripción', 'perención',
            'término', 'plazo', 'tiempo', 'durabilidad', 'vencimiento', 'caducidad',
            'prórroga', 'renovación', 'suspensión', 'interrupción', 'reanudación',
            'término', 'legal', 'judicial', 'convencional', 'convencional', 'voluntario',
            'forzoso', 'obligatorio', 'facultativo', 'perentorio', 'ordinario', 'extraordinario',
            'especial', 'general', 'común', 'privado', 'público', 'mixto', 'gratuito',
            'oneroso', 'luctuoso', 'conmutativo', 'aleatorio', 'intuitivo', 'solemne',
            'libre', 'caprichoso', 'formal', 'material', 'constitutivo', 'declarativo',
            'convalidatorio', 'ratificatorio', 'confirmatorio', 'modificatorio', 'extintivo',
            'prescriptivo', 'conversivo', 'subrogatorio', 'delegatorio', 'mandatario'
        ],
        'palabras_excluyentes': ['penal', 'delito', 'trabajo', 'laboral']
    },
    'procesal_penal': {
        'alta_prioridad': [
            'procesal', 'penal', 'proceso', 'juicio', 'procedimiento', 'instrucción',
            'investigación', 'averiguación', 'preliminar', 'intermedia', 'juicio',
            'ejecución', 'fase', 'etapa', 'estado', 'momento', 'trámite', 'diligencia',
            'actuación', 'órgano', 'jurisdiccional', 'jurisdicción', 'competencia',
            'tribunal', 'corte', 'sala', 'sección', 'ponente', 'magistrado', 'juez',
            'juez de garantía', 'juez de control', 'juez de ejecución', 'tribunal de juicio',
            'tribunal de sentencia', 'corte suprema', 'corte constitucional', 'corte penales',
            'ministerio', 'público', 'fiscal', 'agente', 'ministerio público', 'fiscalía',
            'procurador', 'defensor', 'defensor público', 'defensor privado', 'abogado',
            'querellante', 'denunciante', 'víctima', 'ofendido', 'agraviado', 'perjudicado',
            'imputado', 'acusado', 'procesado', 'sentenciado', 'condenado', 'reo',
            'parte', 'parte accusadora', 'parte defensora', 'parte civil', 'tercero',
            'responsable', 'civil', 'garante', ' garante', 'custodio', 'guarda', 'vigilante',
            'delegado', 'representante', 'representante legal', 'representante procesal',
            'apoderado', 'mandatario', 'litis', 'litisconsorte', 'litispendencia',
            'conexidad', 'acumulación', 'separación', 'demanda', 'querella', 'denuncia',
            'acusación', 'cargo', 'imputación', 'atribución', 'denuncia', 'comunicación',
            'exposición', 'relato', 'narración', 'descripción', 'individualización',
            'identificación', 'determinación', 'calificación', 'tipificación', 'delito',
            'crimen', 'infracción', 'falta', 'contravención', 'ilícito', 'ilgal',
            'infracción penal', 'delito', 'hecho', 'hecho delictivo', 'conducta', 'acción',
            'omisión', 'comisión', 'participación', 'autoría', 'coautoría', 'complicidad',
            'instigación', 'concierto', 'asociación', 'banda', 'organización', 'crimen',
            'organizado', 'elemento', 'objetivo', 'subjetivo', 'tipo', 'tipo penal',
            'tipicidad', 'atipicidad', 'conglobación', 'consumación', 'tentativa',
            'conato', 'fracaso', 'abandono', 'desistimiento', 'voluntario', 'involuntario',
            'imposibilidad', 'facticidad', 'error', 'error de tipo', 'error de prohibición',
            'error de comprensión', 'inimputabilidad', 'imputabilidad', 'dolo', 'culpa',
            'imprudencia', 'negligencia', 'impericia', 'conocimiento', 'voluntad',
            'ánimo', 'ánimo de lucro', 'ánimo de causar', 'ánimo de defraudar', 'ánimo de poseer',
            'animus', 'corpus', 'corpus delicti', 'cuerpo', 'cuerpo del delito', 'cosa',
            'cosa juzgada', 'cosa litigiosa', 'cosa prometida', 'cosa mueble', 'cosa inmueble',
            'cosa fungible', 'cosa infungible', 'cosa consumible', 'cosa慕容', 'cosa principal',
            'cosa accesoria', 'cosa aneja', 'cosa incidente', 'cosa adhesiva', 'cosajoin',
            'cosa join', 'cosa join', 'cosa join', 'cosa join', 'cosa join', 'cosa join',
            'prueba', 'prueba testimonial', 'prueba pericial', 'prueba documental',
            'prueba de inspectión', 'prueba de reconocimiento', 'prueba de careo',
            'prueba de inteligencia', 'prueba científica', 'prueba tecnológica',
            'prueba digital', 'prueba electrónica', 'pruebahemática', 'prueba genética',
            'prueba de adn', 'prueba de huella', 'prueba dactilar', 'prueba fotográfica',
            'prueba videográfica', 'prueba auditiva', 'prueba de sonido', 'prueba de',
            'presunción', 'presunción de inocencia', 'presunción de veracidad', 'presunción',
            'iuris', 'presunción iuris tantum', 'presunción iuris et de iure', 'indicio',
            'indicio', 'indicio', 'indicio', 'indicio', 'indicio', 'indicio', 'indicio',
            'medida', 'cautelar', 'medida preventiva', 'medida provisional', 'medida asegurativa',
            'medida aseguratoria', 'detención', 'detención preventiva', 'detención domiciliaria',
            'prisión', 'prisión preventiva', 'prisión preventiva oficiosa', 'prisión preventiva',
            'justificada', 'prisión preventiva domiciliaria', 'arresto', 'arresto domiciliario',
            'arresto nocturno', 'reclusión', 'reclusión temporal', 'reclusión perpetua',
            'internamiento', 'internamiento preventivo', 'internamiento definitivo',
            'custodia', 'custodia preventiva', 'custodia', 'custodia', 'custodia',
            'embargo', 'embargo preventivo', 'embargo de bienes', 'embargo de salarios',
            'embargo de cuentas', 'embargo de propiedades', 'secuestro', 'secuestro preventivo',
            'secuestro de bienes', 'incautación', 'incautación preventiva', 'decomiso',
            'decomiso de bienes', 'decomiso de instrumentos', 'decomiso de productos',
            'decomiso de ganancias', 'decomiso extendido', 'decomiso sin condena',
            'inmovilización', 'inmovilización de vehículos', 'inmovilización de cuentas',
            'inmovilización de activos', 'inmovilización de bienes', 'inmovilización',
            'embargo', 'fianza', 'fianza de radicar', 'fianza de presentación', 'fianza',
            'caución', 'caución de radicar', 'caución de no huir', 'caución de evitar',
            'caución pecuniaria', 'libertad', 'libertad provisional', 'libertad condicional',
            'libertad bajo', 'fianza', 'libertad bajo', 'fianza', 'libertad bajo', 'protesta',
            'libertad', 'libertad vigilada', 'libertad restringida', 'libertad controlada',
            'libertad', 'trabajo', 'trabajo comunitario', 'trabajo social', 'trabajo',
            'servicio', 'servicio comunitario', 'arresto', 'arresto domiciliario', 'arresto',
            'fin de semana', 'arresto', 'fin de semana', 'multa', 'multa', 'multa',
            'pecuniaria', 'sanción', 'sanción pecuniaria', 'sanción restrictiva', 'sanción',
            'suspensión', 'suspensión condicional', 'suspensión de derechos', 'suspensión',
            'de funciones', 'suspensión de cargo', 'suspensión de actividad', 'suspensión',
            'inhabilitación', 'inhabilitación temporal', 'inhabilitación perpetua',
            'inhabilitación de derechos', 'inhabilitación de funciones', 'destitución',
            'destitución de cargo', 'destitución de función', 'expulsión', 'expulsión',
            'del territorio', 'extranjería', 'extranjero', 'carta de naturaleza', 'carta',
            'de naturaleza', 'carta de ciudadanía', 'carta', 'de residencia', 'carta',
            'de lavor', 'perdón', 'perdón del ofendido', 'perdón judicial', 'amnistía',
            'amnistía', 'indulto', 'indulto particular', 'indulto general', 'gracia',
            'gracia', 'indulgencia', 'remisión', 'remisión de pena', 'remisión condicional',
            'remisión', 'rehabilitación', 'rehabilitación civil', 'rehabilitación',
            'judicial', 'rehabilitación', 'prescripción', 'prescripción de la acción',
            'prescripción de la pena', 'prescripción extintiva', 'prescripción acquisitiva',
            'caducidad', 'caducidad de la acción', 'caducidad del derecho', 'perención',
            'perención de la instancia', 'perención del proceso', 'abandono', 'abandono',
            'de la acción', 'abandono del proceso', 'desistimiento', 'desistimiento',
            'de la acción', 'desistimiento del querellante', 'desistimiento del accusador',
            'arquitectura', 'transacción', 'conciliación', 'conciliación', 'acuerdo',
            'acuerdo reparatorio', 'acuerdo conciliatorio', 'procedimiento', 'abreviado',
            'procedimiento', 'ordinario', 'procedimiento', 'especial', 'procedimiento',
            'sumario', 'procedimiento', 'sumarísimo', 'procedimiento', 'común', 'procedimiento',
            'particular', 'procedimiento', 'genérico', 'procedimiento', 'específico',
            'procedimiento', 'regular', 'procedimiento', 'irregular', 'procedimiento',
            'normal', 'procedimiento', 'anormal', 'trámite', 'trámite ordinario', 'trámite',
            'extraordinario', 'trámite', 'urgente', 'trámite', 'preferente', 'trámite',
            'diferido', 'trámite', 'diferido', 'audiencia', 'audiencia', 'preliminar',
            'audiencia', 'intermedia', 'audiencia', 'dejuicio', 'audiencia', 'de lectura',
            'audiencia', 'deindividualización', 'audiencia', 'de individualización', 'audiencia',
            'de veredicto', 'audiencia', 'de sentencing', 'audiencia', 'de arguments',
            'audiencia', 'de alegatos', 'audiencia', 'de conclusiones', 'audiencia',
            'de sentence', 'audiencia', 'de closing arguments', 'audiencia', 'de',
            'vista', 'audiencia', 'de la causa', 'audiencia', 'pública', 'audiencia',
            'privada', 'audiencia', 'a puerta cerrada', 'audiencia', 'con medios',
            'comunicación', 'audiencia', 'con grabación', 'audiencia', 'con transmisión',
            'audiencia', 'remota', 'audiencia', 'virtual', 'audiencia', 'presencial',
            'audiencia', 'hibrida', 'práctica', 'práctica de prueba', 'práctica de diligencia',
            'práctica de actuación', 'práctica de medio', 'práctica de prueba', 'práctica',
            'de prueba testimonial', 'práctica', 'de prueba pericial', 'práctica', 'de',
            'prueba', 'documental', 'práctica', 'de prueba', 'inspectiva', 'práctica',
            'de prueba', 'de reconocimiento', 'práctica', 'de prueba', 'de careo',
            'práctica', 'de prueba', 'de reconstrucción', 'práctica', 'de prueba',
            'de inspectción ocular', 'práctica', 'de prueba', 'cientifico', 'práctica',
            'de prueba', 'tecnológica', 'práctica', 'de prueba', 'digital', 'práctica',
            'de prueba', 'electrónica', 'práctica', 'de prueba', 'testimonio', 'práctica',
            'de prueba', 'declaratoria', 'práctica', 'de prueba', 'declaración', 'práctica',
            'de prueba', 'declaración de parte', 'práctica', 'de prueba', 'declaración',
            'de testigo', 'práctica', 'de prueba', 'declaración', 'de experto', 'práctica',
            'de prueba', 'declaración', 'de imputado', 'práctica', 'de prueba', 'declaración',
            'de víctima', 'práctica', 'de prueba', 'declaración', 'de ofendido', 'práctica',
            'de prueba', 'declaración', 'de agraviado', 'práctica', 'de prueba',
            'conclusión', 'conclusión de la investigación', 'conclusión del proceso',
            'conclusión de la instruccion', 'conclusión', 'del procedimiento', 'cierre',
            'cierre de la investigación', 'cierre del proceso', 'archivo', 'archivo',
            'temporal', 'archivo', 'definitivo', 'archivo', 'por no ejercicio', 'archivo',
            'por prescripción', 'archivo', 'por muerte', 'archivo', 'por amnistia',
            'archivo', 'por indulto', 'sobreseimiento', 'sobreseimiento provisional',
            'sobreseimiento definitivo', 'sobreseimiento por', 'sobreseimiento', 'por',
            'insuficiencia', 'sobreseimiento', 'por no', 'sobreseimiento', 'por дело',
            'sobreseimiento', 'por no', 'sobreseimiento', 'por дело', 'sobreseimiento',
            'por atipicidad', 'sobreseimiento', 'por muerte', 'sobreseimiento', 'por',
            'amnistía', 'sobreseimiento', 'por prescripción', 'sobreseimiento', 'por',
            'extinción', 'sobreseimiento', 'por', 'cosajuzgada', 'sobreseimiento', 'por',
            'transacción', 'sobreseimiento', 'por', 'conciliación', 'sobreseimiento',
            'por', 'acuerdo', 'sobreseimiento', 'por', 'perdon', 'sobreseimiento',
            'por', 'desistimiento', 'sobreseimiento', 'por', 'abandono', 'sobreseimiento',
            'por', 'perención', 'sobreseimiento', 'libre', 'absolución', 'absolución',
            'de la imputación', 'absolución', 'por', 'inimputabilidad', 'absolución',
            'por', 'atipicidad', 'absolución', 'por', 'inexistencia', 'del hecho',
            'absolución', 'por', 'falta', 'de', 'prueba', 'absolución', 'por', 'presunción',
            'de', 'inocencia', 'absolución', 'por', 'cosa', 'juzgada', 'absolución',
            'por', 'instancia', 'de', 'parte', 'absolución', 'por', 'falta', 'de',
            'legitimación', 'absolución', 'por', 'falta', 'de', 'interés', 'absolución',
            'por', 'transacción', 'absolución', 'por', 'conciliación', 'absolución',
            'por', 'acuerdo', 'absolución', 'por', 'perdon', 'absolución', 'por',
            'desistimiento', 'condena', 'condena', 'a', 'pena', 'de', 'prisión',
            'condena', 'a', 'pena', 'de', 'multa', 'condena', 'a', 'pena', 'de',
            'trabajo', 'condena', 'a', 'pena', 'de', 'servicio', 'condena', 'a',
            'pena', 'de', 'prohibición', 'condena', 'a', 'pena', 'de', 'inhabilitación',
            'condena', 'a', 'pena', 'de', 'destitución', 'condena', 'a', 'pena', 'de',
            'expulsión', 'condena', 'a', 'pena', 'de', 'suspensión', 'condena', 'a',
            'pena', 'de', 'remisión', 'condena', 'condena', 'condenatoria', 'sentencia',
            'condenatoria', 'sentencia', 'absolutoria', 'sentencia', 'mixta', 'sentencia',
            'definitiva', 'sentencia', 'interlocutoria', 'sentencia', 'provisional',
            'sentencia', 'parcial', 'sentencia', 'total', 'sentencia', 'parcial', 'sentencia',
            'completa', 'sentencia', 'firmada', 'sentencia', 'ejecutoriada', 'sentencia',
            'recaída', 'fallo', 'fallo', 'condenatorio', 'fallo', 'absolutm', 'fallo',
            'mixto', 'veredicto', 'veredicto', 'de culpabilidad', 'veredicto', 'de',
            'inocencia', 'veredicto', 'de', 'no', 'culpable', 'veredicto', 'de', 'culpable',
            'veredicto', 'de', 'no', 'culpable', 'por', 'razón', 'de', 'derecho',
            'veredicto', 'de', 'culpable', 'por', 'razón', 'de', 'hecho', 'veredicto',
            'de', 'no', 'culpable', 'por', 'insuficiencia', 'de', 'prueba', 'veredicto',
            'de', 'no', 'culpable', 'por', 'duda', 'veredicto', 'de', 'no', 'culpable',
            'por', 'presunción', 'de', 'inocencia', 'veredicto', 'de', 'no', 'culpable',
            'por', 'cosa', 'juzgada', 'decision', 'decisión', 'jurisdiccional', 'decision',
            'judicial', 'decision', 'procesal', 'decision', 'de', 'juicio', 'decision',
            'de', 'proceso', 'decision', 'de', 'procedimiento', 'decision', 'de', 'trámite',
            'decision', 'de', 'medida', 'decision', 'de', 'prueba', 'decision', 'de',
            'sanción', 'decision', 'de', 'pena', 'decision', 'de', 'sentencia', 'decision',
            'de', 'fallo', 'decision', 'de', 'veredicto', 'decision', 'de', 'absolución',
            'decision', 'de', 'condena', 'decision', 'de', 'sobreseimiento', 'decision',
            'de', 'archivo', 'decision', 'de', 'continuación', 'decision', 'de', 'suspensión',
            'decision', 'de', 'interrupción', 'decision', 'de', 'terminación', 'decision',
            'de', 'cierre', 'decision', 'de', 'extinción', 'decision', 'de', 'prescripción',
            'decision', 'de', 'caducidad', 'decision', 'de', 'perención', 'decision',
            'de', 'desistimiento', 'decision', 'de', 'abandono', 'decision', 'de',
            'transacción', 'decision', 'de', 'conciliación', 'decision', 'de', 'acuerdo',
            'decision', 'de', 'perdon', 'decision', 'de', 'remisión', 'decision', 'de',
            'amnistía', 'decision', 'de', 'indulto', 'decision', 'de', 'gracia', 'decision',
            'de', 'indulgencia', 'decision', 'de', 'rehabilitación', 'decision', 'de',
            'restablecimiento', 'decision', 'de', 'restauración', 'decision', 'de',
            'recuperación', 'decision', 'de', 'reinserción', 'decision', 'de', 'reintegración',
            'decision', 'de', 'resocialización', 'decision', 'de', 'readaptación', 'decision',
            'de', 'readaptación', 'social', 'decision', 'de', 'rehabilitación', 'social',
            'decision', 'de', 'reinserción', 'social', 'decision', 'de', 'reintegración',
            'social', 'decision', 'de', 'resocialización', 'decision', 'de', 'readaptación',
            'social', 'decision', 'de', 'régimen', 'semiabierto', 'decision', 'de', 'régimen',
            'abierto', 'decision', 'de', 'régimen', 'cerrado', 'decision', 'de', 'libertad',
            'condicional', 'decision', 'de', 'libertad', 'provisional', 'decision', 'de',
            'libertad', 'vigilada', 'decision', 'de', 'suspensión', 'condicional', 'de',
            'la', 'pena', 'decision', 'de', 'suspensión', 'condicional', 'del', 'procedimiento'
        ],
        'palabras_excluyentes': ['trabajo', 'laboral', 'civil', 'matrimonio', 'contrato']
    }
}

def normalizar_texto(texto: str) -> str:
    """Normaliza texto: minúsculas, elimina puntuación y acentos."""
    if not texto:
        return ""
    texto = texto.lower()
    acentos = 'áéíóúüàèìòù'
    sin_acentos = 'aeiouuaeiou'
    replacements = str.maketrans(acentos, sin_acentos)
    texto = texto.translate(replacements)
    texto = texto.translate(str.maketrans("", "", string.punctuation))
    return texto

def extraer_texto_de_articulo(articulo: dict) -> str:
    """Extrae todo el texto relevante de un artículo."""
    textos = []
    
    if articulo.get('texto_general'):
        textos.append(articulo['texto_general'])
    
    for fraccion in articulo.get('fracciones', []):
        if fraccion.get('texto_general'):
            textos.append(fraccion['texto_general'])
        for inciso in fraccion.get('incisos', []):
            if inciso.get('texto_general'):
                textos.append(inciso['texto_general'])
    
    for inciso in articulo.get('incisos_directos', []):
        if inciso.get('texto_general'):
            textos.append(inciso['texto_general'])
    
    return ' '.join(textos)

def cargar_y_analizar_json(ruta: Path) -> Tuple[str, Dict[str, int], List[str]]:
    """Carga un JSON y devuelve: nombre, contador de palabras, textos completos."""
    nombre = ruta.stem.replace('_estructurado', '')
    
    with open(ruta, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    
    contador = Counter()
    todos_textos = []
    
    for articulo in datos:
        texto_completo = extraer_texto_de_articulo(articulo)
        if texto_completo:
            todos_textos.append(texto_completo)
            texto_normalizado = normalizar_texto(texto_completo)
            palabras = texto_normalizado.split()
            palabras_filtradas = [p for p in palabras if p not in STOPWORDS and len(p) > 2]
            contador.update(palabras_filtradas)
    
    return nombre, contador, todos_textos

def construir_diccionario_legal() -> Dict[str, Dict]:
    """Construye un diccionario de palabras clave por normativa desde los JSON."""
    resultado = {}
    
    archivos = list(RUTA_STRUCTURED.glob('*_estructurado.json'))
    
    for ruta in archivos:
        nombre, contador, textos = cargar_y_analizar_json(ruta)
        
        palabras_top = [palabra for palabra, _ in contador.most_common(200)]
        
        resultado[nombre] = {
            'palabras_frecuentes': palabras_top,
            'conteo_total': len(textos),
            'palabras_unicas': len(contador),
            'top_50': dict(contador.most_common(50))
        }
        
        print(f"  - {nombre}: {len(textos)} artículos, {len(contador)} palabras únicas")
    
    return resultado

def detectar_area_legal(consulta: str) -> Optional[str]:
    """
    Detecta el área legal más probable basada en palabras clave.
    Retorna el nombre del área o None si no hay detección clara.
    """
    consulta_norm = normalizar_texto(consulta)
    consulta_palabras = set(consulta_norm.split())
    
    # Palabras que NO son legales (indican consulta no legal)
    PALABRAS_NO_LEGALES = {
        'cocina', 'receta', 'cocinar', 'cocinado', 'cocinado', 'cociner',
        'psicologia', 'psicologico', 'mente', 'mental', 'emocion',
        'cocina', 'comida', 'alimento', 'gastronomia', 'gourmet',
        'recetario', 'chef', 'cocinero', 'ingrediente', 'preparacion',
        'futbol', 'deporte', 'ejercicio', 'salud', 'ejercicio',
        'tecnologia', 'computadora', 'celular', 'internet',
        'musica', 'pelicula', 'libro', 'entretenimiento',
        'viaje', 'vacaciones', 'turismo', 'hotel',
        'moda', 'ropa', 'vestimenta', 'estilo',
        'amor', 'relacion', 'pareja', 'amigo',
    }
    
    # Verificar si la consulta tiene palabras no legales dominantes
    palabras_no_legales = consulta_palabras.intersection(PALABRAS_NO_LEGALES)
    
    PRIORIDADES = {
        'penal': 10,
        'laboral': 15,  # Aumentado para priorizar laboral
        'civil': 10,
        'constitucional': 5,
        'procesal_penal': 2,
        'procesal_civil': 2
    }
    
    mejores_puntuaciones = {}
    total_palabras = len(consulta_palabras)
    
    for area, datos in PALABRAS_CLAVE_POR_AREA.items():
        palabras_clave = set(normalizarizarTexto(p) for p in datos['alta_prioridad'])
        palabras_excluyentes = set(normalizarizarTexto(p) for p in datos.get('palabras_excluyentes', []))
        
        coincidencias = consulta_palabras.intersection(palabras_clave)
        exclusiones = consulta_palabras.intersection(palabras_excluyentes)
        
        # Calcular proporción de palabras legales
        if total_palabras > 0:
            proporcion_legal = len(coincidencias) / total_palabras
        else:
            proporcion_legal = 0
        
        # Penalizar si hay muchas palabras no legales
        penalizacion_no_legales = len(palabras_no_legales) * 5
        
        puntuacion = (len(coincidencias) * PRIORIDADES.get(area, 1) - 
                      len(exclusiones) * 3 - 
                      penalizacion_no_legales)
        
        if coincidencias:
            mejores_puntuaciones[area] = {
                'puntuacion': puntuacion,
                'coincidencias': list(coincidencias),
                'exclusiones': list(exclusiones),
                'proporcion_legal': proporcion_legal
            }
    
    if not mejores_puntuaciones:
        return None
    
    area_detectada = max(mejores_puntuaciones.items(), key=lambda x: x[1]['puntuacion'])
    
    # Verificar que la puntuación sea significativa
    if area_detectada[1]['puntuacion'] <= 0:
        return None
    
    # Verificar proporción mínima de palabras legales
    if area_detectada[1]['proporcion_legal'] < 0.1 and len(palabras_no_legales) > 0:
        return None  # Probably not a legal query
    
    return area_detectada[0]

def normalizarizarTexto(texto):
    """Alias para normalizar texto."""
    return normalizar_texto(texto)

def mapear_area_a_documento(area: str, documentos_disponibles: List[str]) -> Optional[str]:
    """Mapea el área detectada al documento disponible más similar."""
    mapeo_area_documento = {
        'laboral': [
            ('ley trabajo', 10),
            ('trabajo', 8),
            ('federal del trabajo', 9),
        ],
        'penal': [
            ('código penal', 10),
            ('codigo penal', 10),
            ('penal', 5),
        ],
        'civil': [
            ('código civil', 10),
            ('codigo civil', 10),
            ('civil', 5),
        ],
        'constitucional': [
            ('constitucion', 10),
            ('constitucional', 8),
        ],
        'procesal_civil': [
            ('procedimiento civil', 10),
            ('procesal civil', 8),
        ],
        'procesal_penal': [
            ('procedimiento penal', 10),
            ('procesal penal', 8),
        ]
    }
    
    terminos_busqueda = mapeo_area_documento.get(area, [])
    
    mejor_doc = None
    mejor_puntuacion = -1
    
    for doc in documentos_disponibles:
        doc_norm = doc.lower()
        for termino, prioridad in terminos_busqueda:
            if termino in doc_norm and prioridad > mejor_puntuacion:
                mejor_doc = doc
                mejor_puntuacion = prioridad
    
    return mejor_doc

def detectar_normativa(consulta: str, documentos_disponibles: List[str]) -> Tuple[Optional[str], dict]:
    """
    Detecta la normativa más probable para una consulta.
    Retorna: (documento_filtrado, info_deteccion)
    """
    area = detectar_area_legal(consulta)
    
    if not area:
        return None, {'area': None, 'mensaje': 'No se detectó área específica'}
    
    documento = mapear_area_a_documento(area, documentos_disponibles)
    
    if not documento:
        return None, {'area': area, 'mensaje': f'Área "{area}" detectada pero sin documento disponible'}
    
    return documento, {'area': area, 'documento': documento}

def analizar_coherencia_consulta(consulta: str) -> Tuple[bool, List[str]]:
    """
    Analiza si una consulta tiene coherencia mínima.
    Retorna: (es_coherente, lista_de_sugerencias)
    """
    sugerencias = []
    consulta_norm = normalizar_texto(consulta)
    palabras = consulta_norm.split()
    
    if len(palabras) < 2:
        return False, ["La consulta es muy corta. Añade más contexto."]
    
    if len(palabras) == 1:
        return False, ["Añade más palabras para describir tu situación."]
    
    palabras_con_significado = [p for p in palabras if p not in STOPWORDS and len(p) > 3]
    
    if len(palabras_con_significado) == 0:
        return False, [
            "Tu consulta solo contiene palabras muy comunes.",
            "Intenta añadir términos más específicos sobre tu situación legal.",
            "Por ejemplo: en lugar de 'ayuda', especifica 'necesito ayuda con despido injustificado'"
        ]
    
    if len(palabras_con_significado) < 2:
        return True, ["Tu consulta es un poco vaga, pero intentaremos ayudarte."]
    
    tiene_palabras_legales = any(
        p in consulta_norm for p in [
            'ley', 'artículo', 'articulo', 'derecho', 'legal', 'demanda', 
            'juicio', 'proceso', 'penal', 'civil', 'laboral', 'contrato',
            'delito', 'crimen', 'robo', 'herencia', 'divorcio', 'despido',
            'salario', 'empleo', 'trabajador', 'patrón', 'demandante', 'demandado'
        ]
    )
    
    if not tiene_palabras_legales:
        sugerencias.append(
            "Tu consulta no parece relacionada con temas legales. "
            "Si es así, intenta añadir más contexto sobre tu situación."
        )
    
    return True, sugerencias if sugerencias else ["Consulta procesable."]

def generar_consulta_corregida(consulta: str) -> str:
    """
    Intenta mejorar una consulta poco coherente.
    """
    es_coherente, sugerencias = analizar_coherencia_consulta(consulta)
    
    if es_coherente:
        return consulta
    
    consulta_norm = normalizar_texto(consulta)
    palabras = consulta_norm.split()
    
    palabras_vagas = {'ayuda', 'problema', 'cosa', 'asunto', 'situacion', 'favor', 'por favor', 'hola', 'buenos', 'dias', 'tardes', 'noches'}
    
    palabras_significativas = [p for p in palabras if p not in STOPWORDS and p not in palabras_vagas and len(p) > 3]
    
    if not palabras_significativas:
        return consulta
    
    return consulta

def obtener_palabras_clave_por_area(area: str) -> List[str]:
    """Obtiene las palabras clave para un área legal específica."""
    return PALABRAS_CLAVE_POR_AREA.get(area, {}).get('alta_prioridad', [])

if __name__ == "__main__":
    print("="*60)
    print("ANALIZADOR LEGAL - Lexis")
    print("="*60)
    print("\nConstruyendo diccionario de palabras clave...")
    
    diccionario = construir_diccionario_legal()
    
    print("\n" + "="*60)
    print("PRUEBA DE DETECCIÓN DE ÁREAS LEGALES")
    print("="*60)
    
    pruebas = [
        "fui despedida injustificadamente y no me quisieron pagar mi liquidación",
        "me robaron mi coche y quiero denunciar",
        "mi vecino no me quiere pagar el alquiler",
        "tengo un problema con mi contrato de arrendamiento",
        "mi esposo quiere el divorcio y me amenaza"
    ]
    
    for consulta in pruebas:
        print(f"\nConsulta: '{consulta}'")
        area = detectar_area_legal(consulta)
        print(f"  Área detectada: {area}")
        
        if area:
            palabras = obtener_palabras_clave_por_area(area)[:10]
            print(f"  Palabras clave: {', '.join(palabras)}")
