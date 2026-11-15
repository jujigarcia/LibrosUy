"""PostgreSQL (Neon) connections for the API and the ETL scripts.

- DATABASE_URL         pooled connection (Neon "-pooler" host): the API, many short requests.
- DATABASE_URL_DIRECT  direct connection: scrapers, sheet sync and schema setup (long sessions).
"""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))


def get_db_connection(direct: bool = False) -> psycopg.Connection:
    url = (os.getenv("DATABASE_URL_DIRECT") if direct else None) or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Falta DATABASE_URL en backend/.env (ver .env.example).")
    return psycopg.connect(url, connect_timeout=20)


def escape_like(text: str) -> str:
    """Escapes LIKE/ILIKE wildcards so user input is matched literally (default escape: backslash)."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
