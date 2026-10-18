"""Elementos para consultar el origen RDF sin saturar las pantallas."""
from __future__ import annotations

import streamlit as st
from core.graph import HeritageGraph, local


def _navigate(eid: str) -> None:
    # Callbacks se ejecutan antes del re-render del control de navegación.
    st.session_state["focused_entity"] = eid
    st.session_state["screen"] = "Explorar"


def _select_related(eid: str) -> None:
    st.session_state["selected_record"] = eid
    st.session_state["catalog_search"] = ""
    st.session_state["catalog_filter"] = "Todos"


def show_evidence(facts: list[dict], store: HeritageGraph, key_prefix="source") -> None:
    with st.expander("Ver información utilizada"):
        if not facts:
            st.caption("No encontramos datos suficientes para mostrar evidencias.")
            return
        st.caption("Estos datos proceden del grafo del proyecto. Sus relaciones pueden explorarse en cada registro.")
        for fact in facts[:7]:
            st.markdown(f"**{fact['subject_label']}** · {fact['predicate_label']}: {fact['value']}")
        if len(facts) > 7:
            st.caption(f"Se recuperaron {len(facts)} hechos en total; se muestran los primeros siete.")
        ids = list(dict.fromkeys(local(f['subject']) for f in facts
                                if local(f['subject']) in store.entities))
        if ids:
            eid = ids[0]
            st.button("Abrir registro: " + store.entities[eid].label + " →",
                      key=f"{key_prefix}_open", on_click=_navigate, args=(eid,))


def record_details(store: HeritageGraph, eid: str) -> None:
    data = store.data_card(eid)
    with st.expander("Ver datos y relaciones del grafo"):
        if data["properties"]:
            st.markdown("**Propiedades**")
            for fact in data["properties"]:
                st.markdown(f"- **{fact['predicate_label']}**: {fact['value']}")
        if data["relations"] or data["incoming"]:
            st.markdown("**Relaciones**")
            for fact in data["relations"]:
                st.markdown(f"- **{fact['predicate_label']}** → {fact['value']}")
            for fact in data["incoming"]:
                st.markdown(f"- {fact['subject_label']} → **{fact['predicate_label']}**")
        if not data["properties"] and not data["relations"] and not data["incoming"]:
            st.caption("Todavía no se han registrado propiedades o relaciones adicionales.")
        st.caption("Identificador de este registro")
        st.code(data["uri"], language=None)
