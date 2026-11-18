"""Suggestions / problem reports from the floating "Sugerencias" button.

Every message is stored in the `feedback` table (so nothing is lost if email fails) and then
emailed with Resend (https://resend.com) when these env vars are set on the server:

    RESEND_API_KEY   Resend API key
    FEEDBACK_EMAIL   address that receives the messages
    FEEDBACK_FROM    optional sender, default "LibrosUy <onboarding@resend.dev>"
                     (Resend's test sender: only delivers to the Resend account's own email
                     until a domain is verified)

Spam protection: a hidden "website" field that people never fill (bots do) and a small
in-memory rate limit per client. The client IP is only used for that limit and never stored.
"""
import logging
import os
import re
import time
from collections import defaultdict, deque

import requests
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from db import get_db_connection

logger = logging.getLogger("librosuy.feedback")
router = APIRouter()

SUBJECT = "[LibrosUySugerencia]"
MAX_MESSAGE = 2000
RATE_LIMIT = 5            # messages...
RATE_WINDOW = 10 * 60     # ...per 10 minutes per client
_recent = defaultdict(deque)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class Feedback(BaseModel):
    message: str
    contact: str | None = None   # optional email so we can answer
    page: str | None = None      # tab the user was on
    website: str | None = None   # honeypot: must stay empty


def _rate_limited(client: str) -> bool:
    now = time.monotonic()
    hits = _recent[client]
    while hits and now - hits[0] > RATE_WINDOW:
        hits.popleft()
    if len(hits) >= RATE_LIMIT:
        return True
    hits.append(now)
    return False


def _send_email(feedback_id: int, message: str, contact: str | None, page: str | None):
    api_key, to = os.getenv("RESEND_API_KEY"), os.getenv("FEEDBACK_EMAIL")
    if not api_key or not to:
        logger.info("Sugerencia %s guardada; email no configurado (RESEND_API_KEY / FEEDBACK_EMAIL)", feedback_id)
        return
    body = (f"{message}\n\n---\n"
            f"Contacto: {contact or '(no dejó)'}\n"
            f"Sección: {page or '-'}\n"
            f"ID: {feedback_id}")
    payload = {
        "from": os.getenv("FEEDBACK_FROM", "LibrosUy <onboarding@resend.dev>"),
        "to": [to],
        "subject": SUBJECT,
        "text": body,
    }
    if contact and EMAIL_RE.match(contact):
        payload["reply_to"] = contact  # "Responder" in the mail goes straight to the user
    try:
        resp = requests.post("https://api.resend.com/emails", json=payload,
                             headers={"Authorization": f"Bearer {api_key}"}, timeout=15)
        resp.raise_for_status()
        with get_db_connection() as conn:
            conn.execute("UPDATE feedback SET emailed = true WHERE feedback_id = %s", (feedback_id,))
    except Exception as e:
        logger.warning("No se pudo enviar el email de la sugerencia %s: %s", feedback_id, e)


@router.post("/api/feedback")
def submit_feedback(data: Feedback, request: Request, background_tasks: BackgroundTasks):
    if data.website:  # Bot filled the hidden field: pretend it worked
        return {"ok": True}
    message = (data.message or "").strip()
    if len(message) < 3:
        raise HTTPException(status_code=400, detail="Escribí tu sugerencia.")
    client = (request.headers.get("x-forwarded-for") or (request.client.host if request.client else "?")).split(",")[0]
    if _rate_limited(client):
        raise HTTPException(status_code=429, detail="Recibimos varios mensajes seguidos. Probá en unos minutos.")

    contact = (data.contact or "").strip()[:200] or None
    page = (data.page or "").strip()[:50] or None
    with get_db_connection() as conn:
        feedback_id = conn.execute(
            "INSERT INTO feedback (message, contact, page) VALUES (%s, %s, %s) RETURNING feedback_id",
            (message[:MAX_MESSAGE], contact, page),
        ).fetchone()[0]

    background_tasks.add_task(_send_email, feedback_id, message[:MAX_MESSAGE], contact, page)
    return {"ok": True}
