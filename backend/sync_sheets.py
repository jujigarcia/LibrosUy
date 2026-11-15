import csv
import requests
import pyodbc
from io import StringIO

DB_CONN_STR = (
    "Driver={SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=LibrosUyDB;"
    "Trusted_Connection=yes;"
)

# Example Google Sheet CSV export link:
# https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/export?format=csv
SHEET_CSV_URL = "TU_LINK_CSV_DE_GOOGLE_SHEETS_AQUI"

def sync_stock_from_sheet(bookstore_id: int, csv_url: str):
    """
    Reads a bookstore's Google Sheet CSV with columns:
    isbn, title, author, genre, price_uyu, stock_quantity, condition, product_url
    and upserts books + inventory_stock into SQL Server.
    """
    conn = pyodbc.connect(DB_CONN_STR)
    cursor = conn.cursor()
    processed = 0

    try:
        response = requests.get(csv_url, timeout=15)
        response.raise_for_status()
        response.encoding = "utf-8"

        reader = csv.DictReader(StringIO(response.text))
        for row in reader:
            isbn = (row.get("isbn") or "").strip()
            title = (row.get("title") or "").strip()
            if not isbn or not title:
                continue

            author = (row.get("author") or "").strip()
            genre = (row.get("genre") or "General").strip()
            price = float(row.get("price_uyu") or 0)
            qty = int(row.get("stock_quantity") or 1)
            condition = (row.get("condition") or "Nuevo").strip()
            url = (row.get("product_url") or "").strip() or None

            # 1. Upsert Book by ISBN
            cursor.execute("SELECT book_id FROM books WHERE isbn = ?", (isbn,))
            book_row = cursor.fetchone()
            if book_row:
                book_id = book_row[0]
            else:
                cursor.execute(
                    "INSERT INTO books (isbn, title, author, genre) OUTPUT INSERTED.book_id VALUES (?, ?, ?, ?)",
                    (isbn, title, author, genre)
                )
                book_id = cursor.fetchone()[0]

            # 2. Upsert Inventory Stock for this store
            cursor.execute(
                "SELECT stock_id FROM inventory_stock WHERE bookstore_id = ? AND book_id = ? AND condition = ?",
                (bookstore_id, book_id, condition)
            )
            stock_row = cursor.fetchone()
            if stock_row:
                cursor.execute("""
                    UPDATE inventory_stock
                    SET price_uyu = ?, stock_quantity = ?, product_url = ?, last_updated = GETDATE()
                    WHERE stock_id = ?
                """, (price, qty, url, stock_row[0]))
            else:
                cursor.execute("""
                    INSERT INTO inventory_stock (bookstore_id, book_id, price_uyu, stock_quantity, condition, product_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (bookstore_id, book_id, price, qty, condition, url))

            processed += 1

        # 3. Record audit log
        cursor.execute("""
            INSERT INTO sync_logs (bookstore_id, sync_channel, status, records_processed)
            VALUES (?, 'google_sheets', 'success', ?)
        """, (bookstore_id, processed))
        conn.commit()
        print(f"¡Sincronización exitosa! {processed} libros actualizados para bookstore_id={bookstore_id}.")

    except Exception as e:
        cursor.execute("""
            INSERT INTO sync_logs (bookstore_id, sync_channel, status, records_processed)
            VALUES (?, 'google_sheets', 'failed', ?)
        """, (bookstore_id, processed))
        conn.commit()
        print(f"Error durante la sincronización: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Para sincronizar una planilla, configurá SHEET_CSV_URL y ejecutá sync_stock_from_sheet().")