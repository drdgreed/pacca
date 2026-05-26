/**
 * SME Case Authoring — Dashboard
 *
 * The landing page when a clinician opens /sme-author. Surfaces:
 *   • Dataset snapshot (total cases, per-list counts)
 *   • Recent sessions in progress
 *   • Top-priority coverage gaps
 *   • Primary CTA: start a new case
 *
 * Design discipline:
 *   - Editorial column for the drop-cap intro
 *   - Wide column for tables / lists
 *   - Hairline rules separate sections
 *   - Small-caps labels precede each section
 *   - Monospace for IDs, timestamps, counts
 *
 * No loaded data → graceful empty states with editorial italic message.
 * Loading states use the monospace .sme-loading class to feel like a
 * status readout, not a spinner.
 */

import { Link } from 'react-router-dom';
import { CaseIDPill } from '../components/CaseIDPill';
import { PageHeader } from '../components/PageHeader';
import { useSessions } from '../hooks/useSessions';
import { useGaps, useStatus } from '../hooks/useStatus';

function formatTimestamp(iso: string): string {
  try {
    const d = new Date(iso);
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, '0');
    const dd = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mins = String(d.getMinutes()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd} ${hh}:${mins}`;
  } catch {
    return iso;
  }
}

export function Dashboard() {
  const status = useStatus();
  const sessions = useSessions();
  const gaps = useGaps();

  const totalCases = status.data?.total_cases ?? null;
  const recentSessions = (sessions.data?.sessions ?? [])
    .slice()
    .sort(
      (a, b) =>
        new Date(b.last_updated_at).getTime() -
        new Date(a.last_updated_at).getTime(),
    )
    .slice(0, 5);
  const topGaps = (gaps.data?.gaps ?? []).slice(0, 5);

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Dashboard"
        title="SME Case Authoring"
        hint="Author golden test cases. Plain English in; validated, audit-ready cases out."
        actions={
          <Link to="/sme-author/new" className="sme-button">
            Author new case
          </Link>
        }
      />

      <section style={{ marginBottom: '3rem' }}>
        <div className="sme-page-text">
          <p className="sme-drop-cap">
            The case dataset is the substrate every PACCA evaluation runs
            against. Each case you author becomes part of the audit trail
            for every iteration that follows. Take the time the work
            deserves; the tooling will catch the small things so you can
            focus on the clinical truth.
          </p>
        </div>
      </section>

      {/* ----------------------------------------------------------------- */}
      <section style={{ marginBottom: '3rem' }}>
        <div className="sme-label">Dataset state</div>
        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: '1rem',
            marginTop: '0.5rem',
            marginBottom: '1.5rem',
          }}
        >
          <span
            className="sme-mono"
            style={{
              fontSize: '3.5rem',
              fontWeight: 500,
              color: 'var(--sme-deep-ink)',
              lineHeight: 1,
              fontVariantNumeric: 'tabular-nums',
            }}
          >
            {status.loading
              ? '…'
              : totalCases !== null
                ? String(totalCases)
                : '—'}
          </span>
          <span className="sme-label">golden cases catalogued</span>
        </div>

        {status.error && (
          <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
            {status.error}
          </p>
        )}

        {status.data && status.data.per_list_counts.length > 0 && (
          <table className="sme-table">
            <thead>
              <tr>
                <th>List</th>
                <th>File</th>
                <th style={{ textAlign: 'right' }}>Count</th>
                <th>ID range</th>
              </tr>
            </thead>
            <tbody>
              {status.data.per_list_counts.map((row) => (
                <tr key={row.list_name}>
                  <td>{row.list_name}</td>
                  <td className="sme-table-mono">{row.file}</td>
                  <td
                    className="sme-table-mono"
                    style={{ textAlign: 'right' }}
                  >
                    {row.count}
                  </td>
                  <td className="sme-table-mono">{row.id_range}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <hr className="sme-rule" />

      {/* ----------------------------------------------------------------- */}
      <section style={{ marginBottom: '3rem' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            marginBottom: '1rem',
          }}
        >
          <div className="sme-label">Recent sessions</div>
          <Link
            to="/sme-author/sessions"
            className="sme-mono"
            style={{
              fontSize: '0.75rem',
              color: 'var(--sme-muted)',
              textDecoration: 'none',
            }}
          >
            view all →
          </Link>
        </div>

        {sessions.loading && (
          <p className="sme-loading">loading sessions…</p>
        )}

        {!sessions.loading && recentSessions.length === 0 && (
          <p className="sme-empty">
            No sessions yet. Start by authoring a new case above.
          </p>
        )}

        {recentSessions.length > 0 && (
          <table className="sme-table">
            <thead>
              <tr>
                <th>Session</th>
                <th>Mode</th>
                <th>Last step</th>
                <th>Case ID</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {recentSessions.map((s) => (
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
                          ? 'sme-status-deny sme-label'
                          : 'sme-label'
                      }
                    >
                      {s.mode}
                    </span>
                  </td>
                  <td className="sme-table-mono">{s.last_step}</td>
                  <td>
                    {s.draft ? <CaseIDPill id={s.draft.case_id} size="sm" /> : '—'}
                  </td>
                  <td className="sme-table-mono">
                    {formatTimestamp(s.last_updated_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <hr className="sme-rule" />

      {/* ----------------------------------------------------------------- */}
      <section>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'baseline',
            marginBottom: '1rem',
          }}
        >
          <div className="sme-label">Priority gaps</div>
          <Link
            to="/sme-author/gaps"
            className="sme-mono"
            style={{
              fontSize: '0.75rem',
              color: 'var(--sme-muted)',
              textDecoration: 'none',
            }}
          >
            view all →
          </Link>
        </div>

        {gaps.loading && <p className="sme-loading">loading gap analysis…</p>}

        {!gaps.loading && topGaps.length === 0 && !gaps.error && (
          <p className="sme-empty">
            No prioritized gaps identified — coverage analyzer reports a
            balanced dataset.
          </p>
        )}

        {gaps.error && (
          <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
            {gaps.error}
          </p>
        )}

        {topGaps.length > 0 && (
          <ol
            style={{
              paddingLeft: '1.5rem',
              maxWidth: 'var(--sme-col-text)',
            }}
          >
            {topGaps.map((g) => (
              <li key={`${g.category}-${g.label}`} style={{ marginBottom: '1rem' }}>
                <div>
                  <span style={{ fontWeight: 600, color: 'var(--sme-deep-ink)' }}>
                    {g.label}
                  </span>{' '}
                  <span className="sme-mono" style={{ color: 'var(--sme-muted)', fontSize: '0.875rem' }}>
                    ({g.current_count}/{g.target_count}; needs {g.cases_needed})
                  </span>
                </div>
                {g.description && (
                  <div
                    style={{
                      color: 'var(--sme-muted)',
                      fontSize: '0.95rem',
                      marginTop: '0.25rem',
                    }}
                  >
                    {g.description}
                  </div>
                )}
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
