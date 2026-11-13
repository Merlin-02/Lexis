import sys
import os
import time
from datetime import datetime
from pathlib import Path

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

DIR_ACTUAL = Path(__file__).resolve().parent
ROOT_DIR = DIR_ACTUAL.parent
sys.path.append(str(DIR_ACTUAL))

load_dotenv(DIR_ACTUAL / ".env", override=True)
load_dotenv(ROOT_DIR / ".env", override=False)

from buscador import (
    inicializar_motores,
    busqueda_hibrida,
    TOP_K_DEFAULT,
    MODELO_NOMBRE
)
from indice_tematico import buscar_por_concepto, detectar_documento
from interaccion import (
    cargar_system_prompt,
    construir_bloque_leyes,
    llamar_groq,
    MAX_FRAGMENTOS
)
from gestor_evaluacion import (
    GestorSesionesEvaluacion,
    generar_dispositivo_id,
    generar_mensaje_id,
    generar_sesion_id,
    obtener_entorno_despliegue,
)
from gestor_usuarios import GestorUsuarios, ROLES_USUARIO

try:
    from analizador_legal import analizar_coherencia_consulta, detectar_normativa
    ANALIZADOR_DISPONIBLE = True
except ImportError:
    ANALIZADOR_DISPONIBLE = False

try:
    from grafo_lexis.integracion_rag import (
        construir_contexto_graphrag,
        obtener_recuperador_grafo,
    )
    from grafo_lexis.visualizador_obsidian import (
        extraer_datos_subgrafo_consulta,
        extraer_datos_cerebro_global,
        generar_html_obsidian,
    )
    GRAPHRAG_DISPONIBLE = True
except ImportError:
    GRAPHRAG_DISPONIBLE = False

st.set_page_config(
    page_title="LEXIS - Asistencia Legal con IA",
    layout="wide"
)

@st.cache_resource(show_spinner="Iniciando motores de búsqueda...")
def preparar_sistema():
    ruta_prompt = ROOT_DIR / "knowledge" / "Prompt.txt"
    sys_prompt = cargar_system_prompt(str(ruta_prompt))
    ruta_db = str(ROOT_DIR / "lexis_vectordb")
    motores = inicializar_motores(ruta_db, MODELO_NOMBRE)
    return sys_prompt, motores

try:
    system_prompt, (
        coleccion,
        motor_bm25,
        modelo_semantico,
        diccionario_textos,
        diccionario_metadatos,
        documentos_disponibles,
        jerarquias_disponibles
    ) = preparar_sistema()
except Exception as err:
    st.error(f"Error inicializando los componentes del backend: {err}")
    st.stop()

if "modo_oscuro" not in st.session_state:
    st.session_state.modo_oscuro = True

if st.session_state.modo_oscuro:
    ruta_logo = ROOT_DIR / "image" / "LogoLexis.png"
    estilos_css = """
    <style>
        .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp span {
            color: #F8FAFC !important;
        }
        .stApp {
            background-color: #0F172A !important;
        }
        [data-testid="stSidebar"], [data-testid="stSidebar"] div {
            background-color: #1E293B !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
            color: #F8FAFC !important;
        }
        button[kind="secondary"] {
            background-color: #334155 !important;
            color: #F8FAFC !important;
            border: 1px solid #475569 !important;
        }
        button[kind="secondary"]:hover {
            background-color: #475569 !important;
            border-color: #64748B !important;
        }
        button[kind="primary"] {
            background-color: #0284C7 !important;
            color: #F8FAFC !important;
            border: 1px solid #38BDF8 !important;
        }
        button[kind="primary"]:hover {
            background-color: #0369A1 !important;
            border-color: #7DD3FC !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #0F172A !important;
            color: #F8FAFC !important;
            border: 1px solid #475569 !important;
        }
        div[data-baseweb="popover"] ul {
            background-color: #1E293B !important;
        }
        div[data-baseweb="popover"] li {
            color: #F8FAFC !important;
        }
        .stChatMessage {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 8px;
        }
        .stChatMessage p, .stChatMessage span, .stChatMessage div {
            color: #F8FAFC !important;
        }
        [data-testid="stExpander"] {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }
        [data-testid="stExpander"] summary {
            background-color: #1E293B !important;
            color: #F8FAFC !important;
        }
        [data-testid="stExpander"] summary svg {
            fill: #F8FAFC !important;
        }
        [data-testid="stExpander"] div, [data-testid="stExpander"] p, [data-testid="stExpander"] li {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
        }
        [data-testid="stBottom"], [data-testid="stBottom"] > div, .stChatFloatingInputContainer {
            background-color: #0F172A !important;
        }
        [data-testid="stChatInput"], 
        [data-testid="stChatInput"] div[data-baseweb="base-input"],
        [data-testid="stChatInput"] > div {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
        }
        [data-testid="stChatInput"] textarea {
            background-color: transparent !important;
            color: #F8FAFC !important;
            -webkit-text-fill-color: #F8FAFC !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: #94A3B8 !important;
            -webkit-text-fill-color: #94A3B8 !important;
        }
    </style>
    """
