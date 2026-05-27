import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
// Tailwind base + utilities (layout only — colors / typography come from theme.css)
import './index.css';
// Editorial-Clinical theme (global; was scoped to .sme-authoring before PR-UI-1)
import './styles/theme.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
