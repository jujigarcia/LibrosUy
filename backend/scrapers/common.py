"""Shared helpers for bookstore scrapers: polite HTTP, robots.txt, genre mapping and DB upserts."""
import re
import time
import unicodedata
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

USER_AGENT = "LibrosUyBot/1.0 (+https://librosuy.com.uy)"


class PoliteSession:
    """requests wrapper that respects robots.txt, waits between requests and backs off on 429/5xx."""

    def __init__(self, base_url: str, delay: float = 1.0):
        self.base_url = base_url.rstrip("/")
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self._last_request = 0.0
        self.robots = RobotFileParser()
        try:
            resp = self.session.get(f"{self.base_url}/robots.txt", timeout=15)
            self.robots.parse(resp.text.splitlines() if resp.status_code == 200 else [])
        except requests.RequestException:
            self.robots.parse([])

    def allowed(self, url: str) -> bool:
        return self.robots.can_fetch(USER_AGENT, url)

    def get(self, path: str, params=None, retries: int = 3):
        return self._request("GET", path, params=params, retries=retries)

    def post(self, path: str, json=None, retries: int = 3):
        return self._request("POST", path, json=json, retries=retries)

    def _request(self, method: str, path: str, params=None, json=None, retries: int = 3):
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if not self.allowed(url):
            raise PermissionError(f"robots.txt no permite acceder a {urlparse(url).path}")

        for attempt in range(retries + 1):
            wait = self.delay - (time.monotonic() - self._last_request)
            if wait > 0:
                time.sleep(wait)
            self._last_request = time.monotonic()
            resp = self.session.request(method, url, params=params, json=json, timeout=60)
            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt == retries:
                    resp.raise_for_status()
                retry_after = resp.headers.get("Retry-After", "")
                time.sleep(int(retry_after) if retry_after.isdigit() else 10 * (attempt + 1))
                continue
            resp.raise_for_status()
            return resp


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return text.lower()


# Store category keywords (normalized, no accents) -> LibrosUy genre tags used in bookstores.specialty
GENRE_KEYWORDS = [
    ("manga", "Manga"),
    ("comic", "Cómics"),
    ("historieta", "Cómics"),
    ("fantas", "Fantasía"),
    ("ciencia ficcion", "Fantasía"),
    ("juvenil", "Juvenil"),
    ("young adult", "Juvenil"),
    ("infantil", "Infantil"),
    ("romanti", "Romance"),
    ("romance", "Romance"),
    ("poesia", "Poesía"),
    ("historia", "Historia"),
    ("biografia", "Historia"),
    ("arte", "Arte"),
    ("medicina", "Medicina"),
    ("educa", "Educativos"),
    ("escolar", "Escolares"),
    ("narrativa", "Ficción"),
    ("novela", "Ficción"),
    ("ficcion", "Ficción"),
    ("literatura", "Ficción"),
]


def classify_genre(category_names, default_genre: str | None = None) -> str | None:
    """Maps a store's own category names to LibrosUy genre tags (comma-separated).
    Unrecognized categories fall back to the store's default genre (e.g. "Cómics" for a
    comic shop) or, without one, to the store's first category name."""
    tags = []
    for name in category_names:
        norm = _normalize(name)
        for keyword, tag in GENRE_KEYWORDS:
            if re.search(rf"\b{keyword}", norm) and tag not in tags:
                tags.append(tag)
    if tags:
        return ", ".join(tags)[:100]
    if default_genre:
        return default_genre
    return category_names[0][:100] if category_names else None


