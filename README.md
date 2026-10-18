# Qoyllur Rit'i Explorer 3.0 — Etapa 1

Explorador patrimonial en **Streamlit** basado en el grafo `qoyllurity.ttl`. Ofrece una entrada sencilla para visitantes y acceso opcional a relaciones y propiedades RDF para investigación.

## Funcionalidades incluidas

- **Inicio:** presentación y cuatro entradas temáticas a la conversación.
- **Preguntar:** chat con historial de sesión, sugerencias basadas en vecinos del grafo y evidencias inspeccionables.
- **Explorar:** catálogo filtrable por nombres, tipos y descripciones; relaciones entrantes y salientes.
- **Fichas:** descripciones, propiedades, relaciones, URI y exportación PDF **sin inventar campos**.
- **Proyecto:** alcance y funcionamiento de la herramienta.
- **Modo sin Groq:** las consultas documentales, el catálogo y las fichas siguen disponibles. La redacción en ese modo es limitada y se basa en datos recuperados.

La app utiliza el Turtle ORIGINAL (**1 060 tripletas, 87 individuos**, 34 entidades con latitud/longitud) y evita incorporar como personas/lugares a clases RDF. Se incluye una etiqueta legible para Ausangate, ausente en su `rdfs:label`, sin alterar el Turtle.

### Alcance

El grafo documenta sobre todo experiencias y entidades relacionadas con **Nación Paucartambo y 2025**. No debe interpretarse como una descripción exhaustiva de todas las naciones o de todos los años de la festividad. Los triples permiten auditar qué registra el dataset; **no sustituyen fuentes primarias y bibliografía revisada**.

## Instalar y ejecutar (Windows / Anaconda Prompt)

```bat
conda create -n qoyllurity3 python=3.11 -y
conda activate qoyllurity3
cd RUTA_A_LA_CARPETA_DEL_REPOSITORIO
pip install -r requirements.txt
streamlit run app.py
```

Se abre una dirección local, normalmente `http://localhost:8501`. También funciona sin configurar Groq (modo documental). El paquete base **no descarga modelos grandes de embeddings** y prioriza una carga rápida: combina TF-IDF por palabras, similitud por caracteres y conexiones RDF. El módulo permite activar embeddings multilingües opcionalmente instalando manualmente `sentence-transformers` y adaptando `load_retriever` para `use_semantic=True`; esta mejora **no** está activada ni evaluada en la etapa 1.

## Activar respuestas explicativas con Groq

En [Streamlit Community Cloud](https://share.streamlit.io/) abre la aplicación, **Settings → Secrets** y conserva o agrega:

```toml
GROQ_API_KEY = "tu_clave_real"
```

- La variable también se puede definir como variable de entorno `GROQ_API_KEY`.
- **Nunca** subas el archivo `.streamlit/secrets.toml` a GitHub.
- El modelo configurado en `config_graphrag.py` es `openai/gpt-oss-120b`. La disponibilidad y los límites dependen del acceso de tu cuenta Groq.
- Cada sesión tiene un máximo sencillo de 20 intentos de generación con Groq y 40 mensajes de chat. **Esto limita solamente una sesión**: para protección de costes o abuso en despliegues públicos se requiere además rate limiting por usuario/servidor y límites en el proveedor.
- Ante error de la API, el visitante recibe una síntesis local, mientras que los datos del grafo continúan accesibles.

## Publicar actualización en GitHub

1. Descarga una copia o crea una rama de respaldo del repositorio actual.
2. Descomprime el ZIP de esta versión en tu equipo.
3. Sustituye en [github.com/javier-vz/qoyllurity](https://github.com/javier-vz/qoyllurity) los archivos antiguos por **los archivos de la raíz** del ZIP, preservando su organización y carpetas internas (`core/`, `views/`, `.streamlit/`, `tests/`).
4. Elimina expresamente los archivos de versiones anteriores que ya no forman parte de esta app, en una rama o commit revisable. **Subir el ZIP descomprimido no borra los archivos existentes.**
5. Confirma los cambios en `main` y verifica que Streamlit apunta a **`app.py`** y la rama correcta.
6. Comprueba «Inicio», «Preguntar», «Explorar» y «Fichas», incluido descargar un PDF. Para comprobar generación con IA, realiza una pregunta después de configurar Secrets.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Incluyen parseo RDF, conteos, recuperación, pruebas de evidencias por URI, errores de API simulados, parámetros Groq y generación PDF.

## Estructura

```text
app.py                      Entrada Streamlit / 5 pantallas
config_graphrag.py          Parámetros y modelo
qoyllurity.ttl              RDF original
core/graph.py               Grafo, entidades, propiedades y relaciones
core/retrieval.py           Búsqueda documental híbrida
core/assistant.py           Respuestas y evidencias
core/pdf.py                 Fichas estructuradas PDF
views/inicio.py             Presentación y sugerencias
views/preguntar.py          Chat e historial
views/explorar.py           Catálogo y navegación
views/fichas.py             Fichas y descarga
views/proyecto.py           Alcance científico y datos
.streamlit/config.toml      Estética
requirements.txt            Dependencias de la aplicación
tests/test_app_core.py      Pruebas de regresión
```

## Próximas etapas (todavía no incluidas)

Mapas de lugares, rutas verificadas, cronología por jornadas, fotografías con procedencia acreditada y evaluación sistemática con preguntas de referencia. La versión 3.0 Etapa 1 constituye el fundamento para añadir esos módulos sin modificar el Turtle original.
