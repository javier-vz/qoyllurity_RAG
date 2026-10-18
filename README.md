# Qoyllur Rit'i — Explorer 3.0 (interfaz simplificada)

Versión de la aplicación pública en **Streamlit** diseñada para visitantes y especialistas. Tiene solo dos espacios: **Conversar** y **Explorar**. Dentro de cada registro se puede descargar su ficha; los datos RDF se muestran solo cuando la persona desea consultarlos.

## Qué se conserva

- El archivo `qoyllurity.ttl` **intacto** (1.060 triples, 87 individuos).
- El motor de recuperación documental y las respuestas explicativas mediante Groq.
- Las preguntas de continuación redactadas por **Groq**, no mediante plantillas.
- Evidencias procedentes del RDF, seguimiento del contexto conversacional y fichas PDF.
- Funcionamiento de consulta documental y fichas aunque Groq falle o no esté configurado.

## Cambios de experiencia

- Inicio directo en el chat: una sola portada breve, tres ejemplos y un cuadro para preguntar.
- Exploración: búsqueda, filtro opcional, lectura del registro y PDF en un único lugar.
- Ya no hay cinco pantallas, métricas en portada ni una ficha como pantalla independiente.
- Textos y botones más cortos; detalles académicos plegados.
- CSS sobrio, legible y adaptable a móvil sin imágenes ni fuentes externas.

## Ejecutar en Windows / Anaconda

```bat
conda create -n qoyllurity3 python=3.11 -y
conda activate qoyllurity3
cd RUTA_DEL_REPOSITORIO
pip install -r requirements.txt
streamlit run app.py
```

En Streamlit Community Cloud: configurar el archivo de entrada `app.py` y conservar en **Settings → Secrets**:

```toml
GROQ_API_KEY = "tu_clave"
```

La clave jamás debe subirse a GitHub. Modelo predeterminado: `openai/gpt-oss-120b`. Groq redacta el texto y hasta tres preguntas de continuación en una sola llamada estructurada, cuando está disponible.

## Reemplazar el repositorio existente

1. Guarda un respaldo de la rama actual o crea una rama nueva.
2. Descomprime este ZIP y **sube el contenido** (no el ZIP mismo) a la raíz del repositorio.
3. Elimina los archivos viejos que el ZIP ya no incluye, especialmente `views/inicio.py`, `views/fichas.py` y `views/proyecto.py`, así como módulos antiguos de GraphRAG que no están en el ZIP.
4. Mantén `qoyllurity.ttl` en la raíz y la carpeta `.streamlit/` con `config.toml`.
5. Streamlit redeplegará la aplicación tras el commit. Si muestra código viejo, reiníciala y recarga el navegador.

**Nota:** GitHub «Upload files» sobrescribe archivos con el mismo nombre, pero no borra automáticamente los que ya no forman parte de esta versión.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Se comprueban la lectura del grafo, la recuperación, las evidencias, la API simulada y los PDF. Las llamadas reales a Groq se deben verificar con tu clave tras desplegar.

## Estructura mínima

```text
app.py
config_graphrag.py
qoyllurity.ttl
requirements.txt
README.md
.gitignore
.streamlit/config.toml
core/{graph,retrieval,assistant,spanish,pdf}.py
views/{preguntar,explorar,shared}.py
tests/test_app_core.py
```

Datos científicos: principalmente experiencia de la Nación Paucartambo (2025). La representación RDF no es por sí sola una referencia bibliográfica contrastada. Las fotografías y rutas verificadas quedan para fases posteriores.
