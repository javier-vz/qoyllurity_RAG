import streamlit as st
from core.graph import HeritageGraph


def render(store: HeritageGraph):
    st.markdown('<div class="eyebrow">PATRIMONIO CULTURAL · CUSCO, PERÚ</div>', unsafe_allow_html=True)
    st.title("Descubre Qoyllur Rit'i")
    st.markdown('**Un espacio para explorar lugares, participantes y acontecimientos de la peregrinación a través de un grafo de conocimiento.**')
    st.caption('Primera etapa · Documentación centrada en la Nación Paucartambo, 2025')
    st.markdown('### ¿Por dónde quieres comenzar?')
    ideas = [
        ('🏔️', 'La festividad', "¿Qué es Qoyllur Rit'i?"),
        ('🥾', 'Los lugares', '¿Qué sabemos sobre el Sinakara?'),
        ('🎭', 'Los participantes', '¿Qué sabemos de los ukukus?'),
        ('🗓️', 'Los acontecimientos', '¿Qué eventos rituales fueron documentados en 2025?'),
    ]
    for start in range(0, len(ideas), 2):
        cols = st.columns(2)
        for col, (emoji, label, query) in zip(cols, ideas[start:start+2]):
            with col:
                with st.container(border=True):
                    st.markdown(f'<div class="home-emoji">{emoji}</div>', unsafe_allow_html=True)
                    st.markdown('**' + label + '**')
                    if st.button('Descubrir →', key='hero_'+label, use_container_width=True):
                        st.session_state['pending_question'] = query
                        st.switch_page(st.session_state['_page_chat'])
    st.markdown('### Un archivo que puedes recorrer')
    a, b, c = st.columns(3)
    stats = store.stats()
    a.metric('Individuos', stats['individuals'])
    b.metric('Tripletas RDF', stats['triples'])
    c.metric('Con coordenadas', stats['geolocated'])
    st.info('Puedes explorar el catálogo y descargar fichas sin utilizar inteligencia artificial. Las consultas conversacionales requieren una conexión a Groq para redactar explicaciones ampliadas.')
