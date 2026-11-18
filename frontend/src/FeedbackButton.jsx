import React, { useEffect, useRef, useState } from 'react';
import { Mail, X, CheckCircle2 } from 'lucide-react';
import { API_URL } from './analytics';

// Floating envelope (bottom-right) that opens a small "Sugerencias" form.
// Messages go to POST /api/feedback: stored in the DB and emailed with subject [LibrosUySugerencia].
const VIOLET = '#7e22ce';

export default function FeedbackButton() {
  const [open, setOpen] = useState(false);
  const [hover, setHover] = useState(false);
  const [message, setMessage] = useState('');
  const [contact, setContact] = useState('');
  const [website, setWebsite] = useState(''); // honeypot: hidden from people, bots fill it
  const [status, setStatus] = useState('idle'); // idle | sending | sent | error
  const [error, setError] = useState('');
  const [isMobile, setIsMobile] = useState(() => window.matchMedia('(max-width: 767px)').matches);
  const textareaRef = useRef(null);

  useEffect(() => {
    const media = window.matchMedia('(max-width: 767px)');
    const onChange = () => setIsMobile(media.matches);
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    textareaRef.current?.focus();
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  const close = () => {
    setOpen(false);
    if (status === 'sent') { setStatus('idle'); setMessage(''); setContact(''); }
  };

  const submit = async (e) => {
    e.preventDefault();
    if (message.trim().length < 3) { setError('Escribí tu sugerencia.'); return; }
    setStatus('sending');
    setError('');
    try {
      const page = window.location.hash.replace('#', '') || document.body.dataset.tab || 'home';
      const res = await fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message.trim(), contact: contact.trim() || null, page, website }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'No se pudo enviar.');
      }
      setStatus('sent');
    } catch (err) {
      setStatus('error');
      setError(err.message === 'Failed to fetch'
        ? 'No se pudo enviar. Si el servidor estaba dormido, probá de nuevo en unos segundos.'
        : err.message);
    }
  };

  // On phones the bottom tab bar is ~58px tall: keep the button above it
  const bottom = isMobile ? 'calc(74px + env(safe-area-inset-bottom))' : '24px';

  return (
    <>
      <div style={{ position: 'fixed', right: isMobile ? '16px' : '24px', bottom, zIndex: 1200, display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Hover label: "Sugerencias" */}
        {hover && !open && !isMobile && (
          <span role="tooltip" style={{ backgroundColor: '#1f2937', color: '#ffffff', fontSize: '0.8rem', fontWeight: 600, padding: '6px 10px', borderRadius: '8px', whiteSpace: 'nowrap', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
            Sugerencias
          </span>
        )}
        <button
          type="button"
          onClick={() => setOpen(true)}
          onMouseEnter={() => setHover(true)}
          onMouseLeave={() => setHover(false)}
          onFocus={() => setHover(true)}
          onBlur={() => setHover(false)}
          aria-label="Sugerencias"
          title="Sugerencias"
          style={{ width: isMobile ? '48px' : '52px', height: isMobile ? '48px' : '52px', borderRadius: '9999px', border: 'none', backgroundColor: VIOLET, color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 6px 18px rgba(126, 34, 206, 0.35)' }}
        >
          <Mail size={isMobile ? 21 : 23} />
        </button>
      </div>

      {open && (
        <div
          role="presentation"
          onClick={close}
          // Centered on every screen (not glued to the bottom edge, where phone browser bars and the
          // keyboard can cover it); scrolls inside if it doesn't fit
          style={{ position: 'fixed', inset: 0, zIndex: 1300, backgroundColor: 'rgba(17, 24, 39, 0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                   padding: isMobile ? 'calc(16px + env(safe-area-inset-top)) 14px calc(16px + env(safe-area-inset-bottom))' : '16px' }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="feedback-title"
            onClick={(e) => e.stopPropagation()}
            style={{ width: '100%', maxWidth: '440px', maxHeight: '100%', overflowY: 'auto', backgroundColor: '#ffffff', borderRadius: '16px', padding: isMobile ? '18px 16px' : '22px', boxShadow: '0 20px 50px rgba(0,0,0,0.25)', fontFamily: 'system-ui, -apple-system, sans-serif' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
              <h2 id="feedback-title" style={{ margin: 0, fontSize: '1.2rem', color: '#4c1d95', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Mail size={20} /> Sugerencias
              </h2>
              <button type="button" onClick={close} aria-label="Cerrar" style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#6b7280', padding: '6px', display: 'flex' }}>
                <X size={20} />
              </button>
            </div>

            {status === 'sent' ? (
              <div style={{ textAlign: 'center', padding: '18px 4px 8px' }}>
                <CheckCircle2 size={40} color="#16a34a" style={{ margin: '0 auto 8px', display: 'block' }} />
                <p style={{ margin: '0 0 4px', fontWeight: 700, color: '#1f2937' }}>¡Gracias! Recibimos tu mensaje.</p>
                <p style={{ margin: '0 0 16px', color: '#6b7280', fontSize: '0.9rem' }}>Lo vamos a leer para seguir mejorando LibrosUy.</p>
                <button type="button" onClick={close} style={{ minHeight: '42px', padding: '0 22px', borderRadius: '9999px', border: 'none', backgroundColor: VIOLET, color: '#ffffff', fontWeight: 700, cursor: 'pointer' }}>
                  Cerrar
                </button>
              </div>
            ) : (
              <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <p style={{ margin: '0 0 4px', color: '#6b7280', fontSize: '0.9rem', lineHeight: 1.45 }}>
                  Contanos qué podemos mejorar o si tuviste algún inconveniente.
                </p>
                <textarea
                  ref={textareaRef}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  maxLength={2000}
                  rows={isMobile ? 4 : 5}
                  placeholder="Tu sugerencia o el problema que encontraste…"
                  aria-label="Tu sugerencia"
                  style={{ fontSize: '16px', padding: '10px 12px', border: '1px solid #e9d5ff', borderRadius: '10px', resize: 'vertical', fontFamily: 'inherit' }}
                />
                <input
                  type="email"
                  value={contact}
                  onChange={(e) => setContact(e.target.value)}
                  maxLength={200}
                  placeholder="Tu email (opcional, si querés respuesta)"
                  aria-label="Tu email (opcional)"
                  style={{ fontSize: '16px', padding: '10px 12px', border: '1px solid #e9d5ff', borderRadius: '10px' }}
                />
                {/* Honeypot: invisible to people, tempting for bots */}
                <input type="text" value={website} onChange={(e) => setWebsite(e.target.value)} tabIndex={-1} autoComplete="off" aria-hidden="true"
                       style={{ position: 'absolute', left: '-9999px', width: '1px', height: '1px', opacity: 0 }} name="website" />
                {error && <p role="alert" style={{ margin: 0, color: '#b91c1c', fontSize: '0.85rem' }}>{error}</p>}
                <button type="submit" disabled={status === 'sending'}
                        style={{ minHeight: '46px', borderRadius: '12px', border: 'none', backgroundColor: VIOLET, color: '#ffffff', fontWeight: 700, fontSize: '1rem', cursor: status === 'sending' ? 'wait' : 'pointer', opacity: status === 'sending' ? 0.7 : 1 }}>
                  {status === 'sending' ? 'Enviando…' : 'Enviar'}
                </button>
                <a href="#privacidad" onClick={close} style={{ fontSize: '0.75rem', color: '#9ca3af', textAlign: 'center' }}>Cómo usamos estos datos</a>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}
