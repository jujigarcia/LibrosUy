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
from scrapers import woocommerce
from scrapers.common import StockWriter

# Librerías cuyo sitio permite leer el catálogo (robots.txt revisado).
# Pendientes: Shopify (Vanir, Isadora, Librería Montevideo, Pocho), Fenicio (Grupo Libros)
# y sitios sin plataforma detectada. Franca Comics y Planeta bloquean bots en robots.txt.
SOURCES = [
    {"website": "puroverso.uy", "platform": "woocommerce", "base_url": "https://puroverso.uy"},
    {"website": "lecturascomics.com.uy", "platform": "woocommerce", "base_url": "https://lecturascomics.com.uy",
     "default_genre": "Cómics"},
    {"website": "librerialannister.com", "platform": "woocommerce", "base_url": "https://librerialannister.com"},
    # Sus categorías son genéricas ("Libros, Revistas y Comics"), no sirven para clasificar
    {"website": "librosleidos.com.uy", "platform": "woocommerce", "base_url": "https://www.librosleidos.com.uy",
     "condition": "Usado", "use_categories": False},
]

PLATFORMS = {"woocommerce": woocommerce.scrape}


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
            source["base_url"], writer, delay=delay, max_pages=max_pages,
            default_condition=source.get("condition", "Nuevo"),
            default_genre=source.get("default_genre"),
            use_categories=source.get("use_categories", True),
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
