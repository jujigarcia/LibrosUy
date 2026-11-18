import React, { useState, useEffect } from 'react';
import { Search, MapPin, Globe, BookOpen, Bookmark, Trash2, RefreshCw, Clock, Instagram, Info, Home, ExternalLink } from 'lucide-react';
import StoreMap from './StoreMap';
import { trackClick } from './analytics';

// Fallback list of all 29 bookstores so the UI works even before the backend is started
const FALLBACK_STORES = [
  { id: 1, name: "Librería Puro Verso", website: "puroverso.uy", specialty: "Ficción, No Ficción, Poesía, Juvenil", tags: ["Ficción", "No Ficción", "Poesía", "Juvenil"], address: "Av. 18 de Julio / Sarandí 675", department: "Montevideo", latitude: -34.9065, longitude: -56.2023, ingestion_method: "web_scraper", featured: true },
  { id: 2, name: "Escaramuza", website: "escaramuza.com.uy", specialty: "Catálogo General, Infantil, Café", tags: ["Catálogo General", "Infantil", "Café"], address: "Dr. Pablo de María 1185", department: "Montevideo", latitude: -34.9080, longitude: -56.1712, ingestion_method: "web_scraper", featured: true },
  { id: 3, name: "Isadora Libros", website: "isadoralibros.com.uy", specialty: "Cómics, Medicina, Ficción", tags: ["Cómics", "Medicina", "Ficción"], address: "José Ellauri 661", department: "Montevideo", latitude: -34.9165, longitude: -56.1568, ingestion_method: "web_scraper", featured: false },
  { id: 4, name: "Babilonia Libros", website: "babilonia.uy", specialty: "Usados, Raros, Agotados", tags: ["Usados", "Raros", "Agotados"], address: "Dr. Tristán Narvaja 1591", department: "Montevideo", latitude: -34.9015, longitude: -56.1764, ingestion_method: "web_scraper", featured: true },
  { id: 5, name: "El Virrey", website: "www.libreriaelvirrey.com.uy", specialty: "Bestsellers, Novedades", tags: ["Bestsellers", "Novedades"], address: "21 de Setiembre", department: "Montevideo", latitude: -34.9142, longitude: -56.1589, ingestion_method: "web_scraper", featured: false },
  { id: 6, name: "Bookshop", website: "bookshop.com.uy", specialty: "Inglés, Catálogo General, Juvenil", tags: ["Inglés", "Catálogo General", "Juvenil"], address: "José Enrique Rodó", department: "Montevideo", latitude: -34.9048, longitude: -56.1742, ingestion_method: "web_scraper", featured: true },
  { id: 7, name: "Mosca", website: "mosca.com.uy", specialty: "Literatura, Educativos, Escolares", tags: ["Literatura", "Educativos", "Escolares"], address: "Av. 18 de Julio", department: "Montevideo", latitude: -34.9058, longitude: -56.1852, ingestion_method: "web_scraper", featured: true },
  { id: 8, name: "Grupo Libros", website: "grupolibros.com.uy", specialty: "Catálogo General", tags: ["Catálogo General"], address: "Tienda Online", department: "Online", latitude: null, longitude: null, ingestion_method: "web_scraper", featured: false },
  { id: 9, name: "Diomedes", website: "librosleidos.com.uy", specialty: "Usados, Raros", tags: ["Usados", "Raros"], address: "Tienda Online", department: "Online", latitude: null, longitude: null, ingestion_method: "web_scraper", featured: false },
  { id: 10, name: "Entrelibros", website: null, instagram: "entre_libros_sanjose", specialty: "Catálogo General", tags: ["Catálogo General"], address: "San José de Mayo", department: "San José", latitude: -34.3375, longitude: -56.7136, ingestion_method: "google_sheets", featured: false },
  { id: 11, name: "Planetadelibros Uruguay", website: "planetadelibros.com.uy", specialty: "Editorial, Ficción, Juvenil", tags: ["Editorial", "Ficción", "Juvenil"], address: "Tienda Online", department: "Online", latitude: null, longitude: null, ingestion_method: "web_scraper", featured: false },
  { id: 12, name: "Librería El Altillo", website: null, specialty: "Catálogo General, Local", tags: ["Catálogo General", "Local"], address: "Ciudad de la Costa", department: "Canelones", latitude: -34.8222, longitude: -55.9547, ingestion_method: "google_sheets", featured: false },
  { id: 13, name: "Librería Ofipando", website: null, specialty: "Catálogo General, Local, Escolares", tags: ["Catálogo General", "Local", "Escolares"], address: "Pando", department: "Canelones", latitude: -34.7167, longitude: -55.9583, ingestion_method: "google_sheets", featured: true },
  { id: 14, name: "La Madriguera Libros", website: null, specialty: "Catálogo General, Local", tags: ["Catálogo General", "Local"], address: "Canelones", department: "Canelones", latitude: -34.5228, longitude: -56.2778, ingestion_method: "google_sheets", featured: false },
  { id: 15, name: "Espacio Chamangá", website: null, specialty: "Independiente, Literatura", tags: ["Independiente", "Literatura"], address: "Maldonado", department: "Maldonado", latitude: -34.9000, longitude: -54.9500, ingestion_method: "google_sheets", featured: false },
  { id: 16, name: "Bookshop (Salto)", website: "bookshop.com.uy", specialty: "Catálogo General", tags: ["Catálogo General"], address: "Salto", department: "Salto", latitude: -31.3833, longitude: -57.9667, ingestion_method: "web_scraper", featured: false },
  { id: 17, name: "Bookshop (Rivera)", website: "bookshop.com.uy", specialty: "Catálogo General", tags: ["Catálogo General"], address: "Rivera", department: "Rivera", latitude: -30.9053, longitude: -55.5508, ingestion_method: "web_scraper", featured: false },
  { id: 18, name: "Librería Entre Libros", website: null, specialty: "Catálogo General", tags: ["Catálogo General"], address: "Paysandú", department: "Paysandú", latitude: -32.3214, longitude: -58.0756, ingestion_method: "google_sheets", featured: false },
  { id: 19, name: "Origami Libros", website: null, specialty: "Catálogo General", tags: ["Catálogo General"], address: "Colonia del Sacramento", department: "Colonia", latitude: -34.4626, longitude: -57.8398, ingestion_method: "google_sheets", featured: false },
  { id: 20, name: "Noctiluca", website: null, specialty: "Librería Itinerante", tags: ["Librería Itinerante", "Independiente"], address: "Móvil (VW Kombi - 19 departamentos)", department: "Móvil", latitude: -34.6000, longitude: -56.0000, ingestion_method: "google_sheets", featured: true },
  { id: 21, name: "Lecturas Cómics", website: "lecturascomics.com.uy", specialty: "Cómics, Manga", tags: ["Cómics", "Manga"], address: "Colonia 892", department: "Montevideo", latitude: -34.9042, longitude: -56.1965, ingestion_method: "web_scraper", featured: true },
  { id: 22, name: "Librería Pocho", website: "libreriapocho.com.uy", specialty: "Manga, Educativos, General", tags: ["Manga", "Educativos", "General"], address: "Av. 18 de Julio 2198", department: "Montevideo", latitude: -34.9012, longitude: -56.1668, ingestion_method: "web_scraper", featured: false },
  { id: 23, name: "Franca Comics", website: "francacomics.uy", specialty: "Cómics, Manga", tags: ["Cómics", "Manga"], address: "Rafael Pérez del Puerto 736", department: "Maldonado", latitude: -34.9088, longitude: -54.9581, ingestion_method: "web_scraper", featured: false },
  { id: 24, name: "Librería Lannister", website: "librerialannister.com", specialty: "Manga, Cómics, Fantasía", tags: ["Manga", "Cómics", "Fantasía"], address: "Tienda Online", department: "Online", latitude: null, longitude: null, ingestion_method: "web_scraper", featured: false },
  { id: 25, name: "Librería Vila", website: "libreriavila.com.uy", specialty: "Manga, Cómics, Textos Estudio", tags: ["Manga", "Cómics", "Textos Estudio"], address: "Tristán Narvaja 1642", department: "Montevideo", latitude: -34.9008, longitude: -56.1762, ingestion_method: "web_scraper", featured: false },
  { id: 26, name: "Librería Vanir", website: "vanir.com.uy", specialty: "Juvenil, Fantasía, Tarot", tags: ["Juvenil", "Fantasía", "Tarot"], address: "Belgrano 2934 BIS", department: "Montevideo", latitude: -34.8875, longitude: -56.1552, ingestion_method: "web_scraper", featured: true },
  { id: 27, name: "Las Karamazov", website: "laskaramazov.com.uy", specialty: "Literatura Independiente, Ficción", tags: ["Literatura Independiente", "Ficción"], address: "Av. Rivera 2670", department: "Montevideo", latitude: -34.9035, longitude: -56.1538, ingestion_method: "web_scraper", featured: true },
  { id: 28, name: "Rizoma", website: "rizomalajuanita.com", specialty: "Catálogo Curado, Café, Libros", tags: ["Catálogo Curado", "Café", "Arte"], address: "La Juanita, José Ignacio", department: "Maldonado", latitude: -34.8415, longitude: -54.6522, ingestion_method: "web_scraper", featured: false },
  { id: 29, name: "Librería Montevideo", website: "libreriamontevideo.com", specialty: "Catálogo General, Historia", tags: ["Catálogo General", "Historia"], address: "Montevideo", department: "Montevideo", latitude: -34.9055, longitude: -56.1915, ingestion_method: "web_scraper", featured: false }
];

