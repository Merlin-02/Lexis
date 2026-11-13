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
            'tiempo extra', 'sobretiempo', 'hora extra', 'horas extras', 'prestaciones', 'beneficio', 'regimen',
            'ley federal del trabajo', 'lft', 'ctm', 'cmg', 'servicio', 'prestador',
            'dependencia', 'subordinación', 'subordinacion', 'dirección', 'organización',
            'inspección', 'vistoria', 'multa', 'sanción', 'infracción', 'reclamación',
            'laudo', 'conciliación laboral', 'tribunal laboral', 'centro de conciliación',
            'laboraba', 'empleo', 'empleando', 'renuncia', 'renunciar', 'renuncie', 'vacante', 'jefe',
            'gerente', 'supervisor', 'encargado', 'patronal', 'empresa',
            'salario', 'sueldo', 'remuneración', 'discriminación laboral',
            'embarazada', 'hostigamiento laboral', 'acoso laboral',
            'ambiente laboral', 'clima laboral', 'mobbing'
        ],
        'palabras_excluyentes': ['penal', 'delito', 'robo', 'asalto', 'homicidio', 'asesinato',
            'civil', 'matrimonio', 'herencia', 'testamento', 'divorcio', 'custodia',
            'adopción', 'adopcion', 'adoptado', 'adoptada', 'adoptante', 'adoptar', 'patria potestad', 'tutela']
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
            'caución', 'fianza', 'cumplimiento', 'suspensión', 'condicional', 'beneficio',
            'remisión', 'perdón', 'gracia', 'indulto', 'amnistía', 'excarcelación',
            'libertad condicional', 'régimen', 'semiabierto', 'abierto',
            'victimario', 'agresor', 'denunciante', 'demanda', 'actuación',
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
            'inocencia', 'dubio', 'in dubio pro reo', 'non bis in idem', 'cosa juzgada',
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
            'caducidad', 'término', 'plazo', 'condición', 'modalidad', 'carga',
            'onus', 'prueba', 'presunción', 'ficción', 'excepción', 'defensa', 'acción',
            'juicio', 'proceso', 'procedimiento', 'sentencia', 'laudo', 'litis',
            'parte', 'demandante', 'demandado', 'tercero', 'interesado', 'legítimo',
            'representante', 'apoderado', 'mandatario', 'tutor', 'curador', 'albacea',
            'heredero', 'legatario', 'testador', 'testamento', 'sucesión', 'herencia',
            'legítima', 'mejora', 'donación', 'entre vivos', 'mortis causa', 'codicilo',
            'matrimonio', 'divorcio', 'divorciarme', 'divorciar', 'concubinato', 'unión', 'pareja', 'filiación',
            'paternidad', 'maternidad', 'adopción', 'adopcion', 'adoptado', 'adoptada', 'adoptante', 'adoptar',
            'revocación de la adopción', 'revocar adopción', 'tutela', 'patria potestad',
            'casa', 'vivienda', 'inmueble', 'departamento', 'terreno', 'lote',
            'propiedad', 'posesión', 'usufructo', 'servidumbre', 'derecho de paso', 'medidor',
            'luz', 'agua', 'servicios', 'servicio público', 'servicios públicos',
            'obligación alimentaria', 'pensión', 'alimenticia', 'alimentos', 'menor', 'incapaz', 'interdicción',
            'embargo', 'medida', 'cautelar', 'provisional', 'precautelar',
            'anexión', 'anexo', 'documento', 'escritura', 'pública', 'protocolo',
            'notario', 'registro', 'inscripción', 'matrícula', 'folio', 'real',
            'hipoteca', 'gravamen', 'liminación', 'cancelación',
            'usucapión', 'prescripción adquisitiva', 'dominio', 'tenencia',
            'arrendamiento', 'renta', 'inquilino', 'arrendador', 'subarrendamiento',
            'comodato', 'préstamo', 'prestamo', 'mutuo', 'depósito', 'deposito', 'mandato',
            'gestión', 'representación', 'sociedad', 'asociación', 'fundación',
            'corporación', 'comercio', 'mercantil', 'letra', 'cambio',
            'cheque', 'pagaré', 'pagare', 'factura', 'conciliación', 'transacción',
            'renuncia', 'remisión', 'compromiso', 'arbitraje', 'jurisdicción', 'voluntad',
            'autonomía', 'privada', 'orden público', 'buenas costumbres', 'moralidad',
            'ilegal', 'ilícito', 'inmoral', 'contravención', 'infracción', 'sanción',
            'indemnización', 'indemnizar', 'daño', 'perjuicio', 'lucro', 'cesante', 'daño moral',
            'responsabilidad', 'contractual', 'extracontractual', 'objetiva',
            'subjetiva', 'directo', 'indirecto', 'consecuencial', 'eximente', 'exculpante',
            'culpa', 'negligencia', 'impericia', 'imprudencia', 'dolo', 'caso fortuito',
            'fuerza mayor', 'hecho', 'propio', 'ajeno', 'causa', 'efecto',
            'relación', 'causal', 'imputación', 'atribución', 'imputabilidad',
            'capacidad', 'capacidad de goce', 'capacidad de ejercicio',
            'mayoría', 'edad', 'emancipación', 'interdicto', 'sonámbulo',
            'borracho', 'drogadicto', 'locura', 'demencia', 'enfermedad', 'mental',
            'incapacidad', 'inhabilitación', 'suspensión', 'quiebra', 'concurso',
            'insolvencia', 'beneficio', 'limitación', 'excarcelación',
            'prisión', 'extraterritorialidad', 'exención', 'privilegio', 'prerrogativa', 'inmunidad',
            'domicilio', 'residencia', 'vecindad', 'nacionalidad', 'ciudadanía', 'extranjero',
            'apátrida', 'refugiado', 'migrante', 'indocumentado', 'visado', 'visa',
            'pasaporte', 'identificación', 'identidad', 'nombre', 'pseudónimo',
            'alias', 'seudónimo', 'renombre', 'firma', 'rúbrica', 'signo', 'marca',
            'logo', 'emblema', 'distintivo', 'denominación', 'razón social',
            'social', 'objeto', 'sede', 'representante legal',
            'poder', 'facultad', 'competencia', 'función',
            'cargo', 'empleo', 'puesto', 'oficio', 'profesión', 'ocupación', 'actividad',
            'industria', 'servicio', 'empresa', 'establecimiento', 'local',
            'negocio', 'oficina', 'despacho', 'consultorio', 'taller', 'fábrica',
            'máquina', 'herramienta', 'instrumento', 'utensilio', 'materia', 'prima',
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
            'ley fundamental', 'ley suprema', 'ley marco', 'ley orgánica', 'ley ordinaria',
            'ley delegada', 'ley habilitante', 'decreto ley', 'decreto legislativo',
            'decreto gubernamental', 'reglamentario', 'oficio',
            'instructivo', 'directriz', 'guía', 'protocolo', 'procedimiento',
            'técnica', 'estándar', 'especificación', 'requisito', 'condición', 'elemento',
            'factor', 'aspecto', 'particular', 'universal', 'absoluto', 'relativo',
            'pleno', 'parcial', 'total', 'global', 'integral', 'completo', 'exhaustivo',
            'exclusivo', 'incluyente', 'excluyente', 'abierto', 'cerrado', 'limitado',
            'ilimitado', 'finito', 'infinito', 'permanente', 'temporal', 'transitorio',
            'provisional', 'definitivo', 'irrevocable', 'revocable', 'renunciable',
            'indisponible', 'disponible', 'transferible', 'intransferible', 'cesible',
            'incesible', 'transmisible', 'intransmisible', 'divisible', 'indivisible',
            'separable', 'inseparable', 'accesible', 'inaccesible', 'abordable',
            'inabordable', 'lícito', 'ilícito', 'legal', 'ilegal', 'legítimo', 'ilegítimo',
            'inconstitucional', 'convencional', 'inconvencional',
            'irregular', 'anormal', 'típico',
            'atípico', 'regular', 'anexo', 'adicional', 'complementario',
            'modificatorio', 'derogatorio', 'abrogatorio', 'refundido', 'compilado'
        ],
        'palabras_excluyentes': []
    },
    'procesal_civil': {
        'alta_prioridad': [
            'procesal', 'procedimiento', 'proceso', 'juicio', 'tramite', 'trámite', 'tramitar', 'tramitará',
            'revocación de la adopción', 'adopción', 'adoptado', 'adoptante', 'diligencia',
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
            'apelación', 'revisión', 'amparo', 'queja', 'denuncia', 'querella',
            'acusación', 'cargo', 'imputación', 'atribución', 'tipificación', 'calificación',
            'delito', 'falta', 'infracción', 'sanción', 'pena', 'multa', 'cárcel',
            'prisión', 'reclusión', 'arresto', 'detención', 'custodia', 'arraigo',
            'medida', 'cautelar', 'provisional', 'precautoria', 'aseguramiento', 'embargo',
            'secuestro', 'incautación', 'decomiso', 'confiscación', 'exhibición',
            'presentación', 'intimación', 'citación', 'notificación', 'emplazamiento',
            'convocatoria', 'llamamiento', 'invitación', 'requerimiento', 'exhorto',
            'comisión', 'despacho', 'orden', 'mandamiento', 'auto', 'sentencia', 'laudo',
            'plazo', 'fallo', 'veredicto', 'resolución', 'decreto', 'proveído', 'dictamen',
            'voto', 'mayoría', 'disidencia', 'opinión', 'razón', 'considerando',
            'resultando', 'antecedente', 'hecho', 'fundamento', 'derecho', 'motivos',
            'dispositivo', 'definitiva', 'interlocutoria',
            'parcial', 'total', 'absoluta', 'condenatoria', 'absolutoria',
            'mixta', 'incidente', 'cuestión', 'tema', 'punto', 'objeto',
            'pretensión', 'reclamación', 'petitum', 'pedimento', 'solicitud', 'petición',
            'gestión', 'instancia', 'expediente', 'expediente judicial', 'carpeta',
            'legajo', 'tomo', 'folio', 'foja', 'documento', 'acta', 'constancia',
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
        'palabras_excluyentes': ['penal', 'delito', 'trabajo', 'laboral', 'pagar', 'pago']
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
            'crimen', 'infracción', 'falta', 'contravención', 'ilícito', 'ilegal',
            'infracción penal', 'hecho', 'hecho delictivo', 'conducta', 'acción',
            'omisión', 'comisión', 'participación', 'autoría', 'coautoría', 'complicidad',
            'instigación', 'concierto', 'asociación', 'banda', 'organización',
            'organizado', 'elemento', 'objetivo', 'subjetivo', 'tipo', 'tipo penal',
            'tipicidad', 'atipicidad', 'conglobación', 'consumación', 'tentativa',
            'conato', 'fracaso', 'abandono', 'desistimiento', 'voluntario', 'involuntario',
            'imposibilidad', 'facticidad', 'error', 'error de tipo', 'error de prohibición',
            'error de comprensión', 'inimputabilidad', 'imputabilidad', 'dolo', 'culpa',
            'imprudencia', 'negligencia', 'impericia', 'conocimiento', 'voluntad',
            'ánimo', 'ánimo de lucro', 'ánimo de causar', 'ánimo de defraudar', 'ánimo de poseer',
            'animus', 'corpus', 'corpus delicti', 'cuerpo', 'cuerpo del delito', 'cosa',
            'cosa juzgada', 'cosa litigiosa', 'cosa prometida', 'cosa mueble', 'cosa inmueble',
            'cosa fungible', 'cosa infungible', 'cosa consumible', 'cosa principal',
            'cosa accesoria', 'cosa aneja', 'cosa incidente', 'cosa adhesiva',
            'prueba', 'prueba testimonial', 'prueba pericial', 'prueba documental',
            'prueba de inspección', 'prueba de reconocimiento', 'prueba de careo',
            'prueba de inteligencia', 'prueba científica', 'prueba tecnológica',
            'prueba digital', 'prueba electrónica', 'prueba hemática', 'prueba genética',
            'prueba de adn', 'prueba de huella', 'prueba dactilar', 'prueba fotográfica',
            'prueba videográfica', 'prueba auditiva', 'prueba de sonido',
            'presunción', 'presunción de inocencia', 'presunción de veracidad',
            'iuris', 'presunción iuris tantum', 'presunción iuris et de iure', 'indicio',
            'medida', 'cautelar', 'medida preventiva', 'medida provisional', 'medida asegurativa',
            'medida aseguratoria', 'detención', 'detención preventiva', 'detención domiciliaria',
            'prisión', 'prisión preventiva', 'prisión preventiva oficiosa',
            'justificada', 'prisión preventiva domiciliaria', 'arresto', 'arresto domiciliario',
            'arresto nocturno', 'reclusión', 'reclusión temporal', 'reclusión perpetua',
            'internamiento', 'internamiento preventivo', 'internamiento definitivo',
            'custodia', 'custodia preventiva',
            'embargo', 'embargo preventivo', 'embargo de bienes', 'embargo de salarios',
            'embargo de cuentas', 'embargo de propiedades', 'secuestro', 'secuestro preventivo',
            'secuestro de bienes', 'incautación', 'incautación preventiva', 'decomiso',
            'decomiso de bienes', 'decomiso de instrumentos', 'decomiso de productos',
            'decomiso de ganancias', 'decomiso extendido', 'decomiso sin condena',
            'inmovilización', 'inmovilización de vehículos', 'inmovilización de cuentas',
            'inmovilización de activos', 'inmovilización de bienes',
            'fianza', 'fianza de radicar', 'fianza de presentación',
            'caución', 'caución de radicar', 'caución de no huir', 'caución de evitar',
            'caución pecuniaria', 'libertad', 'libertad provisional', 'libertad condicional',
            'libertad bajo fianza', 'libertad bajo protesta',
            'libertad vigilada', 'libertad restringida', 'libertad controlada',
            'trabajo comunitario', 'trabajo social',
            'servicio comunitario', 'fin de semana', 'multa',
            'pecuniaria', 'sanción', 'sanción pecuniaria', 'sanción restrictiva',
            'suspensión', 'suspensión condicional', 'suspensión de derechos',
            'suspensión de funciones', 'suspensión de cargo', 'suspensión de actividad',
            'inhabilitación', 'inhabilitación temporal', 'inhabilitación perpetua',
            'inhabilitación de derechos', 'inhabilitación de funciones', 'destitución',
            'destitución de cargo', 'destitución de función', 'expulsión',
            'extranjería', 'extranjero', 'carta de naturaleza',
            'carta de ciudadanía', 'carta de residencia',
            'perdón', 'perdón del ofendido', 'perdón judicial', 'amnistía',
            'indulto', 'indulto particular', 'indulto general', 'gracia',
            'indulgencia', 'remisión', 'remisión de pena', 'remisión condicional',
            'rehabilitación', 'rehabilitación civil', 'rehabilitación judicial',
            'prescripción', 'prescripción de la acción',
            'prescripción de la pena', 'prescripción extintiva', 'prescripción adquisitiva',
            'caducidad', 'caducidad de la acción', 'caducidad del derecho', 'perención',
            'perención de la instancia', 'perención del proceso',
            'abandono de la acción', 'abandono del proceso',
            'desistimiento de la acción', 'desistimiento del querellante', 'desistimiento del acusador',
            'transacción', 'conciliación', 'acuerdo',
            'acuerdo reparatorio', 'acuerdo conciliatorio', 'procedimiento abreviado',
            'procedimiento ordinario', 'procedimiento especial',
            'procedimiento sumario', 'procedimiento sumarísimo',
            'trámite ordinario', 'trámite extraordinario', 'trámite urgente', 'trámite preferente',
            'trámite diferido', 'audiencia preliminar',
            'audiencia intermedia', 'audiencia de juicio', 'audiencia de lectura',
            'audiencia de individualización', 'audiencia de veredicto',
            'audiencia de alegatos', 'audiencia de conclusiones',
            'audiencia de vista', 'audiencia pública', 'audiencia privada',
            'audiencia a puerta cerrada', 'audiencia remota', 'audiencia virtual',
            'audiencia presencial', 'audiencia híbrida',
            'práctica de prueba', 'práctica de diligencia', 'práctica de actuación',
            'inspección ocular', 'declaración de parte', 'declaración de testigo',
            'declaración de perito', 'declaración de imputado', 'declaración de víctima',
            'declaración de ofendido', 'conclusión de la investigación', 'conclusión del proceso',
            'conclusión de la instrucción', 'cierre de la investigación', 'cierre del proceso',
            'archivo temporal', 'archivo definitivo', 'no ejercicio de la acción penal',
            'sobreseimiento', 'sobreseimiento provisional', 'sobreseimiento definitivo',
            'sobreseimiento por atipicidad', 'sobreseimiento por muerte',
            'sobreseimiento por amnistía', 'sobreseimiento por prescripción',
            'sobreseimiento por extinción', 'sobreseimiento por cosa juzgada',
            'sobreseimiento por perdón', 'sobreseimiento por desistimiento',
            'sobreseimiento libre', 'absolución', 'absolución de la imputación',
            'absolución por inimputabilidad', 'absolución por atipicidad',
            'absolución por inexistencia del hecho', 'absolución por falta de prueba',
            'absolución por presunción de inocencia', 'condena', 'pena de prisión',
            'pena de multa', 'sentencia condenatoria', 'sentencia absolutoria',
            'sentencia mixta', 'sentencia definitiva', 'sentencia interlocutoria',
            'sentencia provisional', 'sentencia firme', 'sentencia ejecutoriada',
            'fallo condenatorio', 'fallo absolutorio', 'fallo mixto',
            'veredicto', 'veredicto de culpabilidad', 'veredicto de inocencia',
            'decisión jurisdiccional', 'decisión judicial', 'decisión procesal',
            'reinserción social', 'rehabilitación social', 'readaptación social',
            'régimen semiabierto', 'régimen abierto', 'régimen cerrado',
            'suspensión condicional de la pena', 'suspensión condicional del procedimiento'
        ],
        'palabras_excluyentes': ['trabajo', 'laboral', 'civil', 'matrimonio', 'contrato', 'salario', 'pagar', 'pago']
    }
}

