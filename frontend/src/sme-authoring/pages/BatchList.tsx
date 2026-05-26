/**
 * BatchList — DATASET_GROWTH_ROADMAP batches with progress bars.
 *
 * Each row is one batch (e.g. "Batch Q — geriatric polypharmacy").
 * The progress reads from the per-list count in the underlying batch
 * spec; an empty/zero batch shows a thin rule, a full batch shows a
 * fully-inked one.
 */

import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { ProgressBar } from '../components/ProgressBar';
import { useBatches } from '../hooks/useStatus';

export function BatchList() {
  const batches = useBatches();

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Discovery"
        title="Roadmap batches"
        hint="Each batch is a planned cluster of related cases from DATASET_GROWTH_ROADMAP.md. Click a batch to see its manifest."
      />

      {batches.loading && <p className="sme-loading">loading batches…</p>}

      {batches.error && (
        <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
          {batches.error}
        </p>
      )}

      {!batches.loading &&
        (batches.data?.batches.length ?? 0) === 0 &&
        !batches.error && (
          <p className="sme-empty">
            No batches parsed from the roadmap. Check{' '}
            <code>docs/DATASET_GROWTH_ROADMAP.md</code> § 2 for format.
          </p>
        )}

      {(batches.data?.batches.length ?? 0) > 0 && (
        <div style={{ borderTop: '1px solid var(--sme-rule-soft)' }}>
          {batches.data?.batches.map((b) => {
            const filed = b.cases.length;
            const target = b.case_count;
            const tone =
              filed >= target
                ? 'approve'
                : filed === 0
                  ? 'ink'
                  : 'review';
            return (
              <Link
                key={b.batch_id}
                to={`/sme-author/batches/${encodeURIComponent(b.batch_id)}`}
                style={{
                  display: 'block',
                  textDecoration: 'none',
                  color: 'inherit',
                  padding: '1.25rem 0',
                  borderBottom: '1px solid var(--sme-rule-soft)',
                  transition: 'background-color var(--sme-transition)',
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.backgroundColor =
                    'var(--sme-paper-deep)')
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.backgroundColor = 'transparent')
                }
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'baseline',
                    marginBottom: '0.5rem',
                  }}
                >
                  <div>
                    <span
                      className="sme-mono"
                      style={{
                        fontSize: '0.875rem',
                        color: 'var(--sme-muted)',
                        marginRight: '0.75rem',
                      }}
                    >
                      {b.batch_id}
                    </span>
                    <span
                      style={{
                        fontFamily: 'var(--sme-font-display)',
                        fontWeight: 600,
                        fontSize: '1.125rem',
                        color: 'var(--sme-deep-ink)',
                      }}
                    >
                      {b.name}
                    </span>
                    {b.is_new_file && (
                      <span
                        className="sme-label sme-status-info"
                        style={{ marginLeft: '0.75rem', fontSize: '0.6875rem' }}
                      >
                        new file
                      </span>
                    )}
                  </div>
                  <span
                    className="sme-mono"
                    style={{
                      fontSize: '0.875rem',
                      color: 'var(--sme-muted)',
                      fontVariantNumeric: 'tabular-nums',
                    }}
                  >
                    {filed} / {target}
                  </span>
                </div>
                <div
                  className="sme-mono"
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--sme-muted)',
                    marginBottom: '0.75rem',
                  }}
                >
                  {b.id_range} → {b.target_file}
                </div>
                <ProgressBar
                  current={filed}
                  target={Math.max(1, target)}
                  tone={tone}
                />
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
