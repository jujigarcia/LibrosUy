// Anonymous click tracking for LibrosUy's own stats (see backend/analytics.py).
// Only the event type, the bookstore and the searched text are sent: no personal data.

export const API_URL = (process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

// type: 'whatsapp_click' | 'store_click'
export function trackClick(type, storeId, query = null) {
  if (storeId == null) return;
  const body = JSON.stringify({ type, store_id: storeId, query });
  const url = `${API_URL}/api/events`;
  try {
    // sendBeacon survives the page opening WhatsApp or the store's site.
    // text/plain keeps it a "simple" cross-origin request (no CORS preflight).
    if (navigator.sendBeacon && navigator.sendBeacon(url, new Blob([body], { type: 'text/plain' }))) {
      return;
    }
    fetch(url, { method: 'POST', body, headers: { 'Content-Type': 'text/plain' }, keepalive: true }).catch(() => {});
  } catch {
    // Stats must never get in the way of the user
  }
}
