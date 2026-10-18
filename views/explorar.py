import streamlit as st
from core.graph import HeritageGraph
from views.shared import entity_facts


def render(store: HeritageGraph):
    st.title('Explorar el conocimiento')
    st.write('Conoce las entidades registradas y sigue sus conexiones. Aquí puedes navegar sin necesidad de usar IA.')
    st.caption('Las entidades son individuos RDF, no clases de la ontología.')
    kind = st.selectbox('Tema', ['Todos'] + store.types(), key='filter_kind')
    query = st.text_input('Buscar por nombre o descripción', placeholder='Ej. Ausangate, Ukumari, Sinakara…', key='filter_query')
    results = store.catalog(query, kind)
    st.caption(f'{len(results)} entidades encontradas')
    if not results:
        st.info('No encontramos coincidencias. Prueba otro término o selecciona «Todos».')
        return
    # Mostramos selector accesible y detalles, sin renderizar 87 tarjetas simultáneamente.
    ids = [e.eid for e in results]
    choice = st.selectbox('Selecciona una entidad', ids,
                          format_func=lambda eid: store.entities[eid].label,
                          key=f'catalog_entity_{kind}')
    entity_facts(store, choice, key_prefix='catalog')
    linked = store.related_ids(choice)
    if linked:
        st.markdown('#### Continúa explorando')
        for eid in linked[:8]:
            if st.button('↗ ' + store.entities[eid].label, key='neighbor_'+eid):
                st.session_state['selected_entity'] = eid
                st.switch_page(st.session_state['_page_fichas'])
    if st.button('Ver ficha y descargar PDF', type='primary', use_container_width=True):
        st.session_state['selected_entity'] = choice
        st.switch_page(st.session_state['_page_fichas'])
