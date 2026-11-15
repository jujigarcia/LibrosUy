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
            # Scrapers never need a session; Shopify rate-limits bots that keep its cookies
            self.session.cookies.clear()
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


def classify_genre(category_names, default_genre: str | None = None, raw_fallback: bool = True) -> str | None:
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
    return category_names[0][:100] if category_names and raw_fallback else None


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
    """Buffers scraped offers for one bookstore and writes them to PostgreSQL in batches.

    The database is remote (Neon), so each round trip costs ~150 ms: instead of 2-3 queries
    per product, each page of products is written with ~4 set-based queries on `commit()`.
    """

    def __init__(self, conn, bookstore_id: int, channel: str = "web_scraper"):
        self.conn = conn
        self.bookstore_id = bookstore_id
        self.channel = channel
        self._pending = []
        with conn.cursor() as cur:
            cur.execute("SELECT now()")
            self.run_started = cur.fetchone()[0]
        conn.commit()

    def upsert_offer(self, *, external_id, isbn, title, author, genre, cover_url,
                     price_uyu, stock_quantity, condition, product_url):
        title = (title or "").strip()
        if not title or not external_id:
            return
        self._pending.append({
            "external_id": str(external_id)[:150],
            "isbn": isbn or None,
            "title": title[:500],
            "author": (author or "").strip()[:255] or None,
            "genre": genre or None,
            "cover_url": cover_url or None,
            # Always float: a batch mixing int and float prices can't be sent as one array
            "price_uyu": float(price_uyu) if price_uyu is not None else None,
            "stock_quantity": int(stock_quantity or 0),
            "condition": condition or "Nuevo",
            "product_url": product_url or None,
        })

    def commit(self):
        """Writes the buffered offers and commits (call once per scraped page)."""
        self.flush()
        self.conn.commit()

    def flush(self):
        if not self._pending:
            return
        # Last occurrence wins if the store lists the same product twice in a batch
        items = list({it["external_id"]: it for it in self._pending}.values())
        self._pending = []

        with self.conn.cursor() as cur:
            book_ids = self._upsert_books_with_isbn(cur, items)
            book_ids.update(self._get_or_create_books_without_isbn(cur, items))

            rows = [it for it in items]
            cur.execute("""
                INSERT INTO inventory_stock (bookstore_id, book_id, price_uyu, stock_quantity,
                                             condition, product_url, external_id)
                SELECT %s, * FROM unnest(%s::int[], %s::numeric[], %s::int[], %s::varchar[],
                                         %s::text[], %s::varchar[])
                ON CONFLICT (bookstore_id, external_id) WHERE external_id IS NOT NULL DO UPDATE SET
                    book_id = EXCLUDED.book_id, price_uyu = EXCLUDED.price_uyu,
                    stock_quantity = EXCLUDED.stock_quantity, condition = EXCLUDED.condition,
                    product_url = EXCLUDED.product_url, last_updated = now()
            """, (
                self.bookstore_id,
                [book_ids[self._book_key(it)] for it in rows],
                [it["price_uyu"] for it in rows],
                [it["stock_quantity"] for it in rows],
                [it["condition"] for it in rows],
                [it["product_url"] for it in rows],
                [it["external_id"] for it in rows],
            ))

    @staticmethod
    def _book_key(item):
        return ("isbn", item["isbn"]) if item["isbn"] else ("title", item["title"], item["author"] or "")

    @staticmethod
    def _columns(rows):
        return ([r["title"] for r in rows], [r["author"] for r in rows],
                [r["genre"] for r in rows], [r["cover_url"] for r in rows])

    def _upsert_books_with_isbn(self, cur, items):
        by_isbn = {}
        for it in items:
            if it["isbn"]:
                by_isbn.setdefault(it["isbn"], it)
        if not by_isbn:
            return {}
        rows = list(by_isbn.values())
        # DO UPDATE (not DO NOTHING) so RETURNING also yields existing books; only fills missing metadata
        cur.execute("""
            INSERT INTO books (isbn, title, author, genre, cover_url)
            SELECT * FROM unnest(%s::varchar[], %s::text[], %s::text[], %s::text[], %s::text[])
            ON CONFLICT (isbn) WHERE isbn IS NOT NULL DO UPDATE SET
                author = COALESCE(books.author, EXCLUDED.author),
                genre = COALESCE(books.genre, EXCLUDED.genre),
                cover_url = COALESCE(books.cover_url, EXCLUDED.cover_url)
            RETURNING book_id, isbn
        """, ([r["isbn"] for r in rows], *self._columns(rows)))
        return {("isbn", isbn): book_id for book_id, isbn in cur.fetchall()}

    def _get_or_create_books_without_isbn(self, cur, items):
        by_key = {}
        for it in items:
            if not it["isbn"]:
                by_key.setdefault((it["title"], it["author"] or ""), it)
        if not by_key:
            return {}
        titles = [k[0] for k in by_key]
        authors = [k[1] for k in by_key]
        cur.execute("""
            SELECT DISTINCT ON (b.title, COALESCE(b.author, '')) b.book_id, b.title, COALESCE(b.author, '')
            FROM books b
            JOIN unnest(%s::text[], %s::text[]) AS k(title, author)
              ON b.title = k.title AND COALESCE(b.author, '') = k.author
            ORDER BY b.title, COALESCE(b.author, ''), b.book_id
        """, (titles, authors))
        found = {("title", t, a): book_id for book_id, t, a in cur.fetchall()}

        missing = [it for key, it in by_key.items() if ("title", *key) not in found]
        if missing:
            cur.execute("""
                INSERT INTO books (title, author, genre, cover_url)
                SELECT * FROM unnest(%s::text[], %s::text[], %s::text[], %s::text[])
                RETURNING book_id, title, COALESCE(author, '')
            """, self._columns(missing))
            found.update({("title", t, a): book_id for book_id, t, a in cur.fetchall()})
        return found

    def mark_unseen_out_of_stock(self) -> int:
        """After a COMPLETE run: products that disappeared from the store are set to 0 stock."""
        self.flush()
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE inventory_stock SET stock_quantity = 0
                WHERE bookstore_id = %s AND external_id IS NOT NULL AND last_updated < %s
                  AND stock_quantity <> 0
            """, (self.bookstore_id, self.run_started))
            return cur.rowcount

    def log(self, status: str, records: int):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sync_logs (bookstore_id, sync_channel, status, records_processed)
                VALUES (%s, %s, %s, %s)
            """, (self.bookstore_id, self.channel, status, records))