else:
    ruta_logo = ROOT_DIR / "image" / "LogoLexis2.png"
    estilos_css = """
    <style>
        .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp label, .stApp span {
            color: #0F172A !important;
        }
        .stApp {
            background-color: #F8FAFC !important;
        }
        [data-testid="stSidebar"], [data-testid="stSidebar"] div {
            background-color: #F1F5F9 !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
            color: #0F172A !important;
        }
        button[kind="secondary"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
        }
        button[kind="secondary"]:hover {
            background-color: #E2E8F0 !important;
            border-color: #94A3B8 !important;
        }
        button[kind="primary"] {
            background-color: #0284C7 !important;
            color: #FFFFFF !important;
            border: 1px solid #0369A1 !important;
        }
        button[kind="primary"]:hover {
            background-color: #0369A1 !important;
            border-color: #075985 !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #CBD5E1 !important;
        }
        div[data-baseweb="popover"] ul {
            background-color: #FFFFFF !important;
        }
        div[data-baseweb="popover"] li {
            color: #0F172A !important;
        }
        .stChatMessage {
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px;
        }
        .stChatMessage p, .stChatMessage span, .stChatMessage div {
            color: #0F172A !important;
        }
        [data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 8px !important;
        }
        [data-testid="stExpander"] summary {
            background-color: #F1F5F9 !important;
            color: #0F172A !important;
        }
        [data-testid="stExpander"] summary svg {
            fill: #0F172A !important;
        }
        [data-testid="stExpander"] div, [data-testid="stExpander"] p, [data-testid="stExpander"] li {
            background-color: #FFFFFF !important;
            color: #1E293B !important;
        }
        [data-testid="stBottom"], [data-testid="stBottom"] > div, .stChatFloatingInputContainer {
            background-color: #F8FAFC !important;
        }
        [data-testid="stChatInput"], 
        [data-testid="stChatInput"] div[data-baseweb="base-input"],
        [data-testid="stChatInput"] > div {
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05) !important;
        }
        [data-testid="stChatInput"] textarea {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            -webkit-text-fill-color: #0F172A !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: #94A3B8 !important;
            -webkit-text-fill-color: #94A3B8 !important;
        }
    </style>
    """

st.markdown(estilos_css, unsafe_allow_html=True)

# =============================================================
# GESTIÓN DE ENTORNO (.env), AUTENTICACIÓN Y SESIONES DE USUARIO
# =============================================================
ENTORNO_ACTUAL = obtener_entorno_despliegue()
MODO_PRUEBAS = ENTORNO_ACTUAL == "pruebas"
gestor_sesiones = GestorSesionesEvaluacion()
gestor_usuarios = GestorUsuarios()


def _detectar_dispositivo_actual() -> str:
    """Obtiene o genera un identificador estable por dispositivo/navegador."""
    qp_disp = st.query_params.get("dispositivo")
    if qp_disp:
        return str(qp_disp)
    try:
        headers = st.context.headers
        ua = headers.get("User-Agent", "")
        lang = headers.get("Accept-Language", "")
        host = headers.get("Host", "")
        semilla = f"{ua}|{lang}|{host}"
    except Exception:
        semilla = ""
    return generar_dispositivo_id(semilla)


if "dispositivo_id" not in st.session_state:
    st.session_state.dispositivo_id = _detectar_dispositivo_actual()

if "usuario_actual" not in st.session_state:
    qp_token = st.query_params.get("token")
    perfil_recuperado = gestor_usuarios.validar_token_sesion(str(qp_token)) if qp_token else None
    st.session_state.usuario_actual = perfil_recuperado
    st.session_state.auth_token = str(qp_token) if perfil_recuperado else ""

if "nombre_evaluador" not in st.session_state:
    st.session_state.nombre_evaluador = (
        st.session_state.usuario_actual.get("nombre_completo", "")
        if st.session_state.usuario_actual
        else ""
    )

if "messages" not in st.session_state:
    st.session_state.messages = []
if "historial_rag" not in st.session_state:
    st.session_state.historial_rag = []
if "experiencia_final" not in st.session_state:
    st.session_state.experiencia_final = {
        "calificacion_global_estrellas": None,
        "comentarios_experiencia": "",
        "sugerencias_correccion_futura": "",
        "guardado_en": None,
    }
if "estado_sesion" not in st.session_state:
    st.session_state.estado_sesion = "activa"


def renderizar_bloque_disclaimer_seguridad() -> None:
    """Muestra el aviso de seguridad obligatorio sobre fase de pruebas y no sustitución de un experto."""
    st.warning(
        "**AVISO DE SEGURIDAD Y DESLINDE DE RESPONSABILIDAD LEGAL:**\n\n"
        "1. **No sustituye a un experto:** LEXIS es una herramienta tecnológica de orientación informativa y "
        "consulta normativa asistida por Inteligencia Artificial. Sus respuestas **no constituyen asesoría "
        "jurídica vinculante ni sustituyen la consulta, patrocinio o dictamen de un abogado o especialista en derecho**.\n"
        "2. **Sistema en fase de pruebas:** Esta plataforma se encuentra actualmente en **fase de pruebas**, "
        "por lo que **puede cometer errores**, presentar omisiones o interpretar de forma inexacta algún precepto "
        "legal. Verifique siempre la información con un profesional jurídico acreditado antes de tomar cualquier decisión."
    )


