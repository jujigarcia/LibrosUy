"""
Crea (o recrea) las tablas de LibrosUy en PostgreSQL a partir de datebase/schema.sql
y carga las 29 librerías.

ATENCIÓN: borra todas las tablas y sus datos (stock incluido).

Uso:
    python init_db.py --yes
"""
import sys
from pathlib import Path

from db import get_db_connection

SCHEMA = Path(__file__).resolve().parent.parent / "datebase" / "schema.sql"


def main():
    if "--yes" not in sys.argv:
        print("Esto BORRA y recrea todas las tablas. Si estás segura, ejecutá: python init_db.py --yes")
        return 1
    sql = SCHEMA.read_text(encoding="utf-8")
    with get_db_connection(direct=True) as conn:
        conn.execute(sql)
        conn.commit()
        stores = conn.execute("SELECT count(*) FROM bookstores").fetchone()[0]
    print(f"Esquema creado desde {SCHEMA.name}: {stores} librerías cargadas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
