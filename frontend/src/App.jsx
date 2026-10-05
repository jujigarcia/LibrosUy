import React, { useState } from 'react';
import { Search, MapPin, Phone, BookOpen, Bookmark, Star } from 'lucide-react';
import StoreMap from './StoreMap';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [searchQuery, setSearchQuery] = useState('');

  const sampleStores = [
    {
      id: 1,
      name: "Librería Puro Verso",
      address: "Sarandí 675, Ciudad Vieja",
      city: "Montevideo",
      phone: "+598 2915 2589",
      tags: ["Clásicos", "Historia", "Café Literario"],
      featured: true
    },
    {
      id: 2,
      name: "Escaramuza Libros",
      address: "Dr. Pablo de María 1185, Cordón",
      city: "Montevideo",
      phone: "+598 2401 3475",
      tags: ["Literatura Infantil", "Filosofía", "Café"],
      featured: true
    },
    {
      id: 3,
      name: "Bookshop Pocitos",
      address: "Av. Brasil 2831, Pocitos",
      city: "Montevideo",
      phone: "+598 2707 1515",
      tags: ["Novedades", "Bestsellers", "Juvenil"],
      featured: false
    }
  ];

  const filteredStores = sampleStores.filter(store => {
    const matchesSearch = store.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          store.address.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          store.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSearch;
  });

  return (
    <div style={{ 
      minHeight: '100vh', 
      fontFamily: 'system-ui, -apple-system, sans-serif',
      position: 'relative',
      background: activeTab === 'home' 
        ? 'radial-gradient(circle at 30% 50%, #fdf4ff 0%, #fbcfe8 35%, #e9d5ff 70%, #ecfccb 100%)'
        : '#f9fafb'
    }}>
      
      {/* Navigation Bar */}
      <header style={{ 
        backgroundColor: activeTab === 'home' ? 'transparent' : '#ffffff', 
        borderBottom: activeTab === 'home' ? 'none' : '1px solid #e9d5ff', 
        position: activeTab === 'home' ? 'absolute' : 'sticky', 
        top: 0, 
        left: 0,
        right: 0,
        zIndex: 1000, 
        padding: '30px 4%' 
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          
          <div 
            onClick={() => setActiveTab('home')}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
          >
            {/* Default logo in top left */}
            <BookOpen style={{ color: '#374151' }} size={28} strokeWidth={1} />
            <span style={{ fontSize: '1.4rem', fontWeight: 800, color: '#374151' }}>LibrosUy</span>
          </div>

          <nav style={{ display: 'flex', gap: '32px' }}>
            <button 
              onClick={() => setActiveTab('explore')}
              style={{
                border: 'none',
                backgroundColor: 'transparent',
                color: '#374151',
                fontWeight: 800,
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
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
                color: '#374151',
                fontWeight: 800,
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                padding: 0
              }}
            >
              Buscar por Género
            </button>
            <button 
              onClick={() => setActiveTab('saved')}
              style={{
                border: 'none',
                backgroundColor: 'transparent',
                color: '#374151',
                fontWeight: 800,
                fontSize: '1rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                padding: 0
              }}
            >
              Mi Lista
            </button>
          </nav>
        </div>
      </header>

      {/* Tab 0: Home */}
      {activeTab === 'home' && (
        <main style={{ 
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 8%',
          position: 'relative'
        }}>
          
          {/* Left Column: Typography & Branding */}
          <div style={{ flex: '1 1 50%', display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: '40px' }}>
            
            {/* Stylized Center Logo */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '40px', color: '#374151' }}>
              <span style={{ fontSize: '5.5rem', fontWeight: 800, transform: 'rotate(-8deg)', letterSpacing: '-0.03em' }}>
                Libros
              </span>
              <span style={{ fontSize: '5.5rem', fontWeight: 800, display: 'flex', alignItems: 'center', marginTop: '-30px', marginLeft: '60px', letterSpacing: '-0.03em' }}>
                <span style={{ fontSize: '4.5rem', marginRight: '8px', transform: 'translateY(5px)' }}>✳</span>Uy
              </span>
            </div>
            
            {/* Marketing Phrase */}
            <h1 style={{ 
              fontSize: '4.2rem', 
              fontWeight: 300, 
              color: '#374151', 
              lineHeight: '1.05', 
              margin: 0,
              letterSpacing: '-0.03em',
              textAlign: 'center'
            }}>
            La mejor forma de encontrar<br />tu libro
            </h1>
          </div>

          {/* Right Column: Line Art Book Graphic + Abstract Figure */}
          <div style={{ flex: '1 1 50%', display: 'flex', justifyContent: 'center', alignItems: 'center', position: 'relative' }}>
            
            <svg viewBox="0 0 200 200" style={{ position: 'absolute', width: '650px', height: '650px', zIndex: 0, opacity: 0.7 }}>
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

            <BookOpen size={500} strokeWidth={1} color="#1f2937" style={{ zIndex: 1, position: 'relative', transform: 'rotate(8deg)' }} />
          </div>

          {/* Disclaimer anchored to bottom left */}
          <p style={{ 
            position: 'absolute',
            bottom: '40px',
            left: '4%',
            fontSize: '0.75rem', 
            fontWeight: 800, 
            color: '#374151', 
            textTransform: 'uppercase', 
            letterSpacing: '0.05em',
            margin: 0
          }}>
            STOCK ACTUALIZADO DEPENDIENDO DE LAS LIBRERIAS
          </p>
        </main>
      )}

      {/* Rest of the Tabs */}
      {activeTab !== 'home' && (
        <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 20px' }}>
          
          {activeTab === 'explore' && (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <h2 style={{ fontSize: '2rem', fontWeight: 800, color: '#4c1d95', margin: 0 }}>Mapa de Librerías en Uruguay</h2>
              </div>
              
              <div style={{ maxWidth: '600px', marginBottom: '24px', display: 'flex', gap: '8px', backgroundColor: '#ffffff', padding: '6px', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
                <div style={{ display: 'flex', alignItems: 'center', paddingLeft: '12px', color: '#9ca3af' }}>
                  <Search size={20} />
                </div>
                <input
                  type="text"
                  placeholder="Buscar librería por nombre o ubicación..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ flex: 1, border: 'none', outline: 'none', padding: '10px 8px', fontSize: '1rem' }}
                />
              </div>

              <StoreMap />

              <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#6b21a8', marginBottom: '16px', marginTop: '40px' }}>
                Directorio de Librerías
              </h3>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
                {filteredStores.map(store => (
                  <div key={store.id} style={{ backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #e9d5ff', padding: '24px', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                      <h4 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#374151' }}>{store.name}</h4>
                      {store.featured && (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', backgroundColor: '#fef08a', color: '#854d0e', padding: '4px 8px', borderRadius: '9999px', fontWeight: 600 }}>
                          <Star size={10} fill="#854d0e" /> Destacada
                        </span>
                      )}
                    </div>
                    <p style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '8px 0', fontSize: '0.9rem', color: '#6b7280' }}>
                      <MapPin size={16} color="#c084fc" /> {store.address}
                    </p>
                    <p style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: '8px 0', fontSize: '0.9rem', color: '#6b7280' }}>
                      <Phone size={16} color="#c084fc" /> {store.phone}
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '16px' }}>
                      {store.tags.map((tag, i) => (
                        <span key={i} style={{ fontSize: '0.75rem', backgroundColor: '#f3e8ff', color: '#7e22ce', padding: '4px 10px', borderRadius: '6px', fontWeight: 500 }}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'genres' && (
            <div style={{ backgroundColor: '#ffffff', borderRadius: '24px', border: '1px solid #e9d5ff', padding: '60px 20px', textAlign: 'center' }}>
              <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#4c1d95', marginBottom: '12px' }}>Búsqueda por Género</h3>
              <p style={{ color: '#6b7280', maxWidth: '500px', margin: '0 auto' }}>
                Funcionalidad de búsqueda conectada a Google Books en desarrollo.
              </p>
            </div>
          )}

          {activeTab === 'saved' && (
            <div style={{ backgroundColor: '#ffffff', borderRadius: '24px', border: '1px solid #e9d5ff', padding: '60px 20px', textAlign: 'center' }}>
              <Bookmark size={40} color="#854d0e" style={{ margin: '0 auto 24px auto', fill: '#fef08a' }} />
              <h3 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#4c1d95', marginBottom: '12px' }}>Tu lista guardada</h3>
              <p style={{ color: '#6b7280' }}>Aún no guardaste ninguna librería favorita.</p>
            </div>
          )}
        </main>
      )}
    </div>
  );
}