import { useEffect, useState } from 'react';
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from 'react-router-dom';
import { AppLayout } from './AppLayout';
import { AdminDashboard } from './components/AdminDashboard';
import { DirectorQueue } from './components/DirectorQueue';
import { LoginScreen } from './components/LoginScreen';
import { ProviderDashboard } from './components/ProviderDashboard';
import { BatchDetail } from './sme-authoring/pages/BatchDetail';
import { BatchList } from './sme-authoring/pages/BatchList';
import { Dashboard as SMEDashboard } from './sme-authoring/pages/Dashboard';
import { DatasetStatus } from './sme-authoring/pages/DatasetStatus';
import { GapList } from './sme-authoring/pages/GapList';
import { NewCaseWizard } from './sme-authoring/pages/NewCaseWizard';
import { SessionDetail } from './sme-authoring/pages/SessionDetail';
import { SessionList } from './sme-authoring/pages/SessionList';
import { SMEAuthoringLayout } from './sme-authoring/SMEAuthoringLayout';

/**
 * App — top-level shell.
 *
 * Architecture (PR-UI-1 onward):
 *   - React Router (BrowserRouter) governs all navigation.
 *   - <AppLayout> is the single root shell. It owns the primary
 *     EditorialNav, the skip-to-content link, and the footer.
 *   - Every authenticated surface (Provider / Director / Admin /
 *     SME-author) renders under <AppLayout>, so they all inherit the
 *     same Editorial-Clinical chrome.
 *   - Sub-shells (currently only SMEAuthoringLayout for /sme-author/*)
 *     render a secondary nav strip + their own outlet for child routes.
 *
 * Auth: JWT in localStorage. <RequireAuth/> wraps any authenticated
 * subtree and redirects to /login when the token is absent. Reads
 * localStorage synchronously on first render to avoid login-flash.
 */

/**
 * RequireAuth — auth guard for any subtree behind sign-in.
 *
 * Re-checks localStorage on every render (cheap) AND re-renders on:
 *   - Route navigation (via useLocation dependency).
 *   - Cross-tab sign-out (via the browser's `storage` event, which
 *     fires when localStorage changes in another tab).
 *   - Same-tab sign-out by EditorialNav (which dispatches a synthetic
 *     `pacca:auth-changed` event — the browser doesn't fire `storage`
 *     for changes in the same tab that made them).
 *
 * Pre-fix behavior: used a `useState(() => ...)` initializer that only
 * ran on mount. Because React Router keeps the parent Route element
 * mounted across child-route navigation, the auth state was effectively
 * frozen at first-render. After sign-out, nav'ing back into the
 * protected subtree (without leaving it first) bypassed the check.
 */
function RequireAuth({ children }: { children: JSX.Element }) {
  const location = useLocation();
  const [, forceRerender] = useState(0);

  useEffect(() => {
    const onChange = () => forceRerender((n) => n + 1);
    window.addEventListener('storage', onChange);
    window.addEventListener('pacca:auth-changed', onChange);
    return () => {
      window.removeEventListener('storage', onChange);
      window.removeEventListener('pacca:auth-changed', onChange);
    };
  }, []);

  // Read fresh on every render — also re-runs when `location` changes
  // (React Router updates location on every navigation, including
  // intra-subtree, so this picks up post-signout navigation too).
  const hasToken = Boolean(localStorage.getItem('token'));
  if (!hasToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}

function LoginRoute() {
  const navigate = useNavigate();
  return <LoginScreen onLoginSuccess={() => navigate('/provider')} />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginRoute />} />

        {/* All authenticated surfaces live under AppLayout */}
        <Route
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/provider" replace />} />

          {/* Provider / Director / Admin — Editorial-Clinical reskin
              arrives in PR-UI-2 + PR-UI-3 + PR-UI-4. Until then these
              components still use Tailwind indigo, but they sit inside
              the new editorial chrome (nav + footer + body fonts). */}
          <Route path="/provider" element={<ProviderDashboard />} />
          <Route path="/director" element={<DirectorQueue />} />
          <Route path="/admin" element={<AdminDashboard />} />

          {/* SME Authoring sub-shell mounts its own secondary nav */}
          <Route path="/sme-author" element={<SMEAuthoringLayout />}>
            <Route index element={<SMEDashboard />} />
            <Route path="new" element={<NewCaseWizard />} />
            <Route path="sessions" element={<SessionList />} />
            <Route path="sessions/:sessionId" element={<SessionDetail />} />
            <Route path="batches" element={<BatchList />} />
            <Route path="batches/:batchId" element={<BatchDetail />} />
            <Route path="gaps" element={<GapList />} />
            <Route path="status" element={<DatasetStatus />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
