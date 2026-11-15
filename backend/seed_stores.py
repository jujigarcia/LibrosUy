"""
Descubre librerías de Uruguay en OpenStreetMap y agrega a la tabla `bookstores`
las que todavía no están cargadas.

Las librerías nuevas se insertan con is_active = false (pendientes de revisión) para
que no aparezcan en el mapa hasta que alguien confirme sus datos y especialidad.
Para publicarlas: UPDATE bookstores SET is_active = true, specialty = N'...' WHERE bookstore_id = ...

Uso:
    python seed_stores.py            # inserta las librerías nuevas
    python seed_stores.py --dry-run  # solo muestra qué insertaría
"""
import sys
import requests

from db import get_db_connection

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = """
[out:json][timeout:25];
area["ISO3166-1"="UY"]->.searchArea;
nwr["shop"="books"](area.searchArea);
out center;
"""
DEFAULT_SPECIALTY = "Catálogo General"


def fetch_osm_bookstores():
    response = requests.post(
        OVERPASS_URL,
        data={"data": OVERPASS_QUERY},
        headers={"User-Agent": "LibrosUyApp/1.0 (Local Development)"},
        timeout=60,
    )
    response.raise_for_status()

    stores = []
    for element in response.json().get("elements", []):
        tags = element.get("tags", {})
        name = (tags.get("name") or "").strip()
        lat = element.get("lat") or element.get("center", {}).get("lat")
        lon = element.get("lon") or element.get("center", {}).get("lon")
        if not name or lat is None or lon is None:
            continue  # Sin nombre o sin ubicación no sirve para el directorio

        street = " ".join(p for p in [tags.get("addr:street"), tags.get("addr:housenumber")] if p)
        city = tags.get("addr:city") or ""
        address = street or city or "Dirección a confirmar"
        department = tags.get("addr:state") or city or "A confirmar"
        website = (tags.get("website") or tags.get("contact:website") or "").strip()
        website = website.removeprefix("https://").removeprefix("http://").rstrip("/") or None

        stores.append({
            "name": name[:150],
            "website": website[:255] if website else None,
            "address": address[:255],
            "department": department[:100],
            "latitude": round(float(lat), 6),
            "longitude": round(float(lon), 6),
        })
    return stores


def main(dry_run: bool):
    print("Consultando librerías en OpenStreetMap...")
    osm_stores = fetch_osm_bookstores()
    print(f"OpenStreetMap devolvió {len(osm_stores)} librerías con nombre y ubicación.")

    conn = get_db_connection(direct=True)
    cursor = conn.cursor()
    cursor.execute("SELECT lower(name) FROM bookstores")
    existing = {row[0] for row in cursor.fetchall()}

    inserted, skipped, failed = 0, 0, 0
    try:
        for store in osm_stores:
            if store["name"].lower() in existing:
                skipped += 1
                continue
            existing.add(store["name"].lower())

            if dry_run:
                print(f"  [dry-run] {store['name']} — {store['address']} ({store['department']})")
                inserted += 1
                continue

            try:
                # Savepoint per row: in PostgreSQL one failed INSERT would abort the whole transaction
                with conn.transaction():
                    cursor.execute("""
                        INSERT INTO bookstores (name, website, specialty, address, department,
                                                latitude, longitude, ingestion_method, sync_frequency,
                                                featured, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'google_sheets', 'daily', false, false)
                    """, (store["name"], store["website"], DEFAULT_SPECIALTY, store["address"],
                          store["department"], store["latitude"], store["longitude"]))
                inserted += 1
            except Exception as e:
                failed += 1
                print(f"  No se pudo insertar {store['name']!r}: {e}")

        if not dry_run:
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    action = "Se insertarían" if dry_run else "Insertadas"
    print(f"{action}: {inserted} · Ya existentes: {skipped} · Con error: {failed}")
    if inserted and not dry_run:
        print("Las nuevas quedaron con is_active = false: revisalas antes de publicarlas.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(dry_run="--dry-run" in sys.argv))
