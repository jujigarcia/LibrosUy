import os
import logging
from functools import lru_cache

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import get_db_connection

logger = logging.getLogger("librosuy")

# Optional but strongly recommended: without a key, Google Books uses a shared
# anonymous quota that is frequently exhausted (HTTP 429).
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

GENERAL_TAG = "Catálogo General"

# Maps Google Books English categories to Uruguayan store specialties
CATEGORY_MAP = {
    "Fiction": "Ficción",
    "Juvenile": "Juvenil",
    "Young Adult": "Juvenil",
    "Fantasy": "Fantasía",
    "Science Fiction": "Fantasía",
    "History": "Historia",
    "Biography": "Historia",
    "Romance": "Romance",
    "Comics": "Cómics",
    "Graphic Novels": "Manga",
    "Manga": "Manga",
    "Poetry": "Poesía",
    "Art": "Arte",
    "Education": "Educativos",
    "Medical": "Medicina"
}

# Genre keywords a user may type directly (e.g. "Manga" or "Usados")
DIRECT_GENRE_KEYWORDS = ["Manga", "Cómics", "Fantasía", "Historia", "Usados", "Juvenil", "Poesía", "Ficción", "Romance"]

app = FastAPI(title="LibrosUy API", description="Agregador de librerías y stock de libros en Uruguay.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def split_tags(specialty):
    return [t.strip() for t in (specialty or "").split(",") if t.strip()]


@lru_cache(maxsize=512)
def get_google_book_info(query: str):
    """Queries Google Books API to identify book metadata and categories.
    Cached in memory to save API quota on repeated searches."""
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": query, "maxResults": 3}
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            logger.warning("Google Books respondió %s para %r", response.status_code, query)
            return None, ()
        items = response.json().get("items", [])
        if not items:
            return None, ()

        first_book = items[0].get("volumeInfo", {})
        book_meta = {
            "title": first_book.get("title", query),
            "authors": ", ".join(first_book.get("authors", ["Autor desconocido"])),
            "thumbnail": first_book.get("imageLinks", {}).get("thumbnail"),
            "categories": first_book.get("categories", [])
        }

        all_cats = set()
        for item in items:
            all_cats.update(item.get("volumeInfo", {}).get("categories", []))
        return book_meta, tuple(all_cats)
    except Exception as e:
        logger.warning("Error consultando Google Books para %r: %s", query, e)
        return None, ()


def map_categories_to_tags(google_categories):
    matched_tags = set()
    for category in google_categories:
        for eng_key, esp_tag in CATEGORY_MAP.items():
            if eng_key.lower() in category.lower():
                matched_tags.add(esp_tag)
    return matched_tags


def escape_like(text: str) -> str:
    """Escapes SQL Server LIKE wildcards so user input is matched literally."""
    return text.replace("[", "[[]").replace("%", "[%]").replace("_", "[_]")


@app.get("/")
def read_root():
    return {"message": "LibrosUy API operational."}


@app.get("/api/stores")
def get_stores():
    """Returns all active bookstores for both the Leaflet Map and the Store Directory."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bookstore_id, name, website, specialty, address, department,
                   latitude, longitude, ingestion_method, sync_frequency, featured, whatsapp
            FROM bookstores
            WHERE is_active = 1
            ORDER BY featured DESC, name ASC
        """)
        rows = cursor.fetchall()
        stores = [
            {
                "id": row[0],
                "name": row[1],
                "website": row[2],
                "specialty": row[3],
                "tags": split_tags(row[3]),
                "address": row[4],
                "department": row[5],
                "latitude": float(row[6]) if row[6] is not None else None,
                "longitude": float(row[7]) if row[7] is not None else None,
                "ingestion_method": row[8],
                "sync_frequency": row[9],
                "featured": bool(row[10]),
                "whatsapp": row[11]
            }
            for row in rows
        ]
        cursor.close()
        conn.close()
        return stores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/search")
def search_book(title: str):
    """
    1. Searches local pre-indexed stock (`inventory_stock` + `books`).
    2. Recommends stores that could order the book, based on the genre from the
       local catalog, Google Books categories and genre keywords in the query.
       Falls back to general-catalog stores when no genre can be identified.
    """
    query = title.strip()
    if not query:
        raise HTTPException(status_code=400, detail="La búsqueda no puede estar vacía.")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        like_pattern = f"%{escape_like(query)}%"

        # 1. Check direct stock in SQL database
        cursor.execute("""
            SELECT TOP 60 b.title, b.author, b.isbn, s.name, s.address, s.department, s.website,
                   i.price_uyu, i.stock_quantity, i.condition, i.product_url,
                   s.bookstore_id, s.whatsapp
            FROM inventory_stock i
            JOIN books b ON i.book_id = b.book_id
            JOIN bookstores s ON i.bookstore_id = s.bookstore_id
            WHERE (b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ? OR b.genre LIKE ?)
              AND i.stock_quantity > 0
              AND s.is_active = 1
            ORDER BY i.price_uyu ASC
        """, (like_pattern, like_pattern, like_pattern, like_pattern))

        in_stock_offers = [
            {
                "book_title": r[0],
                "author": r[1],
                "isbn": r[2],
                "store_name": r[3],
                "address": r[4],
                "department": r[5],
                "website": r[6],
                "price_uyu": float(r[7]) if r[7] is not None else None,
                "stock_quantity": r[8],
                "condition": r[9],
                "product_url": r[10],
                "store_id": r[11],
                "whatsapp": r[12]
            }
            for r in cursor.fetchall()
        ]

        # 2. Identify genres to recommend stores that could order the book
        matched_tags = set()

        # 2a. Genre of matching books in our own catalog (works even if Google is down)
        cursor.execute("""
            SELECT DISTINCT genre FROM books
            WHERE genre IS NOT NULL AND (title LIKE ? OR author LIKE ? OR isbn LIKE ?)
        """, (like_pattern, like_pattern, like_pattern))
        for (genre,) in cursor.fetchall():
            matched_tags.update(split_tags(genre))

        # 2b. Google Books categories
        book_meta, google_cats = get_google_book_info(query)
        matched_tags.update(map_categories_to_tags(google_cats))

        # 2c. Genre keywords typed directly by the user
        for keyword in DIRECT_GENRE_KEYWORDS:
            if keyword.lower() in query.lower():
                matched_tags.add(keyword)

        # 2d. Nothing identified: general-catalog stores can usually order any title
        if not matched_tags:
            matched_tags.add(GENERAL_TAG)

        matched_tags = sorted(matched_tags)
        conditions = " OR ".join(["specialty LIKE ?" for _ in matched_tags])
        params = [f"%{escape_like(tag)}%" for tag in matched_tags]
        cursor.execute(f"""
            SELECT bookstore_id, name, website, specialty, address, department, featured, whatsapp
            FROM bookstores
            WHERE is_active = 1 AND ({conditions})
            ORDER BY featured DESC, name ASC
        """, params)
        recommended_stores = [
            {
                "id": r[0],
                "name": r[1],
                "website": r[2],
                "specialty": r[3],
                "tags": split_tags(r[3]),
                "address": r[4],
                "department": r[5],
                "featured": bool(r[6]),
                "whatsapp": r[7]
            }
            for r in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return {
            "query": query,
            "book_metadata": book_meta,
            "matched_genres": matched_tags,
            "in_stock_offers": in_stock_offers,
            "recommended_stores": recommended_stores
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
