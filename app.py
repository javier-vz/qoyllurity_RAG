#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qoyllur Rit'i Explorer — v2.2
Dark mode · Mobile-first · GraphRAG v4.0 · Fichas patrimoniales
"""

import os
import re
import io
import html
from pathlib import Path
from datetime import datetime
import streamlit as st

from config_graphrag import Config

BASE_DIR = Path(__file__).resolve().parent
TTL_PATH = BASE_DIR / "qoyllurity.ttl"
IMAGES_DIR = BASE_DIR / "imagenes"

st.set_page_config(
    page_title="Qoyllur Rit'i Explorer",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.stApp { background: #0d1117 !important; font-family: 'Inter', sans-serif !important; }

.block-container {
    max-width: 700px !important;
    margin: 0 auto !important;
    padding: 0 1.25rem 4rem 1.25rem !important;
    background: transparent !important;
}

#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }

p, span, label, div, li { color: #e6edf3; }
h1,h2,h3,h4,h5,h6 { color: #e6edf3 !important; }
code { background: #21262d !important; color: #79c0ff !important; border-radius: 4px; padding: 0 4px; }

.app-header {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 0.8rem 1.25rem;
    margin: 0 -1.25rem 1.75rem -1.25rem;
    display: flex;
    align-items: center;
}
.app-header-title { font-size: 1.05rem; font-weight: 700; color: #e6edf3; margin: 0; }
.app-header-sub   { font-size: 0.72rem; color: #8b949e; margin-left: auto; }

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22 !important;
    border-radius: 8px !important;
    padding: 3px !important;
    border: 1px solid #30363d !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #8b949e !important;
    border-radius: 6px !important;
    border: none !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    padding: 0.45rem 1.1rem !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: #21262d !important;
    color: #e6edf3 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* INPUTS */
.stTextInput > div > div > input {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 0.9rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #d4a017 !important;
    box-shadow: 0 0 0 2px rgba(212,160,23,.2) !important;
}
.stTextInput > div > div > input::placeholder { color: #8b949e !important; }
.stTextInput label { color: #8b949e !important; font-size: 0.8rem !important; }

/* TEXTAREA */
.stTextArea > div > div > textarea {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
    font-size: 0.88rem !important;
    line-height: 1.7 !important;
}

/* SELECTBOX */
.stSelectbox > div > div {
    background: #21262d !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #e6edf3 !important;
}
.stSelectbox label { color: #8b949e !important; font-size: 0.8rem !important; }
.stSelectbox > div > div > div { color: #e6edf3 !important; }
[data-baseweb="popover"],
[data-baseweb="popover"] > div,
[data-baseweb="popover"] > div > div { background: #21262d !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
[data-baseweb="menu"] { background: #21262d !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
[data-baseweb="menu"] ul, [data-baseweb="menu"] li { background: #21262d !important; color: #e6edf3 !important; }
[role="listbox"], [role="listbox"] > div, [role="listbox"] li, [role="option"] { background: #21262d !important; color: #e6edf3 !important; font-size: 0.88rem !important; }
[role="option"]:hover { background: #30363d !important; }
[aria-selected="true"][role="option"] { background: #30363d !important; color: #e6edf3 !important; }
[data-baseweb="popover"] * { color: #e6edf3 !important; }
[data-baseweb="popover"] div { background: #21262d !important; }

/* RADIO */
.stRadio > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    padding: 0.5rem 0.75rem !important;
    gap: 1.5rem !important;
}
.stRadio label { color: #adbac7 !important; font-size: 0.85rem !important; }

/* BOTONES */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border: none !important;
    transition: all .15s !important;
}
.stButton > button[kind="primary"] {
    background: #d4a017 !important;
    color: #000 !important;
    width: 100% !important;
    padding: 0.6rem !important;
    box-shadow: 0 2px 8px rgba(212,160,23,.3) !important;
}
.stButton > button[kind="primary"]:hover { background: #b8891a !important; }
.stButton > button[kind="secondary"] {
    background: #21262d !important;
    color: #8b949e !important;
    border: 1px solid #30363d !important;
    width: 100% !important;
}

/* EXPANDER */
.streamlit-expanderHeader {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #8b949e !important;
    font-size: 0.83rem !important;
}
.streamlit-expanderContent {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-top: none !important;
}

/* INFO/ALERT */
.stAlert > div {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    color: #8b949e !important;
}

/* METRICS */
[data-testid="metric-container"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
    padding: 0.85rem 1rem !important;
}
[data-testid="stMetricValue"] { color: #d4a017 !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.72rem !important; }

/* DIVIDER */
hr { border-color: #30363d !important; margin: 1rem 0 !important; }

/* CHAT */
.msg-user {
    background: rgba(31,111,235,.1);
    border: 1px solid rgba(56,139,253,.25);
    border-radius: 10px 10px 4px 10px;
    padding: 0.8rem 1rem;
    margin: 0.6rem 0;
}
.msg-user .lbl { font-size:0.68rem; font-weight:700; color:#58a6ff; text-transform:uppercase; letter-spacing:.5px; margin-bottom:5px; }
.msg-user .txt { font-size:0.88rem; color:#e6edf3; }

.msg-bot {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #d4a017;
    border-radius: 4px 10px 10px 10px;
    padding: 0.8rem 1rem;
    margin: 0.6rem 0;
}
.msg-bot .lbl { font-size:0.68rem; font-weight:700; color:#d4a017; text-transform:uppercase; letter-spacing:.5px; margin-bottom:5px; }
.msg-bot .txt { font-size:0.88rem; color:#adbac7; line-height:1.7; }

/* ABOUT */
.about-sec {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.85rem;
}
.about-sec h4 { font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:.5px; color:#d4a017; margin:0 0 0.6rem 0; }
.about-sec p  { font-size:0.84rem; line-height:1.72; color:#adbac7; margin:0; }
.about-sec p+p { margin-top:0.5rem; }

.chips { display:flex; flex-wrap:wrap; gap:0.3rem; margin-top:0.6rem; }
.chip  { font-size:0.67rem; padding:0.18rem 0.5rem; border-radius:4px; font-family:monospace; border:1px solid #30363d; background:rgba(255,255,255,.04); color:#adbac7; }
.chip.b{ background:rgba(56,139,253,.1); border-color:rgba(56,139,253,.3); color:#79c0ff; }
.chip.g{ background:rgba(212,160,23,.1);  border-color:rgba(212,160,23,.3);  color:#d4a017; }

/* FICHA */
.ficha-box {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1.25rem 1.35rem;
    margin-top: 1rem;
    font-size: 0.88rem;
    line-height: 1.75;
    color: #adbac7;
    white-space: pre-wrap;
}
.ficha-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
.ficha-tag {
    font-size: 0.68rem;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    border: 1px solid #30363d;
    background: rgba(212,160,23,.08);
    color: #d4a017;
    font-weight: 600;
}

/* FOOTER */
.tfooter { text-align:center; padding:1.5rem 0 0.5rem; border-top:1px solid #30363d; margin-top:2rem; }
.tfooter p { font-size:0.72rem; color:#8b949e; margin:0.2rem 0; }
.empty-state { text-align:center; padding:2.5rem 1rem; color:#8b949e; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)

# ── PDF GENERATOR ─────────────────────────────────────────────────────────────
def generar_ficha_pdf(texto: str, entidad: str, tipo: str) -> bytes:
    """
    Genera un PDF de ficha patrimonial con reportlab.
    Busca imagen en imagenes/ para incluirla en la portada.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
        Table, TableStyle, Image, KeepTogether
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    PAGE_W, PAGE_H = A4
    GOLD   = colors.HexColor("#d4a017")
    DARK   = colors.HexColor("#0d1117")
    SURF   = colors.HexColor("#161b22")
    MUTED  = colors.HexColor("#8b949e")
    LIGHT  = colors.HexColor("#e6edf3")
    WHITE  = colors.white

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.2*cm, rightMargin=2.2*cm,
        topMargin=2*cm,    bottomMargin=2*cm,
        title=f"Ficha Patrimonial — {entidad}",
        author="Qoyllur Rit'i Explorer · GraphRAG v4.0",
        subject="Patrimonio Cultural Inmaterial",
    )

    # ── Estilos ───────────────────────────────────────────────────────────────
    def sty(name, **kw):
        return ParagraphStyle(name, **kw)

    s_title = sty("title",
        fontSize=20, leading=24, textColor=GOLD,
        fontName="Helvetica-Bold", spaceAfter=4,
        alignment=TA_LEFT)

    s_subtitle = sty("subtitle",
        fontSize=10, leading=13, textColor=MUTED,
        fontName="Helvetica", spaceAfter=2,
        alignment=TA_LEFT)

    s_meta = sty("meta",
        fontSize=8, leading=11, textColor=MUTED,
        fontName="Helvetica", spaceAfter=0)

    s_sec_header = sty("sec_header",
        fontSize=8, leading=10, textColor=GOLD,
        fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=4,
        textTransform="uppercase", letterSpacing=0.8)

    s_body = sty("body",
        fontSize=9.5, leading=15, textColor=LIGHT,
        fontName="Helvetica", spaceAfter=4,
        alignment=TA_JUSTIFY)

    s_footer = sty("footer",
        fontSize=7.5, leading=10, textColor=MUTED,
        fontName="Helvetica", alignment=TA_CENTER)

    # ── Fondo oscuro (canvas callback) ────────────────────────────────────────
    def dark_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # franja dorada izquierda
        canvas.setFillColor(GOLD)
        canvas.rect(0, 0, 0.35*cm, PAGE_H, fill=1, stroke=0)
        # footer line
        canvas.setStrokeColor(colors.HexColor("#30363d"))
        canvas.setLineWidth(0.5)
        canvas.line(2.2*cm, 1.6*cm, PAGE_W - 2.2*cm, 1.6*cm)
        # footer text
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(2.2*cm, 1.1*cm,
            f"Qoyllur Rit'i Explorer · GraphRAG v4.0 · Nación Paucartambo · 2025")
        canvas.drawRightString(PAGE_W - 2.2*cm, 1.1*cm,
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        canvas.restoreState()

    # ── Contenido ─────────────────────────────────────────────────────────────
    story = []

    # Imagen del Apu (si existe)
    img_path = None
    for ext in ["jpg", "jpeg", "png", "webp"]:
        for fname in ["apu", "ausangate", "qoylluriti", "imagen"]:
            p = IMAGES_DIR / f"{fname}.{ext}"
            if p.exists():
                img_path = p
                break
        if img_path:
            break
    # También intentar cualquier imagen en la carpeta
    if not img_path and IMAGES_DIR.exists():
        for f in sorted(IMAGES_DIR.iterdir()):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                img_path = f
                break

    if img_path:
        try:
            from PIL import Image as PILImage
            pil = PILImage.open(img_path)
            orig_w, orig_h = pil.size
            img_w = PAGE_W - 4.4*cm
            img_h = img_w * orig_h / orig_w  # mantener proporcion
            if img_h > 7*cm:
                img_h = 7*cm
                img_w = img_h * orig_w / orig_h
            img = Image(str(img_path), width=img_w, height=img_h)
            img.hAlign = "LEFT"
            story.append(img)
            story.append(Spacer(1, 0.4*cm))
        except Exception:
            pass

    # Header: tipo + título
    story.append(Paragraph(html.escape(tipo.upper()), s_subtitle))
    story.append(Paragraph(html.escape(entidad), s_title))
    story.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor("#30363d"),
        spaceAfter=6, spaceBefore=4
    ))
    story.append(Paragraph(
        f"Festividad del Señor de Qoyllur Rit'i &nbsp;·&nbsp; Nación Paucartambo &nbsp;·&nbsp; Cusco, Perú",
        s_meta
    ))
    story.append(Spacer(1, 0.5*cm))

    # Limpiar markdown del texto LLM antes de parsear
    def strip_md(t):
        t = re.sub(r'\*\*([^*]+)\*\*', r'\1', t)   # **bold**
        t = re.sub(r'\*([^*]+)\*',     r'\1', t)   # *italic*
        t = re.sub(r'^#+\s*', '', t, flags=re.MULTILINE)  # # headers
        t = re.sub(r'^_{1,3}|_{1,3}$', '', t, flags=re.MULTILINE)
        return t

    texto = strip_md(texto)

    # Parsear secciones del texto generado por el LLM
    # Formato esperado: "1. DENOMINACIÓN\n...\n2. ÁMBITO\n..."
    sections = re.split(r'\n(?=\d+\.\s+[A-ZÁÉÍÓÚÑÜ])', texto.strip())

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        lines = sec.split('\n', 1)
        header_line = lines[0].strip()
        body_text   = lines[1].strip() if len(lines) > 1 else ""

        # Remove leading number+dot
        header_clean = re.sub(r'^\d+\.\s*', '', header_line)

        block = []
        block.append(Paragraph(html.escape(header_clean), s_sec_header))
        block.append(HRFlowable(
            width="100%", thickness=0.5,
            color=colors.HexColor("#30363d"),
            spaceAfter=5, spaceBefore=0
        ))

        if body_text:
            # Split bullet-style lines
            for line in body_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # Escape XML chars
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                if line.startswith('-'):
                    line = f"&nbsp;&nbsp;• {line[1:].strip()}"
                block.append(Paragraph(line, s_body))

        story.append(KeepTogether(block))

    story.append(Spacer(1, 1*cm))

    # Build
    doc.build(story, onFirstPage=dark_background, onLaterPages=dark_background)
    return buf.getvalue()


