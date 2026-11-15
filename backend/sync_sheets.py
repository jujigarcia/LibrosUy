"""
Sincroniza el stock de las librerías sin tienda online desde su planilla de Google Sheets.

Cada librería comparte una planilla (Archivo > Compartir > Publicar en la Web > CSV) con columnas:
    isbn, title, author, genre, price_uyu, stock_quantity, condition, product_url
(solo `title` es obligatoria). El enlace CSV se guarda en bookstores.sheet_url:

    UPDATE bookstores SET sheet_url = 'https://docs.google.com/spreadsheets/d/<ID>/export?format=csv'
    WHERE name = 'Librería Ofipando';

Uso:
    python sync_sheets.py                 # todas las librerías con sheet_url
    python sync_sheets.py --store-id 13   # una sola
"""
import argparse
import csv
import sys
from io import StringIO

import requests

from db import get_db_connection
from scrapers.common import USER_AGENT, StockWriter, clean_isbn, parse_uy_price


def _int(value, default=1):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def sync_store(conn, bookstore_id: int, name: str, csv_url: str) -> bool:
    writer = StockWriter(conn, bookstore_id, channel="google_sheets")
    processed, skipped = 0, 0
    try:
        resp = requests.get(csv_url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        resp.encoding = "utf-8"

        for row in csv.DictReader(StringIO(resp.text)):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            title = row.get("title") or row.get("titulo") or row.get("título")
            if not title:
                skipped += 1
                continue
            isbn = clean_isbn(row.get("isbn"))
            condition = row.get("condition") or row.get("estado") or "Nuevo"
            writer.upsert_offer(
                # Stable key per sheet row: ISBN (or title) + condition
                external_id=f"sheet:{isbn or title.lower()}:{condition.lower()}",
                isbn=isbn,
                title=title,
                author=row.get("author") or row.get("autor"),
                genre=row.get("genre") or row.get("genero") or row.get("género"),
                cover_url=None,
                price_uyu=parse_uy_price(row.get("price_uyu") or row.get("precio")),
                stock_quantity=_int(row.get("stock_quantity") or row.get("stock"), 1),
                condition=condition,
                product_url=row.get("product_url") or None,
            )
            processed += 1
            if processed % 200 == 0:
                writer.commit()

        writer.commit()
        removed = writer.mark_unseen_out_of_stock()  # Rows deleted from the sheet -> no stock
        writer.log("success", processed)
        conn.commit()
        print(f"[{name}] OK: {processed} libros"
              f"{f', {skipped} filas sin título omitidas' if skipped else ''}"
              f"{f', {removed} marcados sin stock' if removed else ''}")
        return True
    except Exception as e:
        conn.rollback()
        writer.log("failed", processed)
        conn.commit()
        print(f"[{name}] ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Sincroniza planillas de stock de LibrosUy")
    parser.add_argument("--store-id", type=int, help="bookstore_id de una sola librería")
    args = parser.parse_args()

    conn = get_db_connection(direct=True)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT bookstore_id, name, sheet_url FROM bookstores
                WHERE is_active AND sheet_url IS NOT NULL AND (%(id)s::int IS NULL OR bookstore_id = %(id)s)
                ORDER BY bookstore_id
            """, {"id": args.store_id})
            stores = cur.fetchall()
        conn.commit()
        if not stores:
            print("No hay librerías con sheet_url cargado.")
            return 0
        results = [sync_store(conn, *store) for store in stores]
    finally:
        conn.close()
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
