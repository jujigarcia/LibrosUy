"""
Busca librerías nuevas de Uruguay en OpenStreetMap (gratis) y las agrega a `bookstores`.

Pensado para correr una vez por semana (tarea "LibrosUy Nuevas Librerías"). Las librerías
nuevas quedan OCULTAS (is_active = false) hasta que alguien revise sus datos:

    python seed_stores.py --pending      # lista las pendientes de revisión
    UPDATE bookstores SET is_active = true, specialty = 'Ficción, Juvenil', department = 'Montevideo'
    WHERE bookstore_id = 42;             # publicarla

Cada librería guarda su osm_id, así no se vuelve a insertar aunque se le cambie el nombre.
Para descartar una para siempre, dejala oculta (no la borres): si se borra, vuelve a aparecer.

Uso:
    python seed_stores.py              # inserta las librerías nuevas (ocultas)
    python seed_stores.py --dry-run    # solo muestra qué insertaría
    python seed_stores.py --pending    # lista las pendientes de revisión
"""
import re
import sys
import time
import unicodedata
from urllib.parse import urlparse

import requests

from db import get_db_connection

# Main public server + community mirror (https://wiki.openstreetmap.org/wiki/Overpass_API)
OVERPASS_SERVERS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
OVERPASS_QUERY = """
[out:json][timeout:60];
area["ISO3166-1"="UY"]->.searchArea;
nwr["shop"="books"](area.searchArea);
out center tags;
"""
USER_AGENT = "LibrosUyBot/1.0 (+https://librosuy.com.uy)"
DEFAULT_SPECIALTY = "Catálogo General"

# Words that don't identify a store ("Librería Puro Verso" == "Puro Verso")
STOPWORDS = {"libreria", "librerias", "libros", "libro", "la", "el", "los", "las", "de", "del", "y",
             "book", "books", "bookstore", "store", "shop", "tienda", "sucursal", "uy"}


def normalize_name(name: str) -> str:
    """Comparison key: no accents, case, punctuation, spaces or generic words.
    Names made only of generic words ("Bookshop", "Libros Libros") keep all their words."""
    text = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode().lower()
    words = [w for w in re.split(r"[^a-z0-9]+", text) if w]
    meaningful = [w for w in words if w not in STOPWORDS]
    return "".join(meaningful or words)


def domain(url: str | None) -> str | None:
    if not url:
        return None
    host = urlparse(url if "://" in url else f"https://{url}").netloc.lower()
    return host.removeprefix("www.") or None


def same_store(a: str, b: str) -> bool:
    """Same normalized name, or one contains the other (min. 5 chars to avoid false matches)."""
    if not a or not b:
        return False
    if a == b:
        return True
    short, long_ = sorted((a, b), key=len)
    return len(short) >= 5 and short in long_


def _whatsapp(tags: dict) -> str | None:
    raw = tags.get("contact:whatsapp") or tags.get("whatsapp")
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits and not digits.startswith("598"):
        digits = "598" + digits.lstrip("0")
    return digits if len(digits) >= 11 else None


def _instagram(tags: dict) -> str | None:
    raw = (tags.get("contact:instagram") or tags.get("instagram") or "").strip()
    match = re.search(r"(?:instagram\.com/)?@?([A-Za-z0-9_.]{2,30})/?$", raw)
    return match.group(1) if match else None


def _query_overpass():
    """The public Overpass servers are often busy (429/502/504): retry, then try a mirror."""
    last_error = None
    for url in OVERPASS_SERVERS:
        for attempt in range(3):
            try:
                response = requests.post(url, data={"data": OVERPASS_QUERY},
                                         headers={"User-Agent": USER_AGENT}, timeout=120)
                if response.status_code in (429, 502, 503, 504):
                    raise requests.HTTPError(f"{response.status_code} en {url}")
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                last_error = e
                print(f"  Overpass no respondió ({e}); reintento en {30 * (attempt + 1)}s...")
                time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"OpenStreetMap no disponible: {last_error}")


