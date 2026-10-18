import streamlit as st
from core.graph import HeritageGraph
from core.retrieval import Retriever
from core.assistant import answer_question
from views.shared import show_evidence

MAX_API_CALLS_SESSION = 20


def render(store: HeritageGraph, retriever: Retriever, api_key: str | None):
    st.title('Pregúntale al explorador')
    st.caption('Haz preguntas con tus propias palabras. Puedes continuar la conversación y consultar los hechos del grafo utilizados.')
    if not api_key:
        st.info('Modo de exploración documental: las preguntas se responden con datos del grafo. La generación de explicaciones con IA estará disponible cuando el administrador configure Groq.')
    with st.expander('Cómo interpretar una respuesta'):
        st.write('El texto generado resume registros del grafo, principalmente de la Nación Paucartambo en 2025. Abre «Información utilizada» para revisar las entidades y los hechos RDF recuperados; el sistema puede tener lagunas o errores y requiere revisión de fuentes para usos académicos.')
    st.session_state.setdefault('chat_history', [])
    st.session_state.setdefault('groq_calls', 0)
    history = st.session_state['chat_history']
    if not history:
        prompts = ['¿Qué sabemos de los ukukus?', '¿Dónde se ubica Sinakara?',
                   '¿Qué vestimenta documenta el grafo?']
        cols = st.columns(1 if len(prompts) > 2 else 2)
        for ix, q in enumerate(prompts):
            with cols[ix % len(cols)]:
                if st.button(q, key='starter_'+str(ix), use_container_width=True):
                    st.session_state['pending_question'] = q
                    st.rerun()
    for ix, message in enumerate(history):
        with st.chat_message(message['role'], avatar='🏔️' if message['role']=='assistant' else None):
            st.markdown(message['text'])
            if message['role'] == 'assistant':
                if message.get('status') == 'api_no_disponible':
                    st.caption('Groq no respondió. Se muestra una síntesis directa del grafo.')
                elif message.get('status') == 'sin_api':
                    st.caption('Síntesis directa de la ontología (sin modelo generativo).')
                show_evidence(message.get('evidence', []), store=store, key_prefix=f'chat_{ix}')
                if ix == len(history)-1:
                    for j, q in enumerate(message.get('suggestions', [])):
                        if st.button('↗ ' + q, key=f'suggest_{ix}_{j}', use_container_width=False):
                            st.session_state['pending_question'] = q
                            st.rerun()
    if history and st.button('Limpiar conversación', key='clear_chat'):
        st.session_state['chat_history'] = []
        st.session_state.pop('previous_eid', None)
        st.rerun()
    typed = st.chat_input('Escribe tu pregunta sobre Qoyllur Rit\'i…', max_chars=500)
    question = st.session_state.pop('pending_question', None) or typed
    if question:
        if len(history) >= 40:
            st.warning('Esta conversación alcanzó su límite. Puedes limpiarla y empezar de nuevo.')
            return
        use_api = api_key if st.session_state['groq_calls'] < MAX_API_CALLS_SESSION else None
        if api_key and use_api:
            st.session_state['groq_calls'] += 1
        with st.spinner('Buscando evidencias en el grafo…'):
            result = answer_question(store, retriever, question, use_api,
                        st.session_state.get('previous_eid'), history)
        history.append({'role':'user', 'text':question})
        history.append({'role':'assistant', 'text':result.text,
                        'evidence':result.evidence, 'ids':result.ids,
                        'suggestions':result.suggestions, 'status':result.status})
        st.session_state['chat_history'] = history
        if result.ids:
            st.session_state['previous_eid'] = result.ids[0]
        st.rerun()