# ── TTL PARSER ────────────────────────────────────────────────────────────────
@st.cache_resource
def cargar_entidades_ttl(ttl_path: str = str(TTL_PATH)) -> dict:
    """Lee individuos y relaciones desde el RDF real (sin regex frágiles)."""
    from rdflib import Graph, Literal, URIRef
    from rdflib.namespace import RDF, RDFS, OWL

    if not Path(ttl_path).exists():
        return {}

    grafo = Graph()
    grafo.parse(ttl_path, format="turtle")
    TYPE_PRIORITY = [
        "Nacion", "LugarSagrado", "Apu", "Lugar", "EventoRitual",
        "Danza", "Vestimenta", "ObjetoRitual", "Ukumari"
    ]
    TYPE_LABELS = {
        "Nacion": "🏳️ Nación", "LugarSagrado": "🏔️ Lugar Sagrado",
        "Apu": "⛰️ Apu", "Lugar": "📍 Lugar", "EventoRitual": "🎭 Evento Ritual",
        "Danza": "💃 Danza", "Vestimenta": "👘 Vestimenta",
        "ObjetoRitual": "🔮 Objeto Ritual", "Ukumari": "🐻 Ukumari",
    }

    def nombre_local(uri):
        return str(uri).rsplit("#", 1)[-1].rsplit("/", 1)[-1]

    def literal_pref(literals):
        vals = list(literals)
        return next((str(x) for x in vals if getattr(x, "language", None) == "es"),
                    str(vals[0]) if vals else "")

    grouped = {tipo: [] for tipo in TYPE_PRIORITY}
    full = {}
    individuos = set(grafo.subjects(RDF.type, OWL.NamedIndividual))
    for subj in individuos:
        eid = nombre_local(subj)
        label = literal_pref(grafo.objects(subj, RDFS.label))
        if not label:
            continue
        tipos = sorted({nombre_local(x) for x in grafo.objects(subj, RDF.type)
                        if x != OWL.NamedIndividual})
        comentario = literal_pref(grafo.objects(subj, RDFS.comment))
        rels, data_props = [], {}
        for pred, obj in grafo.predicate_objects(subj):
            if pred in (RDF.type, RDFS.label, RDFS.comment):
                continue
            pred_name = nombre_local(pred)
            if isinstance(obj, URIRef) and obj in individuos:
                rels.append((pred_name, nombre_local(obj)))
            elif isinstance(obj, Literal):
                data_props[pred_name] = str(obj)
        full[eid] = {
            "label": label, "tipos": tipos, "comment": comentario,
            "rels": sorted(set(rels)), "data_props": data_props,
        }
        for tipo in TYPE_PRIORITY:
            if tipo in tipos:
                grouped[tipo].append((eid, label))
                break
    for tipo in grouped:
        grouped[tipo].sort(key=lambda x: x[1].casefold())
    return {"grouped": grouped, "labels": TYPE_LABELS, "full": full}

