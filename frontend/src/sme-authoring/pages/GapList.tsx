/**
 * GapList — full prioritized coverage-gap list.
 *
 * Reads from gap_analyzer's parse of docs/EVALUATION_COVERAGE.md.
 * Higher priority sorts earlier; ties broken by larger `cases_needed`.
 *
 * "Author from this gap" pre-fills the wizard's failure_mode_label
 * hint via URL params — but the wizard's URL-state restoration is v1.2.
 * In v1.1 the affordance is a plain link to /sme-author/new.
 */

import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { ProgressBar } from '../components/ProgressBar';
import { useGaps } from '../hooks/useStatus';

export function GapList() {
  const gaps = useGaps();

  const sorted = useMemo(() => {
    const list = gaps.data?.gaps ?? [];
    return list.slice().sort((a, b) => {
      if (a.priority !== b.priority) return b.priority - a.priority;
      return b.cases_needed - a.cases_needed;
    });
  }, [gaps.data]);

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Discovery"
        title="Priority gaps"
        hint="Coverage gaps the agent has identified from EVALUATION_COVERAGE.md. Sorted by priority then by cases needed."
        actions={
          <Link to="/sme-author/new" className="sme-button">
            Author from a gap
          </Link>
        }
      />

      {gaps.loading && <p className="sme-loading">loading gaps…</p>}

      {gaps.error && (
        <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
          {gaps.error}
        </p>
      )}

      {!gaps.loading && sorted.length === 0 && !gaps.error && (
        <p className="sme-empty">
          No prioritized gaps identified — coverage analyzer reports a
          balanced dataset.
        </p>
      )}

      {sorted.length > 0 && (
        <div style={{ borderTop: '1px solid var(--sme-rule-soft)' }}>
          {sorted.map((g, idx) => {
            const tone =
              g.priority >= 8
                ? 'deny'
                : g.priority >= 5
                  ? 'review'
                  : 'ink';
            return (
              <div
                key={`${g.category}-${g.label}-${idx}`}
                style={{
                  padding: '1.25rem 0',
                  borderBottom: '1px solid var(--sme-rule-soft)',
                  display: 'grid',
                  gridTemplateColumns: '4rem 1fr 8rem',
                  gap: '1rem',
                  alignItems: 'baseline',
                }}
              >
                <div
                  className="sme-mono"
                  style={{
                    fontSize: '1.5rem',
                    fontWeight: 500,
                    color: 'var(--sme-deep-ink)',
                    fontVariantNumeric: 'tabular-nums',
                  }}
                  title={`Priority ${g.priority}`}
                >
                  {g.priority}
                </div>
                <div>
                  <div
                    style={{
                      fontFamily: 'var(--sme-font-display)',
                      fontWeight: 600,
                      fontSize: '1.0625rem',
                      color: 'var(--sme-deep-ink)',
                    }}
                  >
                    {g.label}
                  </div>
                  <div
                    className="sme-mono"
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--sme-muted)',
                      marginTop: '0.25rem',
                    }}
                  >
                    {g.category}
                  </div>
                  {g.description && (
                    <p
                      style={{
                        marginTop: '0.5rem',
                        marginBottom: 0,
                        color: 'var(--sme-muted)',
                        fontSize: '0.9375rem',
                      }}
                    >
                      {g.description}
                    </p>
                  )}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div
                    className="sme-mono"
                    style={{
                      fontSize: '0.875rem',
                      color: 'var(--sme-muted)',
                      fontVariantNumeric: 'tabular-nums',
                      marginBottom: '0.5rem',
                    }}
                  >
                    {g.current_count} / {g.target_count}
                  </div>
                  <ProgressBar
                    current={g.current_count}
                    target={Math.max(1, g.target_count)}
                    tone={tone}
                  />
                  <div
                    className="sme-label"
                    style={{
                      marginTop: '0.5rem',
                      fontSize: '0.6875rem',
                      color:
                        g.cases_needed > 0
                          ? 'var(--sme-deep-ink)'
                          : 'var(--sme-muted)',
                    }}
                  >
                    {g.cases_needed > 0
                      ? `${g.cases_needed} needed`
                      : 'satisfied'}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
