/**
 * SMEAuthoringLayout — the route-subtree wrapper for the SME surface.
 *
 * Responsibilities:
 *   1. Apply the `.sme-authoring` className so the Editorial-Clinical
 *      theme's CSS variables + scoped rules take effect on this subtree
 *      and nowhere else.
 *   2. Import `./theme.css` so the stylesheet is bundled when (and only
 *      when) any SME-authoring route loads.
 *   3. Render the editorial nav bar at the top + the dataset-state
 *      monospace footer at the bottom.
 *   4. Host the React Router <Outlet/> for child routes.
 *
 * Aesthetic isolation note: the import of `./theme.css` makes Vite bundle
 * the styles, but every rule is wrapped in `.sme-authoring { ... }`, so
 * even though the stylesheet is loaded globally, NO RULE matches outside
 * this subtree. Existing Provider / Director / Admin surfaces are
 * unaffected. Verified by the aesthetic-isolation acceptance criterion.
 */

import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useStatus } from './hooks/useStatus';
import { safeLogout } from './lib/safeLogout';
import './theme.css';

interface SMEAuthoringLayoutProps {
  /** Optional logout handler — passed through from App.tsx. */
  onLogout?: () => void;
}

export function SMEAuthoringLayout({ onLogout }: SMEAuthoringLayoutProps) {
  // Status powers the footer's "GC-N of M" dataset-state indicator.
  // We load it once at the layout level and pass it to children via
  // a re-fetch when they need fresh data; this keeps the footer
  // stable as the user navigates between sub-pages.
  const status = useStatus();
  const navigate = useNavigate();

  const handleLogout = () => {
    // safeLogout clears the JWT AND scrubs any unexpected localStorage
    // entries (with a dev-mode warning if any contained PHI patterns).
    // We call it regardless of whether the parent passes onLogout — the
    // parent's hook may not run a defensive scan.
    safeLogout();
    if (onLogout) onLogout();
    navigate('/');
  };

  const totalCases = status.data?.total_cases;
  const buildVersion =
    (import.meta as ImportMeta & { env?: { VITE_VERSION?: string } }).env
      ?.VITE_VERSION ?? 'dev';
  const buildTimestamp = new Date().toISOString().slice(0, 16).replace('T', ' ');

  return (
    <div className="sme-authoring">
      {/* Skip-to-content link — visible only when focused via keyboard.
          A11y essential for screen-reader + keyboard-only users so they
          don't have to tab through the entire nav on every page. */}
      <a href="#sme-main" className="sme-skip-link">
        Skip to main content
      </a>

      <nav className="sme-nav" aria-label="Primary navigation">
        <NavLink to="/sme-author" className="sme-nav-brand" end>
          PACCA
          <span className="sme-nav-brand-mark">case authoring</span>
        </NavLink>
        <div className="sme-nav-links">
          <NavLink
            to="/sme-author"
            end
            className={({ isActive }) =>
              `sme-nav-link${isActive ? ' is-active' : ''}`
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/sme-author/new"
            className={({ isActive }) =>
              `sme-nav-link${isActive ? ' is-active' : ''}`
            }
          >
            New case
          </NavLink>
          <NavLink
            to="/sme-author/sessions"
            className={({ isActive }) =>
              `sme-nav-link${isActive ? ' is-active' : ''}`
            }
          >
            Sessions
          </NavLink>
          <NavLink
            to="/sme-author/batches"
            className={({ isActive }) =>
              `sme-nav-link${isActive ? ' is-active' : ''}`
            }
          >
            Batches
          </NavLink>
          <NavLink
            to="/sme-author/gaps"
            className={({ isActive }) =>
              `sme-nav-link${isActive ? ' is-active' : ''}`
            }
          >
            Gaps
          </NavLink>
          <NavLink
            to="/sme-author/status"
            className={({ isActive }) =>
              `sme-nav-link${isActive ? ' is-active' : ''}`
            }
          >
            Status
          </NavLink>
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: '1.5rem',
          }}
        >
          <span className="sme-nav-meta">
            {totalCases !== undefined ? `${totalCases} cases` : '— cases'}
          </span>
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
        </div>
      </nav>

      <main id="sme-main" tabIndex={-1}>
        <Outlet />
      </main>

      <footer className="sme-footer">
        {totalCases !== undefined
          ? `dataset · ${totalCases} cases · build ${buildVersion} · ${buildTimestamp}`
          : `dataset · build ${buildVersion} · ${buildTimestamp}`}
      </footer>
    </div>
  );
}
