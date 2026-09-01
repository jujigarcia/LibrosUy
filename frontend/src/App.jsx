import { useState } from "react";
import { Search, MapPin, BookOpen, Sparkles, Home, X } from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";

// Fix for default map marker icons in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png"),
  iconUrl: require("leaflet/dist/images/marker-icon.png"),
  shadowUrl: require("leaflet/dist/images/marker-shadow.png"),
});

// ---------- Estilos compartidos ----------
const COLORS = {
  bg: "#F7F0FB",
  card: "#FFFCFF",
  cardBorder: "#E7D6F0",
  violet: "#7C4FA6",
  violetDark: "#5B3782",
  pink: "#E56FA0",
  pinkSoft: "#F6D3E4",
  text: "#3D2A52",
  textMuted: "#8776A0",
};

function Pill({ active, onClick, children, icon: Icon }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        background: active ? COLORS.violet : "transparent",
        color: active ? "#fff" : COLORS.violetDark,
        border: `1.5px solid ${active ? COLORS.violet : COLORS.cardBorder}`,
        borderRadius: 20,
        padding: "7px 16px",
        fontSize: 14,
        fontWeight: 600,
        cursor: "pointer",
        fontFamily: "'IBM Plex Sans', sans-serif",
      }}
    >
      {Icon && <Icon size={14} />}
      {children}
    </button>
  );
}

// ---------- Vistas ----------

function HomeView() {
  return (
    <section style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "56px 24px", gap: 12 }}>
      <h1 className="serif" style={{ fontSize: "clamp(30px, 5vw, 46px)", lineHeight: 1.15, fontWeight: 600, margin: 0, color: COLORS.text, textAlign: "center" }}>
        Bienvenido a LibrosUY
      </h1>
      <svg viewBox="0 0 420 320" style={{ width: "min(560px, 80vw)", height: "auto", opacity: 0.14, pointerEvents: "none" }}>
        <path d="M210 44 C 170 20, 90 12, 30 26 L 30 268 C 90 254, 170 262, 210 286 Z" fill="none" stroke={COLORS.violetDark} strokeWidth="6" strokeLinejoin="round" />
        <path d="M210 44 C 250 20, 330 12, 390 26 L 390 268 C 330 254, 250 262, 210 286 Z" fill="none" stroke={COLORS.violetDark} strokeWidth="6" strokeLinejoin="round" />
        <line x1="210" y1="44" x2="210" y2="286" stroke={COLORS.violetDark} strokeWidth="5" />
        {[70, 100, 130].map((y) => <line key={"l" + y} x1="55" y1={y} x2="185" y2={y - 10} stroke={COLORS.violetDark} strokeWidth="3" strokeLinecap="round" />)}
        {[70, 100, 130].map((y) => <line key={"r" + y} x1="235" y1={y - 10} x2="365" y2={y} stroke={COLORS.violetDark} strokeWidth="3" strokeLinecap="round" />)}
      </svg>
    </section>
  );
}

