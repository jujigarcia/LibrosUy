import os
import logging
import re
import unicodedata
from functools import lru_cache

import requests
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import analytics
import feedback
from db import escape_like, get_db_connection

logger = logging.getLogger("librosuy")

# Optional but strongly recommended: without a key, Google Books uses a shared
# anonymous quota that is frequently exhausted (HTTP 429).
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

GENERAL_TAG = "Catálogo General"

# Distinct books shown under "Libros identificados" (e.g. several titles when searching an author)
MAX_BOOK_CANDIDATES = 6

# Genre detection from our own catalog: keep at most this many genres, each covering at
# least this share of the matching books
MAX_CATALOG_GENRES = 2
MIN_GENRE_SHARE = 0.2

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

# Umbrella genres with no store tag of their own: they match stores tagged with any of
# these specialties ("Escolares" stays a separate genre on purpose).
GENRE_GROUPS = {
    "Académicos": ["Educativos", "Textos Estudio", "Medicina"],
}

# Accent-free prefixes in the query that select an umbrella genre ("académico", "universitarios"...)
GENRE_GROUP_KEYWORDS = {
    "Académicos": ["academ", "universitari"],
}


def expand_genre(tag):
    """'Académicos' -> its store specialties; any other tag -> itself."""
    return GENRE_GROUPS.get(tag, [tag])

app = FastAPI(title="LibrosUy API", description="Agregador de librerías y stock de libros en Uruguay.")

# Comma-separated list of allowed frontend origins in production, e.g.
# ALLOWED_ORIGINS=https://librosuy.com.uy,https://librosuy.vercel.app  (default: any origin)
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Where a store's stock comes from, so the UI can warn when it cannot be confirmed:
#   verified      -> synced (scraper or sheet) in the last 14 days
#   pending_sheet -> store without e-commerce whose stock sheet we don't have yet
#   unverified    -> has a website but its stock can't be read (blocked, no catalog, ...)
STOCK_SOURCE_SQL = """
    CASE
        WHEN EXISTS (SELECT 1 FROM sync_logs l
                     WHERE l.bookstore_id = s.bookstore_id
                       AND l.status IN ('success', 'partial')
                       AND l.executed_at >= now() - interval '14 days') THEN 'verified'
        WHEN s.ingestion_method = 'google_sheets' THEN 'pending_sheet'
        ELSE 'unverified'
    END
"""