// Backend base URL: set REACT_APP_API_URL in Vercel (e.g. https://librosuy.onrender.com);
// defaults to the local FastAPI server for development.
const API_URL = (process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');

const QUICK_GENRES = ["Ficción", "Fantasía", "Manga", "Cómics", "Juvenil", "Historia", "Académicos", "Usados", "Poesía"];

// Umbrella genres with no store tag of their own (mirrors GENRE_GROUPS in backend/main.py)
const GENRE_GROUPS = {
  'Académicos': ['Educativos', 'Textos Estudio', 'Medicina']
};

const normalizeText = (text) => (text || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

// Same rule as the backend: the store's specialty contains the genre (or one of its group's tags)
const storeMatchesGenre = (store, genre) => {
  const specialty = normalizeText(store.specialty || (store.tags || []).join(', '));
  return (GENRE_GROUPS[genre] || [genre]).some((tag) => specialty.includes(normalizeText(tag)));
};

// Normalizes a Uruguayan phone number to the international format wa.me expects (e.g. 59899123456)
const toWhatsAppNumber = (raw) => {
  if (!raw) return null;
  let digits = String(raw).replace(/\D/g, '');
  if (digits.startsWith('00')) digits = digits.slice(2);
  if (!digits.startsWith('598')) {
    if (digits.startsWith('0')) digits = digits.slice(1);
    if (digits.length === 8) digits = `598${digits}`;
  }
  return digits.length >= 10 ? digits : null;
};

const buildWhatsAppLink = (raw, message) => {
  const number = toWhatsAppNumber(raw);
  return number ? `https://wa.me/${number}?text=${encodeURIComponent(message)}` : null;
};

// How much we can trust a store's stock on LibrosUy (stock_source from the API).
// Neutral wording: missing stock is on LibrosUy's side, not the bookstore's.
const NO_STOCK_YET = {
  Icon: Clock,
  label: 'Aún no tenemos su stock',
  color: '#475569',
  background: '#f1f5f9'
};
const STOCK_NOTICES = {
  verified: {
    Icon: RefreshCw,
    label: 'Stock en línea',
    color: '#166534',
    background: '#dcfce7'
  },
  unverified: NO_STOCK_YET,
  pending_sheet: NO_STOCK_YET
};

// Official WhatsApp glyph (Simple Icons, CC0)
function WhatsAppIcon({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" style={{ display: 'block', flexShrink: 0 }}>
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
    </svg>
  );
}

// Compact pill: just the phrase, no explanation
function StockNotice({ source }) {
  const notice = STOCK_NOTICES[source];
  if (!notice) return null;
  const { Icon } = notice;
  return (
    <span title={notice.label} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', minWidth: 0, backgroundColor: notice.background, color: notice.color, borderRadius: '9999px', padding: '4px 8px', fontSize: '0.72rem', fontWeight: 700, whiteSpace: 'nowrap' }}>
      <Icon size={12} style={{ flexShrink: 0 }} />
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{notice.label}</span>
    </span>
  );
}

// Prices: Uruguayan pesos as "$ 1.250" (decimals only when there are cents, "$ 552,50");
// dollars as "U$D 25". Stored prices are pesos unless the API says otherwise.
const formatPrice = (value, currency = 'UYU') => {
  const amount = Number(value);
  const cents = !Number.isInteger(amount);
  const number = amount.toLocaleString('es-UY', { minimumFractionDigits: cents ? 2 : 0, maximumFractionDigits: 2 });
  return `${currency === 'USD' ? 'U$D' : '$'} ${number}`;
};

// "RAYUELA EDICIÓN CONMEMORATIVA" -> true; "Rayuela" -> false
const isAllCaps = (text) => /\p{L}/u.test(text || '') && text === text.toUpperCase();

// Book cover with a fixed 2:3 box (so cards line up) and a neutral placeholder when there's
// no image or it fails to load
function BookCover({ src, title, width = 64 }) {
  const [failed, setFailed] = useState(false);
  const box = { width: `${width}px`, height: `${Math.round(width * 1.5)}px`, flexShrink: 0, borderRadius: '6px', overflow: 'hidden', backgroundColor: '#f3e8ff', border: '1px solid #e9d5ff' };
  if (!src || failed) {
    return (
      <div style={{ ...box, display: 'flex', alignItems: 'center', justifyContent: 'center' }} aria-hidden="true">
        <BookOpen size={Math.round(width / 2.6)} color="#c084fc" strokeWidth={1.5} />
      </div>
    );
  }
  return (
    <div style={box}>
      <img src={src} alt={`Portada de ${title}`} loading="lazy" referrerPolicy="no-referrer" onError={() => setFailed(true)}
        style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
    </div>
  );
}

// Phones (portrait and small landscape): bottom tab bar, stacked layouts, bigger tap targets
const MOBILE_QUERY = '(max-width: 767px)';

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(
    () => typeof window !== 'undefined' && window.matchMedia(MOBILE_QUERY).matches
  );
  useEffect(() => {
    const media = window.matchMedia(MOBILE_QUERY);
    const onChange = () => setIsMobile(media.matches);
    onChange();
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, []);
  return isMobile;
}

// Same min/max column width everywhere; min(...) keeps a single column on narrow phones
const CARD_GRID = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(320px, 100%), 1fr))', gap: '20px' };