def construir_contexto_ficha(eid: str, datos: dict) -> str:
    """Build a rich context string for the LLM from TTL data."""
    full = datos.get('full', {})
    ent = full.get(eid)
    if not ent:
        return ""

    lines = []
    lines.append(f"ENTIDAD: {ent['label']}")
    lines.append(f"TIPO(S): {', '.join(ent['tipos'])}")
    if ent['comment']:
        lines.append(f"DESCRIPCIÓN: {ent['comment']}")

    if ent['data_props']:
        lines.append("\nPROPIEDADES:")
        for k, v in ent['data_props'].items():
            lines.append(f"  - {k}: {v}")

    if ent['rels']:
        lines.append("\nRELACIONES:")
        # Resolve labels where possible
        for pred, obj in ent['rels']:
            obj_label = full.get(obj, {}).get('label', obj.replace('_', ' '))
            lines.append(f"  - {pred}: {obj_label}")

    # Also find inverse relations (who points to this entity)
    inv = []
    for other_id, other in full.items():
        if other_id == eid:
            continue
        for pred, obj in other.get('rels', []):
            if obj == eid:
                inv.append(f"  - {other['label']} → {pred} → {ent['label']}")
    if inv:
        lines.append("\nRELACIONES INVERSAS (quién menciona esta entidad):")
        lines.extend(inv[:10])

    return '\n'.join(lines)

