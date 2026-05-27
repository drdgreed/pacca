/**
 * AdminDashboard — provider/reviewer account provisioning.
 *
 * Reskinned in PR-UI-4 to the Editorial-Clinical aesthetic. Drops
 * the emerald brand color (the previous file's only departure from
 * the indigo palette) — the entire app now consolidates to one
 * Editorial-Clinical palette.
 *
 * PHI scrub: the previous file had a titled-full-name placeholder
 * which matched the PHI full-name regex. Replaced with neutral
 * placeholders that don't match any PHI pattern. See git history
 * for the pre-scrub content.
 *
 * Bug fix: hardcoded `http://127.0.0.1:8000` URL replaced with
 * relative `/api/v1/...` (works through Vite proxy + nginx).
 */

import { useState, type FormEvent } from 'react';
import { StatusInk, type StatusOutcome } from './StatusInk';
import { PageHeader } from '../sme-authoring/components/PageHeader';

interface ProvisionStatus {
  outcome: StatusOutcome;
  message: string;
}

export function AdminDashboard() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<ProvisionStatus | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleRegisterUser = async (e: FormEvent) => {
    e.preventDefault();
    setStatus(null);
    setSubmitting(true);

    try {
      const response = await fetch('/api/v1/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token') ?? ''}`,
        },
        body: JSON.stringify({
          username,
          password,
          email,
          full_name: fullName,
        }),
      });

      if (response.ok) {
        setStatus({
          outcome: 'approved',
          message: `Account provisioned for ${username}.`,
        });
        setUsername('');
        setPassword('');
        setFullName('');
        setEmail('');
      } else {
        const body = await response.json().catch(() => ({}));
        setStatus({
          outcome: 'denied',
          message: body.detail || `Failed to create user (HTTP ${response.status}).`,
        });
      }
    } catch {
      setStatus({
        outcome: 'denied',
        message: 'Connection error. Is the backend running on port 8000?',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit =
    !submitting &&
    username.trim().length > 0 &&
    password.trim().length > 0 &&
    fullName.trim().length > 0 &&
    email.trim().length > 0;

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Admin"
        title="System administration"
        hint="Provision new provider and reviewer accounts. Passwords are temporary; users rotate on first sign-in."
      />

      <div className="sme-page-text">
        <div className="sme-card-emphasis">
          <div className="sme-label">Create new user</div>
          <h2
            style={{
              fontSize: '1.5rem',
              marginTop: '0.5rem',
              marginBottom: '1.5rem',
            }}
          >
            Provision account
          </h2>

          {status && (
            <div
              style={{
                marginBottom: '1.5rem',
                borderLeft: `2px solid var(--sme-${
                  status.outcome === 'approved' ? 'approve' : 'deny'
                })`,
                paddingLeft: '0.75rem',
              }}
            >
              <StatusInk outcome={status.outcome}>{status.message}</StatusInk>
            </div>
          )}

          <form onSubmit={handleRegisterUser}>
            <div style={{ marginBottom: '1.25rem' }}>
              <label
                htmlFor="admin-full-name"
                className="sme-label"
                style={{ display: 'block', marginBottom: '0.5rem' }}
              >
                Full name
              </label>
              <input
                id="admin-full-name"
                type="text"
                className="sme-input"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="last, first &middot; credentials"
                disabled={submitting}
                required
              />
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label
                htmlFor="admin-email"
                className="sme-label"
                style={{ display: 'block', marginBottom: '0.5rem' }}
              >
                Email address
              </label>
              <input
                id="admin-email"
                type="email"
                className="sme-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="work email"
                disabled={submitting}
                required
              />
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <label
                htmlFor="admin-username"
                className="sme-label"
                style={{ display: 'block', marginBottom: '0.5rem' }}
              >
                Username
              </label>
              <input
                id="admin-username"
                type="text"
                className="sme-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="username"
                autoComplete="off"
                disabled={submitting}
                required
              />
            </div>

            <div style={{ marginBottom: '2rem' }}>
              <label
                htmlFor="admin-password"
                className="sme-label"
                style={{ display: 'block', marginBottom: '0.5rem' }}
              >
                Temporary password
              </label>
              <input
                id="admin-password"
                type="password"
                className="sme-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                disabled={submitting}
                required
              />
              <div
                className="sme-mono"
                style={{
                  marginTop: '0.5rem',
                  fontSize: '0.75rem',
                  color: 'var(--sme-muted)',
                }}
              >
                user will be prompted to rotate on first sign-in.
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                type="submit"
                className="sme-button"
                disabled={!canSubmit}
                style={{
                  opacity: canSubmit ? 1 : 0.6,
                  cursor: canSubmit ? 'pointer' : 'not-allowed',
                }}
              >
                {submitting ? 'Provisioning…' : 'Provision account'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
