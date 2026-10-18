"""Qoyllur Rit'i Explorer 3.0 — Etapa 1.

Navegación para visitantes y profundidad opcional para investigación.
Ejecución: streamlit run app.py
"""
from __future__ import annotations
import os
import streamlit as st
from config_graphrag import TTL_PATH
from core.graph import HeritageGraph
from core.retrieval import Retriever
from views import inicio, preguntar, explorar, fichas, proyecto

st.set_page_config(page_title="Qoyllur Rit'i Explorer 3.0", page_icon='🏔️',
                   layout='wide', initial_sidebar_state='collapsed')

STYLE = """
<style>
:root { --ink: #1d2e36; --warm: #b58a40; }
.stApp { color: #24343c; }
.block-container { max-width: 1040px; padding-top: 1.7rem; padding-bottom: 4rem; }
h1, h2, h3 { letter-spacing: -.025em; }
h1 { font-size: clamp(2rem, 4vw, 3rem) !important; color: #23353e; }
h2, h3 { color: #263a43; }
.eyebrow { font-size:.77rem; letter-spacing:.16em; color: #946d29; font-weight:700; margin:0 0 .7rem; }
.home-emoji { font-size:1.8rem; margin-bottom:.35rem; }
[data-testid="stMetric"] { border:1px solid #e3dcca; padding:1rem; border-radius:.8rem; }
[data-testid="stChatMessage"] { border-radius: 14px; border:1px solid #e7e2d8; }
a { color:#855f26; }
@media(max-width:600px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top:1rem; }
  h1 { font-size: 2rem !important; }
}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

@st.cache_resource(show_spinner='Cargando grafo RDF…')
def load_graph(path: str):
    return HeritageGraph(path)

@st.cache_resource(show_spinner='Preparando el buscador documental…')
def load_retriever(path: str):
    graph = load_graph(path)
    return Retriever(graph, use_semantic=False)


def groq_key():
    try:
        return st.secrets.get('GROQ_API_KEY', '') or os.getenv('GROQ_API_KEY', '')
    except (FileNotFoundError, RuntimeError, KeyError):
        return os.getenv('GROQ_API_KEY', '')


try:
    store = load_graph(str(TTL_PATH))
    retriever = load_retriever(str(TTL_PATH))
except Exception:
    st.error('No se pudo cargar el archivo RDF o el índice. Verifica que qoyllurity.ttl esté en la raíz del repositorio.')
    st.stop()

# st.Page acepta funciones: cada pantalla hereda la configuración visual anterior.
def page_home():
    inicio.render(store)

def page_chat():
    preguntar.render(store, retriever, groq_key())

def page_explore():
    explorar.render(store)

def page_cards():
    fichas.render(store)

def page_about():
    proyecto.render(store)

pages = [
    st.Page(page_home, title='Inicio', icon='🏠', url_path='inicio', default=True),
    st.Page(page_chat, title='Preguntar', icon='💬', url_path='preguntar'),
    st.Page(page_explore, title='Explorar', icon='🧭', url_path='explorar'),
    st.Page(page_cards, title='Fichas', icon='📖', url_path='fichas'),
    st.Page(page_about, title='Proyecto', icon='ℹ️', url_path='proyecto'),
]
st.session_state['_page_chat'] = pages[1]
st.session_state['_page_fichas'] = pages[3]
selected = st.navigation(pages, position='top')
selected.run()
st.divider()
st.caption('Qoyllur Rit\'i Explorer · Registro documental basado en el grafo RDF. Cobertura principal: Nación Paucartambo, 2025.')