# ── ESTADO ────────────────────────────────────────────────────────────────────
if 'mensajes' not in st.session_state:
    st.session_state.mensajes = []
if 'ficha_generada' not in st.session_state:
    st.session_state.ficha_generada = None
if 'ficha_entidad' not in st.session_state:
    st.session_state.ficha_entidad = None

def agregar_mensaje(tipo, texto):
    st.session_state.mensajes.append({'tipo': tipo, 'texto': texto})

def limpiar_chat():
    st.session_state.mensajes = []

# ── PREGUNTAS ─────────────────────────────────────────────────────────────────
PREGUNTAS = [
    "¿Qué es Qoyllur Rit'i?",
    "¿Dónde está el santuario?",
    "Háblame de la vestimenta de los ukukus",
    "¿Qué es el Ausangate?",
    "¿Dónde está Sinakara?",
    "¿Dónde está el glaciar Colque Punku?",
    "¿Qué hacen los ukukus?",
    "¿Qué es la lomada?",
    "¿Cuánto dura la lomada?",
    "¿Qué naciones participan?",
    "¿Cuál es el recorrido de la peregrinación?",
]

# ── MOTOR ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def cargar_motor(groq_key: str):
    from graphrag_v4_api import GraphRAG_v4_API
    return GraphRAG_v4_API(ttl_path=str(TTL_PATH), groq_api_key=groq_key, verbose=False)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="app-header-title">🏔 Qoyllur Rit'i</div>
    <div class="app-header-sub">GraphRAG Explorer</div>
