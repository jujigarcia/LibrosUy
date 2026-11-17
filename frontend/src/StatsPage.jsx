import React, { useCallback, useEffect, useState } from 'react';
import { BarChart3, Search, MessageCircle, ExternalLink, SearchX, Lock } from 'lucide-react';
import { API_URL } from './analytics';

// Private dashboard at /#estadisticas. Data comes from GET /api/stats, protected by STATS_KEY.
const KEY_STORAGE = 'librosuy_stats_key';
const PERIODS = [7, 30, 90];

const card = { backgroundColor: '#ffffff', border: '1px solid #e9d5ff', borderRadius: '14px', padding: '18px' };

function readStoredKey() {
  try { return sessionStorage.getItem(KEY_STORAGE) || ''; } catch { return ''; }
}

function Kpi({ Icon, label, value, hint }) {
  return (
    <div style={card}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6b21a8', fontSize: '0.85rem', fontWeight: 700 }}>
        <Icon size={16} /> {label}
      </div>
      <div style={{ fontSize: '2rem', fontWeight: 800, color: '#1f2937', marginTop: '6px', fontVariantNumeric: 'tabular-nums' }}>
        {value.toLocaleString('es-UY')}
      </div>
      {hint && <div style={{ fontSize: '0.78rem', color: '#6b7280', marginTop: '2px' }}>{hint}</div>}
    </div>
  );
}

