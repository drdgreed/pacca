/**
 * EditorialNav — the global primary navigation for PACCA (post-auth).
 *
 * Replaces the legacy indigo Tailwind nav that lived in App.tsx's
 * DashboardShell. Renders all surface tabs in the small-caps editorial
 * style, with a Spectral brand wordmark + monospace subtitle.
 *
 * Sub-shells (currently just SME Authoring) render their own secondary
 * `.sme-subnav` strip beneath this primary nav.
 */

import { NavLink, useNavigate } from 'react-router-dom';
import { safeLogout } from '../sme-authoring/lib/safeLogout';

interface SurfaceLink {
  to: string;
  label: string;
  end?: boolean;
}

const SURFACES: SurfaceLink[] = [
  { to: '/provider', label: 'Submit case' },
  { to: '/director', label: 'Director queue' },
  { to: '/admin', label: 'Admin' },
  { to: '/sme-author', label: 'SME authoring' },
];

export function EditorialNav() {
  const navigate = useNavigate();

  const handleLogout = () => {
    safeLogout();
    navigate('/login');
  };

  return (
    <nav className="sme-nav" aria-label="Primary navigation">
      <NavLink to="/provider" className="sme-nav-brand">
        PACCA
        <span className="sme-nav-brand-mark">prior authorization</span>
      </NavLink>
      <div className="sme-nav-links">
        {SURFACES.map((s) => (
          <NavLink
            key={s.to}
            to={s.to}
            end={s.end}
            className={({ isActive }) =>
              `sme-nav-link${isActive ? ' is-active' : ''}`
            }
          >
            {s.label}
          </NavLink>
        ))}
      </div>
      <button
        type="button"
        onClick={handleLogout}
        className="sme-nav-link"
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: 0,
          fontFamily: 'inherit',
          font: 'inherit',
          fontVariant: 'small-caps',
          letterSpacing: '0.06em',
          color: 'var(--sme-muted)',
        }}
      >
        Sign out
      </button>
    </nav>
  );
}