def normalizar_texto(texto: str) -> str:
    """Normaliza texto: minúsculas, elimina puntuación y acentos."""
    if not texto:
        return ""
    texto = texto.lower()
    acentos = 'áéíóúüàèìòùñ'
    sin_acentos = 'aeiouuaeioun'
    replacements = str.maketrans(acentos, sin_acentos)
    texto = texto.translate(replacements)
    texto = texto.translate(str.maketrans("", "", string.punctuation + "¡¿«»“”‘’—"))
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
        'laboral': 7,
        'penal': 7,
        'civil': 7,
        'procesal_civil': 6,
        'procesal_penal': 6,
        'constitucional': 5
    }
    
    mejores_puntuaciones = {}
    total_palabras = len(consulta_palabras)
    
    for area, datos in PALABRAS_CLAVE_POR_AREA.items():
        palabras_clave = list(dict.fromkeys(normalizarizarTexto(p) for p in datos['alta_prioridad']))
        palabras_excluyentes = list(dict.fromkeys(normalizarizarTexto(p) for p in datos.get('palabras_excluyentes', [])))
        
        # Buscar palabras completas o frases con límite de palabra
        coincidencias = set()
        bono_frases = 0
        for kw in palabras_clave:
            if not kw:
                continue
            if ' ' in kw:
                if re.search(r'\b' + re.escape(kw) + r'\b', consulta_norm):
                    coincidencias.add(kw)
                    bono_frases += 3  # Mayor especificidad para frases jurídicas compuestas
            elif kw in consulta_palabras:
                coincidencias.add(kw)
        
        exclusiones = set()
        for kw in palabras_excluyentes:
            if not kw:
                continue
            if ' ' in kw:
                if re.search(r'\b' + re.escape(kw) + r'\b', consulta_norm):
                    exclusiones.add(kw)
            elif kw in consulta_palabras:
                exclusiones.add(kw)
        
        # Calcular proporción de palabras legales
        if total_palabras > 0:
            proporcion_legal = len(coincidencias) / total_palabras
        else:
            proporcion_legal = 0
        
        # Penalizar si hay muchas palabras no legales
        penalizacion_no_legales = len(palabras_no_legales) * 5
        
        puntuacion = (len(coincidencias) * PRIORIDADES.get(area, 1) +
                      bono_frases -
                      len(exclusiones) * 3 - 
                      penalizacion_no_legales)
        
        if coincidencias:
            mejores_puntuaciones[area] = {
                'puntuacion': puntuacion,
                'coincidencias': list(coincidencias),
                'exclusiones': list(exclusiones),
                'proporcion_legal': proporcion_legal,
                'especificidad': sum(len(c) for c in coincidencias)
            }
    
    if not mejores_puntuaciones:
        return None
    
    area_detectada = max(
        mejores_puntuaciones.items(),
        key=lambda x: (x[1]['puntuacion'], len(x[1]['coincidencias']), x[1]['especificidad'])
    )
    
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

