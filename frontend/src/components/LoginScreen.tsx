/**
 * LoginScreen — pre-auth landing page.
 *
 * Editorial-Clinical aesthetic from first paint (per PR-UI-1 plan):
 *   - Cream paper background (body owns this; the form is a card)
 *   - Spectral display heading
 *   - .sme-input form fields
 *   - .sme-button primary action
 *   - Status-deny ink color for errors (no filled red banner)
 *
 * The login endpoint URL is relative (`/api/v1/login/`) so Vite's
 * dev-server proxy + production nginx both work without code changes.
 * The previous hardcoded `http://127.0.0.1:8000` URL has been removed.
 */

import { useState, type FormEvent } from 'react';

interface LoginScreenProps {
  onLoginSuccess: () => void;
}

export function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const response = await fetch('/api/v1/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        // Notify RequireAuth so any mounted guard re-checks immediately
        // (same-tab change; browser's `storage` event doesn't fire for it).
        window.dispatchEvent(new Event('pacca:auth-changed'));
        onLoginSuccess();
        return;
      }
      const body = await response.json().catch(() => ({}));
      setError(body.detail || `Sign-in failed (HTTP ${response.status})`);
    } catch {
      setError('Could not reach the server. Is the backend running on port 8000?');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main
      id="pacca-main"
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--sme-space-lg)',
      }}
    >
      <div
        className="sme-card-emphasis"
        style={{
          width: '100%',
          maxWidth: '420px',
        }}
      >
        <div className="sme-label">Sign in</div>
        <h1
          style={{
            fontSize: '2rem',
            marginTop: '0.5rem',
            marginBottom: '0.25rem',
          }}
        >
          PACCA
        </h1>
        <p
          className="sme-mono"
          style={{
            fontSize: '0.75rem',
            color: 'var(--sme-muted)',
            marginBottom: '2rem',
          }}
        >
          prior authorization &amp; care coordination agent
        </p>

        {error && (
          <p
            className="sme-status-deny"
            style={{
              fontStyle: 'italic',
              borderLeft: '2px solid var(--sme-deny)',
              paddingLeft: '0.75rem',
              marginBottom: '1.5rem',
            }}
          >
            {error}
          </p>
        )}

        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label
              htmlFor="login-username"
              className="sme-label"
              style={{ display: 'block', marginBottom: '0.5rem' }}
            >
              Username
            </label>
            <input
              id="login-username"
              type="text"
              autoComplete="username"
              className="sme-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={submitting}
            />
          </div>
          <div style={{ marginBottom: '2rem' }}>
            <label
              htmlFor="login-password"
              className="sme-label"
              style={{ display: 'block', marginBottom: '0.5rem' }}
            >
              Password
            </label>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              className="sme-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={submitting}
            />
          </div>
          <button
            type="submit"
            className="sme-button"
            style={{
              width: '100%',
              opacity: submitting ? 0.6 : 1,
              cursor: submitting ? 'not-allowed' : 'pointer',
            }}
            disabled={submitting}
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </main>
  );
}
