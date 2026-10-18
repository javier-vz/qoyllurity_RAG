# Qoyllur Rit’i — GraphRAG Explorer

Aplicación web [Streamlit](https://qoyllurity.streamlit.app/) para consultas en lenguaje natural sobre el grafo RDF de Qoyllur Rit’i y generación de fichas patrimoniales en PDF.

## Contenido

- `app.py`: interfaz, consultas y fichas PDF.
- `graphrag_v4_api.py`: construcción de contexto y consultas a Groq.
- `graphrag_v2.py`: índice del grafo y búsqueda híbrida.
- `config_graphrag.py`: prompts y configuración del modelo.
- `qoyllurity.ttl`: ontología y datos RDF originales (sin modificaciones).
- `imagenes/`: fotografía optimizada que se utiliza en las fichas PDF.
- `requirements.txt`: dependencias necesarias para Streamlit Cloud.

## Despliegue en Streamlit Community Cloud

1. Sube **el contenido de esta carpeta** a la raíz del repositorio de GitHub. El archivo de entrada es `app.py`.
2. En la configuración de la aplicación Streamlit → **Secrets**, agrega tu clave de Groq:

   ```toml
   GROQ_API_KEY = "tu_clave_de_groq"
   ```

   También puedes configurar `GROQ_API_KEY` como variable de entorno al ejecutar localmente. Nunca guardes la clave en GitHub.
3. Desde Streamlit Community Cloud, reinicia o redepliega la aplicación si sigue ejecutando la versión anterior.
4. Prueba una consulta y la generación de una ficha PDF.

**Modelo predeterminado:** `openai/gpt-oss-120b` en `config_graphrag.py`. Si Groq modifica su catálogo, cambia `Config.MODELO_GROQ` y vuelve a desplegar. La clave debe tener acceso al modelo. Consulta: <https://console.groq.com/docs/models>.

## Ejecución local (Anaconda / Windows)

```bash
pip install -r requirements.txt
streamlit run app.py
```

En la primera ejecución, `sentence-transformers` descarga los pesos del modelo semántico; puede tardar varios minutos según la conexión y memoria disponibles. Las peticiones de Groq necesitan conexión a Internet y pueden estar sujetas a límites o costos según tu plan.

## Consideraciones

- El modelo generativo sólo recibe el contexto recuperado del grafo; conviene verificar cualquier ficha antes de utilizarla como fuente de investigación.
- La fotografía se ha reducido de resolución para agilizar la carga y la exportación de PDF. El archivo RDF se conserva íntegro.
- Este paquete sólo incluye los archivos necesarios para la aplicación Streamlit. No incluye versiones históricas, scripts para Raspberry Pi ni archivos temporales.