def strip_accents(text: str) -> str:
    """'Fantasía' -> 'fantasia' so typed genre keywords match with or without accents."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def split_tags(specialty):
    return [t.strip() for t in (specialty or "").split(",") if t.strip()]


def _book_from_volume(info: dict, query: str) -> dict:
    thumbnail = info.get("imageLinks", {}).get("thumbnail")
    isbns = {i.get("type"): i.get("identifier") for i in info.get("industryIdentifiers", [])}
    return {
        "title": info.get("title", query),
        "authors": ", ".join(info.get("authors", ["Autor desconocido"])),
        # Google serves http:// thumbnails; https avoids mixed-content blocking on the site
        "thumbnail": thumbnail.replace("http://", "https://", 1) if thumbnail else None,
        "publisher": info.get("publisher"),
        "published_date": info.get("publishedDate"),
        "isbn": isbns.get("ISBN_13") or isbns.get("ISBN_10"),
        "categories": info.get("categories", [])
    }


QUERY_STOPWORDS = {"el", "la", "los", "las", "un", "una", "de", "del", "y", "en", "con", "por", "para", "que", "libro"}


def _matches_query(info: dict, query: str) -> bool:
    """Keeps a Google result only if its title/authors contain ALL the words of the search.
    Avoids unrelated books (e.g. Italian titles for "la tregua", since "tregua" is also Italian).
    ISBN searches are trusted as they are."""
    words = [w for w in re.findall(r"[a-z0-9]+", strip_accents(query)) if len(w) >= 3 and w not in QUERY_STOPWORDS]
    if not words or re.fullmatch(r"[\d\-xX ]{10,17}", query.strip()):
        return True
    text = strip_accents(f"{info.get('title', '')} {info.get('subtitle', '')} {' '.join(info.get('authors', []))}")
    # Every searched word must appear as a whole word (not inside another word)
    text_words = set(re.findall(r"[a-z0-9]+", text))
    return all(w in text_words for w in words)


def _book_key(info: dict) -> str:
    """Groups editions of the same book by title (without subtitle, accents or punctuation).
    Author is left out: Google spells it differently across editions ("Benedetti, Mario")."""
    title = strip_accents(info.get("title", "")).split(":")[0]
    return " ".join(re.findall(r"[a-z0-9]+", title))


@lru_cache(maxsize=512)
def get_google_book_info(query: str):
    """Queries Google Books to identify the searched book(s) and their categories.
    Returns (main_book, candidates, categories): candidates are up to MAX_BOOK_CANDIDATES distinct
    books (editions of the same title grouped), e.g. several books when searching an author.
    Cached in memory to save API quota on repeated searches."""
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": query, "maxResults": 15, "printType": "books", "langRestrict": "es"}
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY
    try:
        # Spanish editions first (Uruguayan stores); any language only if there are none
        items = []
        for lang in ("es", None):
            if lang is None:
                params.pop("langRestrict", None)
            response = requests.get(url, params=params, timeout=5)
            if response.status_code != 200:
                logger.warning("Google Books respondió %s para %r", response.status_code, query)
                return None, (), ()
            items = [i for i in response.json().get("items", []) if _matches_query(i.get("volumeInfo", {}), query)]
            if items:
                break
        if not items:
            return None, (), ()

        # Spanish editions first (stable sort keeps Google's relevance order otherwise)
        items.sort(key=lambda i: i.get("volumeInfo", {}).get("language") != "es")
        candidates, seen = [], set()
        for item in items:
            info = item.get("volumeInfo", {})
            key = _book_key(info)
            if not info.get("title") or key in seen:
                continue
            seen.add(key)
            candidates.append(_book_from_volume(info, query))
            if len(candidates) >= MAX_BOOK_CANDIDATES:
                break

        # Categories only from the top results: they decide which stores are recommended
        all_cats = set()
        for item in items[:3]:
            all_cats.update(item.get("volumeInfo", {}).get("categories", []))
        return (candidates[0] if candidates else None), tuple(candidates), tuple(all_cats)
    except Exception as e:
        logger.warning("Error consultando Google Books para %r: %s", query, e)
        return None, (), ()


def map_categories_to_tags(google_categories):
    matched_tags = set()
    for category in google_categories:
        for eng_key, esp_tag in CATEGORY_MAP.items():
            if eng_key.lower() in category.lower():
                matched_tags.add(esp_tag)
    return matched_tags


app.include_router(analytics.router)
app.include_router(feedback.router)


@app.get("/")
def read_root():
    return {"message": "LibrosUy API operational."}


@app.get("/api/stores")
def get_stores():
    """Returns all active bookstores for both the Leaflet Map and the Store Directory."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT s.bookstore_id, s.name, s.website, s.specialty, s.address, s.department,
                   s.latitude, s.longitude, s.ingestion_method, s.sync_frequency, s.featured, s.whatsapp,
                   s.instagram, {STOCK_SOURCE_SQL} AS stock_source
            FROM bookstores s
            WHERE s.is_active
            ORDER BY s.featured DESC, s.name ASC
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
                "whatsapp": row[11],
                "instagram": row[12],
                "stock_source": row[13]
            }
            for row in rows
        ]
        cursor.close()
        conn.close()
        return stores
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/search")
def search_book(title: str, background_tasks: BackgroundTasks = None):
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
            SELECT b.title, b.author, b.isbn, s.name, s.address, s.department, s.website,
                   i.price_uyu, i.stock_quantity, i.condition, i.product_url,
                   s.bookstore_id, s.whatsapp, b.cover_url
            FROM inventory_stock i
            JOIN books b ON i.book_id = b.book_id
            JOIN bookstores s ON i.bookstore_id = s.bookstore_id
            WHERE (unaccent(b.title) ILIKE unaccent(%(q)s) OR unaccent(b.author) ILIKE unaccent(%(q)s)
                   OR b.isbn ILIKE %(q)s OR unaccent(b.genre) ILIKE unaccent(%(q)s))
              AND i.stock_quantity > 0
              AND s.is_active
            ORDER BY i.price_uyu ASC NULLS LAST
            LIMIT 60
        """, {"q": like_pattern})

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
                "whatsapp": r[12],
                # Cover from the store's own listing: the edition it actually sells
                "cover_url": r[13],
                # Scrapers only store peso prices today (dollar prices are skipped); the field
                # lets the UI show "U$D" once dollar prices are kept
                "currency": "UYU"
            }
            for r in cursor.fetchall()
        ]

        # 2. Identify genres to recommend stores that could order the book
        matched_tags = set()

        # 2a. Genre of matching books in our own catalog (works even if Google is down)
        # Only the dominant genres count: a common word in titles ("fantasía", "historia")
        # matches books of every genre, which would recommend almost every store.
        cursor.execute("""
            SELECT genre, count(*) FROM books
            WHERE genre IS NOT NULL
              AND (unaccent(title) ILIKE unaccent(%(q)s) OR unaccent(author) ILIKE unaccent(%(q)s)
                   OR isbn ILIKE %(q)s)
            GROUP BY genre
            ORDER BY count(*) DESC
            LIMIT 30
        """, {"q": like_pattern})
        tag_counts = {}
        for genre, count in cursor.fetchall():
            for tag in split_tags(genre):
                tag_counts[tag] = tag_counts.get(tag, 0) + count
        total = sum(tag_counts.values())
        for tag, count in sorted(tag_counts.items(), key=lambda kv: kv[1], reverse=True)[:MAX_CATALOG_GENRES]:
            if count >= total * MIN_GENRE_SHARE:
                matched_tags.add(tag)

        # 2b. Google Books categories
        book_meta, book_candidates, google_cats = get_google_book_info(query)
        matched_tags.update(map_categories_to_tags(google_cats))

        # 2c. Genre keywords typed directly by the user
        normalized_query = strip_accents(query)
        for keyword in DIRECT_GENRE_KEYWORDS:
            if strip_accents(keyword) in normalized_query:
                matched_tags.add(keyword)
        for group, prefixes in GENRE_GROUP_KEYWORDS.items():
            if any(p in normalized_query for p in prefixes):
                matched_tags.add(group)

        # 2d. Nothing identified: general-catalog stores can usually order any title
        if not matched_tags:
            matched_tags.add(GENERAL_TAG)

        matched_tags = sorted(matched_tags)
        specialties = [s for tag in matched_tags for s in expand_genre(tag)]
        conditions = " OR ".join(["unaccent(s.specialty) ILIKE unaccent(%s)" for _ in specialties])
        params = [f"%{escape_like(s)}%" for s in specialties]
        # Stores that can't confirm stock come first: they may have the book even if it's not indexed
        cursor.execute(f"""
            SELECT * FROM (
                SELECT s.bookstore_id, s.name, s.website, s.specialty, s.address, s.department,
                       s.featured, s.whatsapp, s.instagram, {STOCK_SOURCE_SQL} AS stock_source
                FROM bookstores s
                WHERE s.is_active AND ({conditions})
            ) r
            ORDER BY CASE r.stock_source WHEN 'verified' THEN 1 ELSE 0 END, r.featured DESC, r.name ASC
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
                "whatsapp": r[7],
                "instagram": r[8],
                "stock_source": r[9]
            }
            for r in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        # Anonymous usage stats, written after the response is sent (see analytics.py)
        if background_tasks is not None:
            background_tasks.add_task(analytics.log_search, query, len(in_stock_offers))

        return {
            "query": query,
            "book_metadata": book_meta,
            "book_candidates": list(book_candidates),
            "matched_genres": matched_tags,
            "in_stock_offers": in_stock_offers,
            "recommended_stores": recommended_stores
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
