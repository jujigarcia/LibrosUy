import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Analytics } from '@vercel/analytics/react';
import App from './App';
import StatsPage from './StatsPage';
import PrivacyPage from './PrivacyPage';
import FeedbackButton from './FeedbackButton';
import './index.css';

// Secondary pages live under a hash so they work on any static host without server routes:
//   /#estadisticas  -> private usage dashboard (needs the stats key)
//   /#privacidad    -> privacy notice
function Root() {
  const [hash, setHash] = useState(() => window.location.hash);
  useEffect(() => {
    const onChange = () => { setHash(window.location.hash); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);

  if (hash === '#estadisticas') return <StatsPage />;
  if (hash === '#privacidad') return <PrivacyPage />;
  return (
    <>
      <App />
      <FeedbackButton />
    </>
  );
}

const container = document.getElementById('root');
const root = createRoot(container);

root.render(
  <React.StrictMode>
    <Root />
    {/* Vercel Web Analytics: anonymous page views, no cookies (enable it in Vercel > Analytics) */}
    <Analytics />
  </React.StrictMode>
);