def renderizar_pantalla_autenticacion() -> None:
    """Renderiza el portal de Inicio de Sesión y Creación de Cuenta antes de acceder al chat."""
    with st.sidebar:
        if ruta_logo.exists():
            st.image(str(ruta_logo), width="stretch")
        st.title("Asistente LEXIS")
        st.caption("Sistema de Asesoría Legal Basado en RAG y Grafo de Conocimiento")
        st.caption(f"Entorno activo (.env): **{ENTORNO_ACTUAL.upper()}**")
        modo_sel = st.toggle("Modo Oscuro", value=st.session_state.modo_oscuro, key="toggle_dark_auth")
        if modo_sel != st.session_state.modo_oscuro:
            st.session_state.modo_oscuro = modo_sel
            st.rerun()

    col_izq, col_centro, col_der = st.columns([1, 3, 1])
    with col_centro:
        c_logo, c_tit = st.columns([1, 5], vertical_alignment="center")
        with c_logo:
            if ruta_logo.exists():
                st.image(str(ruta_logo), width=85)
        with c_tit:
            st.title("Acceso a LEXIS")
            st.caption("Orientación Jurídica Inteligente con Grafo de Conocimiento")

        renderizar_bloque_disclaimer_seguridad()

        tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Crear Cuenta"])

        with tab_login:
            st.subheader("Iniciar Sesión en tu Cuenta")
            with st.form("form_login_lexis", clear_on_submit=False):
                identificador_in = st.text_input(
                    "Nombre de usuario o correo electrónico:",
                    placeholder="Ej. usuario123 o correo@dominio.com",
                )
                password_in = st.text_input(
                    "Contraseña:",
                    type="password",
                    placeholder="Ingresa tu contraseña",
                )
                btn_ingresar = st.form_submit_button(
                    "Iniciar Sesión",
                    type="primary",
                    use_container_width=True,
                )
                if btn_ingresar:
                    ok, msg_auth, perfil = gestor_usuarios.autenticar_usuario(
                        identificador_in, password_in
                    )
                    if ok and perfil:
                        token = gestor_usuarios.crear_token_sesion(
                            perfil["username"], st.session_state.dispositivo_id
                        )
                        st.session_state.usuario_actual = perfil
                        st.session_state.auth_token = token
                        st.session_state.nombre_evaluador = perfil["nombre_completo"]
                        st.session_state.sesion_id = generar_sesion_id()
                        st.session_state.messages = []
                        st.session_state.historial_rag = []
                        st.query_params["token"] = token
                        st.query_params["sesion"] = st.session_state.sesion_id
                        st.rerun()
                    else:
                        st.error(msg_auth)

        with tab_registro:
            st.subheader("Crear una Nueva Cuenta")
            st.caption(
                "Cualquier usuario puede crear una cuenta para realizar consultas legales, guardar su historial de conversaciones y calificar las respuestas del asistente."
            )
            with st.form("form_registro_lexis", clear_on_submit=False):
                reg_nombre = st.text_input(
                    "Nombre completo:",
                    placeholder="Ej. María López Hernández",
                )
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    reg_username = st.text_input(
                        "Nombre de usuario:",
                        placeholder="Ej. maria_lopez",
                    )
                with col_u2:
                    reg_correo = st.text_input(
                        "Correo electrónico (opcional):",
                        placeholder="Ej. maria@correo.com",
                    )
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    reg_pass1 = st.text_input(
                        "Contraseña (mínimo 6 caracteres):",
                        type="password",
                    )
                with col_p2:
                    reg_pass2 = st.text_input(
                        "Confirmar contraseña:",
                        type="password",
                    )

                reg_es_juridico_tlaxcala = st.checkbox(
                    "Soy abogado, estudiante de Derecho o me desempeño en un área afín en el Estado de Tlaxcala.",
                    value=False,
                )

                reg_disclaimer = st.checkbox(
                    "He leído y acepto que LEXIS se encuentra en fase de pruebas, puede cometer errores "
                    "y que sus respuestas tienen carácter informativo y NO sustituyen la asesoría de un abogado o experto.",
                    value=False,
                )

                btn_registrar = st.form_submit_button(
                    "Crear Cuenta e Ingresar",
                    type="primary",
                    use_container_width=True,
                )
                if btn_registrar:
                    if reg_pass1 != reg_pass2:
                        st.error("Las contraseñas ingresadas no coinciden.")
                    else:
                        ok_reg, msg_reg, perfil_nuevo = gestor_usuarios.registrar_usuario(
                            username=reg_username,
                            password=reg_pass1,
                            nombre_completo=reg_nombre,
                            correo=reg_correo,
                            acepta_disclaimer=reg_disclaimer,
                            es_area_juridica_tlaxcala=reg_es_juridico_tlaxcala,
                        )
                        if ok_reg and perfil_nuevo:
                            token = gestor_usuarios.crear_token_sesion(
                                perfil_nuevo["username"], st.session_state.dispositivo_id
                            )
                            st.session_state.usuario_actual = perfil_nuevo
                            st.session_state.auth_token = token
                            st.session_state.nombre_evaluador = perfil_nuevo["nombre_completo"]
                            st.session_state.sesion_id = generar_sesion_id()
                            st.session_state.messages = []
                            st.session_state.historial_rag = []
                            st.query_params["token"] = token
                            st.query_params["sesion"] = st.session_state.sesion_id
                            st.rerun()
                        else:
                            st.error(msg_reg)


if st.session_state.usuario_actual is None:
    renderizar_pantalla_autenticacion()
    st.stop()

usuario_activo = st.session_state.usuario_actual
st.session_state.nombre_evaluador = usuario_activo.get("nombre_completo", "")

if "sesion_id" not in st.session_state:
    qp_ses = st.query_params.get("sesion")
    cargada = gestor_sesiones.cargar_sesion(qp_ses) if qp_ses else None
    if cargada and (
        not cargada.get("usuario_id")
        or cargada.get("usuario_id") == usuario_activo.get("usuario_id")
    ):
        st.session_state.sesion_id = cargada["sesion_id"]
        st.session_state.dispositivo_id = cargada.get("dispositivo_id", st.session_state.dispositivo_id)
        st.session_state.messages = cargada.get("messages", [])
        st.session_state.historial_rag = [tuple(x) for x in cargada.get("historial_rag", [])]
        st.session_state.experiencia_final = cargada.get(
            "experiencia_final", st.session_state.experiencia_final
        )
        st.session_state.estado_sesion = cargada.get("estado", "activa")
    else:
        st.session_state.sesion_id = generar_sesion_id()

st.query_params["dispositivo"] = st.session_state.dispositivo_id
st.query_params["sesion"] = st.session_state.sesion_id
if st.session_state.get("auth_token"):
    st.query_params["token"] = st.session_state.auth_token


def sincronizar_sesion_en_disco() -> None:
    """Guarda el estado completo de la sesión actual vinculada a la cuenta del usuario."""
    datos = gestor_sesiones.crear_estructura_sesion(
        sesion_id=st.session_state.sesion_id,
        dispositivo_id=st.session_state.dispositivo_id,
        entorno=ENTORNO_ACTUAL,
        nombre_evaluador=usuario_activo.get("nombre_completo", ""),
        usuario_id=usuario_activo.get("usuario_id", ""),
        username=usuario_activo.get("username", ""),
        rol_usuario=usuario_activo.get("rol", "Usuario General"),
        es_area_juridica_tlaxcala=bool(
            usuario_activo.get("es_area_juridica_tlaxcala", False)
        ),
    )
    datos["estado"] = st.session_state.estado_sesion
    datos["messages"] = st.session_state.messages
    datos["historial_rag"] = [list(x) for x in st.session_state.historial_rag]
    datos["experiencia_final"] = st.session_state.experiencia_final
    gestor_sesiones.guardar_sesion(datos)


