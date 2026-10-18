import streamlit as st
from core.graph import HeritageGraph
from config_graphrag import APP_VERSION


def render(store: HeritageGraph):
    st.title('Sobre el proyecto')
    st.markdown('**Qoyllur Rit\'i Explorer** utiliza un grafo RDF para facilitar la consulta de lugares, actores, vestimentas, objetos y acontecimientos vinculados a la peregrinación.')
    st.markdown('### Qué contiene este prototipo')
    stats = store.stats()
    st.markdown(f"- **{stats['individuals']} individuos** del grafo RDF.\n- **{stats['triples']} tripletas**.\n- **{stats['geolocated']} entidades** con latitud y longitud documentadas.")
    st.markdown('### Alcance y límites')
    st.write('La documentación se concentra principalmente en la experiencia de la Nación Paucartambo de 2025. El grafo puede tener vacíos de cobertura, etiquetas incompletas o descripciones pendientes de contrastar. Los hechos RDF deben distinguirse de testimonios o referencias bibliográficas verificadas.')
    st.markdown('### Cómo funciona')
    st.markdown('**Pregunta → búsqueda de entidades → consulta de propiedades y relaciones RDF → respuesta con evidencias.**')
    st.write('Cuando hay una clave Groq válida, el asistente redacta una síntesis en lenguaje natural. Si falta la clave o el servicio presenta problemas, se conserva la consulta documental y la generación de fichas.')
    st.markdown('### Información técnica y datos')
    st.markdown('- [Repositorio público del proyecto](https://github.com/javier-vz/qoyllurity)\n- [Archivo Turtle original](https://github.com/javier-vz/qoyllurity/blob/main/qoyllurity.ttl)')
    st.caption(f'Qoyllur Rit\'i Explorer · {APP_VERSION} · Streamlit · RDFLib · Groq opcional')
