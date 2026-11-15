import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { MapPin, Tag } from 'lucide-react';

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

function StoreMap({ stores = [], loading = false }) {
  const geolocatedStores = stores.filter(
    (s) => s.latitude != null && s.longitude != null
  );

  return (
    <div style={{ marginTop: '20px', marginBottom: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h3 style={{ margin: 0, color: '#1f2937' }}>Mapa Interactivo (Montevideo e Interior)</h3>
        <span style={{ fontSize: '0.875rem', color: '#6b7280', fontWeight: 600 }}>
          {loading ? 'Cargando ubicaciones...' : `${geolocatedStores.length} librerías geolocalizadas en el mapa`}
        </span>
      </div>

      <div style={{ height: '440px', width: '100%', borderRadius: '16px', overflow: 'hidden', border: '1px solid #e9d5ff', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
        <MapContainer
          center={[-34.65, -56.05]}
          zoom={8}
          minZoom={7}
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
                  <p style={{ display: 'flex', alignItems: 'center', gap: '6px', margin: '4px 0', fontSize: '0.78rem', color: '#6b21a8' }}>
                    <Tag size={13} color="#c084fc" /> {store.specialty}
                  </p>
                  {store.website && (
                    <a
                      href={`https://${store.website}`}
                      target="_blank"
                      rel="noreferrer"
                      style={{ display: 'inline-block', marginTop: '6px', fontSize: '0.8rem', color: '#7e22ce', fontWeight: 700 }}
                    >
                      Visitar {store.website} →
                    </a>
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