"""Scraper for WooCommerce stores via the public Store API (/wp-json/wc/store/v1/products).

Uses the same JSON the store's own pages consume, so it is light on the site:
100 products per request instead of loading every product page.
"""
import html
import re

from .common import PoliteSession, classify_genre, clean_isbn

PRODUCTS_PATH = "/wp-json/wc/store/v1/products"
PER_PAGE = 100
AUTHOR_ATTRIBUTES = {"autor", "autores", "author", "autor/a"}


def _parse_product(p: dict, default_condition: str, default_genre: str | None, use_categories: bool):
    title = html.unescape(p.get("name") or "").strip()
    if not title:
        return None

    prices = p.get("prices") or {}
    minor = int(prices.get("currency_minor_unit") or 0)
    try:
        price = int(prices.get("price") or 0) / (10 ** minor)
    except ValueError:
        price = 0
    if prices.get("currency_code") not in (None, "UYU"):
        price = 0  # Only UYU prices are comparable on LibrosUy

    if p.get("is_in_stock"):
        availability = (p.get("stock_availability") or {}).get("text") or ""
        match = re.search(r"\d+", availability)
        qty = int(match.group()) if match else 1
    else:
        qty = 0

    author = None
    for attr in p.get("attributes") or []:
        if (attr.get("name") or "").strip().lower() in AUTHOR_ATTRIBUTES:
            author = ", ".join(html.unescape(t["name"]).strip() for t in attr.get("terms", []) if t.get("name"))
            break

    images = p.get("images") or []
    cover = (images[0].get("thumbnail") or images[0].get("src")) if images else None
    all_categories = [html.unescape(c.get("name") or "") for c in p.get("categories") or []]
    categories = all_categories if use_categories else []
    condition = "Usado" if any("usad" in c.lower() for c in all_categories) else default_condition

    return {
        "external_id": str(p["id"]),
        "isbn": clean_isbn(p.get("sku")),
        "title": title,
        "author": author or None,
        "genre": classify_genre(categories, default_genre),
        "cover_url": cover[:500] if cover else None,
        "price_uyu": price or None,
        "stock_quantity": qty,
        "condition": condition,
        "product_url": (p.get("permalink") or "")[:500] or None,
    }


def scrape(base_url: str, writer, *, delay: float = 1.0, max_pages: int | None = None,
           default_condition: str = "Nuevo", default_genre: str | None = None,
           use_categories: bool = True, progress=print, **_):
    """Walks the catalog page by page and upserts each product. Returns (processed, complete)."""
    http = PoliteSession(base_url, delay=delay)
    page, total_pages, processed = 1, None, 0

    while True:
        resp = http.get(PRODUCTS_PATH, params={"per_page": PER_PAGE, "page": page})
        if total_pages is None:
            total_pages = int(resp.headers.get("X-WP-TotalPages") or 1)
            progress(f"  {resp.headers.get('X-WP-Total', '?')} productos en {total_pages} páginas")

        products = resp.json()
        if not products:
            break
        for p in products:
            item = _parse_product(p, default_condition, default_genre, use_categories)
            if item:
                writer.upsert_offer(**item)
                processed += 1
        writer.commit()

        if page % 10 == 0:
            progress(f"  página {page}/{total_pages} · {processed} productos")
        if page >= total_pages:
            return processed, True
        if max_pages and page >= max_pages:
            return processed, False
        page += 1

    return processed, True
