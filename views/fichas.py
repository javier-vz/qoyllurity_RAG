import streamlit as st
from core.graph import HeritageGraph, normalize
from core.pdf import create_pdf
from views.shared import entity_facts


def render(store: HeritageGraph):
    st.title('Fichas patrimoniales')
    st.write('Consulta los registros documentados y descarga una ficha creada directamente desde las propiedades y relaciones RDF.')
    ids = [e.eid for e in store.catalog()]
    chosen = st.session_state.pop('selected_entity', None)
    if chosen in ids:
        st.session_state['ficha_select'] = chosen
    eid = st.selectbox('Entidad', ids,
                       format_func=lambda x: store.entities[x].label,
                       key='ficha_select')
    entity_facts(store, eid, 'ficha')
    card = store.data_card(eid)
    pdf = create_pdf(card)
    st.download_button('⬇ Descargar ficha PDF', data=pdf,
                       file_name=f"ficha_{normalize(eid).replace(' ', '_')}.pdf",
                       mime='application/pdf', type='primary', use_container_width=True)
    st.caption('Documento automático construido desde el grafo. Los campos ausentes se mantienen como tales; la ficha no sustituye una revisión académica de la fuente.')
