/**
 * DatasetStatus — full dataset snapshot.
 *
 * The Dashboard shows a 3-section summary (total, per-list, top 5
 * gaps). This page is the canonical detail surface: every per-list
 * file, every milestone gap, and a callout for coverage-parse errors
 * that the agent encountered.
 */

import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { ProgressBar } from '../components/ProgressBar';
import { useStatus } from '../hooks/useStatus';

// PACCA milestone targets per DATASET_GROWTH_ROADMAP.md
const MILESTONES = [
  { label: 'Production-pilot', target: 100, note: 'Sufficient for narrow-payer pilots' },
  { label: 'General-payer', target: 300, note: 'Hits per-cell CI requirements' },
  { label: 'SaMD-grade', target: 500, note: 'FDA-submission ready' },
];

export function DatasetStatus() {
  const status = useStatus();
  const total = status.data?.total_cases ?? 0;

  const milestoneProgress = useMemo(
    () =>
      MILESTONES.map((m) => ({
        ...m,
        ratio: Math.min(1, total / m.target),
        remaining: Math.max(0, m.target - total),
        hit: total >= m.target,
      })),
    [total],
  );

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Discovery"
        title="Dataset state"
        hint="Where the case dataset stands today, with every per-file count and every prioritized gap."
        actions={
          <Link
            to="/sme-author"
            className="sme-button sme-button-secondary"
          >
            ← Dashboard
          </Link>
        }
      />

      {status.loading && <p className="sme-loading">loading status…</p>}

      {status.error && (
        <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
          {status.error}
        </p>
      )}

      {status.data && (
        <>
          {/* Headline counter */}
          <section style={{ marginBottom: '2.5rem' }}>
            <div className="sme-label">Total catalogued</div>
            <div
              className="sme-mono"
              style={{
                fontSize: '4.5rem',
                lineHeight: 1,
                color: 'var(--sme-deep-ink)',
                fontVariantNumeric: 'tabular-nums',
                marginTop: '0.5rem',
              }}
            >
              {total}
            </div>
          </section>

          <hr className="sme-rule" />

          {/* Milestones */}
          <section style={{ marginBottom: '2.5rem' }}>
            <div className="sme-label" style={{ marginBottom: '1rem' }}>
              Milestone progress
            </div>
            <div>
              {milestoneProgress.map((m) => (
                <div
                  key={m.label}
                  style={{
                    padding: '1rem 0',
                    borderBottom: '1px solid var(--sme-rule-soft)',
                    display: 'grid',
                    gridTemplateColumns: '12rem 1fr 8rem',
                    gap: '1rem',
                    alignItems: 'baseline',
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontFamily: 'var(--sme-font-display)',
                        fontWeight: 600,
                        color: 'var(--sme-deep-ink)',
                      }}
                    >
                      {m.label}
                    </div>
                    <div
                      style={{
                        fontSize: '0.8125rem',
                        color: 'var(--sme-muted)',
                        marginTop: '0.125rem',
                      }}
                    >
                      {m.note}
                    </div>
                  </div>
                  <ProgressBar
                    current={total}
                    target={m.target}
                    tone={m.hit ? 'approve' : 'ink'}
                  />
                  <div
                    className="sme-mono"
                    style={{
                      textAlign: 'right',
                      color: m.hit
                        ? 'var(--sme-approve)'
                        : 'var(--sme-muted)',
                      fontVariantNumeric: 'tabular-nums',
                      fontSize: '0.875rem',
                    }}
                  >
                    {m.hit
                      ? `✓ hit (${total} of ${m.target})`
                      : `${m.remaining} to go`}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <hr className="sme-rule" />

          {/* Per-file counts */}
          <section style={{ marginBottom: '2.5rem' }}>
            <div className="sme-label" style={{ marginBottom: '1rem' }}>
              Per-file counts
            </div>
            {status.data.per_list_counts.length === 0 ? (
              <p className="sme-empty">No case files registered.</p>
            ) : (
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

          {/* All milestone gaps (link to GapList for detail) */}
          <section style={{ marginBottom: '2.5rem' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                marginBottom: '1rem',
              }}
            >
              <div className="sme-label">Milestone gaps</div>
              <Link
                to="/sme-author/gaps"
                className="sme-mono"
                style={{
                  fontSize: '0.75rem',
                  color: 'var(--sme-muted)',
                  textDecoration: 'none',
                }}
              >
                detailed view →
              </Link>
            </div>
            {status.data.milestone_gaps.length === 0 ? (
              <p className="sme-empty">No active milestone gaps.</p>
            ) : (
              <ul style={{ paddingLeft: '1.5rem' }}>
                {status.data.milestone_gaps.map((g, idx) => (
                  <li key={`${g.label}-${idx}`} style={{ marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 600 }}>{g.label}</span>{' '}
                    <span
                      className="sme-mono"
                      style={{ color: 'var(--sme-muted)', fontSize: '0.875rem' }}
                    >
                      ({g.current_count}/{g.target_count}; priority {g.priority})
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Coverage parse health */}
          {!status.data.coverage_parsed_ok && (
            <section>
              <div
                className="sme-card"
                style={{
                  borderLeft: '4px solid var(--sme-review)',
                }}
              >
                <div className="sme-label sme-status-review">Coverage parse warning</div>
                <p style={{ marginTop: '0.5rem', marginBottom: 0 }}>
                  {status.data.coverage_parse_error ||
                    'EVALUATION_COVERAGE.md could not be fully parsed. Some gap data may be missing.'}
                </p>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
