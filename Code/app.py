import sys
import os
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
# GESTIÓN DE ENTORNO (.env) Y SESIONES PERSISTENTES POR DISPOSITIVO
# =============================================================
ENTORNO_ACTUAL = obtener_entorno_despliegue()
MODO_PRUEBAS = ENTORNO_ACTUAL == "pruebas"
gestor_sesiones = GestorSesionesEvaluacion()


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

if "nombre_evaluador" not in st.session_state:
    st.session_state.nombre_evaluador = ""

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

if "sesion_id" not in st.session_state:
    qp_ses = st.query_params.get("sesion")
    cargada = gestor_sesiones.cargar_sesion(qp_ses) if qp_ses else None
    if cargada:
        st.session_state.sesion_id = cargada["sesion_id"]
        st.session_state.dispositivo_id = cargada.get("dispositivo_id", st.session_state.dispositivo_id)
        st.session_state.nombre_evaluador = cargada.get("nombre_evaluador", "")
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


def sincronizar_sesion_en_disco() -> None:
    """Guarda el estado completo de la sesión actual en sesiones_evaluacion/."""
    datos = gestor_sesiones.crear_estructura_sesion(
        sesion_id=st.session_state.sesion_id,
        dispositivo_id=st.session_state.dispositivo_id,
        entorno=ENTORNO_ACTUAL,
        nombre_evaluador=st.session_state.nombre_evaluador,
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
    st.session_state.nombre_evaluador = datos.get("nombre_evaluador", st.session_state.nombre_evaluador)
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


def renderizar_controles_evaluacion_mensaje(msg: dict, idx: int) -> None:
    """
    Muestra los botones de Like y Dislike cuando LEXIS_ENV=pruebas y, tras votar,
    despliega la calificación de 0 a 5 estrellas junto con el campo opcional de
    corrección jurídica para validación por Licenciados en Derecho.
    """
    if not MODO_PRUEBAS:
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
    st.caption(
        "Validación de respuesta (Modo Pruebas — Evaluación por Licenciados en Derecho):"
    )

    col_like, col_dislike, col_estado = st.columns([2, 2, 4], vertical_alignment="center")
    with col_like:
        etiqueta_like = "Like ( Seleccionado )" if voto_actual == "like" else "Like ( Respuesta adecuada )"
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
                f"{estrellas_actuales}/5 estrellas"
                if estrellas_actuales is not None
                else "Pendiente puntuar de 0 a 5 estrellas"
            )
            st.caption(f"Estado de evaluación: **{voto_txt}** | **{est_txt}**")

    # Después de pulsar Like o Dislike, aparecen las estrellas de 0 a 5 y la observación jurídica
    if voto_actual in ("like", "dislike"):
        st.caption("Califica la calidad y precisión jurídica de esta respuesta (de 0 a 5 estrellas):")
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
            "Agregar observación o corrección jurídica para esta respuesta (opcional)",
            expanded=bool(ev.get("correccion_juridica")),
        ):
            nota_actual = ev.get("correccion_juridica", "")
            nueva_nota = st.text_area(
                "Indica qué artículo, criterio o interpretación legal debe corregirse o reforzarse:",
                value=nota_actual,
                key=f"txt_corr_{id_msg}",
                height=85,
            )
            if st.button("Guardar observación jurídica", key=f"btn_save_corr_{id_msg}"):
                ev["correccion_juridica"] = nueva_nota.strip()
                sincronizar_sesion_en_disco()
                st.success("Observación jurídica guardada en el registro de evaluación.")


with st.sidebar:
    if ruta_logo.exists():
        st.image(str(ruta_logo), width="stretch")
    st.title("Asistente LEXIS")
    st.caption("Sistema de Asesoría Legal Basado en RAG y Grafo de Conocimiento")
    st.caption(f"Entorno activo (.env): **{ENTORNO_ACTUAL.upper()}** | Sesión: `{st.session_state.sesion_id}`")
    
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
    st.subheader("Sesiones del Dispositivo")
    nuevo_evaluador = st.text_input(
        "Nombre del Evaluador / Lic. en Derecho:",
        value=st.session_state.nombre_evaluador,
        placeholder="Ej. Lic. Juan Pérez",
    )
    if nuevo_evaluador != st.session_state.nombre_evaluador:
        st.session_state.nombre_evaluador = nuevo_evaluador
        if st.session_state.messages:
            sincronizar_sesion_en_disco()

    ver_todas_sesiones = st.checkbox(
        "Mostrar sesiones de todos los dispositivos",
        value=False,
    )
    filtro_disp = None if ver_todas_sesiones else st.session_state.dispositivo_id
    sesiones_guardadas = gestor_sesiones.listar_sesiones(dispositivo_id=filtro_disp)

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
                    if cargar_sesion_en_estado(id_elegido):
                        st.rerun()
    else:
        st.caption("Aún no hay conversaciones previas guardadas para este dispositivo.")

    col_nueva, col_limpiar = st.columns(2)
    with col_nueva:
        if st.button("Nueva sesión", use_container_width=True):
            iniciar_nueva_conversacion()
            st.rerun()
    with col_limpiar:
        if st.button("Limpiar actual", use_container_width=True):
            st.session_state.messages = []
            st.session_state.historial_rag = []
            sincronizar_sesion_en_disco()
            st.rerun()

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

if prompt := st.chat_input("Escribe tu consulta legal aquí..."):
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
                    for rt in res_tematicos[:10]:
                        hits_fallback.append({
                            "documento": rt.get("documento", ""),
                            "articulo": rt.get("articulo", ""),
                            "jerarquia": rt.get("tema", "General"),
                            "texto": f"Fundamento legal temático sobre {rt.get('tema')}: {rt.get('articulo')}",
                            "origen": "tematico",
                            "tema": rt.get("tema", "")
                        })
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
                            v.get("nodo_id")
                            for v in exp_info.get("vecinos_citados_salientes", [])
                            if v.get("nodo_id")
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
        nuevo_mensaje = {
            "id_mensaje": generar_mensaje_id(nuevo_idx),
            "role": "assistant",
            "content": respuesta,
            "consulta_origen": prompt,
            "ley_filtrada": ley_seleccionada,
            "fuentes": fuentes_md,
            "articulos_recuperados": articulos_recuperados_meta,
            "nodos_grafo": nodos_grafo_usados,
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
        renderizar_controles_evaluacion_mensaje(nuevo_mensaje, nuevo_idx)

# =============================================================
# APARTADO ANTES DE TERMINAR LA CONVERSACIÓN: COMENTARIOS DE EXPERIENCIA
# =============================================================
if st.session_state.messages:
    st.markdown("---")
    with st.expander(
        "Comentarios sobre la Experiencia y Cierre de Conversación",
        expanded=(st.session_state.estado_sesion == "finalizada"),
    ):
        st.caption(
            "Antes de concluir tu sesión, registra tus comentarios sobre la experiencia, la calidad jurídica de las respuestas y cualquier recomendación para futuras mejoras del modelo."
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
            "Calificación general de la sesión (0 a 5 estrellas):",
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
            "Observaciones jurídicas generales para corrección futura de respuestas (Licenciados en Derecho):",
            value=exp_actual.get("sugerencias_correccion_futura", ""),
            placeholder="Indica criterios jurisprudenciales, artículos omitidos o ajustes recomendados para el modelo...",
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
