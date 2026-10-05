import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet marker icon asset paths when bundled with Webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function StoreMap() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://127.0.0.1:8000/api/stores')
      .then((res) => res.json())
      .then((data) => {
        setStores(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error cargando librerías:", err);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ marginTop: '20px', marginBottom: '30px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h3 style={{ margin: 0, color: '#1f2937' }}>Mapa de Librerías en Uruguay</h3>
        <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
          {loading ? 'Cargando ubicaciones...' : `${stores.length} librerías geolocalizadas`}
        </span>
      </div>

      <div style={{ height: '420px', width: '100%', borderRadius: '12px', overflow: 'hidden', border: '1px solid #e5e7eb', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)' }}>
        <MapContainer
          center={[-34.9011, -56.1645]}
          zoom={12}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {stores.map((store, idx) => (
            <Marker key={idx} position={[store.latitude, store.longitude]}>
              <Popup>
                <div style={{ padding: '2px' }}>
                  <strong style={{ fontSize: '1rem', color: '#111827' }}>{store.name}</strong>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.8rem', color: '#4b5563' }}>
                    Coordenadas: {store.latitude.toFixed(4)}, {store.longitude.toFixed(4)}
                  </p>
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