def parse_uy_price(text) -> float | None:
    """Parses Uruguayan-formatted prices: '$U 1.341', 'UYU 841,50', '$1.090' -> float (None if 0/invalid)."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text) or None
    match = re.search(r"\d[\d.,]*", str(text))
    if not match:
        return None
    number = match.group().rstrip(".,")
    if "," in number:
        number = number.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", number):
        number = number.replace(".", "")
    try:
        return float(number) or None
    except ValueError:
        return None


def stock_from_label(label: str | None, default: int = 1) -> int:
    """Maps availability labels ('Disponible', 'Agotado', 'Sin stock') to a quantity."""
    norm = _normalize(label or "")
    if any(k in norm for k in ("agotad", "sin stock", "no disponible", "sold out", "out of stock", "outofstock")):
        return 0
    return default


def clean_isbn(raw: str) -> str | None:
    """Returns a valid-looking ISBN-10/13 (digits only) or None."""
    digits = re.sub(r"[^0-9Xx]", "", raw or "").upper()
    if len(digits) == 13 and digits.startswith(("978", "979")) and digits.isdigit():
        return digits
    if len(digits) == 10 and digits[:9].isdigit():
        return digits
    return None


class StockWriter:
    """Upserts scraped offers into books + inventory_stock for one bookstore."""

    def __init__(self, conn, bookstore_id: int):
        self.conn = conn
        self.cursor = conn.cursor()
        self.bookstore_id = bookstore_id
        self.cursor.execute("SELECT GETDATE()")
        self.run_started = self.cursor.fetchone()[0]

    def _get_or_create_book(self, isbn, title, author, genre, cover_url):
        if isbn:
            self.cursor.execute("SELECT book_id FROM books WHERE isbn = ?", (isbn,))
        else:
            self.cursor.execute(
                "SELECT TOP 1 book_id FROM books WHERE title = ? AND ISNULL(author, '') = ?",
                (title, author or ""),
            )
        row = self.cursor.fetchone()
        if row:
            # Fill in metadata the catalog was missing
            self.cursor.execute("""
                UPDATE books SET author = COALESCE(author, ?), genre = COALESCE(genre, ?),
                                 cover_url = COALESCE(cover_url, ?)
                WHERE book_id = ?
            """, (author, genre, cover_url, row[0]))
            return row[0]

        self.cursor.execute(
            "INSERT INTO books (isbn, title, author, genre, cover_url) OUTPUT INSERTED.book_id VALUES (?, ?, ?, ?, ?)",
            (isbn, title, author, genre, cover_url),
        )
        return self.cursor.fetchone()[0]

    def upsert_offer(self, *, external_id, isbn, title, author, genre, cover_url,
                     price_uyu, stock_quantity, condition, product_url):
        book_id = self._get_or_create_book(isbn, title[:255], (author or None) and author[:255], genre, cover_url)
        self.cursor.execute(
            "SELECT stock_id FROM inventory_stock WHERE bookstore_id = ? AND external_id = ?",
            (self.bookstore_id, external_id),
        )
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute("""
                UPDATE inventory_stock
                SET book_id = ?, price_uyu = ?, stock_quantity = ?, condition = ?, product_url = ?,
                    last_updated = GETDATE()
                WHERE stock_id = ?
            """, (book_id, price_uyu, stock_quantity, condition, product_url, row[0]))
        else:
            self.cursor.execute("""
                INSERT INTO inventory_stock (bookstore_id, book_id, price_uyu, stock_quantity, condition,
                                             product_url, external_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.bookstore_id, book_id, price_uyu, stock_quantity, condition, product_url, external_id))

    def mark_unseen_out_of_stock(self) -> int:
        """After a COMPLETE run: products that disappeared from the store are set to 0 stock."""
        self.cursor.execute("""
            UPDATE inventory_stock SET stock_quantity = 0
            WHERE bookstore_id = ? AND external_id IS NOT NULL AND last_updated < ?
        """, (self.bookstore_id, self.run_started))
        return self.cursor.rowcount

    def log(self, status: str, records: int):
        self.cursor.execute("""
            INSERT INTO sync_logs (bookstore_id, sync_channel, status, records_processed)
            VALUES (?, 'web_scraper', ?, ?)
        """, (self.bookstore_id, status, records))
