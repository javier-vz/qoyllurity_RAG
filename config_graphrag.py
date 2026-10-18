"""Parámetros de la aplicación. No almacena credenciales."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TTL_PATH = ROOT / "qoyllurity.ttl"
APP_VERSION = "3.0.0-etapa1"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
MAX_OUTPUT_TOKENS = 1300
MAX_EVIDENCE = 22
MAX_HISTORY_MESSAGES = 8
SEARCH_TOP_K = 6
# Opcional: requiere instalar sentence-transformers y descargar modelo.
SEMANTIC_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
