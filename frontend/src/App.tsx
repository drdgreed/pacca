import { useState } from 'react';
import {
  BrowserRouter,
  Navigate,
  NavLink,
  Outlet,
  Route,
  Routes,
  useNavigate,
} from 'react-router-dom';
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
 * Architecture:
 *   - React Router (BrowserRouter) governs all navigation.
 *   - The legacy Provider / Director / Admin tabs live under <DashboardShell/>
 *     which preserves the existing Inter + Tailwind indigo aesthetic.
 *   - The new SME-authoring surface lives under /sme-author/* and renders
 *     <SMEAuthoringLayout/>, which scopes the Editorial-Clinical theme.
 *
 * Auth: same JWT-in-localStorage pattern as before. <RequireAuth/> wraps
 * any authenticated subtree and redirects to /login when the token is
 * absent or invalid.
 */

function RequireAuth({ children }: { children: JSX.Element }) {
  // Read localStorage synchronously on first render — avoids the flash
  // of "no auth" before useEffect settles. localStorage is fast enough
  // that this doesn't block paint.
  const [hasToken] = useState<boolean>(() =>
    Boolean(localStorage.getItem('token')),
  );

  if (!hasToken) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

/**
 * The legacy Provider / Director / Admin surface — same indigo Tailwind
 * dashboard as before, but the tab buttons are now React Router NavLinks
 * so deep-linking works.
 */
function DashboardShell() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-indigo-700 text-white shadow-md">
        <div className="max-w-6xl mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-6">
            <h1 className="text-2xl font-bold tracking-tight">PACCA</h1>
            <div className="space-x-1">
              <NavLink
                to="/provider"
                className={({ isActive }) =>
                  `px-4 py-2 rounded-md transition-colors ${
                    isActive
                      ? 'bg-indigo-800 font-semibold'
                      : 'hover:bg-indigo-600'
                  }`
                }
              >
                Submit Case
              </NavLink>
              <NavLink
                to="/director"
                className={({ isActive }) =>
                  `px-4 py-2 rounded-md transition-colors ${
                    isActive
                      ? 'bg-indigo-800 font-semibold'
                      : 'hover:bg-indigo-600'
                  }`
                }
              >
                Director Queue
              </NavLink>
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  `px-4 py-2 rounded-md transition-colors ${
                    isActive
                      ? 'bg-indigo-800 font-semibold'
                      : 'hover:bg-indigo-600'
                  }`
                }
              >
                Admin Panel
              </NavLink>
              <NavLink
                to="/sme-author"
                className={({ isActive }) =>
                  `px-4 py-2 rounded-md transition-colors ${
                    isActive
                      ? 'bg-indigo-800 font-semibold'
                      : 'hover:bg-indigo-600'
                  }`
                }
              >
                SME Authoring
              </NavLink>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="text-sm bg-indigo-600 hover:bg-indigo-500 px-4 py-2 rounded border border-indigo-500 transition-colors"
          >
            Sign Out
          </button>
        </div>
      </nav>

      <main className="py-8">
        <Outlet />
      </main>
    </div>
  );
}

function LoginRoute() {
  const navigate = useNavigate();
  return <LoginScreen onLoginSuccess={() => navigate('/provider')} />;
}

function App() {
  const handleLogout = () => {
    localStorage.removeItem('token');
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginRoute />} />

        {/* Legacy Tailwind/indigo surfaces */}
        <Route
          element={
            <RequireAuth>
              <DashboardShell />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/provider" replace />} />
          <Route path="/provider" element={<ProviderDashboard />} />
          <Route path="/director" element={<DirectorQueue />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Route>

        {/* NEW Editorial-Clinical SME-authoring surface */}
        <Route
          path="/sme-author"
          element={
            <RequireAuth>
              <SMEAuthoringLayout onLogout={handleLogout} />
            </RequireAuth>
          }
        >
          <Route index element={<SMEDashboard />} />
          <Route path="new" element={<NewCaseWizard />} />
          <Route path="sessions" element={<SessionList />} />
          <Route path="sessions/:sessionId" element={<SessionDetail />} />
          <Route path="batches" element={<BatchList />} />
          <Route path="batches/:batchId" element={<BatchDetail />} />
          <Route path="gaps" element={<GapList />} />
          <Route path="status" element={<DatasetStatus />} />
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
