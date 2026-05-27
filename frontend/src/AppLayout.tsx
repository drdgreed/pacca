/**
 * AppLayout — root authenticated shell for PACCA.
 *
 * Owns:
 *   - The skip-to-content link (a11y)
 *   - The primary EditorialNav
 *   - The <Outlet> for surface routes
 *   - The editorial footer with build metadata
 *
 * Replaces the legacy `DashboardShell` component that previously lived
 * in App.tsx. After PR-UI-1, every authenticated surface (Provider,
 * Director, Admin, SME-author) renders under this layout, so they all
 * inherit the same Editorial-Clinical chrome.
 *
 * Sub-shells (currently just SMEAuthoringLayout) render their own
 * secondary nav strip + sub-page content inside the main outlet.
 */

import { Outlet } from 'react-router-dom';
import { EditorialNav } from './components/EditorialNav';

export function AppLayout() {
  const buildVersion =
    (import.meta as ImportMeta & { env?: { VITE_VERSION?: string } }).env
      ?.VITE_VERSION ?? 'dev';
  const buildTimestamp = new Date().toISOString().slice(0, 16).replace('T', ' ');

  return (
    <>
      {/* Skip-to-content link for keyboard / screen-reader users.
          Visible only when focused via Tab from the top of the page. */}
      <a href="#pacca-main" className="sme-skip-link">
        Skip to main content
      </a>

      <EditorialNav />

      <main id="pacca-main" tabIndex={-1}>
        <Outlet />
      </main>

      <footer className="sme-footer">
        PACCA · build {buildVersion} · {buildTimestamp}
      </footer>
    </>
  );
}
