/**
 * SessionList — all in-progress + completed sessions, sortable.
 *
 * Mode chips filter the table; clicking a row → SessionDetail.
 * Defaults to most-recent-first ordering by last_updated_at.
 */

import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { CaseIDPill } from '../components/CaseIDPill';
import { PageHeader } from '../components/PageHeader';
import { useSessions } from '../hooks/useSessions';
import { formatRelative, formatTimestamp } from '../lib/format';
import type { SessionMode } from '../types';

type ModeFilter = 'all' | SessionMode;
const MODE_FILTERS: { label: string; value: ModeFilter }[] = [
  { label: 'All', value: 'all' },
  { label: 'Sandbox', value: 'sandbox' },
  { label: 'Production', value: 'production' },
  { label: 'Worktree', value: 'git_worktree' },
];

export function SessionList() {
  const sessions = useSessions();
  const [filter, setFilter] = useState<ModeFilter>('all');

  const filtered = useMemo(() => {
    const list = sessions.data?.sessions ?? [];
    const sorted = list
      .slice()
      .sort(
        (a, b) =>
          new Date(b.last_updated_at).getTime() -
          new Date(a.last_updated_at).getTime(),
      );
    if (filter === 'all') return sorted;
    return sorted.filter((s) => s.mode === filter);
  }, [sessions.data, filter]);

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Discovery"
        title="Sessions"
        hint="Every authoring session — in-progress, completed, abandoned. Click any row to open the detail view."
        actions={
          <Link to="/sme-author/new" className="sme-button">
            New case
          </Link>
        }
      />

      <div
        style={{
          display: 'flex',
          gap: '0.75rem',
          marginBottom: '1.5rem',
          alignItems: 'baseline',
        }}
      >
        <span className="sme-label">Filter</span>
        {MODE_FILTERS.map((m) => {
          const isActive = filter === m.value;
          return (
            <button
              key={m.value}
              type="button"
              onClick={() => setFilter(m.value)}
              className="sme-label"
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: '0.25rem 0',
                borderBottom: `1px solid ${
                  isActive ? 'var(--sme-deep-ink)' : 'transparent'
                }`,
                color: isActive ? 'var(--sme-deep-ink)' : 'var(--sme-muted)',
                fontWeight: isActive ? 600 : 400,
                transition: 'color var(--sme-transition)',
              }}
            >
              {m.label}
            </button>
          );
        })}
      </div>

      {sessions.loading && <p className="sme-loading">loading sessions…</p>}

      {sessions.error && (
        <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
          {sessions.error}
        </p>
      )}

      {!sessions.loading && filtered.length === 0 && !sessions.error && (
        <p className="sme-empty">
          {filter === 'all'
            ? 'No sessions yet. Start by authoring a new case above.'
            : `No sessions in mode "${filter}".`}
        </p>
      )}

      {filtered.length > 0 && (
        <table className="sme-table">
          <thead>
            <tr>
              <th>Session</th>
              <th>Mode</th>
              <th>Last step</th>
              <th>Case ID</th>
              <th>Attested</th>
              <th>Updated</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr key={s.session_id}>
                <td>
                  <Link
                    to={`/sme-author/sessions/${s.session_id}`}
                    className="sme-mono"
                    style={{
                      color: 'var(--sme-deep-ink)',
                      textDecoration: 'none',
                      borderBottom: '1px solid var(--sme-rule-soft)',
                    }}
                  >
                    {s.session_id.slice(0, 8)}
                  </Link>
                </td>
                <td>
                  <span
                    className={
                      s.mode === 'production'
                        ? 'sme-label sme-status-deny'
                        : s.mode === 'git_worktree'
                          ? 'sme-label sme-status-info'
                          : 'sme-label'
                    }
                  >
                    {s.mode}
                  </span>
                </td>
                <td className="sme-table-mono">{s.last_step}</td>
                <td>
                  {s.draft ? (
                    <CaseIDPill id={s.draft.case_id} size="sm" tone="ink" />
                  ) : (
                    <span style={{ color: 'var(--sme-muted)' }}>—</span>
                  )}
                </td>
                <td
                  className="sme-label"
                  style={{
                    color: s.sme_attestation
                      ? 'var(--sme-approve)'
                      : 'var(--sme-muted)',
                  }}
                >
                  {s.sme_attestation ? '✓ yes' : '—'}
                </td>
                <td className="sme-table-mono" title={formatTimestamp(s.last_updated_at)}>
                  {formatRelative(s.last_updated_at)}
                </td>
                <td className="sme-table-mono">
                  {formatTimestamp(s.created_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