def cargar_sesion_en_estado(sesion_id_destino: str) -> bool:
    """Carga una conversación guardada desde disco en st.session_state."""
    datos = gestor_sesiones.cargar_sesion(sesion_id_destino)
    if not datos:
        return False
    st.session_state.sesion_id = datos["sesion_id"]
    st.session_state.dispositivo_id = datos.get("dispositivo_id", st.session_state.dispositivo_id)
    st.session_state.messages = datos.get("messages", [])
    st.session_state.historial_rag = [tuple(x) for x in datos.get("historial_rag", [])]
    st.session_state.experiencia_final = datos.get(
        "experiencia_final",
        {
            "calificacion_global_estrellas": None,
            "comentarios_experiencia": "",
            "sugerencias_correccion_futura": "",
            "guardado_en": None,
        },
    )
    st.session_state.estado_sesion = datos.get("estado", "activa")
    st.query_params["sesion"] = st.session_state.sesion_id
    return True


def iniciar_nueva_conversacion() -> None:
    """Inicia una nueva sesión conservando intactas las anteriores en disco."""
    if st.session_state.messages:
        sincronizar_sesion_en_disco()
    st.session_state.sesion_id = generar_sesion_id()
    st.session_state.messages = []
    st.session_state.historial_rag = []
    st.session_state.experiencia_final = {
        "calificacion_global_estrellas": None,
        "comentarios_experiencia": "",
        "sugerencias_correccion_futura": "",
        "guardado_en": None,
    }
    st.session_state.estado_sesion = "activa"
    st.query_params["sesion"] = st.session_state.sesion_id


def cerrar_sesion_usuario() -> None:
    """Guarda la conversación activa, revoca el token y cierra la sesión del usuario."""
    if st.session_state.messages:
        sincronizar_sesion_en_disco()
    tok = st.session_state.get("auth_token", "")
    if tok:
        gestor_usuarios.cerrar_token_sesion(tok)
    st.session_state.usuario_actual = None
    st.session_state.auth_token = ""
    st.session_state.messages = []
    st.session_state.historial_rag = []
    if "token" in st.query_params:
        del st.query_params["token"]
    if "sesion" in st.query_params:
        del st.query_params["sesion"]


def mensaje_esta_evaluado(msg: dict) -> bool:
    """Verifica si un mensaje del asistente ya cuenta con voto (Like/Dislike) y estrellas (0 a 5)."""
    if msg.get("role") != "assistant":
        return True
    if ENTORNO_ACTUAL == "produccion":
        return True
    ev = msg.get("evaluacion", {})
    return ev.get("voto") in ("like", "dislike") and ev.get("estrellas") is not None


def contar_respuestas_sin_evaluar(mensajes: list[dict]) -> int:
    """Cuenta cuántas respuestas del asistente aún no han sido evaluadas por el usuario."""
    if ENTORNO_ACTUAL == "produccion":
        return 0
    return sum(
        1
        for m in mensajes
        if m.get("role") == "assistant" and not mensaje_esta_evaluado(m)
    )


def renderizar_controles_evaluacion_mensaje(msg: dict, idx: int) -> None:
    """
    Muestra para cualquier usuario los botones obligatorios de Like y Dislike y,
    tras votar, despliega la calificación obligatoria de 0 a 5 estrellas junto con
    el campo opcional de comentarios o corrección sobre la respuesta.
    """
    if ENTORNO_ACTUAL == "produccion":
        return

    if "id_mensaje" not in msg:
        msg["id_mensaje"] = generar_mensaje_id(idx)
    id_msg = msg["id_mensaje"]

    ev = msg.setdefault(
        "evaluacion",
        {
            "voto": None,
            "estrellas": None,
            "correccion_juridica": "",
            "evaluado_en": None,
        },
    )
    voto_actual = ev.get("voto")
    estrellas_actuales = ev.get("estrellas")

    st.markdown("---")
    if voto_actual is None:
        st.info(
            "**Evaluación obligatoria (Paso 1 de 2):** Selecciona **Like** o **Dislike** para calificar esta respuesta."
        )
    elif estrellas_actuales is None:
        st.warning(
            "**Evaluación obligatoria (Paso 2 de 2):** Ahora selecciona una puntuación de **0 a 5 estrellas** abajo para poder continuar con otra consulta."
        )
    else:
        st.caption(
            "Calificación registrada (puedes modificar tu voto o estrellas si lo deseas):"
        )

    col_like, col_dislike, col_estado = st.columns([2, 2, 4], vertical_alignment="center")
    with col_like:
        etiqueta_like = "Like ( Seleccionado )" if voto_actual == "like" else "Like ( Respuesta útil / adecuada )"
        if st.button(
            etiqueta_like,
            key=f"btn_like_{id_msg}",
            type="primary" if voto_actual == "like" else "secondary",
            use_container_width=True,
        ):
            ev["voto"] = "like"
            sincronizar_sesion_en_disco()
            st.rerun()

    with col_dislike:
        etiqueta_dislike = (
            "Dislike ( Seleccionado )"
            if voto_actual == "dislike"
            else "Dislike ( Respuesta incorrecta / incompleta )"
        )
        if st.button(
            etiqueta_dislike,
            key=f"btn_dislike_{id_msg}",
            type="primary" if voto_actual == "dislike" else "secondary",
            use_container_width=True,
        ):
            ev["voto"] = "dislike"
            sincronizar_sesion_en_disco()
            st.rerun()

    with col_estado:
        if voto_actual in ("like", "dislike"):
            voto_txt = "Like" if voto_actual == "like" else "Dislike"
            est_txt = (
                f"{estrellas_actuales}/5 estrellas (Completado)"
                if estrellas_actuales is not None
                else "Falta puntuar de 0 a 5 estrellas (Obligatorio)"
            )
            st.caption(f"Estado de tu evaluación: **{voto_txt}** | **{est_txt}**")

    # Después de pulsar Like o Dislike, aparecen las estrellas de 0 a 5 y el comentario opcional
    if voto_actual in ("like", "dislike"):
        st.caption("Puntúa la calidad, claridad y utilidad de esta respuesta (de 0 a 5 estrellas — obligatorio):")
        cols_estrellas = st.columns(6)
        for num_est in range(6):
            with cols_estrellas[num_est]:
                simbolos = "★" * num_est if num_est > 0 else "0"
                etiqueta_est = f"{num_est}/5 ({simbolos})" if num_est > 0 else "0/5 (0 ★)"
                es_seleccionada = estrellas_actuales == num_est
                if st.button(
                    etiqueta_est,
                    key=f"btn_star_{id_msg}_{num_est}",
                    type="primary" if es_seleccionada else "secondary",
                    use_container_width=True,
                ):
                    ev["estrellas"] = num_est
                    sincronizar_sesion_en_disco()
                    st.rerun()

        with st.expander(
            "Agregar comentario, observación o sugerencia sobre esta respuesta (opcional)",
            expanded=bool(ev.get("correccion_juridica")),
        ):
            nota_actual = ev.get("correccion_juridica", "")
            nueva_nota = st.text_area(
                "Indica qué te pareció la respuesta o si detectaste algún artículo, dato o criterio que deba corregirse:",
                value=nota_actual,
                key=f"txt_corr_{id_msg}",
                height=85,
            )
            if st.button("Guardar comentario de respuesta", key=f"btn_save_corr_{id_msg}"):
                ev["correccion_juridica"] = nueva_nota.strip()
                sincronizar_sesion_en_disco()
                st.success("Comentario guardado en el registro de evaluación.")


