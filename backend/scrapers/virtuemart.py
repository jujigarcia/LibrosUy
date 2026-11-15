"""Scraper for Joomla + VirtueMart stores (e.g. Las Karamazov).

Walks every subject category (/temas/<categoria>.html?start=N, 24 books per page). Cards
include title, author, ISBN and price; the category gives the genre. The listing does not
show stock, so listed books are assumed available.
"""
import re

from bs4 import BeautifulSoup

from .common import PoliteSession, classify_genre, clean_isbn, parse_uy_price

PER_PAGE = 24


def _categories(http, root_path):
    soup = BeautifulSoup(http.get(root_path).text, "html.parser")
    seen = {}
    for a in soup.find_all("a", href=re.compile(r"^/temas/[a-z0-9-]+\.html$")):
        seen.setdefault(a["href"], a.get_text(" ", strip=True) or a["href"])
    return seen


def scrape(base_url: str, writer, *, delay: float = 1.0, max_pages: int | None = None,
           default_condition: str = "Nuevo", default_genre: str | None = None,
           root_path: str = "/", progress=print, **_):
    http = PoliteSession(base_url, delay=delay)
    base = base_url.rstrip("/")
    categories = _categories(http, root_path)
    progress(f"  {len(categories)} categorías")
    processed, pages_done, seen = 0, 0, set()

    for path, cat_name in categories.items():
        start = 0
        genre = classify_genre([cat_name, path.split("/")[-1].replace("-", " ")], default_genre)
        while True:
            if max_pages and pages_done >= max_pages:
                return processed, False
            soup = BeautifulSoup(http.get(path, params={"start": start} if start else None).text, "html.parser")
            pages_done += 1
            cards = soup.select(".vm-product")
            for card in cards:
                link = card.select_one(".vm-title-teaser a[href]")
                price_el = card.select_one(".product-price[id]")
                if not link:
                    continue
                external_id = price_el["id"].replace("productPrice", "") if price_el else link["href"]
                if external_id in seen:  # Same book listed under several subjects
                    continue
                seen.add(external_id)
                sku_el = card.select_one(".vm-product-sku")
                author_el = card.select_one(".vm-description-short")
                sale_el = card.select_one(".PricesalesPrice")
                writer.upsert_offer(
                    external_id=external_id[:100],
                    isbn=clean_isbn(sku_el.get_text() if sku_el else None),
                    title=(link.get("title") or link.get_text(" ", strip=True))[:255],
                    author=(author_el.get_text(" ", strip=True).title() if author_el else None) or None,
                    genre=genre,
                    cover_url=None,
                    price_uyu=parse_uy_price(sale_el.get_text() if sale_el else None),
                    stock_quantity=1,
                    condition=default_condition,
                    product_url=f"{base}{link['href']}",
                )
                processed += 1
            writer.conn.commit()
            if len(cards) < PER_PAGE:
                break
            start += PER_PAGE
        progress(f"  {cat_name}: {processed} productos acumulados")

    return processed, True
