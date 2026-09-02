import sys
import os
from pathlib import Path

os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY"] = "False"

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DIR_ACTUAL = Path(__file__).resolve().parent
ROOT_DIR = DIR_ACTUAL.parent
sys.path.append(str(DIR_ACTUAL))

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

try:
    from analizador_legal import analizar_coherencia_consulta, detectar_normativa
    ANALIZADOR_DISPONIBLE = True
except ImportError:
    ANALIZADOR_DISPONIBLE = False

st.set_page_config(
    page_title="LEXIS - Asistencia Legal con IA",
    page_icon="⚖️",
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

with st.sidebar:
    if ruta_logo.exists():
        st.image(str(ruta_logo), width="stretch")
    st.title("⚖️ Asistente LEXIS")
    st.caption("Sistema de Asesoría Legal Basado en RAG")
    
    modo_seleccionado = st.toggle("Modo Oscuro 🌙", value=st.session_state.modo_oscuro)
    if modo_seleccionado != st.session_state.modo_oscuro:
        st.session_state.modo_oscuro = modo_seleccionado
        st.rerun()

    st.markdown("---")
    
    opciones_ley = ["Automático"] + documentos_disponibles
    ley_seleccionada = st.selectbox("Filtrar por legislación:", opciones_ley)
    
    st.markdown("---")
    if st.button("🧹 Limpiar historial"):
        st.session_state.messages = []
        st.session_state.historial_rag = []
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

if "messages" not in st.session_state:
    st.session_state.messages = []
if "historial_rag" not in st.session_state:
    st.session_state.historial_rag = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "fuentes" in msg and msg["fuentes"]:
            with st.expander("📚 Ver fundamentos y normativas consultadas"):
                st.markdown(msg["fuentes"])

if prompt := st.chat_input("Escribe tu consulta legal aquí..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if ANALIZADOR_DISPONIBLE:
            es_coherente, sugerencias = analizar_coherencia_consulta(prompt)
            if not es_coherente:
                st.warning(f"⚠️ {sugerencias[0]}")
            elif any("vaga" in s.lower() for s in sugerencias):
                st.info(f"💡 {sugerencias[0]}")

        with st.spinner("Buscando leyes aplicables y redactando asesoría..."):
            filtro_doc = None if ley_seleccionada == "Automático" else ley_seleccionada
            if not filtro_doc and ANALIZADOR_DISPONIBLE:
                filtro_doc, _ = detectar_normativa(prompt, documentos_disponibles)
            if not filtro_doc:
                filtro_doc = detectar_documento(prompt)

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
                res_tematicos = buscar_por_concepto(prompt, filtro_doc)
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

            if not hits:
                respuesta = "No encontré artículos normativos relacionados directamente con tu caso en la base de datos actual. ¿Podrías darme más contexto o detalles específicos?"
                fuentes_md = ""
                st.markdown(respuesta)
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

                fuentes_md = ""
                hits_top = hits[:MAX_FRAGMENTOS] if len(hits) > MAX_FRAGMENTOS else hits
                for h in hits_top:
                    fuentes_md += f"* **{h.get('documento', 'N/D')}** — *{h.get('articulo', 'N/D')}* ({h.get('jerarquia', 'N/D')})\n"
                
                with st.expander("📚 Ver fundamentos y normativas consultadas"):
                    st.markdown(fuentes_md)

                st.session_state.historial_rag.append((prompt, f"Ley: {filtro_doc or 'General'}"))

        st.session_state.messages.append({
            "role": "assistant",
            "content": respuesta,
            "fuentes": fuentes_md
        })