def fetch_osm_bookstores():
    data = _query_overpass()

    stores = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = (tags.get("name") or "").strip()
        lat = element.get("lat") or element.get("center", {}).get("lat")
        lon = element.get("lon") or element.get("center", {}).get("lon")
        if not name or lat is None or lon is None:
            continue  # Sin nombre o sin ubicación no sirve para el directorio

        street = " ".join(p for p in [tags.get("addr:street"), tags.get("addr:housenumber")] if p)
        city = tags.get("addr:city") or ""
        website = (tags.get("website") or tags.get("contact:website") or "").strip()
        stores.append({
            "osm_id": f"{element['type']}/{element['id']}",
            "name": name[:150],
            "website": (domain(website) if website else None),
            "address": (street or city or "Dirección a confirmar")[:255],
            "department": (tags.get("addr:state") or city or "A confirmar")[:100],
            "latitude": round(float(lat), 6),
            "longitude": round(float(lon), 6),
            "whatsapp": _whatsapp(tags),
            "instagram": _instagram(tags),
        })
    return stores


def list_pending():
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT bookstore_id, name, address, department, website, discovered_at::date
            FROM bookstores WHERE NOT is_active AND osm_id IS NOT NULL
            ORDER BY discovered_at DESC, name
        """).fetchall()
    if not rows:
        print("No hay librerías pendientes de revisión.")
        return 0
    print(f"{len(rows)} librerías pendientes de revisión (ocultas en el sitio):")
    for store_id, name, address, department, website, found in rows:
        print(f"  [{store_id:>4}] {name} — {address} ({department})"
              f"{f' · {website}' if website else ''} · encontrada {found}")
    return 0


def main(dry_run: bool):
    print("Consultando librerías en OpenStreetMap...")
    osm_stores = fetch_osm_bookstores()
    print(f"OpenStreetMap devolvió {len(osm_stores)} librerías con nombre y ubicación.")

    conn = get_db_connection(direct=True)
    cursor = conn.cursor()
    cursor.execute("SELECT name, website, osm_id FROM bookstores")
    known_osm_ids, known_names, known_domains = set(), [], set()
    for name, website, osm_id in cursor.fetchall():
        if osm_id:
            known_osm_ids.add(osm_id)
        known_names.append(normalize_name(name))
        if website:
            known_domains.add(domain(website))

    new, skipped, failed = [], 0, 0
    try:
        for store in osm_stores:
            norm = normalize_name(store["name"])
            if (store["osm_id"] in known_osm_ids
                    or (store["website"] and store["website"] in known_domains)
                    or any(same_store(norm, known) for known in known_names)):
                skipped += 1
                continue
            known_osm_ids.add(store["osm_id"])
            known_names.append(norm)

            if dry_run:
                new.append(store)
                continue
            try:
                # Savepoint per row: in PostgreSQL one failed INSERT would abort the whole transaction
                with conn.transaction():
                    cursor.execute("""
                        INSERT INTO bookstores (name, website, whatsapp, instagram, specialty, address,
                                                department, latitude, longitude, ingestion_method,
                                                sync_frequency, featured, is_active, osm_id, discovered_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'google_sheets', 'daily',
                                false, false, %s, now())
                    """, (store["name"], store["website"], store["whatsapp"], store["instagram"],
                          DEFAULT_SPECIALTY, store["address"], store["department"],
                          store["latitude"], store["longitude"], store["osm_id"]))
                new.append(store)
            except Exception as e:
                failed += 1
                print(f"  No se pudo insertar {store['name']!r}: {e}")

        if not dry_run:
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    for store in new:
        print(f"  {'[dry-run] ' if dry_run else '+ '}{store['name']} — {store['address']} ({store['department']})")
    action = "Se insertarían" if dry_run else "Nuevas (ocultas, para revisar)"
    print(f"{action}: {len(new)} · Ya conocidas: {skipped} · Con error: {failed}")
    if new and not dry_run:
        print("Revisalas con: python seed_stores.py --pending")
    return 1 if failed else 0


if __name__ == "__main__":
    if "--pending" in sys.argv:
        sys.exit(list_pending())
    sys.exit(main(dry_run="--dry-run" in sys.argv))
