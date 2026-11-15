"""
Sincroniza el stock de las librerías con tienda online.

Uso:
    python run_scrapers.py                                # todas las fuentes, catálogo completo
    python run_scrapers.py --store puroverso.uy           # una sola librería
    python run_scrapers.py --store puroverso.uy --max-pages 3   # prueba rápida (300 productos)
    python run_scrapers.py --list                         # muestra las fuentes configuradas

Solo una corrida completa marca como "sin stock" los productos que desaparecieron del sitio;
una corrida parcial (--max-pages) solo agrega o actualiza.
"""
import argparse
import sys
import time

from db import get_db_connection
from scrapers import escaramuza, fenicio, magento, shopify, virtuemart, woocommerce
from scrapers.common import StockWriter

# Librerías cuyo sitio permite leer el catálogo (robots.txt revisado).
# Cualquier clave extra (default_condition, default_genre, category_uid, ...) se pasa al scraper.
#
# Sin scraper (ver README): Franca Comics y Planeta bloquean bots en robots.txt; Librería Vila
# responde 403 a bots; El Virrey: el dominio no existe; Babilonia (tienda Hostinger) y Rizoma
# no exponen un catálogo legible desde su propio sitio; Entrelibros es un blog, no una tienda.
SOURCES = [
    # WooCommerce (Store API)
    {"website": "puroverso.uy", "platform": "woocommerce", "base_url": "https://puroverso.uy"},
    {"website": "lecturascomics.com.uy", "platform": "woocommerce", "base_url": "https://lecturascomics.com.uy",
     "default_genre": "Cómics"},
    {"website": "librerialannister.com", "platform": "woocommerce", "base_url": "https://librerialannister.com"},
    # Sus categorías son genéricas ("Libros, Revistas y Comics"), no sirven para clasificar
    {"website": "librosleidos.com.uy", "platform": "woocommerce", "base_url": "https://www.librosleidos.com.uy",
     "default_condition": "Usado", "use_categories": False},
    # Magento 2 (GraphQL)
    {"website": "bookshop.com.uy", "platform": "magento", "base_url": "https://www.bookshop.com.uy"},
    # Mosca vende también juguetes, papelería y tecnología: solo la categoría "Libros"
    {"website": "mosca.com.uy", "platform": "magento", "base_url": "https://www.mosca.com.uy",
     "category_uid": "Mzc0"},
    # Fenicio
    {"website": "grupolibros.com.uy", "platform": "fenicio", "base_url": "https://grupolibros.com.uy"},
    # Catálogo propio (HTML)
    {"website": "escaramuza.com.uy", "platform": "escaramuza", "base_url": "https://escaramuza.com.uy"},
    {"website": "laskaramazov.com.uy", "platform": "virtuemart", "base_url": "https://laskaramazov.com.uy"},
    # Shopify (páginas de colección HTML; products.json está bloqueado para bots)
    {"website": "vanir.com.uy", "platform": "shopify", "base_url": "https://vanir.com.uy", "min_delay": 3},
    {"website": "isadoralibros.com.uy", "platform": "shopify", "base_url": "https://isadoralibros.com.uy", "min_delay": 3},
    {"website": "libreriamontevideo.com", "platform": "shopify", "base_url": "https://libreriamontevideo.com", "min_delay": 3},
    {"website": "libreriapocho.com.uy", "platform": "shopify", "base_url": "https://www.libreriapocho.com.uy", "min_delay": 3},
]

PLATFORMS = {
    "woocommerce": woocommerce.scrape,
    "magento": magento.scrape,
    "fenicio": fenicio.scrape,
    "escaramuza": escaramuza.scrape,
    "virtuemart": virtuemart.scrape,
    "shopify": shopify.scrape,
}
SOURCE_META_KEYS = {"website", "platform", "base_url", "min_delay"}


def run_source(conn, source, max_pages, delay):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT TOP 1 bookstore_id, name FROM bookstores WHERE website = ? AND is_active = 1 ORDER BY bookstore_id",
        (source["website"],),
    )
    row = cursor.fetchone()
    if not row:
        print(f"[{source['website']}] No hay librería activa con ese sitio en la base; se omite.")
        return False

    bookstore_id, name = row
    print(f"[{name}] Sincronizando {source['base_url']} ({source['platform']})...")
    writer = StockWriter(conn, bookstore_id)
    started = time.monotonic()
    processed = 0
    try:
        processed, complete = PLATFORMS[source["platform"]](
            source["base_url"], writer, delay=max(delay, source.get("min_delay", 0)), max_pages=max_pages,
            **{k: v for k, v in source.items() if k not in SOURCE_META_KEYS},
        )
        removed = writer.mark_unseen_out_of_stock() if complete else 0
        writer.log("success" if complete else "partial", processed)
        conn.commit()
        print(f"[{name}] OK: {processed} productos"
              f"{f', {removed} marcados sin stock' if removed else ''}"
              f"{'' if complete else ' (corrida parcial)'} en {time.monotonic() - started:.0f}s")
        return True
    except Exception as e:
        conn.rollback()
        writer.log("failed", processed)
        conn.commit()
        print(f"[{name}] ERROR: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Scrapers de stock de LibrosUy")
    parser.add_argument("--store", help="Sitio de una sola librería, ej. puroverso.uy")
    parser.add_argument("--max-pages", type=int, help="Límite de páginas de 100 productos (prueba)")
    parser.add_argument("--delay", type=float, default=1.0, help="Segundos entre pedidos al mismo sitio")
    parser.add_argument("--list", action="store_true", help="Lista las fuentes configuradas")
    args = parser.parse_args()

    if args.list:
        for s in SOURCES:
            print(f"{s['website']:28} {s['platform']:12} {s['base_url']}")
        return 0

    sources = [s for s in SOURCES if not args.store or s["website"] == args.store]
    if not sources:
        print(f"No hay una fuente configurada para {args.store!r}. Usá --list.")
        return 1

    conn = get_db_connection()
    try:
        results = [run_source(conn, s, args.max_pages, args.delay) for s in sources]
    finally:
        conn.close()
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
