"""Anonymous usage events and the private stats endpoint.

What is stored (table `events`): event type, the searched text, the bookstore involved and
the number of results. No IP address, cookie, user agent or any personal data.

- Searches are logged by the API itself after answering (see log_search).
- Clicks on "Consultar aquí" (WhatsApp) and "Ver en tienda" arrive via POST /api/events,
  sent with navigator.sendBeacon from the frontend.
- GET /api/stats returns the dashboard data; it requires the STATS_KEY env var as header.
"""
import hmac
import json
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request

from db import get_db_connection

logger = logging.getLogger("librosuy.analytics")
router = APIRouter()

CLICK_EVENTS = {"whatsapp_click", "store_click"}
MAX_QUERY_LENGTH = 200


def log_search(query: str, results_count: int):
    """Runs as a FastAPI background task, after the response was sent."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO events (event_type, query, results_count) VALUES ('search', %s, %s)",
                (query.strip().lower()[:MAX_QUERY_LENGTH], results_count),
            )
    except Exception as e:  # Analytics must never break the site
        logger.warning("No se pudo registrar la búsqueda: %s", e)


@router.post("/api/events", status_code=204)
async def track_event(request: Request):
    """Click events. Body is JSON sent as text/plain (sendBeacon avoids a CORS preflight)."""
    try:
        data = json.loads((await request.body())[:2000] or b"{}")
        event_type = data.get("type")
        store_id = int(data["store_id"]) if data.get("store_id") is not None else None
        query = (data.get("query") or "").strip().lower()[:MAX_QUERY_LENGTH] or None
    except (ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=400, detail="Evento inválido")
    if event_type not in CLICK_EVENTS or store_id is None:
        raise HTTPException(status_code=400, detail="Evento inválido")

    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO events (event_type, bookstore_id, query)
                SELECT %s, bookstore_id, %s FROM bookstores WHERE bookstore_id = %s
            """, (event_type, query, store_id))
    except Exception as e:
        logger.warning("No se pudo registrar el evento: %s", e)


@router.get("/api/stats")
def get_stats(days: int = 30, x_stats_key: str = Header(default="")):
    expected = os.getenv("STATS_KEY", "")
    if not expected or not hmac.compare_digest(x_stats_key, expected):
        raise HTTPException(status_code=401, detail="Clave de estadísticas incorrecta")
    days = max(1, min(days, 365))

    with get_db_connection() as conn:
        def rows(sql, *params):
            return conn.execute(sql, params).fetchall()

        since = "created_at >= now() - make_interval(days => %s)"
        totals = dict(rows(f"""
            SELECT event_type, count(*) FROM events WHERE {since} GROUP BY event_type
        """, days))
        no_results = rows(f"""
            SELECT count(*) FROM events WHERE event_type = 'search' AND results_count = 0 AND {since}
        """, days)[0][0]
        per_day = rows(f"""
            SELECT to_char(date_trunc('day', created_at AT TIME ZONE 'America/Montevideo'), 'YYYY-MM-DD') AS day,
                   count(*) FILTER (WHERE event_type = 'search'),
                   count(*) FILTER (WHERE event_type = 'whatsapp_click'),
                   count(*) FILTER (WHERE event_type = 'store_click')
            FROM events WHERE {since} GROUP BY 1 ORDER BY 1
        """, days)
        top_searches = rows(f"""
            SELECT query, count(*) FROM events
            WHERE event_type = 'search' AND {since} GROUP BY query ORDER BY 2 DESC, 1 LIMIT 20
        """, days)
        top_not_found = rows(f"""
            SELECT query, count(*) FROM events
            WHERE event_type = 'search' AND results_count = 0 AND {since}
            GROUP BY query ORDER BY 2 DESC, 1 LIMIT 20
        """, days)
        per_store = rows(f"""
            SELECT s.name,
                   count(*) FILTER (WHERE e.event_type = 'whatsapp_click') AS whatsapp,
                   count(*) FILTER (WHERE e.event_type = 'store_click') AS tienda
            FROM events e JOIN bookstores s USING (bookstore_id)
            WHERE e.event_type IN ('whatsapp_click', 'store_click') AND e.{since}
            GROUP BY s.name ORDER BY count(*) DESC, s.name
        """, days)

    return {
        "days": days,
        "totals": {
            "searches": totals.get("search", 0),
            "searches_without_stock": no_results,
            "whatsapp_clicks": totals.get("whatsapp_click", 0),
            "store_clicks": totals.get("store_click", 0),
        },
        "per_day": [{"day": d, "searches": s, "whatsapp": w, "store": t} for d, s, w, t in per_day],
        "top_searches": [{"query": q, "count": c} for q, c in top_searches],
        "top_not_found": [{"query": q, "count": c} for q, c in top_not_found],
        "per_store": [{"store": n, "whatsapp": w, "store_clicks": t} for n, w, t in per_store],
    }