function RankTable({ title, rows, columns, empty }) {
  return (
    <div style={card}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '1.05rem', color: '#4c1d95' }}>{title}</h3>
      {rows.length === 0 ? (
        <p style={{ margin: 0, color: '#9ca3af', fontSize: '0.9rem' }}>{empty}</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
          <thead>
            <tr>
              {columns.map((c) => (
                <th key={c.key} style={{ textAlign: c.numeric ? 'right' : 'left', color: '#6b7280', fontWeight: 600, padding: '6px 4px', borderBottom: '1px solid #f3e8ff' }}>{c.label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {columns.map((c) => (
                  <td key={c.key} style={{ textAlign: c.numeric ? 'right' : 'left', padding: '6px 4px', borderBottom: '1px solid #faf5ff', color: '#1f2937', fontVariantNumeric: c.numeric ? 'tabular-nums' : undefined }}>
                    {row[c.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function DailyBars({ days }) {
  const max = Math.max(1, ...days.map((d) => d.searches));
  if (days.length === 0) return null;
  return (
    <div style={card}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '1.05rem', color: '#4c1d95' }}>Búsquedas por día</h3>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', height: '140px' }}>
        {days.map((d) => (
          <div key={d.day} title={`${d.day}: ${d.searches} búsquedas, ${d.whatsapp} WhatsApp, ${d.store} tienda`}
               style={{ flex: 1, minWidth: '4px', height: `${Math.max(2, (d.searches / max) * 100)}%`, backgroundColor: '#c084fc', borderRadius: '4px 4px 0 0' }} />
        ))}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#6b7280', marginTop: '6px' }}>
        <span>{days[0].day}</span><span>{days[days.length - 1].day}</span>
      </div>
    </div>
  );
}

export default function StatsPage() {
  const [key, setKey] = useState(readStoredKey);
  const [draftKey, setDraftKey] = useState('');
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    if (!key) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/stats?days=${days}`, { headers: { 'X-Stats-Key': key } });
      if (res.status === 401) {
        setError('Clave incorrecta.');
        setKey('');
        try { sessionStorage.removeItem(KEY_STORAGE); } catch { /* ignore */ }
        return;
      }
      if (!res.ok) throw new Error();
      setData(await res.json());
    } catch {
      setError('No se pudieron cargar las estadísticas. Si el servidor estaba dormido, probá de nuevo en unos segundos.');
    } finally {
      setLoading(false);
    }
  }, [key, days]);

  useEffect(() => { load(); }, [load]);

  const submitKey = (e) => {
    e.preventDefault();
    const k = draftKey.trim();
    if (!k) return;
    try { sessionStorage.setItem(KEY_STORAGE, k); } catch { /* ignore */ }
    setKey(k);
    setDraftKey('');
  };

  const page = { minHeight: '100vh', backgroundColor: '#f9fafb', fontFamily: 'system-ui, -apple-system, sans-serif', padding: '24px 16px 48px' };

  if (!key) {
    return (
      <div style={page}>
        <form onSubmit={submitKey} style={{ ...card, maxWidth: '380px', margin: '10vh auto 0', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#4c1d95', fontWeight: 800, fontSize: '1.2rem' }}>
            <Lock size={20} /> Estadísticas de LibrosUy
          </div>
          <label htmlFor="stats-key" style={{ fontSize: '0.88rem', color: '#6b7280' }}>Clave de estadísticas</label>
          <input id="stats-key" type="password" value={draftKey} onChange={(e) => setDraftKey(e.target.value)} autoComplete="off"
                 style={{ fontSize: '16px', padding: '10px 12px', border: '1px solid #e9d5ff', borderRadius: '10px' }} />
          {error && <p style={{ margin: 0, color: '#b91c1c', fontSize: '0.85rem' }}>{error}</p>}
          <button type="submit" style={{ minHeight: '44px', backgroundColor: '#7e22ce', color: '#ffffff', border: 'none', borderRadius: '10px', fontWeight: 700, fontSize: '1rem', cursor: 'pointer' }}>
            Ver estadísticas
          </button>
          <a href="/" style={{ color: '#7e22ce', fontSize: '0.85rem', textAlign: 'center' }}>Volver a LibrosUy</a>
        </form>
      </div>
    );
  }

  const t = data?.totals;
  return (
    <div style={page}>
      <div style={{ maxWidth: '1100px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.6rem', color: '#4c1d95' }}>
            <BarChart3 size={26} /> Estadísticas de LibrosUy
          </h1>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            {PERIODS.map((p) => (
              <button key={p} onClick={() => setDays(p)}
                      style={{ padding: '7px 12px', borderRadius: '9999px', border: '1px solid #e9d5ff', cursor: 'pointer', fontWeight: 700, fontSize: '0.85rem',
                               backgroundColor: days === p ? '#7e22ce' : '#ffffff', color: days === p ? '#ffffff' : '#6b21a8' }}>
                {p} días
              </button>
            ))}
            <a href="/" style={{ marginLeft: '8px', color: '#7e22ce', fontSize: '0.85rem' }}>Volver</a>
          </div>
        </div>

        <p style={{ margin: 0, color: '#6b7280', fontSize: '0.88rem' }}>
          Datos anónimos: solo qué se busca y qué librerías se contactan, sin datos personales.
          Las visitas al sitio están en Vercel → Analytics.
        </p>

        {error && <p style={{ margin: 0, color: '#b91c1c' }}>{error}</p>}
        {loading && !data && <p style={{ margin: 0, color: '#6b7280' }}>Cargando…</p>}

        {t && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(220px, 100%), 1fr))', gap: '12px' }}>
              <Kpi Icon={Search} label="Búsquedas" value={t.searches} />
              <Kpi Icon={SearchX} label="Búsquedas sin stock" value={t.searches_without_stock}
                   hint={t.searches ? `${Math.round((t.searches_without_stock / t.searches) * 100)}% del total` : null} />
              <Kpi Icon={MessageCircle} label="Consultas por WhatsApp" value={t.whatsapp_clicks} hint="Contactos enviados a librerías" />
              <Kpi Icon={ExternalLink} label="Visitas a tiendas" value={t.store_clicks} hint='Clics en "Ver en tienda"' />
            </div>

            <DailyBars days={data.per_day} />

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(340px, 100%), 1fr))', gap: '12px' }}>
              <RankTable title="Contactos por librería" rows={data.per_store} empty="Todavía no hay clics."
                         columns={[{ key: 'store', label: 'Librería' }, { key: 'whatsapp', label: 'WhatsApp', numeric: true }, { key: 'store_clicks', label: 'Tienda', numeric: true }]} />
              <RankTable title="Lo más buscado" rows={data.top_searches} empty="Todavía no hay búsquedas."
                         columns={[{ key: 'query', label: 'Búsqueda' }, { key: 'count', label: 'Veces', numeric: true }]} />
              <RankTable title="Buscado y sin stock" rows={data.top_not_found} empty="Todavía no hay búsquedas sin stock."
                         columns={[{ key: 'query', label: 'Búsqueda' }, { key: 'count', label: 'Veces', numeric: true }]} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
