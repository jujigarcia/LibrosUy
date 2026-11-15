"""Scraper for Magento 2 stores via the public storefront GraphQL API (/graphql).

The same API the store's own pages use: 100 products per request with ISBN (sku),
final UYU price, stock status and categories. `category_uid` limits the catalog to books
for stores that also sell other things (e.g. Mosca: toys, stationery, tech).
"""
from .common import PoliteSession, classify_genre, clean_isbn

PAGE_SIZE = 100
QUERY = """
query ($filter: ProductAttributeFilterInput, $page: Int!, $size: Int!) {
  products(search: "", filter: $filter, pageSize: $size, currentPage: $page) {
    total_count
    page_info { total_pages }
    items {
      uid name sku url_key url_suffix stock_status
      small_image { url }
      categories { name }
      price_range { minimum_price { final_price { value currency } } }
    }
  }
}
"""


def scrape(base_url: str, writer, *, delay: float = 1.0, max_pages: int | None = None,
           default_condition: str = "Nuevo", default_genre: str | None = None,
           use_categories: bool = True, category_uid: str | None = None, progress=print, **_):
    http = PoliteSession(base_url, delay=delay)
    base = base_url.rstrip("/")
    variables = {"page": 1, "size": PAGE_SIZE,
                 "filter": {"category_uid": {"eq": category_uid}} if category_uid else {}}
    processed, total_pages = 0, None

    while True:
        resp = http.post("/graphql", json={"query": QUERY, "variables": variables})
        payload = resp.json()
        if payload.get("errors"):
            raise RuntimeError(f"GraphQL: {payload['errors'][0].get('message')}")
        data = payload["data"]["products"]
        if total_pages is None:
            total_pages = data["page_info"]["total_pages"] or 1
            progress(f"  {data['total_count']} productos en {total_pages} páginas")

        for item in data["items"]:
            price = item["price_range"]["minimum_price"]["final_price"]
            categories = [c["name"] for c in item.get("categories") or []] if use_categories else []
            url_key = item.get("url_key")
            writer.upsert_offer(
                external_id=item["uid"],
                isbn=clean_isbn(item.get("sku")),
                title=(item.get("name") or "").strip()[:255],
                author=None,
                genre=classify_genre(categories, default_genre),
                cover_url=((item.get("small_image") or {}).get("url") or "")[:500] or None,
                price_uyu=price["value"] if price.get("currency") == "UYU" and price.get("value") else None,
                stock_quantity=1 if item.get("stock_status") == "IN_STOCK" else 0,
                condition=default_condition,
                product_url=f"{base}/{url_key}{item.get('url_suffix') or '.html'}" if url_key else None,
            )
            processed += 1
        writer.conn.commit()

        page = variables["page"]
        if page % 10 == 0:
            progress(f"  página {page}/{total_pages} · {processed} productos")
        if page >= total_pages:
            return processed, True
        if max_pages and page >= max_pages:
            return processed, False
        variables["page"] = page + 1