</div>
""", unsafe_allow_html=True)

# ── API KEY (global, shared across tabs) ──────────────────────────────────────
groq_key = ""
try:
    groq_key = st.secrets.get("GROQ_API_KEY", "")
except Exception:
    pass
if not groq_key:
    groq_key = os.getenv("GROQ_API_KEY", "")
if not groq_key:
    groq_key = st.text_input(
        "🔑 Groq API Key",
        placeholder="gsk_...",
        type="password",
        help="Obtén tu key gratis en console.groq.com"
    )
if not groq_key:
    st.info("Ingresa tu Groq API key para activar el asistente.")
    st.stop()

# ── TABS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<p style="font-size:.82rem;color:#8b949e;line-height:1.65;margin-bottom:.75rem">
Explora el conocimiento documentado sobre el Señor de Qoyllur Rit'i: consulta en lenguaje
natural sobre la festividad, genera fichas patrimoniales en PDF por entidad, o revisa
los detalles del proyecto y la ontología.
</p>
""", unsafe_allow_html=True)

tab_chat, tab_fichas, tab_about = st.tabs(["💬  Consultas", "📋  Fichas", "ℹ️  Acerca de"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB CONSULTAS
# ─────────────────────────────────────────────────────────────────────────────
with tab_chat:
    try:
        with st.spinner("Inicializando sistema..."):
            motor = cargar_motor(groq_key)
    except ImportError as e:
        st.error(f"Archivo faltante: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error al inicializar: {e}")
        st.stop()

    modo = st.radio(
        "modo", ["📋 Preguntas sugeridas", "✍️ Pregunta libre"],
        horizontal=True, label_visibility="collapsed"
    )

    pregunta = ""
    if modo == "📋 Preguntas sugeridas":
        pregunta = st.selectbox(
            "pregunta", options=[""] + PREGUNTAS,
            format_func=lambda x: "Selecciona una pregunta..." if x == "" else x,
            label_visibility="collapsed"
        )
    else:
        pregunta = st.text_input(
            "pregunta", placeholder="¿Dónde está el glaciar Colque Punku?",
            label_visibility="collapsed"
        )
        with st.expander("💡 Ver ejemplos"):
            for p in PREGUNTAS[:6]:
                st.markdown(f"- {p}")

    if st.button("✨  Preguntar", type="primary", use_container_width=True):
        if pregunta:
            with st.spinner("Consultando grafo de conocimiento..."):
                try:
                    respuesta = motor.responder(pregunta, use_api=True, modo="hibrido", verbose=False)
                except Exception as e:
                    # Los fallos de API deben ser avisos, no respuestas del asistente.
                    st.error(f"No se pudo completar la consulta: {e}")
                else:
                    agregar_mensaje('user', pregunta)
                    agregar_mensaje('bot', respuesta)
                    st.rerun()

    if st.session_state.mensajes:
        st.markdown("---")
        for msg in reversed(st.session_state.mensajes):
            if msg['tipo'] == 'user':
                st.markdown(f'<div class="msg-user"><div class="lbl">Tú</div><div class="txt">{html.escape(str(msg["texto"])).replace(chr(10), "<br>")}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg-bot"><div class="lbl">Asistente</div><div class="txt">{html.escape(str(msg["texto"])).replace(chr(10), "<br>")}</div></div>', unsafe_allow_html=True)
        st.markdown(" ")
        if st.button("🗑️  Limpiar historial", use_container_width=True):
            limpiar_chat()
            st.rerun()
    else:
        st.markdown('<div class="empty-state">Selecciona o escribe una pregunta para comenzar</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB FICHAS
# ─────────────────────────────────────────────────────────────────────────────
with tab_fichas:

    datos = cargar_entidades_ttl(str(TTL_PATH))
    if not datos:
        st.error("No se pudo cargar qoyllurity.ttl")
        st.stop()

    grouped = datos['grouped']
    type_labels = datos['labels']

    # ── Selector de tipo ──────────────────────────────────────────────────────
    tipos_disponibles = [t for t in grouped if grouped[t]]
    tipo_opts = {type_labels[t]: t for t in tipos_disponibles}

    tipo_sel_label = st.selectbox(
        "Tipo de entidad",
        options=list(tipo_opts.keys()),
        label_visibility="visible"
    )
    tipo_sel = tipo_opts[tipo_sel_label]

    # ── Selector de entidad ───────────────────────────────────────────────────
    entidades = grouped[tipo_sel]
    ent_opts  = {label: eid for eid, label in entidades}

    ent_sel_label = st.selectbox(
        "Entidad",
        options=list(ent_opts.keys()),
        label_visibility="visible"
    )
    ent_sel_id = ent_opts[ent_sel_label]

    # ── Vista previa del contexto ─────────────────────────────────────────────
    contexto = construir_contexto_ficha(ent_sel_id, datos)
    with st.expander("🔍 Ver datos del grafo", expanded=False):
        st.code(contexto, language=None)

    # ── Generar ficha ─────────────────────────────────────────────────────────
    if st.button("📋  Generar ficha patrimonial", type="primary", use_container_width=True):
        prompt = f"""Eres un experto en patrimonio cultural inmaterial peruano. 
A partir de los siguientes datos extraídos de una ontología OWL/RDF sobre la festividad del Señor de Qoyllur Rit'i, 
redacta una ficha patrimonial completa y precisa.

DATOS DEL GRAFO:
{contexto}

Redacta la ficha con las siguientes secciones claramente separadas:
1. DENOMINACIÓN
2. ÁMBITO (categoría de patrimonio inmaterial según UNESCO/Ministerio de Cultura)
3. DESCRIPCIÓN (párrafo narrativo, 3-5 oraciones)
4. COMUNIDAD PORTADORA
5. LOCALIZACIÓN GEOGRÁFICA (si aplica)
6. ELEMENTOS ASOCIADOS (objetos, danzas, vestimentas, lugares o eventos relacionados)
7. SIGNIFICADO RITUAL Y SIMBÓLICO

Usa solo la información provista en los datos. Si un campo no aplica, indícalo brevemente.
Escribe en español formal, en tercera persona."""

        with st.spinner("Generando ficha con IA..."):
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                
                resp = client.chat.completions.create(
                    model=Config.MODELO_GROQ,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=Config.TEMPERATURE_FICHA,
                    max_tokens=Config.MAX_TOKENS_FICHA,
                    reasoning_effort=Config.REASONING_EFFORT,
                    include_reasoning=False,
                )

                ficha_texto = (resp.choices[0].message.content or "").strip()
                if not ficha_texto:
                    raise RuntimeError("Groq devolvió una ficha vacía.")
                st.session_state.ficha_generada  = ficha_texto
                st.session_state.ficha_entidad   = ent_sel_label
            except Exception as e:
                st.error(f"Error al generar ficha: {e}")

    # ── Mostrar ficha generada ────────────────────────────────────────────────
    if st.session_state.ficha_generada and st.session_state.ficha_entidad == ent_sel_label:
        st.markdown(f"""
<div class="ficha-meta">
  <span class="ficha-tag">📋 Ficha Patrimonial</span>
  <span class="ficha-tag">{html.escape(tipo_sel_label)}</span>
  <span class="ficha-tag">Qoyllur Rit'i · 2025</span>
</div>""", unsafe_allow_html=True)

        # Renderizar texto limpio (sin markdown) como HTML
        import html as _html
        def _render_ficha_html(texto):
            """Convierte el texto de la ficha a HTML limpio."""
            import re as _re
            # Strip markdown
            texto = _re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', texto)
            texto = _re.sub(r'\*([^*]+)\*', r'\1', texto)
            texto = _re.sub(r'^#+\s*', '', texto, flags=_re.MULTILINE)
            lines = texto.strip().split('\n')
            html_parts = []
            for line in lines:
                line = line.strip()
                if not line:
                    html_parts.append('<div style="height:.5rem"></div>')
                    continue
                # Section headers: "1. DENOMINACIÓN" or "**1. DENOMINACIÓN**"
                m = _re.match(r'^(\d+\.\s+[A-ZÁÉÍÓÚÑÜ ]+)$', line.replace('<strong>','').replace('</strong>',''))
                if m:
                    clean = _re.sub(r'</?strong>', '', line)
                    html_parts.append(f'<div style="font-size:.7rem;font-weight:700;color:#d4a017;text-transform:uppercase;letter-spacing:.6px;margin-top:1.1rem;margin-bottom:.3rem;padding-bottom:.25rem;border-bottom:1px solid #30363d">{_html.escape(clean)}</div>')
                elif line.startswith('•') or line.startswith('-'):
                    txt = _html.escape(line.lstrip('•- ').strip())
                    html_parts.append(f'<div style="font-size:.86rem;color:#adbac7;line-height:1.65;padding-left:1rem">• {txt}</div>')
                else:
                    txt = line  # already has <strong> tags if needed
                    # escape everything except allowed tags
                    txt = _re.sub(r'<strong>(.*?)</strong>', lambda m: '<b>'+_html.escape(m.group(1))+'</b>', txt)
                    txt = _html.escape(txt).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')
                    html_parts.append(f'<div style="font-size:.86rem;color:#adbac7;line-height:1.7">{txt}</div>')
            return ''.join(html_parts)

        ficha_html = _render_ficha_html(st.session_state.ficha_generada)
        st.markdown(f'''
<div style="background:#161b22;border:1px solid #30363d;border-radius:10px;
padding:1.25rem 1.35rem;margin-bottom:.75rem">
{ficha_html}
</div>''', unsafe_allow_html=True)

        try:
            pdf_bytes = generar_ficha_pdf(
                st.session_state.ficha_generada,
                entidad=ent_sel_label,
                tipo=tipo_sel_label
            )
            st.download_button(
                label="⬇️  Descargar ficha (.pdf)",
                data=pdf_bytes,
                file_name=f"ficha_{ent_sel_id}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e_pdf:
            st.warning(f"PDF no disponible (instala reportlab): {e_pdf}")
            st.download_button(
                label="⬇️  Descargar ficha (.txt)",
                data=st.session_state.ficha_generada,
                file_name=f"ficha_{ent_sel_id}.txt",
                mime="text/plain",
                use_container_width=True,
            )

# ─────────────────────────────────────────────────────────────────────────────
# TAB ACERCA DE
# ─────────────────────────────────────────────────────────────────────────────
with tab_about:
    st.markdown("""
<div class="about-sec">
<h4>🏔 La festividad</h4>
<p>El Señor de Qoyllur Rit'i es una peregrinación andina que sincretiza el catolicismo
colonial con tradiciones ancestrales en torno al Apu Ausangate, espíritu protector de
la montaña más alta del Cusco (6,384 msnm). La festividad reúne a múltiples
<em>naciones</em> —comunidades con identidad ritual propia— que participan con danzas,
vestimentas ceremoniales y rituales específicos.</p>
<p>Entre sus elementos centrales destacan la subida nocturna de los Ukumaris al glaciar
Colque Punku (5,200 msnm), la <em>Lomada</em> —caminata ritual de 24 horas— y las
procesiones de las distintas naciones peregrinas. Declarada Patrimonio Cultural
Inmaterial de la Humanidad por la UNESCO.</p>
</div>
<div class="about-sec">
<h4>🔬 El proyecto</h4>
<p>Esta aplicación forma parte de una investigación sobre <strong>grafos de conocimiento
para el patrimonio inmaterial peruano</strong>. La ontología fue construida a partir de
trabajo de campo etnográfico con la Nación Paucartambo en la edición 2025.</p>
<p>El sistema implementa un pipeline <strong>GraphRAG</strong>
(<em>Retrieval-Augmented Generation</em>) que combina búsqueda semántica sobre el grafo
RDF con generación de lenguaje natural, permitiendo consultas en lenguaje natural sobre
el conocimiento documentado.</p>
</div>
<div class="about-sec">
<h4>⚙️ Stack técnico</h4>
<div class="chips">
  <span class="chip g">GraphRAG v4.0</span>
  <span class="chip g">Knowledge Graph</span>
  <span class="chip g">Patrimonio Inmaterial</span>
  <span class="chip b">OWL 2</span>
  <span class="chip b">Turtle (.ttl)</span>
  <span class="chip b">RDF / RDFS</span>
  <span class="chip">Groq API</span>
  <span class="chip">Groq GPT-OSS</span>
  <span class="chip">sentence-transformers</span>
  <span class="chip">rdflib</span>
  <span class="chip">Streamlit</span>
</div>
</div>
<div class="about-sec">
<h4>📐 Arquitectura</h4>
<p>La ontología modela eventos rituales, lugares sagrados, participantes, objetos
ceremoniales, danzas y vestimentas. La búsqueda híbrida combina embeddings semánticos
(<code>paraphrase-multilingual-MiniLM-L12-v2</code>) con coincidencia léxica para recuperar
las entidades más relevantes. El contexto se entrega al LLM junto con un prompt que
prioriza precisión factual sobre interpretación libre.</p>
</div>
""", unsafe_allow_html=True)

    try:
        from rdflib import Graph as RDFGraph
        _g = RDFGraph()
        _g.parse(str(TTL_PATH), format='turtle')
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Tripletas RDF", len(_g))
        with c2:
            st.metric("Entidades", len(set(s for s, _, _ in _g)))
        with c3:
            st.metric("Propiedades", len(set(p for _, p, _ in _g)))
    except Exception:
        pass

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tfooter">
    <p>🏔️ <b>Qoyllur Rit'i Explorer</b> · GraphRAG v4.0</p>
    <p>Knowledge Graph + RAG · Datos de campo · Nación Paucartambo · 2025</p>
    <p style="color:#30363d;font-size:0.65rem;margin-top:0.3rem;">
        OWL 2 / Turtle · Groq API · Embeddings multilingües
    </p>
</div>
""", unsafe_allow_html=True)
