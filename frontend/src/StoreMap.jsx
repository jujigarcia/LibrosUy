import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { MapPin, Tag } from 'lucide-react';
import { trackClick } from './analytics';

// Fix Leaflet marker icon paths in Webpack/React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Uruguay's bounding box (with a small margin) — the map cannot be panned outside it
const URUGUAY_BOUNDS = [
  [-35.2, -58.6], // South-west (Colonia / Río de la Plata)
  [-29.9, -52.9]  // North-east (Artigas / Rivera / Rocha)
];

// compact: phone layout (shorter map, so the page can still be scrolled around it)
function StoreMap({ stores = [], loading = false, compact = false }) {
  const geolocatedStores = stores.filter(
    (s) => s.latitude != null && s.longitude != null
  );

  return (
    <div style={{ marginTop: compact ? '12px' : '20px', marginBottom: compact ? '20px' : '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: '4px 12px', marginBottom: '10px' }}>
        {/* Small label (same style as "Libro identificado"): the map itself is the content */}
        <h3 style={{ margin: 0, color: '#7e22ce', fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Mapa interactivo Uruguay
        </h3>
        {loading && (
          <span style={{ fontSize: compact ? '0.78rem' : '0.875rem', color: '#6b7280', fontWeight: 600 }}>
            Cargando ubicaciones...
          </span>
        )}
      </div>

      {/* position + zIndex 0: own stacking context, so Leaflet's controls and attribution
          (z-index 1000) stay under the sticky header instead of painting over it */}
      <div style={{ position: 'relative', zIndex: 0, height: compact ? '320px' : '440px', width: '100%', borderRadius: '16px', overflow: 'hidden', border: '1px solid #e9d5ff', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
        <MapContainer
          center={[-34.65, -56.05]}
          zoom={compact ? 6 : 8}
          minZoom={compact ? 6 : 7}
          scrollWheelZoom={true}
          touchZoom={true}
          zoomControl={true}
          maxBounds={URUGUAY_BOUNDS}
          maxBoundsViscosity={1.0}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            bounds={URUGUAY_BOUNDS}
          />
          {geolocatedStores.map((store) => (
            <Marker key={store.id} position={[store.latitude, store.longitude]}>
              <Popup>
                <div style={{ padding: '4px', minWidth: '180px' }}>
                  <strong style={{ fontSize: '1rem', color: '#4c1d95' }}>{store.name}</strong>
                  <p style={{ display: 'flex', alignItems: 'center', gap: '6px', margin: '4px 0', fontSize: '0.82rem', color: '#374151' }}>
                    <MapPin size={13} color="#c084fc" /> {store.address} ({store.department})
                  </p>
                  {/* Catalog line = link to the store's website (violet); grey, not clickable, without one */}
                  {store.website ? (
                    <a
                      href={`https://${store.website}`}
                      target="_blank"
                      rel="noreferrer"
                      onClick={() => trackClick('store_click', store.id)}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', margin: '4px 0', fontSize: '0.78rem', color: '#7e22ce', textDecoration: 'none' }}
                    >
                      <Tag size={13} color="#c084fc" /> {store.specialty}
                    </a>
                  ) : (
                    <p style={{ display: 'flex', alignItems: 'center', gap: '6px', margin: '4px 0', fontSize: '0.78rem', color: '#9ca3af' }}>
                      <Tag size={13} color="#d1d5db" /> {store.specialty}
                    </p>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

export default StoreMap;