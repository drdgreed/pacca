/**
 * SMEAuthoringLayout — sub-shell for the SME Case Authoring surface.
 *
 * Mounted under AppLayout's <Outlet>. Renders the SME-specific secondary
 * navigation strip (Dashboard / New case / Sessions / Batches / Gaps /
 * Status) + a dataset-state badge.
 *
 * Pre-PR-UI-1 history: this component used to own the global Editorial
 * chrome (primary nav, footer, theme.css import, .sme-authoring scope
 * class). PR-UI-1 promoted those responsibilities up to AppLayout so
 * the entire app shares the editorial aesthetic. SMEAuthoringLayout
 * shrank to just the secondary nav.
 */

import { NavLink, Outlet } from 'react-router-dom';
import { useStatus } from './hooks/useStatus';

export function SMEAuthoringLayout() {
  // Status powers the sub-nav's "N cases" indicator. Loaded once at the
  // layout level so it stays stable as the user navigates between
  // sub-pages.
  const status = useStatus();
  const totalCases = status.data?.total_cases;

  return (
    <>
      <nav className="sme-subnav" aria-label="SME Authoring secondary navigation">
        <div
          className="sme-nav-brand-mark"
          style={{ marginLeft: 0, marginRight: '0.5rem' }}
        >
          case authoring
        </div>
        <div className="sme-nav-links" style={{ flex: 1 }}>
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
        <span className="sme-nav-meta">
          {totalCases !== undefined ? `${totalCases} cases` : '— cases'}
        </span>
      </nav>

      <Outlet />
    </>
  );
}
