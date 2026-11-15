"""Scraper for Escaramuza's own catalog pages (/libros/N, 30 books per page).

Each listing card has title, author, final UYU price, an availability label and the
product URL (/p/<slug>/<id>/<variant>). ISBN is only on the product page, so it is not
fetched (that would be ~30x more requests).
"""
import re

from bs4 import BeautifulSoup

from .common import PoliteSession, parse_uy_price, stock_from_label

PRODUCT_ID_RE = re.compile(r"/p/[^/]+/(\d+)/(\d+)")


def scrape(base_url: str, writer, *, delay: float = 1.0, max_pages: int | None = None,
           default_condition: str = "Nuevo", default_genre: str | None = None,
           listing_path: str = "/libros", progress=print, **_):
    http = PoliteSession(base_url, delay=delay)
    base = base_url.rstrip("/")
    page, processed, total_pages = 1, 0, None

    while True:
        resp = http.get(f"{listing_path}/{page}")
        soup = BeautifulSoup(resp.text, "html.parser")
        if total_pages is None:
            nav = soup.select_one("[data-page-count]")
            total_pages = int(nav["data-page-count"]) if nav else 1
            progress(f"  {total_pages} páginas")

        cards = soup.select("a.productViewContainer[href]")
        if not cards:
            return processed, True

        for card in cards:
            href = card["href"]
            ids = PRODUCT_ID_RE.search(href)
            title_el = card.select_one(".productViewName")
            if not ids or not title_el:
                continue
            author_el = card.select_one("#productAuthor, .productAuthor")
            price_el = card.select_one(".productViewPrice")
            label_el = card.select_one(".productViewAditionalInfo")
            image_el = card.select_one(".productViewImage")
            cover = None
            if image_el and "url(" in (image_el.get("style") or ""):
                cover = re.search(r"url\(['\"]?([^'\")]+)", image_el["style"]).group(1)

            writer.upsert_offer(
                external_id=f"{ids.group(1)}/{ids.group(2)}",
                isbn=None,
                title=title_el.get_text(" ", strip=True)[:255],
                author=(author_el.get_text(" ", strip=True) if author_el else None) or None,
                genre=default_genre,
                cover_url=cover[:500] if cover else None,
                price_uyu=parse_uy_price(price_el.get_text() if price_el else None),
                stock_quantity=stock_from_label(label_el.get_text() if label_el else None),
                condition=default_condition,
                product_url=f"{base}{href}" if href.startswith("/") else href,
            )
            processed += 1
        writer.conn.commit()

        if page % 25 == 0:
            progress(f"  página {page}/{total_pages} · {processed} productos")
        if page >= total_pages:
            return processed, True
        if max_pages and page >= max_pages:
            return processed, False
        page += 1