ABREVIATURAS_LEGALES = {
    r'\barts?\.\s*': 'artículo ',
    r'\bfracc?\.\s*': 'fracción ',
    r'\binc\.\s*': 'inciso ',
    r'\blft\b': 'Ley Federal del Trabajo',
    r'\bcpeum\b': 'Constitución Política de los Estados Unidos Mexicanos',
    r'\bcc\b': 'Código Civil',
    r'\bcp\b': 'Código Penal',
    r'\bmp\b': 'Ministerio Público',
}


def generar_consulta_corregida(consulta: str) -> str:
    """
    Mejora y normaliza una consulta expandiendo abreviaturas jurídicas
    y depurando muletillas cuando la consulta tiene baja densidad léxica.
    """
    if not consulta or not consulta.strip():
        return consulta

    consulta_expandida = consulta.strip()
    for patron, reemplazo in ABREVIATURAS_LEGALES.items():
        consulta_expandida = re.sub(patron, reemplazo, consulta_expandida, flags=re.IGNORECASE)

    es_coherente, _ = analizar_coherencia_consulta(consulta_expandida)

    palabras_vagas = {
        'ayuda', 'problema', 'cosa', 'asunto', 'situacion', 'situación',
        'favor', 'hola', 'buenos', 'buenas', 'dias', 'días', 'tardes', 'noches',
        'disculpe', 'disculpa', 'oye', 'quisiera', 'necesito'
    }

    tokens_originales = consulta_expandida.split()
    tokens_filtrados = [
        t for t in tokens_originales
        if normalizar_texto(t) not in palabras_vagas
    ]

    if not es_coherente:
        consulta_norm = normalizar_texto(consulta_expandida)
        palabras = consulta_norm.split()
        palabras_significativas = [
            p for p in palabras
            if p not in STOPWORDS and p not in palabras_vagas and len(p) > 2
        ]
        if palabras_significativas:
            return " ".join(palabras_significativas)

    if tokens_filtrados and len(tokens_filtrados) < len(tokens_originales):
        return " ".join(tokens_filtrados)

    return consulta_expandida

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
