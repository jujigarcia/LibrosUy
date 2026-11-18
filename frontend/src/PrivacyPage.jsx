import React from 'react';
import { ShieldCheck } from 'lucide-react';

// Public privacy notice at /#privacidad. Plain-language draft; review it before relying on it legally.
const section = { margin: '0 0 18px 0' };
const h2 = { fontSize: '1.1rem', color: '#4c1d95', margin: '0 0 6px 0' };
const p = { margin: '0 0 8px 0', lineHeight: 1.6, color: '#374151' };

export default function PrivacyPage() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', fontFamily: 'system-ui, -apple-system, sans-serif', padding: '24px 16px 48px' }}>
      <article style={{ maxWidth: '720px', margin: '0 auto', backgroundColor: '#ffffff', border: '1px solid #e9d5ff', borderRadius: '16px', padding: '28px 22px' }}>
        <h1 style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.6rem', color: '#4c1d95', margin: '0 0 6px 0' }}>
          <ShieldCheck size={26} /> Privacidad
        </h1>
        <p style={{ ...p, color: '#6b7280', fontSize: '0.9rem' }}>Última actualización: noviembre de 2026</p>

        <div style={section}>
          <h2 style={h2}>Qué es LibrosUy</h2>
          <p style={p}>
            LibrosUy es un buscador que reúne el catálogo publicado por librerías de Uruguay para que encuentres un libro
            y contactes directamente a la librería. No vendemos libros ni procesamos pagos.
          </p>
        </div>

        <div style={section}>
          <h2 style={h2}>Qué datos registramos</h2>
          <p style={p}>Para saber si LibrosUy es útil, guardamos estadísticas anónimas de uso:</p>
          <ul style={{ ...p, paddingLeft: '20px' }}>
            <li>los textos que se buscan y cuántos resultados hubo;</li>
            <li>los clics en «Consultar aquí» (WhatsApp) y «Ver en tienda», y a qué librería corresponden;</li>
            <li>visitas al sitio de forma agregada (cantidad de visitas, páginas, país y tipo de dispositivo), mediante Vercel Web Analytics.</li>
          </ul>
          <p style={p}>
            No guardamos tu nombre, correo, teléfono ni dirección IP, no usamos cookies de seguimiento y no te pedimos crear una cuenta.
          </p>
        </div>

        <div style={section}>
          <h2 style={h2}>Sugerencias</h2>
          <p style={p}>
            Si nos escribís con el botón «Sugerencias», guardamos tu mensaje y nos llega por correo. El email es opcional:
            solo lo pedimos si querés que te respondamos, y lo usamos únicamente para eso.
          </p>
        </div>

        <div style={section}>
          <h2 style={h2}>Tu lista de librerías</h2>
          <p style={p}>
            Las librerías que guardás en «Mi Lista» quedan solo en tu navegador (almacenamiento local). No se envían a nuestros servidores.
          </p>
        </div>

        <div style={section}>
          <h2 style={h2}>WhatsApp y sitios de las librerías</h2>
          <p style={p}>
            Al tocar «Consultar aquí» se abre WhatsApp con un mensaje ya escrito para la librería; la conversación es entre vos y la librería.
            Al tocar «Ver en tienda» vas al sitio de la librería. En ambos casos rigen las políticas de privacidad de WhatsApp y de cada librería.
          </p>
        </div>

        <div style={section}>
          <h2 style={h2}>Para qué usamos las estadísticas</h2>
          <p style={p}>
            Para mejorar el buscador, saber qué libros se buscan y no se encuentran, y mostrar a las librerías cuántas consultas reciben a través de LibrosUy,
            siempre en forma agregada y sin identificar a ninguna persona.
          </p>
        </div>

        <div style={section}>
          <h2 style={h2}>Tus derechos</h2>
          <p style={p}>
            En Uruguay, la Ley N.º 18.331 de Protección de Datos Personales te da derecho a acceder, rectificar y suprimir tus datos.
            Como no registramos datos que te identifiquen, normalmente no tenemos información personal tuya; igualmente podés escribirnos por cualquier consulta.
          </p>
        </div>

        <a href="/" style={{ display: 'inline-block', marginTop: '6px', color: '#ffffff', backgroundColor: '#7e22ce', padding: '10px 18px', borderRadius: '9999px', textDecoration: 'none', fontWeight: 700 }}>
          Volver a LibrosUy
        </a>
      </article>
    </div>
  );
}
