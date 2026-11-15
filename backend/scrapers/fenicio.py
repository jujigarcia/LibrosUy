"""Scraper for Fenicio stores (Uruguayan e-commerce platform), e.g. Grupo Libros.

Fenicio loads the catalog with "Ver más" via `/catalogo?js=1&pag=N`, which returns the
next block of product cards. Each card carries availability (`data-disp`), the product
code (usually the ISBN) and a hidden JSON with name, price and publisher.
"""
import html
import json

from bs4 import BeautifulSoup

from .common import PoliteSession, clean_isbn


def scrape(base_url: str, writer, *, delay: float = 1.0, max_pages: int | None = None,
           default_condition: str = "Nuevo", default_genre: str | None = None,
           catalog_path: str = "/catalogo", progress=print, **_):
    http = PoliteSession(base_url, delay=delay)
    page, processed, seen = 1, 0, set()

    while True:
        resp = http.get(catalog_path, params={"js": 1, "pag": page})
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(".aListProductos > .it")
        if page == 1:
            listing = soup.select_one(".aListProductos")
            total = listing.get("data-totabs") if listing else "?"
            progress(f"  {total} productos")
        if not cards:
            return processed, True

        new_on_page = 0
        for card in cards:
            raw = card.select_one("input.json")
            if not raw:
                continue
            data = json.loads(html.unescape(raw.get("value") or "{}"))
            variant = data.get("variante") or {}
            code = card.get("data-codprod") or (data.get("producto") or {}).get("codigo")
            if not code or code in seen:
                continue
            seen.add(code)
            new_on_page += 1

            price = data.get("precioMonto")
            currency = (data.get("moneda") or {}).get("cod")
            img = (variant.get("img") or {}).get("u")
            writer.upsert_offer(
                external_id=str(code),
                isbn=clean_isbn(code),
                title=(data.get("nombre") or variant.get("nombre") or "").strip()[:255],
                author=None,
                genre=default_genre,
                cover_url=(f"https:{img}" if img and img.startswith("//") else img),
                price_uyu=float(price) if price and currency in (None, "UYU") else None,
                stock_quantity=1 if card.get("data-disp") == "1" else 0,
                condition=default_condition,
                product_url=variant.get("url"),
            )
            processed += 1
        writer.commit()

        if new_on_page == 0:  # The site repeats the last page instead of returning empty
            return processed, True
        if page % 25 == 0:
            progress(f"  página {page} · {processed} productos")
        if max_pages and page >= max_pages:
            return processed, False
        page += 1