function WhatsAppButton({ number, message, small = false, onClick }) {
  const link = buildWhatsAppLink(number, message);
  if (!link) return null; // No number yet: show nothing rather than a disabled button

  return (
    <a
      href={link}
      target="_blank"
      rel="noreferrer"
      aria-label="Consultar por WhatsApp"
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: small ? '5px' : '7px',
        padding: small ? '6px 10px' : '8px 14px',
        minHeight: small ? '32px' : '36px',
        borderRadius: '9999px',
        backgroundColor: '#25d366',
        color: '#ffffff',
        fontSize: small ? '0.78rem' : '0.85rem',
        fontWeight: 700,
        lineHeight: 1, // tight text box: its center matches the letters, not the font's extra space
        textDecoration: 'none',
        whiteSpace: 'nowrap'
      }}
    >
      <WhatsAppIcon size={small ? 14 : 16} />
      <span style={{ display: 'block' }}>Consultar aquí</span>
    </a>
  );
}

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const isMobile = useIsMobile();

  // Lets other components (e.g. the Sugerencias form) know which tab is open
  useEffect(() => { document.body.dataset.tab = activeTab; }, [activeTab]);
  const [stores, setStores] = useState(FALLBACK_STORES);
  const [loadingStores, setLoadingStores] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Book & Genre Search state
  const [bookQuery, setBookQuery] = useState('');
  const [bookSearchLoading, setBookSearchLoading] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  // Genre chip selected in the results to narrow the recommended stores (null = all)
  const [genreFilter, setGenreFilter] = useState(null);

  // Saved Stores (Mi Lista) persisted in localStorage
  const [savedStoreIds, setSavedStoreIds] = useState(() => {
    try {
      const saved = localStorage.getItem('librosuy_saved_stores');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    fetch(`${API_URL}/api/stores`)
      .then((res) => {
        if (!res.ok) throw new Error('API offline');
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setStores(data);
        }
        setLoadingStores(false);
      })
      .catch(() => {
        // Uses the 29 fallback stores if backend isn't running yet
        setLoadingStores(false);
      });
  }, []);

  const toggleSaveStore = (storeId) => {
    setSavedStoreIds((prev) => {
      const updated = prev.includes(storeId)
        ? prev.filter((id) => id !== storeId)
        : [...prev, storeId];
      localStorage.setItem('librosuy_saved_stores', JSON.stringify(updated));
      return updated;
    });
  };

  const handleBookSearch = async (queryText) => {
    const q = (queryText ?? bookQuery).trim();
    if (!q) return;
    setBookQuery(q);
    setBookSearchLoading(true);
    setGenreFilter(null);

    try {
      const res = await fetch(`${API_URL}/api/search?title=${encodeURIComponent(q)}`);
      if (!res.ok) throw new Error('Error en servidor');
      const data = await res.json();
      setSearchResult(data);
    } catch {
      // Offline fallback: match against local 29 stores by tag/specialty,
      // or recommend general-catalog stores that can usually order any title
      const matched = stores.filter((s) =>
        storeMatchesGenre(s, q) ||
        normalizeText(s.name).includes(normalizeText(q))
      );
      const general = stores.filter((s) => (s.specialty || '').includes('Catálogo General'));
      setSearchResult({
        query: q,
        book_metadata: null,
        matched_genres: matched.length > 0 ? [q] : ['Catálogo General'],
        in_stock_offers: [],
        recommended_stores: matched.length > 0 ? matched : general
      });
    } finally {
      setBookSearchLoading(false);
    }
  };

  const filteredStores = stores.filter((store) => {
    const q = searchQuery.toLowerCase();
    return (
      store.name.toLowerCase().includes(q) ||
      store.address.toLowerCase().includes(q) ||
      (store.department && store.department.toLowerCase().includes(q)) ||
      (store.tags && store.tags.some((tag) => tag.toLowerCase().includes(q)))
    );
  });

  const savedStoresList = stores.filter((s) => savedStoreIds.includes(s.id));

  // Store card grid: tighter on phones so more stores fit on screen
  const storeGrid = isMobile ? { ...CARD_GRID, gap: '12px' } : CARD_GRID;

  // bookQuery: when the card is shown as a search recommendation, the message asks for that book
  const renderStoreCard = (store, bookQuery = null) => {
    const isSaved = savedStoreIds.includes(store.id);
    const whatsappMessage = bookQuery
      ? `¡Hola ${store.name}! Estoy buscando el libro "${bookQuery}" y los encontré en LibrosUy. ¿Lo tienen o podrían conseguirlo por encargo?`
      : `¡Hola ${store.name}! Los encontré en LibrosUy y quería hacerles una consulta.`;
    return (
      <div
        key={store.id}
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '14px',
          border: '1px solid #e9d5ff',
          padding: isMobile ? '14px' : '18px',
          boxShadow: '0 2px 6px rgba(0,0,0,0.03)',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* flex: 1 takes the spare height, so genres and footer sit at the bottom and line up
            across cards in the same grid row whatever the name/address length */}
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '6px' }}>
            <h4 style={{ margin: 0, fontSize: isMobile ? '1.02rem' : '1.1rem', fontWeight: 700, color: '#374151' }}>{store.name}</h4>
            <button
              onClick={() => toggleSaveStore(store.id)}
              title={isSaved ? "Quitar de Mi Lista" : "Guardar en Mi Lista"}
              style={{
                border: '1px solid #e9d5ff',
                backgroundColor: isSaved ? '#fef08a' : '#faf5ff',
                borderRadius: '8px',
                padding: isMobile ? '7px' : '5px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                flexShrink: 0
              }}
              aria-label={isSaved ? "Quitar de Mi Lista" : "Guardar en Mi Lista"}
            >
              <Bookmark size={isMobile ? 16 : 15} color="#6b21a8" fill={isSaved ? "#6b21a8" : "none"} />
            </button>
          </div>

          <p style={{ display: 'flex', alignItems: 'center', gap: '7px', margin: '3px 0', fontSize: '0.84rem', color: '#6b7280' }}>
            <MapPin size={14} color="#c084fc" style={{ flexShrink: 0 }} /> {store.address} ({store.department})
          </p>

          {store.website ? (
            <p style={{ display: 'flex', alignItems: 'center', gap: '7px', margin: '3px 0', fontSize: '0.84rem' }}>
              <Globe size={14} color="#c084fc" style={{ flexShrink: 0 }} />
              <a href={`https://${store.website}`} target="_blank" rel="noreferrer" style={{ color: '#7e22ce', textDecoration: 'none', fontWeight: 600 }}>
                {store.website}
              </a>
            </p>
          ) : null}

          {store.instagram && (
            <p style={{ display: 'flex', alignItems: 'center', gap: '7px', margin: '3px 0', fontSize: '0.84rem' }}>
              <Instagram size={14} color="#c084fc" style={{ flexShrink: 0 }} />
              <a href={`https://www.instagram.com/${store.instagram}/`} target="_blank" rel="noreferrer" style={{ color: '#7e22ce', textDecoration: 'none', fontWeight: 600 }}>
                @{store.instagram}
              </a>
            </p>
          )}
        </div>

        {/* Genres as plain text (not pill-shaped, so they don't look clickable), always one
            line tall: long lists are cut with "…" and shown in full on hover */}
        {(store.tags || []).length > 0 && (
          <p
            title={store.tags.join(' · ')}
            style={{ margin: '10px 0 0 0', fontSize: '0.78rem', color: '#6b7280', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
          >
            {store.tags.join(' · ')}
          </p>
        )}

        {/* Footer: stock pill and WhatsApp always on one line (never wraps, so every card
            keeps the same footer height; on very narrow cards the pill text gets "…").
            minHeight = button height, so cards with and without WhatsApp align */}
        {(STOCK_NOTICES[store.stock_source] || store.whatsapp) && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '6px', marginTop: '10px', minHeight: '32px' }}>
            <StockNotice source={store.stock_source} />
            {store.whatsapp && (
              <span style={{ marginLeft: 'auto', flexShrink: 0 }}>
                <WhatsAppButton number={store.whatsapp} message={whatsappMessage} small onClick={() => trackClick('whatsapp_click', store.id, bookQuery)} />
              </span>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="screen-min-height" style={{
      fontFamily: 'system-ui, -apple-system, sans-serif',
      position: 'relative',
      // Column layout: the footer (Privacidad) sits at the bottom edge even when the content is short
      display: 'flex',
      flexDirection: 'column',
      background: activeTab === 'home'
        ? 'radial-gradient(circle at 30% 50%, #fdf4ff 0%, #fbcfe8 35%, #e9d5ff 70%, #ecfccb 100%)'
        : '#f9fafb'
    }}>

      {/* Top Navigation Bar */}
      <header style={{
        backgroundColor: activeTab === 'home' ? 'transparent' : '#ffffff',
        borderBottom: activeTab === 'home' ? 'none' : '1px solid #e9d5ff',
        position: activeTab === 'home' ? 'absolute' : 'sticky',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        padding: isMobile ? 'calc(14px + env(safe-area-inset-top)) 16px 14px' : '30px 4%'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div
            onClick={() => setActiveTab('home')}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
          >
            <BookOpen style={{ color: '#374151' }} size={isMobile ? 24 : 28} strokeWidth={1} />
            <span style={{ fontSize: isMobile ? '1.2rem' : '1.4rem', fontWeight: 800, color: '#374151' }}>LibrosUy</span>
          </div>

          {/* Desktop: top navigation. Phones use the bottom tab bar below */}
          {!isMobile && (
          <nav style={{ display: 'flex', gap: '32px' }}>
            <button
              onClick={() => setActiveTab('explore')}
              style={{
                border: 'none',
                backgroundColor: 'transparent',
                color: activeTab === 'explore' ? '#7e22ce' : '#374151',
                fontWeight: 800,
                fontSize: '1rem',
                cursor: 'pointer',
                padding: 0
              }}
            >
              Explorar Librerías
            </button>
            <button
              onClick={() => setActiveTab('genres')}
              style={{
                border: 'none',
                backgroundColor: 'transparent',
                color: activeTab === 'genres' ? '#7e22ce' : '#374151',
                fontWeight: 800,
                fontSize: '1rem',
                cursor: 'pointer',
                padding: 0
              }}
            >
              Buscar por Libro
            </button>
            <button
              onClick={() => setActiveTab('saved')}
              style={{
                border: 'none',
                backgroundColor: 'transparent',
                color: activeTab === 'saved' ? '#7e22ce' : '#374151',
                fontWeight: 800,
                fontSize: '1rem',
                cursor: 'pointer',
                padding: 0
              }}
            >
              Mi Lista
            </button>
          </nav>
          )}
        </div>
      </header>

      {/* TAB 0: HOME (Minimalist Landing Page) */}
      {activeTab === 'home' && (
        <main className="screen-min-height" style={{
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          alignItems: 'center',
          justifyContent: isMobile ? 'center' : 'space-between',
          padding: isMobile ? '88px 20px calc(110px + env(safe-area-inset-bottom))' : '0 8%',
          position: 'relative',
          overflow: 'hidden'
        }}>
          {/* Left Column: Stylized Logo & Hook */}
          <div style={{ flex: isMobile ? '0 0 auto' : '1 1 50%', display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: isMobile ? 0 : '40px', position: 'relative', zIndex: 2 }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: isMobile ? '24px' : '40px', color: '#374151' }}>
              <span style={{ fontSize: isMobile ? '3.4rem' : '5.5rem', fontWeight: 800, transform: 'rotate(-8deg)', letterSpacing: '-0.03em' }}>
                Libros
              </span>
              <span style={{ fontSize: isMobile ? '3.4rem' : '5.5rem', fontWeight: 800, display: 'flex', alignItems: 'center', marginTop: isMobile ? '-16px' : '-30px', marginLeft: isMobile ? '36px' : '60px', letterSpacing: '-0.03em' }}>
                {/* Drawn as SVG: the ✳ character renders as a green emoji on iOS */}
                <svg
                  aria-hidden="true"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.6"
                  strokeLinecap="round"
                  style={{ width: isMobile ? '2.2rem' : '3.6rem', height: isMobile ? '2.2rem' : '3.6rem', marginRight: isMobile ? '10px' : '14px', transform: 'translateY(5px)', flexShrink: 0 }}
                >
                  <path d="M12 3v18M3 12h18M5.6 5.6l12.8 12.8M18.4 5.6L5.6 18.4" />
                </svg>Uy
              </span>
            </div>

            <h1 style={{
              fontSize: isMobile ? '2.1rem' : '4.2rem',
              fontWeight: 300,
              color: '#374151',
              lineHeight: '1.05',
              margin: 0,
              letterSpacing: '-0.03em',
              textAlign: 'center',
              textWrap: 'balance'
            }}>
              {isMobile ? 'La mejor forma de encontrar tu libro' : <>La mejor forma de encontrar<br />tu libro</>}
            </h1>

            {/* Phones: direct entry points (desktop uses the top navigation) */}
            {isMobile && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%', maxWidth: '320px', marginTop: '28px' }}>
                <button
                  onClick={() => setActiveTab('genres')}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', minHeight: '50px', backgroundColor: '#7e22ce', color: '#ffffff', border: 'none', borderRadius: '14px', fontSize: '1rem', fontWeight: 700 }}
                >
                  <Search size={18} /> Buscar un libro
                </button>
                <button
                  onClick={() => setActiveTab('explore')}
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', minHeight: '50px', backgroundColor: 'rgba(255,255,255,0.75)', color: '#4c1d95', border: '1px solid #e9d5ff', borderRadius: '14px', fontSize: '1rem', fontWeight: 700 }}
                >
                  <MapPin size={18} /> Ver librerías en el mapa
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Abstract Line Art + Open Book */}
          <div style={isMobile
            ? { position: 'absolute', right: '-70px', bottom: '70px', opacity: 0.18, pointerEvents: 'none', zIndex: 0 }
            : { flex: '1 1 50%', display: 'flex', justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
            <svg viewBox="0 0 200 200" style={{ position: 'absolute', width: isMobile ? '320px' : '650px', height: isMobile ? '320px' : '650px', zIndex: 0, opacity: 0.7 }}>
              <path d="M 0 80 Q 50 20 100 80 T 200 80" stroke="#ffffff" strokeWidth="1.5" fill="none" />
              <path d="M 0 100 Q 50 40 100 100 T 200 100" stroke="#ffffff" strokeWidth="1.5" fill="none" />
              <path d="M 0 120 Q 50 60 100 120 T 200 120" stroke="#ffffff" strokeWidth="1.5" fill="none" />
              <path d="M 0 140 Q 50 80 100 140 T 200 140" stroke="#ffffff" strokeWidth="1.5" fill="none" />
              <path d="M 0 160 Q 50 100 100 160 T 200 160" stroke="#ffffff" strokeWidth="1.5" fill="none" />
              <path d="M 80 0 Q 20 50 80 100 T 80 200" stroke="#ffffff" strokeWidth="1.5" fill="none" />
              <path d="M 100 0 Q 40 50 100 100 T 100 200" stroke="#ffffff" strokeWidth="1.5" fill="none" />
              <path d="M 120 0 Q 60 50 120 100 T 120 200" stroke="#ffffff" strokeWidth="1.5" fill="none" />
              <path d="M 140 0 Q 80 50 140 100 T 140 200" stroke="#ffffff" strokeWidth="1.5" fill="none" />
            </svg>
            <BookOpen size={isMobile ? 260 : 500} strokeWidth={1} color="#1f2937" style={{ zIndex: 1, position: 'relative', transform: 'rotate(8deg)' }} />
          </div>

          {/* Bottom-left Disclaimer */}
          <p style={{
            position: 'absolute',
            bottom: isMobile ? 'calc(84px + env(safe-area-inset-bottom))' : '40px',
            left: isMobile ? '16px' : '4%',
            right: isMobile ? '16px' : undefined,
            textAlign: isMobile ? 'center' : undefined,
            fontSize: isMobile ? '0.65rem' : '0.75rem',
            fontWeight: 800,
            color: '#374151',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            margin: 0
          }}>
            STOCK ACTUALIZADO DEPENDIENDO DE LAS LIBRERIAS
            {' · '}
            <a href="#privacidad" style={{ color: 'inherit' }}>Privacidad</a>
          </p>
        </main>
      )}

      {/* INNER TABS */}
      {activeTab !== 'home' && (
        <main style={{ flex: '1 0 auto', width: '100%', maxWidth: '1200px', margin: '0 auto', padding: isMobile ? '20px 16px 8px' : '32px 20px 8px' }}>

          {/* TAB 1: EXPLORAR LIBRERÍAS (Map + Store Directory) */}
          {activeTab === 'explore' && (
            <div>
              <h2 style={{ fontSize: isMobile ? '1.5rem' : '2rem', fontWeight: 800, color: '#4c1d95', margin: '0 0 16px 0' }}>
                Explorar Librerías en Uruguay
              </h2>

              <div style={{ maxWidth: '640px', marginBottom: '24px', display: 'flex', gap: '8px', backgroundColor: '#ffffff', padding: '6px', borderRadius: '12px', border: '1px solid #e9d5ff' }}>
                <div style={{ display: 'flex', alignItems: 'center', paddingLeft: '12px', color: '#9ca3af' }}>
                  <Search size={20} />
                </div>
                <input
                  type="text"
                  placeholder={isMobile ? 'Nombre, departamento o especialidad' : 'Filtrar por nombre, departamento (ej. Canelones, Maldonado) o especialidad...'}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ flex: 1, minWidth: 0, border: 'none', outline: 'none', padding: '10px 8px', fontSize: '16px' }}
                />
              </div>

              <StoreMap stores={filteredStores} loading={loadingStores} compact={isMobile} />

              <h3 style={{ fontSize: '1.3rem', fontWeight: 700, color: '#6b21a8', marginBottom: '16px', marginTop: '36px' }}>
                Directorio de Librerías ({filteredStores.length})
              </h3>

              <div style={storeGrid}>
                {filteredStores.map((store) => renderStoreCard(store))}
              </div>
            </div>
          )}

          {/* TAB 2: BUSCAR POR GÉNERO / LIBRO (Local Stock + Google Books API) */}
          {activeTab === 'genres' && (
            <div>
              <div style={{ backgroundColor: '#ffffff', borderRadius: '20px', border: '1px solid #e9d5ff', padding: isMobile ? '22px 16px' : '36px 28px', marginBottom: '28px' }}>
                <h2 style={{ fontSize: isMobile ? '1.5rem' : '1.9rem', fontWeight: 800, color: '#4c1d95', margin: '0 0 8px 0' }}>
                  Búsqueda por Libro
                </h2>
                <p style={{ color: '#6b7280', margin: '0 0 20px 0', fontSize: '0.98rem' }}>
                  Buscá por título, autor, ISBN o género. Consultamos el stock indexado de las librerías y clasificamos el libro con Google Books API.
                </p>

                <form
                  onSubmit={(e) => { e.preventDefault(); handleBookSearch(); }}
                  style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '18px' }}
                >
                  <div style={{ flex: '1 1 260px', minWidth: 0, display: 'flex', alignItems: 'center', backgroundColor: '#f9fafb', border: '2px solid #c084fc', borderRadius: '12px', padding: '4px 14px' }}>
                    <Search size={18} color="#7e22ce" />
                    <input
                      type="text"
                      value={bookQuery}
                      onChange={(e) => setBookQuery(e.target.value)}
                      placeholder={isMobile ? 'Título, autor o ISBN' : 'Ej: La tregua, Alas de sangre, Chainsaw Man, Galeano...'}
                      enterKeyHint="search"
                      style={{ flex: 1, minWidth: 0, border: 'none', outline: 'none', backgroundColor: 'transparent', padding: '10px', fontSize: '16px' }}
                    />
                  </div>
                  <button
                    type="submit"
                    style={{
                      backgroundColor: '#7e22ce',
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '12px',
                      padding: '0 26px',
                      minHeight: '48px',
                      flex: isMobile ? '1 1 100%' : '0 0 auto',
                      fontWeight: 700,
                      fontSize: '1rem',
                      cursor: 'pointer'
                    }}
                  >
                    {bookSearchLoading ? 'Buscando...' : 'Buscar Libro'}
                  </button>
                </form>

                {/* Quick Genre Filter Pills */}
                <div className={isMobile ? 'scroll-row' : undefined} style={{ display: 'flex', alignItems: 'center', flexWrap: isMobile ? 'nowrap' : 'wrap', gap: '8px', margin: isMobile ? '0 -16px' : 0, padding: isMobile ? '2px 16px' : 0 }}>
                  <span style={{ fontSize: '0.82rem', color: '#6b7280', fontWeight: 600, marginRight: '4px', whiteSpace: 'nowrap', flexShrink: 0 }}>
                    Explorar género rápido:
                  </span>
                  {QUICK_GENRES.map((genre) => (
                    <button
                      key={genre}
                      onClick={() => handleBookSearch(genre)}
                      style={{
                        backgroundColor: '#f3e8ff',
                        color: '#6b21a8',
                        border: '1px solid #e9d5ff',
                        borderRadius: '9999px',
                        padding: isMobile ? '9px 16px' : '5px 14px',
                        whiteSpace: 'nowrap',
                        flexShrink: 0,
                        fontSize: isMobile ? '0.88rem' : '0.8rem',
                        fontWeight: 700,
                        cursor: 'pointer'
                      }}
                    >
                      {genre}
                    </button>
                  ))}
                </div>
              </div>

              {/* Search Results */}
              {searchResult && (
                <div>
                  {/* 0a. Several books identified (e.g. searching an author): swipeable row; tap one to search it */}
                  {(searchResult.book_candidates || []).length > 1 && (
                    <div style={{ backgroundColor: '#ffffff', border: '1px solid #e9d5ff', borderRadius: '16px', padding: isMobile ? '14px 0' : '16px 0', marginBottom: '28px' }}>
                      <div style={{ padding: isMobile ? '0 14px' : '0 18px', display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '0.72rem', color: '#7e22ce', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Libros identificados ({searchResult.book_candidates.length})
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>Tocá uno para buscarlo en las librerías</span>
                      </div>
                      <div className="scroll-row" style={{ display: 'flex', gap: '12px', padding: isMobile ? '12px 14px 2px' : '12px 18px 2px' }}>
                        {searchResult.book_candidates.map((book, i) => (
                          <button
                            key={`${book.title}-${i}`}
                            onClick={() => handleBookSearch(book.title)}
                            title={`Buscar "${book.title}"`}
                            style={{ flex: '0 0 auto', width: isMobile ? '112px' : '128px', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '6px', padding: 0, border: 'none', background: 'transparent', cursor: 'pointer', textAlign: 'left' }}
                          >
                            <BookCover src={book.thumbnail} title={book.title} width={isMobile ? 72 : 80} />
                            <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1f2937', lineHeight: 1.25, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                              {book.title}
                            </span>
                            <span style={{ fontSize: '0.74rem', color: '#6b7280', lineHeight: 1.2, display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                              {[book.authors, (book.published_date || '').slice(0, 4)].filter(Boolean).join(' · ')}
                            </span>
                          </button>
                        ))}
                      </div>
                      <p style={{ margin: '8px 0 0 0', padding: isMobile ? '0 14px' : '0 18px', fontSize: '0.75rem', color: '#9ca3af' }}>
                        Datos de Google Books. Cada librería puede tener otra edición: fijate en la portada de cada ejemplar.
                      </p>
                    </div>
                  )}

                  {/* 0b. A single book identified by Google Books: cover, author, publisher and year */}
                  {searchResult.book_metadata && (searchResult.book_candidates || []).length <= 1 && (
                    <div style={{ display: 'flex', gap: isMobile ? '14px' : '18px', alignItems: 'flex-start', backgroundColor: '#ffffff', border: '1px solid #e9d5ff', borderRadius: '16px', padding: isMobile ? '14px' : '18px', marginBottom: '28px' }}>
                      <BookCover src={searchResult.book_metadata.thumbnail} title={searchResult.book_metadata.title} width={isMobile ? 72 : 88} />
                      <div style={{ minWidth: 0 }}>
                        <span style={{ fontSize: '0.72rem', color: '#7e22ce', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                          Libro identificado
                        </span>
                        <h3 style={{ margin: '4px 0 2px 0', fontSize: isMobile ? '1.1rem' : '1.3rem', fontWeight: 800, color: '#1f2937' }}>
                          {searchResult.book_metadata.title}
                        </h3>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: '#4b5563' }}>{searchResult.book_metadata.authors}</p>
                        <p style={{ margin: '6px 0 0 0', fontSize: '0.8rem', color: '#6b7280' }}>
                          {[searchResult.book_metadata.publisher, (searchResult.book_metadata.published_date || '').slice(0, 4), searchResult.book_metadata.isbn && `ISBN ${searchResult.book_metadata.isbn}`].filter(Boolean).join(' · ')}
                        </p>
                        <p style={{ margin: '6px 0 0 0', fontSize: '0.75rem', color: '#9ca3af' }}>
                          Datos de Google Books. Cada librería puede tener otra edición: fijate en la portada de cada ejemplar.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* 1. In-Stock Offers from SQL inventory_stock */}
                  <div style={{ marginBottom: '32px' }}>
                    <h3 style={{ fontSize: isMobile ? '1.15rem' : '1.3rem', fontWeight: 800, color: '#4c1d95', marginBottom: '12px' }}>
                      Ejemplares en stock confirmado ({searchResult.in_stock_offers?.length || 0})
                    </h3>
                    {searchResult.in_stock_offers && searchResult.in_stock_offers.length > 0 ? (
                      <div style={{ ...CARD_GRID, gap: '16px' }}>
                        {searchResult.in_stock_offers.map((offer, idx) => (
                          <div key={idx} style={{ backgroundColor: '#ffffff', borderRadius: '14px', border: '2px solid #c084fc', padding: isMobile ? '18px' : '20px', display: 'flex', flexDirection: 'column' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px' }}>
                              {/* Cover from the store's own listing = the edition that store sells */}
                              <BookCover src={offer.cover_url} title={offer.book_title} width={isMobile ? 56 : 64} />
                              <div style={{ minWidth: 0, flex: 1 }}>
                                {/* Cover and "Disponible" pill start at the same top; the title's first
                                    line is centered on the pill (pill ≈ 17.6px tall → center 8.8px; the
                                    letters' center sits 0.66em below the top margin at lineHeight 1.2).
                                    ALL-CAPS titles (as many stores publish them) take a smaller size so
                                    long ones don't break into many lines */}
                                <h4 style={{ margin: 'calc(8.8px - 0.66em) 0 2px 0', lineHeight: 1.2, fontSize: isAllCaps(offer.book_title) ? (isMobile ? '0.86rem' : '0.95rem') : (isMobile ? '1rem' : '1.1rem'), color: '#1f2937', overflowWrap: 'anywhere' }}>{offer.book_title}</h4>
                                <p style={{ margin: 0, fontSize: '0.85rem', color: '#6b7280' }}>{offer.author}</p>
                              </div>
                              {/* Right column: small status pills in the top-right corner, price under them */}
                              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', flexShrink: 0 }}>
                                {/* Most stores only publish in/out of stock (stored as 1): show a count only when it's real */}
                                <span style={{ fontSize: '0.66rem', backgroundColor: '#dcfce7', color: '#166534', padding: '2px 7px', borderRadius: '9999px', fontWeight: 700, whiteSpace: 'nowrap' }}>
                                  {offer.stock_quantity > 1 ? `${offer.stock_quantity} disponibles` : 'Disponible'}
                                </span>
                                {offer.condition === 'Usado' && (
                                  <span style={{ fontSize: '0.66rem', backgroundColor: '#fef08a', color: '#854d0e', padding: '2px 7px', borderRadius: '9999px', fontWeight: 700, whiteSpace: 'nowrap' }}>
                                    Usado
                                  </span>
                                )}
                                {offer.price_uyu != null && (
                                  <span style={{ marginTop: '4px', fontSize: isMobile ? '1.05rem' : '1.2rem', fontWeight: 600, color: '#4c1d95', whiteSpace: 'nowrap', fontVariantNumeric: 'tabular-nums' }}>
                                    {formatPrice(offer.price_uyu, offer.currency)}
                                  </span>
                                )}
                              </div>
                            </div>
                            <hr style={{ border: 'none', borderTop: '1px solid #f3e8ff', margin: '12px 0' }} />
                            <div style={{ minWidth: 0 }}>
                              <strong style={{ fontSize: '0.92rem', color: '#374151' }}>{offer.store_name}</strong>
                              <p style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', margin: '2px 0 0 0', fontSize: '0.8rem', color: '#6b7280' }}>
                                <MapPin size={13} color="#c084fc" style={{ flexShrink: 0, marginTop: '2px' }} /> {offer.address} ({offer.department})
                              </p>
                            </div>

                            {/* Footer always at the bottom; "Ver en tienda" always bottom-right */}
                            <div style={{ marginTop: 'auto', paddingTop: '14px', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', gap: '10px', flexWrap: 'wrap' }}>
                              <WhatsAppButton
                                onClick={() => trackClick('whatsapp_click', offer.store_id, searchResult.query)}
                                number={offer.whatsapp}
                                message={`¡Hola ${offer.store_name}! Vi en LibrosUy que tienen "${offer.book_title}"${offer.author ? ` de ${offer.author}` : ''}${offer.price_uyu != null ? ` a ${formatPrice(offer.price_uyu, offer.currency)}` : ''}${offer.condition === 'Usado' ? ' (usado)' : ''}. ¿Sigue disponible?`}
                              />
                              {offer.product_url && (
                                <a
                                  href={offer.product_url}
                                  target="_blank"
                                  rel="noreferrer"
                                  onClick={() => trackClick('store_click', offer.store_id, searchResult.query)}
                                  style={{ marginLeft: 'auto', display: 'inline-flex', alignItems: 'center', gap: '6px', minHeight: '36px', backgroundColor: '#7e22ce', color: '#ffffff', textDecoration: 'none', padding: '8px 14px', borderRadius: '9999px', fontSize: '0.85rem', fontWeight: 700, whiteSpace: 'nowrap' }}
                                >
                                  Ver en tienda <ExternalLink size={14} />
                                </a>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p style={{ color: '#6b7280', backgroundColor: '#ffffff', padding: '16px 20px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
                        Por ahora no encontramos ejemplares en stock, pero las librerías de abajo podrían conseguirlo por encargo.
                      </p>
                    )}
                  </div>

                  {/* 2. Recommended Bookstores by Genre (genre chips filter the list) */}
                  {(() => {
                    const allRecs = searchResult.recommended_stores || [];
                    const recs = genreFilter ? allRecs.filter((s) => storeMatchesGenre(s, genreFilter)) : allRecs;
                    return (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginBottom: '16px' }}>
                      <h3 style={{ fontSize: isMobile ? '1.15rem' : '1.3rem', fontWeight: 800, color: '#4c1d95', margin: 0 }}>
                        Librerías que podrían conseguirlo por encargo ({recs.length})
                      </h3>
                      {(searchResult.matched_genres || []).map((g) => {
                        const active = genreFilter === g;
                        return (
                          <button
                            key={g}
                            type="button"
                            onClick={() => setGenreFilter(active ? null : g)}
                            aria-pressed={active}
                            title={active ? 'Quitar filtro' : `Ver solo librerías de ${g}`}
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '6px',
                              backgroundColor: active ? '#854d0e' : '#fef08a',
                              color: active ? '#fef08a' : '#854d0e',
                              border: '1px solid #854d0e',
                              padding: isMobile ? '7px 14px' : '4px 12px',
                              borderRadius: '9999px',
                              fontSize: '0.78rem',
                              fontWeight: 700,
                              cursor: 'pointer'
                            }}
                          >
                            Género: {g}{active && <span aria-hidden="true">✕</span>}
                          </button>
                        );
                      })}
                    </div>

                    {(() => {
                      const unconfirmed = recs.filter((s) => s.stock_source && s.stock_source !== 'verified');
                      if (unconfirmed.length === 0) return null;
                      return (
                        <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', backgroundColor: '#fffbeb', border: '1px solid #fde68a', color: '#78350f', borderRadius: '12px', padding: '14px 16px', marginBottom: '18px', fontSize: '0.9rem', lineHeight: 1.45 }}>
                          <Info size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
                          <div>
                            <strong>
                              {unconfirmed.length === 1
                                ? '1 de estas librerías puede tener el libro, pero todavía no tenemos su stock.'
                                : `${unconfirmed.length} de estas librerías pueden tener el libro, pero todavía no tenemos su stock.`}
                            </strong>{' '}
                            Consultales antes de ir.
                          </div>
                        </div>
                      );
                    })()}

                    <div style={storeGrid}>
                      {recs.map((store) => renderStoreCard(store, searchResult.query))}
                    </div>
                  </div>
                    );
                  })()}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: MI LISTA (Saved Bookstores) */}
          {activeTab === 'saved' && (
            <div>
              <h2 style={{ fontSize: isMobile ? '1.5rem' : '2rem', fontWeight: 800, color: '#4c1d95', margin: '0 0 20px 0' }}>
                Librerías guardadas
              </h2>

              <div
                role="note"
                style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', backgroundColor: '#faf5ff', border: '1px solid #e9d5ff', borderRadius: '12px', padding: isMobile ? '12px 14px' : '12px 16px', marginBottom: '20px', color: '#4c1d95', fontSize: '0.875rem', lineHeight: 1.5 }}
              >
                <Info size={18} color="#7e22ce" style={{ flexShrink: 0, marginTop: '1px' }} />
                <span>
                  Tu lista se guarda solo en este navegador y dispositivo. No se sincroniza con otros dispositivos, y se pierde si borrás los datos del sitio o usás modo incógnito.
                </span>
              </div>

              {savedStoresList.length === 0 ? (
                <div style={{ backgroundColor: '#ffffff', borderRadius: '24px', border: '1px solid #e9d5ff', padding: isMobile ? '40px 20px' : '60px 20px', textAlign: 'center' }}>
                  <Bookmark size={40} color="#854d0e" style={{ margin: '0 auto 20px auto', fill: '#fef08a' }} />
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#4c1d95', marginBottom: '10px' }}>
                    Tu lista está vacía
                  </h3>
                  <p style={{ color: '#6b7280', maxWidth: '460px', margin: '0 auto 20px auto' }}>
                    {isMobile ? 'Tocá' : 'Hacé clic en'} el ícono de marcador en cualquier librería de "Explorar Librerías" o "Buscar por Libro" para guardarla acá.
                  </p>
                  <button
                    onClick={() => setActiveTab('explore')}
                    style={{ backgroundColor: '#7e22ce', color: '#ffffff', border: 'none', borderRadius: '10px', padding: '10px 22px', fontWeight: 700, cursor: 'pointer' }}
                  >
                    Explorar las {stores.length} librerías
                  </button>
                </div>
              ) : (
                <div>
                  <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'flex-end' }}>
                    <button
                      onClick={() => {
                        setSavedStoreIds([]);
                        localStorage.removeItem('librosuy_saved_stores');
                      }}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#fee2e2', color: '#991b1b', border: 'none', borderRadius: '8px', padding: '8px 14px', fontWeight: 600, cursor: 'pointer', fontSize: '0.85rem' }}
                    >
                      <Trash2 size={14} /> Vaciar Mi Lista
                    </button>
                  </div>
                  <div style={storeGrid}>
                    {savedStoresList.map((store) => renderStoreCard(store))}
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      )}

      {/* Footer pinned to the bottom of the page (the home page has its own line with the link) */}
      {activeTab !== 'home' && (
        <footer style={{ textAlign: 'center', fontSize: '0.8rem', padding: isMobile ? '16px 16px calc(76px + env(safe-area-inset-bottom))' : '20px 20px 24px' }}>
          <a href="#privacidad" style={{ color: '#7e22ce' }}>Privacidad</a>
        </footer>
      )}

      {/* Phones: bottom tab bar (Android/iOS pattern), above the home indicator */}
      {isMobile && (
        <nav
          aria-label="Navegación principal"
          style={{
            position: 'fixed',
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 1100,
            display: 'flex',
            backgroundColor: 'rgba(255,255,255,0.96)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            borderTop: '1px solid #e9d5ff',
            paddingBottom: 'env(safe-area-inset-bottom)'
          }}
        >
          {[
            { id: 'home', label: 'Inicio', Icon: Home },
            { id: 'explore', label: 'Librerías', Icon: MapPin },
            { id: 'genres', label: 'Buscar', Icon: Search },
            { id: 'saved', label: 'Mi Lista', Icon: Bookmark }
          ].map(({ id, label, Icon }) => {
            const active = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => { setActiveTab(id); window.scrollTo(0, 0); }}
                aria-current={active ? 'page' : undefined}
                style={{
                  flex: 1,
                  minHeight: '58px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '3px',
                  border: 'none',
                  background: 'transparent',
                  color: active ? '#7e22ce' : '#6b7280',
                  fontSize: '0.7rem',
                  fontWeight: active ? 800 : 600,
                  position: 'relative'
                }}
              >
                <Icon size={22} strokeWidth={active ? 2.4 : 1.8} />
                {label}
              </button>
            );
          })}
        </nav>
      )}
    </div>
  );
}