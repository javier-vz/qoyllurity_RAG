"""Pantalla principal: un único chat, sin controles técnicos innecesarios."""
from __future__ import annotations

import streamlit as st

from core.graph import HeritageGraph
from core.retrieval import Retriever
from core.assistant import answer_question
from views.shared import show_evidence

MAX_API_CALLS_SESSION = 20
SUGGESTED_STARTERS = [
    "¿Qué es Qoyllur Rit'i?",
    "¿Quiénes son los ukukus?",
    "¿Qué ocurre en el Sinakara?",
]


def _queue_question(question: str) -> None:
    st.session_state["pending_question"] = question


def _clear_chat() -> None:
    st.session_state["chat_history"] = []
    st.session_state.pop("previous_eid", None)
    st.session_state.pop("pending_question", None)


def render(store: HeritageGraph, retriever: Retriever, api_key: str | None) -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("groq_calls", 0)
    history = st.session_state["chat_history"]

    if not history:
        st.markdown('''<div class="q-hero">
          <div class="q-overline">PATRIMONIO CULTURAL · CUSCO</div>
          <div class="q-hero-title">Descubre Qoyllur Rit'i,<br>a tu ritmo.</div>
          <p class="q-hero-copy">Pregunta por sus lugares, participantes y celebraciones.
          Explora las historias que reúne nuestro archivo patrimonial.</p>
        </div>''', unsafe_allow_html=True)
        st.markdown('<div class="q-eyebrow">Puedes empezar por aquí</div>', unsafe_allow_html=True)
        cols = st.columns(3, gap="small")
        for col, question in zip(cols, SUGGESTED_STARTERS):
            with col:
                st.button(question, key="starter_" + question, use_container_width=True,
                          on_click=_queue_question, args=(question,))
        st.caption("O escribe tu propia pregunta en el cuadro inferior.")
    else:
        left, right = st.columns([4, 1], vertical_alignment="center")
        with left:
            st.markdown("### Tu conversación")
        with right:
            st.button("Reiniciar", icon="🔄", key="clear_chat", use_container_width=True,
                      on_click=_clear_chat, help="Iniciar una conversación nueva")

    for ix, message in enumerate(history):
        assistant = message.get("role") == "assistant"
        with st.chat_message("assistant" if assistant else "user", avatar="🏔️" if assistant else None):
            st.markdown(message.get("text", ""))
            if assistant:
                # Las evidencias son consultables, pero no abruman la conversación.
                show_evidence(message.get("evidence", []), store, key_prefix=f"chat_{ix}")
                if ix == len(history) - 1 and message.get("suggestions"):
                    st.caption("Si quieres, también puedes preguntar:")
                    # Todas las sugerencias son generadas por el LLM.
                    for j, question in enumerate(message["suggestions"][:3]):
                        st.button("↗ " + question, key=f"followup_{ix}_{j}",
                                  on_click=_queue_question, args=(question,))
                if message.get("status") not in ("groq", None):
                    st.caption("Respuesta construida con los datos del archivo.")

    if not api_key and not history:
        st.caption("El asistente usa los registros disponibles; las explicaciones ampliadas requieren que el proyecto tenga Groq configurado.")

    typed = st.chat_input("Escribe lo que te gustaría saber…", max_chars=500)
    question = st.session_state.pop("pending_question", None) or typed
    if not question:
        return
    if len(history) >= 40:
        st.warning("La conversación es muy larga. Pulsa «Reiniciar» para comenzar otra.")
        return
    use_api = api_key if st.session_state["groq_calls"] < MAX_API_CALLS_SESSION else None
    if api_key and use_api:
        st.session_state["groq_calls"] += 1
    with st.spinner("Buscando en el archivo…"):
        result = answer_question(store, retriever, question, use_api,
                                 st.session_state.get("previous_eid"), history)
    history.extend([
        {"role": "user", "text": question},
        {"role": "assistant", "text": result.text, "evidence": result.evidence,
         "ids": result.ids, "suggestions": result.suggestions, "status": result.status},
    ])
    if result.ids:
        st.session_state["previous_eid"] = result.ids[0]
    st.rerun()