function BuscadorView() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [matchedGenres, setMatchedGenres] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/search?title=${encodeURIComponent(query)}`);
      const data = await response.json();

      setResults(data.stores || []);
      setMatchedGenres(data.matched_genres || []);
    } catch (error) {
      console.error("Error fetching data from backend:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section style={{ padding: "40px 24px 64px", maxWidth: 880, margin: "0 auto" }}>
      <h1 className="serif" style={{ fontSize: "clamp(24px, 4vw, 34px)", fontWeight: 600, margin: "0 0 10px", color: COLORS.text }}>
        Buscá un libro
      </h1>
      <p style={{ fontSize: 15, color: COLORS.textMuted, margin: "0 0 28px", maxWidth: 520 }}>
        Escribí un título o autor. Identificamos el género y te mostramos qué librerías uruguayas se especializan en él.
      </p>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <div style={{ flex: "1 1 320px", display: "flex", alignItems: "center", gap: 10, background: COLORS.card, border: `2px solid ${COLORS.violet}`, borderRadius: 14, padding: "12px 16px" }}>
          <Search size={18} color={COLORS.violet} style={{ flexShrink: 0 }} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ej: Fourth Wing, Harry Potter, Dune..."
            style={{ border: "none", background: "transparent", fontSize: 16, width: "100%", fontFamily: "'IBM Plex Sans', sans-serif", color: COLORS.text }}
          />
        </div>
        <button type="submit" style={{ background: COLORS.violet, color: "#fff", border: "none", borderRadius: 14, padding: "0 28px", fontSize: 15, fontWeight: 600, cursor: "pointer", fontFamily: "'IBM Plex Sans', sans-serif" }}>
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </form>

      {searched && !loading && (
        <div style={{ marginTop: 36 }}>
          {matchedGenres.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <span style={{ fontSize: 13, color: COLORS.textMuted }}>Géneros detectados: </span>
              {matchedGenres.map((g) => (
                <span key={g} style={{ background: COLORS.pinkSoft, color: COLORS.violetDark, padding: "3px 10px", borderRadius: 12, fontSize: 12, fontWeight: 600, marginLeft: 6 }}>
                  {g}
                </span>
              ))}
            </div>
          )}

          <div style={{ display: "grid", gap: 12 }}>
            {results.length === 0 ? (
              <p style={{ color: COLORS.textMuted, fontSize: 15 }}>
                No encontramos librerías asociadas a las categorías de este libro.
              </p>
            ) : (
              results.map((store) => (
                <div key={store.name} style={{ background: COLORS.card, border: `1.5px solid ${COLORS.cardBorder}`, borderRadius: 14, padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
                  <div>
                    <div className="serif" style={{ fontSize: 18, fontWeight: 600, color: COLORS.text }}>
                      {store.name}
                    </div>
                    <div style={{ fontSize: 13, color: COLORS.textMuted, marginTop: 4 }}>
                      <MapPin size={13} style={{ display: "inline", verticalAlign: "middle", marginRight: 4 }} />
                      {store.address}, {store.city} ({store.department})
                    </div>
                  </div>
                  <a
                    href={`https://wa.me/${store.whatsapp}?text=Hola!%20Vi%20en%20LibrosUY%20que%20tienen%20libros%20de%20este%20género.%20¿Tienen%20disponible%20${encodeURIComponent(query)}?`}
                    target="_blank"
                    rel="noreferrer"
                    style={{ background: "#25D366", color: "#fff", textDecoration: "none", padding: "9px 16px", borderRadius: 10, fontWeight: 600, fontSize: 13 }}
                  >
                    Consultar por WhatsApp
                  </a>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function MapaView() {
  const uruguayCenter = [-32.5228, -55.7658];
  const activeStores = [
    { id: 1, name: "Librería Puro Verso", lat: -34.9065, lng: -56.2023, city: "Montevideo", address: "Peatonal Sarandí 675" },
    { id: 2, name: "Bookshop Canelones", lat: -34.5247, lng: -56.2801, city: "Canelones", address: "Treinta y Tres 550" },
    { id: 3, name: "Librería Local", lat: -34.7167, lng: -55.9500, city: "Pando", address: "Centro Comercial" }
  ];

  return (
    <section style={{ padding: "40px 24px 64px", maxWidth: 980, margin: "0 auto" }}>
      <h1 className="serif" style={{ fontSize: "clamp(24px, 4vw, 34px)", fontWeight: 600, margin: "0 0 10px", color: COLORS.text }}>
        Mapa de librerías
      </h1>
      <p style={{ fontSize: 15, color: COLORS.textMuted, margin: "0 0 28px", maxWidth: 560 }}>
        Navegá por el mapa real para encontrar las librerías más cercanas a vos.
      </p>

      <div style={{ background: COLORS.card, border: `1.5px solid ${COLORS.cardBorder}`, borderRadius: 20, overflow: "hidden", height: "600px", width: "100%", position: "relative", zIndex: 1 }}>
        <MapContainer center={uruguayCenter} zoom={7} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {activeStores.map((store) => (
            <Marker key={store.id} position={[store.lat, store.lng]}>
              <Popup>
                <div style={{ fontFamily: "'IBM Plex Sans', sans-serif" }}>
                  <strong style={{ fontSize: 14, color: COLORS.violetDark }}>{store.name}</strong><br/>
                  <span style={{ fontSize: 12, color: COLORS.textMuted }}>{store.address}, {store.city}</span>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </section>
  );
}

// ---------- Componente principal ----------
export default function BuscaLibroUY() {
  const [view, setView] = useState("home");

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, color: COLORS.text, fontFamily: "'IBM Plex Sans', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
        * { box-sizing: border-box; }
        .serif { font-family: 'Fraunces', serif; }
        input:focus, button:focus-visible { outline: 2px solid ${COLORS.violet}; outline-offset: 2px; }
        ::selection { background: ${COLORS.pink}; color: #fff; }
      `}</style>

      <header style={{ borderBottom: `1.5px solid ${COLORS.cardBorder}`, padding: "18px 24px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 12, background: COLORS.card }}>
        <button onClick={() => setView("home")} style={{ display: "flex", alignItems: "baseline", gap: 8, background: "none", border: "none", cursor: "pointer" }}>
          <span className="serif" style={{ fontSize: 21, fontWeight: 700, color: COLORS.violet }}>LibrosUY</span>
        </button>
        <nav style={{ display: "flex", gap: 8 }}>
          <Pill active={view === "home"} onClick={() => setView("home")} icon={Home}>Inicio</Pill>
          <Pill active={view === "buscador"} onClick={() => setView("buscador")} icon={Search}>Buscador</Pill>
          <Pill active={view === "mapa"} onClick={() => setView("mapa")} icon={MapPin}>Mapa</Pill>
        </nav>
      </header>

      {view === "home" && <HomeView />}
      {view === "buscador" && <BuscadorView />}
      {view === "mapa" && <MapaView />}

      <footer style={{ borderTop: `1.5px solid ${COLORS.cardBorder}`, padding: "20px 24px", textAlign: "center" }}>
        <p style={{ fontSize: 12, color: COLORS.textMuted, margin: 0 }}>
          Frontend conectado a FastAPI con mapas reales de Leaflet.
        </p>
      </footer>
    </div>
  );
}
