"""Componentes sencillos reutilizables entre pantallas de Streamlit."""
from __future__ import annotations
import streamlit as st
from core.graph import HeritageGraph, local
from core.spanish import polish_spanish


def entity_facts(store: HeritageGraph, eid: str, key_prefix='card'):
    card = store.data_card(eid)
    st.markdown('#### ' + card['name'])
    st.caption(' · '.join(card['kinds']) or 'Entidad documental')
    st.write(polish_spanish(card['description']) if card['description'] else 'El registro todavía no contiene una descripción.')
    if card['properties']:
        with st.expander('Propiedades documentadas', expanded=False):
            for f in card['properties']:
                st.markdown(f"**{f['predicate_label']}**: {f['value']}")
    if card['relations'] or card['incoming']:
        with st.expander('Relaciones y conexiones', expanded=False):
            for f in card['relations']:
                st.markdown(f"**{f['predicate_label']}** → {f['value']}")
            for f in card['incoming']:
                st.markdown(f"{f['subject_label']} → **{f['predicate_label']}** → {card['name']}")
    with st.expander('Datos técnicos RDF', expanded=False):
        st.code(card['uri'], language=None)
        st.caption('Estos identificadores indican los hechos del grafo; no equivalen por sí solos a referencias bibliográficas verificadas.')


def show_evidence(facts: list[dict], caption='Información utilizada', store=None, key_prefix='evidence'):
    with st.expander(f'{caption} ({len(facts)} hechos RDF)', expanded=False):
        if not facts:
            st.caption('No se recuperaron hechos suficientes.')
        for fact in facts:
            st.markdown(f"**{fact['subject_label']}** · {fact['predicate_label']} → {fact['value']}")
            st.caption(f"`{local(fact['predicate'])}` · `{local(fact['subject'])}`")
        st.info('Son hechos contenidos en el RDF. La evidencia documental externa y su revisión académica deben consignarse por separado.')
        if store is not None:
            entity_ids = list(dict.fromkeys(
                local(f['subject']) for f in facts if local(f['subject']) in store.entities))
            if entity_ids:
                choice = st.selectbox('Abrir ficha de una entidad citada', entity_ids,
                                      format_func=lambda eid: store.entities[eid].label,
                                      key=f'{key_prefix}_entity')
                if st.button('Ver ficha y relaciones →', key=f'{key_prefix}_goto'):
                    st.session_state['selected_entity'] = choice
                    st.switch_page(st.session_state['_page_fichas'])
