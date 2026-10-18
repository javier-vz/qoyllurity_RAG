"""Qoyllur Rit'i — explorador patrimonial de acceso sencillo.

Dos espacios de uso: conversación y catálogo. Los detalles técnicos son opcionales.
Ejecutar con: streamlit run app.py
"""
from __future__ import annotations

import os
import streamlit as st

from config_graphrag import TTL_PATH
from core.graph import HeritageGraph
from core.retrieval import Retriever
from views import preguntar, explorar

st.set_page_config(
    page_title="Qoyllur Rit'i · Explorador patrimonial",
    page_icon="🏔️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Diseño deliberadamente sobrio: más espacio en blanco, tipografía legible y
# dos destinos de navegación. No depende de fuentes o imágenes externas.
CSS = """
<style>
:root { --q-ink:#25352f; --q-green:#315a50; --q-soft:#f7f7f2;
        --q-muted:#60716b; --q-accent:#c39358; --q-edge:#e4e8e1; }
.stApp { background: #fcfcf9; color: var(--q-ink); }
.block-container { max-width: 830px; padding-top: 1.35rem; padding-bottom: 4.2rem; }
#MainMenu {visibility:hidden;}
header[data-testid="stHeader"] { background:transparent; }
h1, h2, h3 { color:var(--q-ink); letter-spacing:-.035em; }
h1 { font-weight:730; }
h2 { font-size:1.55rem; }
p { line-height:1.63; }
.q-brand { display:flex; align-items:center; gap:.65rem; margin:0 0 1.1rem; }
.q-mark { display:flex; justify-content:center; align-items:center; width:39px;
          height:39px; border-radius:13px; background:#345f54; color:white;
          font-size:1.2rem; }
.q-brand-name {font-size:1.08rem; font-weight:750; letter-spacing:-.035em; color:#253c35;}
.q-brand-note {font-size:.75rem; color:#6a7972; margin-top:-.18rem;}
.q-hero { background:linear-gradient(115deg,#e9eee4 0%, #f3f0e7 62%, #f8f6f0 100%);
          border:1px solid #e2e8df; padding:2.2rem 2.3rem 2.35rem;
          border-radius:22px; margin:1.3rem 0 1.6rem; position:relative;
          overflow:hidden; }
.q-hero:after { content:""; pointer-events:none; position:absolute; width:250px;
          height:250px; right:-125px; bottom:-155px; border:1px solid #c8d2c2;
          border-radius:50%; box-shadow:0 0 0 38px #ffffff24, 0 0 0 75px #ffffff20; }
.q-overline {font-size:.72rem; font-weight:750; text-transform:uppercase;
             letter-spacing:.14em; color:#547266; margin-bottom:1rem;}
.q-hero-title {font-size:clamp(2rem,5.5vw,2.85rem); font-weight:760;
               letter-spacing:-.055em; line-height:1.12; color:#203b31;
               margin-bottom:.9rem; max-width:640px; }
.q-hero-copy {font-size:1.04rem; line-height:1.65; color:#52665c;
              max-width:570px; margin-bottom:0; position:relative; z-index:1;}
.q-eyebrow {letter-spacing:.13em; text-transform:uppercase; color:#657a70;
            font-size:.72rem; font-weight:740; margin:.5rem 0 .8rem;}
.q-intro {font-size:1.02rem; color:#65746c; margin-top:-.1rem;}
.q-muted {color:#77867c; font-size:.83rem;}
.q-record-title {font-size:1.55rem; font-weight:730; letter-spacing:-.03em;
                 color:#263e34; margin:0 0 .4rem;}
.q-record-tag {display:inline-block; padding:.25rem .7rem; background:#edf2ec;
               border:1px solid #e2e8dd; border-radius:20px; color:#516c5f;
               font-size:.78rem; margin-bottom:1rem;}
[data-testid="stChatMessage"] {border:1px solid #e7ebe3; border-radius:16px;
   padding:1.0rem 1.05rem; background:white; margin-bottom:1rem;}
[data-testid="stChatMessage"] p {line-height:1.69;}
[data-testid="stChatInput"] {border-radius:15px;}
[data-testid="stExpander"] {border:1px solid #e6e9e3 !important;
   background:#fff; border-radius:13px !important;}
.stButton > button {border:1px solid #dfe5dc; border-radius:12px;
   padding:.48rem .85rem; transition:background-color .2s;
   color:#345449; background:#fff; font-weight:560;}
.stButton > button:hover {border-color:#95ada0; color:#254c3d;
   background:#f4f8f3;}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
   background:#345f54; border-color:#345f54; color:white;}
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover {
   background:#24493f; border-color:#24493f; color:white;}
[data-testid="stSegmentedControl"] {margin-bottom:.5rem;}
[data-testid="stSegmentedControl"] button {border-radius:10px;}
.q-rule {height:1px; background:#e8ebe5; margin:1.3rem 0 1rem;}
.q-footer {font-size:.78rem; color:#8b958c; padding-bottom:.8rem;}
@media (max-width:650px) {
 .block-container { padding:1.15rem .95rem 4rem; }
 .q-hero {padding:1.6rem 1.2rem 1.75rem; border-radius:18px; }
 .q-hero-title {font-size:2rem;}
 .q-hero-copy {font-size:.98rem;}
 [data-testid="stChatMessage"] {padding:.8rem .85rem;}
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

@st.cache_resource(show_spinner="Abriendo el archivo patrimonial…")
def graph_resource(path: str) -> HeritageGraph:
    return HeritageGraph(path)

@st.cache_resource(show_spinner="Preparando la búsqueda…")
def retriever_resource(path: str) -> Retriever:
    return Retriever(graph_resource(path), use_semantic=False)


def groq_key() -> str:
    try:
        return st.secrets.get("GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    except (FileNotFoundError, RuntimeError, KeyError):
        return os.getenv("GROQ_API_KEY", "")


try:
    store = graph_resource(str(TTL_PATH))
    retriever = retriever_resource(str(TTL_PATH))
except Exception:
    st.error("No se pudo abrir el archivo de conocimiento. Comprueba que 'qoyllurity.ttl' esté en la raíz del proyecto.")
    st.stop()

st.markdown('''<div class="q-brand"><span class="q-mark">✦</span>
<div><div class="q-brand-name">Qoyllur Rit'i</div>
<div class="q-brand-note">Explorador del patrimonio</div></div></div>''', unsafe_allow_html=True)

st.session_state.setdefault("screen", "Conversar")
st.segmented_control("Ir a", ["Conversar", "Explorar"], key="screen", label_visibility="collapsed")

if st.session_state["screen"] == "Explorar":
    explorar.render(store)
else:
    preguntar.render(store, retriever, groq_key())

st.markdown('<div class="q-rule"></div>', unsafe_allow_html=True)
with st.expander("Sobre este proyecto"):
    st.write("Un explorador del conocimiento documentado sobre la peregrinación de Qoyllur Rit'i. "
             "El archivo RDF registra principalmente la experiencia de la Nación Paucartambo en 2025; "
             "puede contener vacíos y no representa la totalidad de las tradiciones o comunidades.")
    st.write("Puedes consultar las entidades y descargar sus fichas sin IA. "
             "Cuando Groq está disponible, ayuda a redactar las respuestas y las preguntas relacionadas "
             "a partir de los registros recuperados.")
    st.markdown("[Código y datos en GitHub](https://github.com/javier-vz/qoyllurity)")
st.markdown('<div class="q-footer">Proyecto de documentación patrimonial · Cusco, Perú</div>', unsafe_allow_html=True)