respuestas_pendientes_global = contar_respuestas_sin_evaluar(st.session_state.messages)

with st.sidebar:
    if ruta_logo.exists():
        st.image(str(ruta_logo), width="stretch")
    st.title("Asistente LEXIS")
    st.caption("Sistema de Asesoría Legal Basado en RAG y Grafo de Conocimiento")
    st.caption(f"Entorno activo (.env): **{ENTORNO_ACTUAL.upper()}** | Sesión: `{st.session_state.sesion_id}`")

    with st.container(border=True):
        st.markdown(f"**Cuenta activa:** {usuario_activo['nombre_completo']}")
        st.caption(
            f"Usuario: `{usuario_activo['username']}` | Perfil: **{usuario_activo.get('rol', 'Usuario General')}**"
        )
        if st.button("Cerrar sesión", use_container_width=True):
            if respuestas_pendientes_global > 0:
                st.error(
                    "Primero califica la respuesta pendiente (Like/Dislike y de 0 a 5 estrellas) antes de cerrar sesión."
                )
            else:
                cerrar_sesion_usuario()
                st.rerun()
    
    modo_seleccionado = st.toggle("Modo Oscuro", value=st.session_state.modo_oscuro)
    if modo_seleccionado != st.session_state.modo_oscuro:
        st.session_state.modo_oscuro = modo_seleccionado
        st.rerun()

    st.markdown("---")
    
    opciones_ley = ["Automático"] + documentos_disponibles
    ley_seleccionada = st.selectbox("Filtrar por legislación:", opciones_ley)

    mostrar_cerebro_global = st.toggle("Explorar Grafo de Conocimiento Global", value=False)
    if mostrar_cerebro_global and GRAPHRAG_DISPONIBLE:
        max_nodos_cerebro = st.slider("Nodos a mostrar en el grafo:", min_value=60, max_value=300, value=160, step=20)
    
    st.markdown("---")
    st.subheader("Mis Conversaciones Guardadas")

    ver_todas_sesiones = st.checkbox(
        "Mostrar sesiones de este dispositivo sin cuenta",
        value=False,
    )
    if ver_todas_sesiones:
        sesiones_guardadas = gestor_sesiones.listar_sesiones(
            dispositivo_id=st.session_state.dispositivo_id
        )
    else:
        sesiones_guardadas = gestor_sesiones.listar_sesiones(
            dispositivo_id=st.session_state.dispositivo_id,
            usuario_id=usuario_activo.get("usuario_id"),
            username=usuario_activo.get("username"),
        )

    if sesiones_guardadas:
        opciones_sesiones = ["(Seleccionar conversación guardada...)"] + [
            f"{s['sesion_id']} | {s['titulo']} ({s['num_mensajes']} msgs, {s['estado']})"
            for s in sesiones_guardadas
        ]
        seleccion_sesion = st.selectbox(
            "Retomar conversación anterior:",
            opciones_sesiones,
        )
        if seleccion_sesion != "(Seleccionar conversación guardada...)":
            id_elegido = seleccion_sesion.split(" | ")[0].strip()
            if id_elegido != st.session_state.sesion_id:
                if st.button("Cargar conversación seleccionada", use_container_width=True):
                    if respuestas_pendientes_global > 0:
                        st.error(
                            "Primero califica la respuesta pendiente (Like/Dislike y 0 a 5 estrellas) antes de cambiar de conversación."
                        )
                    elif cargar_sesion_en_estado(id_elegido):
                        st.rerun()
    else:
        st.caption("Aún no tienes conversaciones previas guardadas en tu cuenta.")

    col_nueva, col_limpiar = st.columns(2)
    with col_nueva:
        if st.button("Nueva sesión", use_container_width=True):
            if respuestas_pendientes_global > 0:
                st.error(
                    "Califica primero la respuesta pendiente antes de iniciar una nueva sesión."
                )
            else:
                iniciar_nueva_conversacion()
                st.rerun()
    with col_limpiar:
        if st.button("Limpiar actual", use_container_width=True):
            if respuestas_pendientes_global > 0:
                st.error(
                    "Califica primero la respuesta pendiente antes de limpiar la conversación."
                )
            else:
                st.session_state.messages = []
                st.session_state.historial_rag = []
                sincronizar_sesion_en_disco()
                st.rerun()

    st.markdown("---")
    with st.expander("Exportar Evaluaciones y Usuarios (Admin)"):
        clave_admin_esperada = os.getenv("LEXIS_ADMIN_KEY", "").strip()
        if not clave_admin_esperada:
            st.caption(
                "Panel deshabilitado: defina la variable de entorno LEXIS_ADMIN_KEY para habilitar la exportación."
            )
        else:
            clave_admin_in = st.text_input(
                "Clave de administrador:",
                type="password",
                key="input_admin_export_key",
            )
            if clave_admin_in and clave_admin_in == clave_admin_esperada:
                if gestor_sesiones.archivo_consolidado.exists():
                    bytes_eval = gestor_sesiones.archivo_consolidado.read_bytes()
                    st.download_button(
                        "Descargar evaluaciones_consolidado.json",
                        data=bytes_eval,
                        file_name="evaluaciones_consolidado.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                else:
                    st.caption("Aún no existe evaluaciones_consolidado.json.")

                if gestor_usuarios.archivo_usuarios.exists():
                    import json as _json

                    raw_usrs = gestor_usuarios._cargar_usuarios()
                    usrs_limpios = {
                        u: gestor_usuarios._sanitizar_perfil(d) for u, d in raw_usrs.items()
                    }
                    st.download_button(
                        "Descargar usuarios_registrados.json",
                        data=_json.dumps(usrs_limpios, ensure_ascii=False, indent=2).encode("utf-8"),
                        file_name="usuarios_registrados.json",
                        mime="application/json",
                        use_container_width=True,
                    )
            elif clave_admin_in:
                st.error("Clave de administrador incorrecta.")

col_logo, col_titulo = st.columns([1, 6], vertical_alignment="center")

with col_logo:
    if ruta_logo.exists():
        st.image(str(ruta_logo), width=90)

with col_titulo:
    st.title("Asesoría Jurídica Inteligente")

st.markdown(
    "Describe tu situación legal. Lexis analiza la consulta, recupera los artículos "
    "aplicables en la base de datos y genera una orientación fundamentada."
)

renderizar_bloque_disclaimer_seguridad()

if mostrar_cerebro_global and GRAPHRAG_DISPONIBLE:
    with st.container(border=True):
        st.subheader("Grafo de Conocimiento Jurídico LEXIS (Vista interactiva tipo Obsidian)")
        st.caption(
            "Usa la rueda del ratón para hacer zoom, arrastra los nodos o haz clic sobre cualquier nodo para inspeccionar su contenido y las conexiones entre leyes."
        )
        rec_global = obtener_recuperador_grafo()
        datos_globales = extraer_datos_cerebro_global(
            rec_global.grafo, max_nodos_articulos=max_nodos_cerebro
        )
        html_global = generar_html_obsidian(datos_globales, altura_px=560)
        components.html(html_global, height=580, scrolling=False)

for idx_msg, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("grafo_html"):
            with st.expander("Ver Grafo de Nodos Activados y Concatenados (Vista Obsidian)", expanded=False):
                components.html(msg["grafo_html"], height=490, scrolling=False)
        if "fuentes" in msg and msg["fuentes"]:
            with st.expander("Ver fundamentos y normativas consultadas"):
                st.markdown(msg["fuentes"])
        if msg["role"] == "assistant":
            renderizar_controles_evaluacion_mensaje(msg, idx_msg)

bloqueo_por_evaluacion_pendiente = respuestas_pendientes_global > 0
if bloqueo_por_evaluacion_pendiente:
    st.warning(
        "**Evaluación requerida para continuar:** Antes de realizar una nueva consulta o finalizar la sesión, "
        "por favor califica la respuesta anterior seleccionando **Like o Dislike** y asignando una puntuación de **0 a 5 estrellas**."
    )

placeholder_chat = (
    "Primero califica la respuesta anterior (Like/Dislike y 0 a 5 estrellas) para hacer otra consulta..."
    if bloqueo_por_evaluacion_pendiente
    else "Escribe tu consulta legal aquí..."
)

if prompt := st.chat_input(
    placeholder_chat,
    disabled=bloqueo_por_evaluacion_pendiente,
):
    st.session_state.messages.append({"role": "user", "content": prompt})
    sincronizar_sesion_en_disco()
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if ANALIZADOR_DISPONIBLE:
            es_coherente, sugerencias = analizar_coherencia_consulta(prompt)
            if not es_coherente:
                st.warning(f"Aviso: {sugerencias[0]}")
            elif any("vaga" in s.lower() for s in sugerencias):
                st.info(f"Sugerencia: {sugerencias[0]}")

        with st.spinner("Buscando leyes aplicables y redactando asesoría..."):
            t_inicio_consulta = time.time()
            # En modo "Automático", buscamos en todas las leyes simultáneamente (ChromaDB + BM25 + Grafo)
            # para permitir consultas inter-ley (ej. Código Civil + Procedimientos Civiles).
            filtro_doc = None if ley_seleccionada == "Automático" else ley_seleccionada

            try:
                hits = busqueda_hibrida(
                    consulta=prompt,
                    coleccion=coleccion,
                    motor_bm25=motor_bm25,
                    modelo=modelo_semantico,
                    diccionario_textos=diccionario_textos,
                    diccionario_metadatos=diccionario_metadatos,
                    top_k=TOP_K_DEFAULT,
                    filtro_documento=filtro_doc,
                    filtro_jerarquia=None,
                )
            except Exception as e:
                hits = []
                st.error(f"Error en la búsqueda: {e}")

            if not hits or len(hits) < 3:
                doc_sugerido = filtro_doc
                if not doc_sugerido and ANALIZADOR_DISPONIBLE:
                    doc_sugerido, _ = detectar_normativa(prompt, documentos_disponibles)
                if not doc_sugerido:
                    doc_sugerido = detectar_documento(prompt)
                res_tematicos = buscar_por_concepto(prompt, doc_sugerido)
                if res_tematicos:
                    hits_fallback = []
                    rec_fb = obtener_recuperador_grafo() if GRAPHRAG_DISPONIBLE else None
                    for rt in res_tematicos[:10]:
                        doc_rt = rt.get("documento", "")
                        art_rt = rt.get("articulo", "")
                        art_id_rt = rt.get("articulo_id", "")
                        texto_real = ""
                        jerarquia_real = rt.get("tema", "General")

                        if rec_fb is not None:
                            nodo_fb = art_id_rt if (art_id_rt and art_id_rt in rec_fb.grafo) else rec_fb.mapear_hit_a_nodo_articulo(rt)
                            if nodo_fb and nodo_fb in rec_fb.grafo:
                                datos_nodo = rec_fb.grafo.nodes[nodo_fb]
                                texto_real = datos_nodo.get("texto_completo", "").strip()
                                jerarquia_real = datos_nodo.get("jerarquia") or jerarquia_real
                                art_id_rt = nodo_fb

                        if not texto_real and diccionario_metadatos and diccionario_textos:
                            for cid, meta in diccionario_metadatos.items():
                                if meta.get("documento") == doc_rt and meta.get("articulo") == art_rt:
                                    texto_real = diccionario_textos.get(cid, "").strip()
                                    jerarquia_real = meta.get("jerarquia") or jerarquia_real
                                    break

                        if not texto_real:
                            continue

                        hits_fallback.append({
                            "documento": doc_rt,
                            "articulo": art_rt,
                            "articulo_id": art_id_rt,
                            "jerarquia": jerarquia_real,
                            "texto": texto_real,
                            "origen": "tematico",
                            "tema": rt.get("tema", "")
                        })
                    if hits_fallback:
                        hits = hits_fallback

            nodos_grafo_usados = []
            articulos_recuperados_meta = []

            if not hits:
                respuesta = "No encontré artículos normativos relacionados directamente con tu caso en la base de datos actual. ¿Podrías darme más contexto o detalles específicos?"
                fuentes_md = ""
                grafo_html_consulta = ""
                st.markdown(respuesta)
            else:
                resumen_grafo_md = ""
                grafo_html_consulta = ""
                if GRAPHRAG_DISPONIBLE:
                    try:
                        rec = obtener_recuperador_grafo()
                        ctx_grafo = construir_contexto_graphrag(
                            hits,
                            max_fragmentos_base=MAX_FRAGMENTOS,
                            max_vecinos_grafo=4,
                            recuperador=rec,
                        )
                        bloque_leyes = ctx_grafo["bloque_prompt"]
                        resumen_grafo_md = ctx_grafo["resumen_grafo_md"]
                        exp_info = ctx_grafo.get("expansion", {})
                        nodos_grafo_usados = list(exp_info.get("nodos_semilla", [])) + [
                            v.get("articulo_id") or v.get("nodo_id")
                            for v in exp_info.get("vecinos_citados_salientes", [])
                            if v.get("articulo_id") or v.get("nodo_id")
                        ]
                        datos_subgrafo = extraer_datos_subgrafo_consulta(
                            rec.grafo, exp_info, incluir_nodos_ley=True
                        )
                        if datos_subgrafo["nodes"]:
                            grafo_html_consulta = generar_html_obsidian(
                                datos_subgrafo, altura_px=470
                            )
                    except Exception:
                        bloque_leyes = construir_bloque_leyes(hits)
                else:
                    bloque_leyes = construir_bloque_leyes(hits)

                contexto_hist = ""
                if st.session_state.historial_rag:
                    contexto_hist = "[HISTORIAL DE LA CONVERSACIÓN]\n"
                    for i, (preg, tema) in enumerate(st.session_state.historial_rag[-3:], 1):
                        contexto_hist += f"Interacción {i}:\nUsuario: {preg}\nContexto: {tema}\n"
                    contexto_hist += "\n"

                user_prompt = f"""{contexto_hist}[CONSULTA ACTUAL DEL USUARIO]
{prompt}

[NOTA: Esta es una continuación de la conversación. Considera el contexto anterior.]

[LEYES RECUPERADAS]
{bloque_leyes}"""

                respuesta = llamar_groq(system_prompt, user_prompt)
                st.markdown(respuesta)

                if grafo_html_consulta:
                    with st.expander(
                        "Ver Grafo de Nodos Activados y Concatenados (Vista Obsidian)",
                        expanded=True,
                    ):
                        st.caption(
                            "Los nodos cian son los artículos recuperados directamente por tu consulta; los nodos conectados muestran qué otros artículos o leyes se concatenaron desde el grafo para construir la respuesta. Haz clic en cualquier nodo para ver el fragmento exacto."
                        )
                        components.html(grafo_html_consulta, height=490, scrolling=False)

                fuentes_md = "#### Artículos recuperados directamente\n"
                hits_top = hits[:MAX_FRAGMENTOS] if len(hits) > MAX_FRAGMENTOS else hits
                for h in hits_top:
                    doc_h = h.get("documento", "N/D")
                    art_h = h.get("articulo", "N/D")
                    jer_h = h.get("jerarquia", "N/D")
                    fuentes_md += f"* **{doc_h}** — *{art_h}* ({jer_h})\n"
                    articulos_recuperados_meta.append(
                        {"documento": doc_h, "articulo": art_h, "jerarquia": jer_h}
                    )
                if resumen_grafo_md:
                    fuentes_md += "\n#### Artículos conectados en el Grafo de Conocimiento (GraphRAG)\n" + resumen_grafo_md + "\n"
                
                with st.expander("Ver fundamentos y normativas consultadas"):
                    st.markdown(fuentes_md)

                st.session_state.historial_rag.append((prompt, f"Ley: {filtro_doc or 'General'}"))

        nuevo_idx = len(st.session_state.messages)
        tiempo_resp_seg = round(time.time() - t_inicio_consulta, 2)
        nuevo_mensaje = {
            "id_mensaje": generar_mensaje_id(nuevo_idx),
            "role": "assistant",
            "content": respuesta,
            "consulta_origen": prompt,
            "ley_filtrada": ley_seleccionada,
            "fuentes": fuentes_md,
            "articulos_recuperados": articulos_recuperados_meta,
            "nodos_grafo": nodos_grafo_usados,
            "tiempo_respuesta_seg": tiempo_resp_seg,
            "grafo_html": grafo_html_consulta,
            "evaluacion": {
                "voto": None,
                "estrellas": None,
                "correccion_juridica": "",
                "evaluado_en": None,
            },
        }
        st.session_state.messages.append(nuevo_mensaje)
        sincronizar_sesion_en_disco()
        st.rerun()


def generar_orientacion_legal_markdown(
    messages: list[dict],
    sesion_id: str,
    usuario: dict,
) -> str:
    """Construye un documento Markdown descargable con el historial de consultas, artículos citados y aviso legal."""
    lineas = [
        "# LEXIS — Reporte de Orientación Jurídica Preliminar",
        "",
        f"- **Sesión:** `{sesion_id}`",
        f"- **Usuario:** {usuario.get('nombre_completo', 'N/D')} (`@{usuario.get('username', 'N/D')}`)",
        f"- **Perfil:** {usuario.get('rol', 'Usuario General')}",
        f"- **Fecha de exportación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "> **AVISO DE SEGURIDAD Y LIMITACIÓN DE RESPONSABILIDAD:**",
        "> Este documento constituye únicamente una orientación jurídica preliminar de carácter informativo y académico generada mediante recuperación aumentada por grafos (GraphRAG). **NO sustituye la asesoría, dictamen ni representación legal de un Licenciado en Derecho o profesional jurídico certificado.** El sistema se encuentra en fase de pruebas y puede cometer omisiones o imprecisiones interpretativas.",
        "",
        "---",
        "",
    ]

    turno = 0
    for msg in messages:
        if msg.get("role") == "user":
            turno += 1
            lineas.append(f"## Consulta {turno}")
            lineas.append("")
            lineas.append(msg.get("content", "").strip())
            lineas.append("")
        elif msg.get("role") == "assistant":
            lineas.append("### Orientación Generada por LEXIS")
            lineas.append("")
            lineas.append(msg.get("content", "").strip())
            lineas.append("")
            arts = msg.get("articulos_recuperados", [])
            if arts:
                lineas.append("#### Fundamentos Normativos Consultados")
                for a in arts:
                    lineas.append(
                        f"- **{a.get('documento', 'N/D')}** — *{a.get('articulo', 'N/D')}* ({a.get('jerarquia', 'General')})"
                    )
                lineas.append("")
            nodos = msg.get("nodos_grafo", [])
            if nodos:
                lineas.append(f"- **Nodos del Grafo Jurídico activados:** `{', '.join(nodos)}`")
                lineas.append("")
            lineas.append("---")
            lineas.append("")

    return "\n".join(lineas)


# =============================================================
# APARTADO ANTES DE TERMINAR LA CONVERSACIÓN: COMENTARIOS DE EXPERIENCIA
# =============================================================
if st.session_state.messages:
    st.markdown("---")
    md_export_orientacion = generar_orientacion_legal_markdown(
        st.session_state.messages,
        st.session_state.sesion_id,
        usuario_activo,
    )
    st.download_button(
        label="Descargar orientación legal (.md)",
        data=md_export_orientacion.encode("utf-8"),
        file_name=f"orientacion_lexis_{st.session_state.sesion_id}.md",
        mime="text/markdown",
        use_container_width=True,
    )
    with st.expander(
        "Puntuación General del Chat, Comentarios sobre la Experiencia y Cierre de Conversación",
        expanded=(st.session_state.estado_sesion == "finalizada"),
    ):
        st.caption(
            "Antes de concluir tu sesión, registra tu puntuación general del chat (de 0 a 5 estrellas), tus comentarios con respecto a la experiencia y cualquier sugerencia para mejorar las respuestas del modelo."
        )
        exp_actual = st.session_state.experiencia_final

        opciones_estrellas_global = [0, 1, 2, 3, 4, 5]
        val_global_actual = exp_actual.get("calificacion_global_estrellas")
        idx_global = (
            opciones_estrellas_global.index(val_global_actual)
            if val_global_actual in opciones_estrellas_global
            else 5
        )

        calif_global = st.selectbox(
            "Calificación general del chat (0 a 5 estrellas):",
            options=opciones_estrellas_global,
            index=idx_global,
            format_func=lambda x: f"{x}/5 estrellas ({'★' * x})" if x > 0 else "0/5 estrellas (0 ★)",
            key="sel_calif_global_exp",
        )

        comentarios_exp = st.text_area(
            "Comentarios con respecto a la experiencia de uso y utilidad del asistente:",
            value=exp_actual.get("comentarios_experiencia", ""),
            placeholder="Escribe aquí tus impresiones sobre la experiencia, claridad y desempeño general...",
            height=90,
            key="txt_comentarios_exp",
        )

        sugerencias_futuras = st.text_area(
            "Observaciones o correcciones sugeridas para mejorar las respuestas del modelo (opcional):",
            value=exp_actual.get("sugerencias_correccion_futura", ""),
            placeholder="Indica si alguna respuesta omitió información relevante, artículos aplicables o si tienes sugerencias de mejora...",
            height=90,
            key="txt_sugerencias_futuras",
        )

        col_guardar_exp, col_finalizar_exp = st.columns(2)
        with col_guardar_exp:
            if st.button("Guardar comentarios de experiencia", use_container_width=True):
                st.session_state.experiencia_final = {
                    "calificacion_global_estrellas": int(calif_global),
                    "comentarios_experiencia": comentarios_exp.strip(),
                    "sugerencias_correccion_futura": sugerencias_futuras.strip(),
                    "guardado_en": exp_actual.get("guardado_en"),
                }
                sincronizar_sesion_en_disco()
                st.success("Comentarios de experiencia guardados correctamente en la sesión.")

        with col_finalizar_exp:
            if st.button(
                "Guardar comentarios y finalizar conversación",
                type="primary",
                use_container_width=True,
            ):
                if respuestas_pendientes_global > 0:
                    st.error(
                        "Antes de finalizar la conversación, por favor califica la respuesta pendiente arriba (Like/Dislike y de 0 a 5 estrellas)."
                    )
                else:
                    st.session_state.experiencia_final = {
                        "calificacion_global_estrellas": int(calif_global),
                        "comentarios_experiencia": comentarios_exp.strip(),
                        "sugerencias_correccion_futura": sugerencias_futuras.strip(),
                        "guardado_en": exp_actual.get("guardado_en"),
                    }
                    st.session_state.estado_sesion = "finalizada"
                    sincronizar_sesion_en_disco()
                    st.success(
                        f"Conversación `{st.session_state.sesion_id}` finalizada y guardada. Puedes retomarla cuando lo necesites desde el panel lateral o iniciar una nueva sesión."
                    )

st.caption(
    "Recordatorio de seguridad: LEXIS se encuentra en una fase de pruebas y puede cometer errores. "
    "La orientación proporcionada es de carácter informativo y no sustituye la asesoría de un abogado o experto legal."
)
