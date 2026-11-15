"""Scraper for Shopify stores via the public collection pages (/collections/all?page=N).

Shopify blocks its JSON endpoints (products.json) for bots, but robots.txt allows the
HTML catalog. Each collection page embeds `var meta = {...}` with id, ISBN (sku), price
and vendor for every product; availability is read from each product card ("Agotado").
"""
import json
import re

from bs4 import BeautifulSoup

from .common import PoliteSession, classify_genre, clean_isbn, stock_from_label

META_RE = re.compile(r"var meta = (\{.*?\});\s*\n", re.S)
SOLD_OUT_RE = re.compile(r"agotad|sold[\s-]?out|sin stock", re.I)


def _card_sold_out(soup: BeautifulSoup, handle: str) -> bool:
    """Finds the product card that links to this handle and checks for a sold-out marker."""
    link = soup.find("a", href=re.compile(rf"/products/{re.escape(handle)}(?:[?#\"]|$)"))
    node = link
    # Walk up until reaching a container that holds the whole card (price + badges)
    for _ in range(8):
        if node is None or node.parent is None:
            break
        node = node.parent
        classes = " ".join(node.get("class") or [])
        if node.name in ("li", "article") or re.search(r"card|product-item|grid__item|product-block", classes):
            break
    if node is None:
        return False
    text = node.get_text(" ", strip=True)
    classes = " ".join(" ".join(el.get("class") or []) for el in node.find_all(True, class_=True))
    return bool(SOLD_OUT_RE.search(text) or SOLD_OUT_RE.search(classes))


def _title_from_variant(variant: dict, handle: str) -> str:
    name = (variant.get("name") or "").strip()
    public = variant.get("public_title")
    if public and name.endswith(f" - {public}"):
        name = name[: -len(f" - {public}")]
    return name or handle.replace("-", " ").title()


def scrape(base_url: str, writer, *, delay: float = 1.0, max_pages: int | None = None,
           default_condition: str = "Nuevo", default_genre: str | None = None,
           collection: str = "all", progress=print, **_):
    http = PoliteSession(base_url, delay=delay)
    base = base_url.rstrip("/")
    page, processed = 1, 0

    while True:
        resp = http.get(f"/collections/{collection}", params={"page": page})
        match = META_RE.search(resp.text)
        products = json.loads(match.group(1)).get("products", []) if match else []
        if not products:
            return processed, True

        soup = BeautifulSoup(resp.text, "html.parser")
        for p in products:
            variants = p.get("variants") or []
            if not variants:
                continue
            v = variants[0]
            price = (v.get("price") or 0) / 100  # Shopify meta prices are in cents
            sold_out = _card_sold_out(soup, p["handle"])
            writer.upsert_offer(
                external_id=str(p["id"]),
                isbn=clean_isbn(v.get("sku")),
                title=_title_from_variant(v, p["handle"]),
                author=None,
                genre=classify_genre([p.get("type") or ""] if p.get("type") else [], default_genre),
                cover_url=None,
                price_uyu=price or None,
                stock_quantity=stock_from_label("Agotado" if sold_out else None),
                condition=default_condition,
                product_url=f"{base}/products/{p['handle']}",
            )
            processed += 1
        writer.conn.commit()

        if page % 10 == 0:
            progress(f"  página {page} · {processed} productos")
        if max_pages and page >= max_pages:
            return processed, False
        page += 1
