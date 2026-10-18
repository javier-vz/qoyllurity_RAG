"""Exploración simple: buscar, leer y descargar la ficha de un registro."""
from __future__ import annotations

import streamlit as st

from core.graph import HeritageGraph, normalize
from core.pdf import create_pdf
from core.spanish import polish_spanish
from views.shared import record_details, _select_related


def render(store: HeritageGraph) -> None:
    st.markdown("## Explora el archivo")
    st.markdown('<p class="q-intro">Busca un lugar, participante, objeto o acontecimiento y descubre cómo se relaciona con los demás.</p>',
                unsafe_allow_html=True)

    # El enlace desde las evidencias llega antes de crear los controles de entrada.
    focused = st.session_state.pop("focused_entity", None)
    if focused in store.entities:
        st.session_state["catalog_search"] = ""
        st.session_state["catalog_filter"] = "Todos"
        st.session_state["selected_record"] = focused

    search = st.text_input("Buscar un registro", key="catalog_search",
                           placeholder="Prueba con Ausangate, Sinakara o ukuku…")
    with st.expander("Filtrar resultados"):
        kind = st.selectbox("Tipo de registro", ["Todos"] + store.types(), key="catalog_filter")

    found = store.catalog(search, kind)
    if not found:
        st.info("No encontramos registros con esos términos. Prueba una búsqueda más sencilla.")
        return
    st.caption(f"{len(found)} {'registro' if len(found) == 1 else 'registros'}")

    ids = [item.eid for item in found]
    if st.session_state.get("selected_record") not in ids:
        st.session_state["selected_record"] = ids[0]

    eid = st.selectbox("Selecciona un registro", ids,
                       format_func=lambda x: store.entities[x].label,
                       key="selected_record")
    entity = store.entities[eid]
    st.markdown('<div class="q-rule"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="q-record-title">{escape_text(entity.label)}</div>', unsafe_allow_html=True)
    if entity.kinds:
        st.markdown(f'<div class="q-record-tag">{escape_text(" · ".join(entity.kinds))}</div>',
                    unsafe_allow_html=True)
    st.write(polish_spanish(entity.description) if entity.description
             else "Este registro aún no tiene una descripción. Puedes consultar los datos relacionados a continuación.")

    related = store.related_ids(eid)
    if related:
        st.markdown("**También puedes descubrir**")
        cols = st.columns(2)
        for index, related_eid in enumerate(related[:4]):
            with cols[index % 2]:
                st.button("↗ " + store.entities[related_eid].label,
                          use_container_width=True, key="related_" + related_eid,
                          on_click=_select_related, args=(related_eid,))

    record_details(store, eid)
    data = create_pdf(store.data_card(eid))
    st.download_button("Descargar ficha en PDF ↓", data=data,
                       mime="application/pdf", type="primary", use_container_width=True,
                       file_name=f"ficha_{normalize(eid).replace(' ', '_')}.pdf")
    st.caption("Ficha generada a partir del registro RDF; puede requerir revisión académica.")


def escape_text(text: str) -> str:
    from html import escape
    return escape(text, quote=True)
