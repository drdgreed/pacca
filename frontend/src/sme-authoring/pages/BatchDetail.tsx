/**
 * BatchDetail — one roadmap batch's case-slot manifest.
 *
 * Shows the planned cases in the batch (case_id + description) plus
 * the routing target. Each row is just informational in v1.1; v1.2
 * could add a "draft this slot" affordance that pre-fills the wizard
 * with the slot's description as the scenario hint.
 */

import { Link, useParams } from 'react-router-dom';
import { CaseIDPill } from '../components/CaseIDPill';
import { PageHeader } from '../components/PageHeader';
import { ProgressBar } from '../components/ProgressBar';
import { useBatch } from '../hooks/useStatus';

export function BatchDetail() {
  const { batchId = '' } = useParams<{ batchId: string }>();
  const batch = useBatch(batchId);

  if (batch.loading) {
    return (
      <div className="sme-page sme-page-enter sme-page-enter-active">
        <PageHeader label="Batch" title="Loading…" />
        <p className="sme-loading">loading batch…</p>
      </div>
    );
  }

  if (batch.error || !batch.data) {
    return (
      <div className="sme-page sme-page-enter sme-page-enter-active">
        <PageHeader
          label="Batch"
          title="Not found"
          actions={
            <Link
              to="/sme-author/batches"
              className="sme-button sme-button-secondary"
            >
              ← Back to list
            </Link>
          }
        />
        <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
          {batch.error ?? 'Batch could not be loaded.'}
        </p>
      </div>
    );
  }

  const b = batch.data.batch;
  const filed = b.cases.length;
  const target = b.case_count;
  const tone =
    filed >= target ? 'approve' : filed === 0 ? 'ink' : 'review';

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Batch"
        title={b.name}
        hint={`${b.batch_id} · ${b.id_range}`}
        actions={
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Link
              to="/sme-author/batches"
              className="sme-button sme-button-secondary"
            >
              ← Back
            </Link>
            <Link to="/sme-author/new" className="sme-button">
              Draft a case
            </Link>
          </div>
        }
      />

      <section style={{ marginBottom: '2.5rem' }}>
        <div
          style={{
            display: 'flex',
            gap: '3rem',
            alignItems: 'baseline',
            marginBottom: '1rem',
          }}
        >
          <div>
            <div className="sme-label">Progress</div>
            <div
              className="sme-mono"
              style={{
                fontSize: '2.5rem',
                color: 'var(--sme-deep-ink)',
                fontVariantNumeric: 'tabular-nums',
                lineHeight: 1,
              }}
            >
              {filed} <span style={{ color: 'var(--sme-muted)' }}>/ {target}</span>
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <ProgressBar current={filed} target={Math.max(1, target)} tone={tone} />
          </div>
        </div>
        <div
          className="sme-mono"
          style={{ fontSize: '0.875rem', color: 'var(--sme-muted)' }}
        >
          target file: <code>{b.target_file}</code>
          {b.is_new_file && (
            <span className="sme-label sme-status-info" style={{ marginLeft: '1rem' }}>
              new file
            </span>
          )}
        </div>
      </section>

      <hr className="sme-rule" />

      <section>
        <div className="sme-label" style={{ marginBottom: '1rem' }}>
          Case manifest
        </div>

        {b.cases.length === 0 && (
          <p className="sme-empty">
            No cases drafted for this batch yet. Start with the first slot.
          </p>
        )}

        {b.cases.length > 0 && (
          <table className="sme-table">
            <thead>
              <tr>
                <th>Slot</th>
                <th>Case ID</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {b.cases.map((c, idx) => (
                <tr key={c.case_id}>
                  <td
                    className="sme-mono"
                    style={{
                      fontSize: '0.875rem',
                      color: 'var(--sme-muted)',
                      width: '4rem',
                    }}
                  >
                    {String(idx + 1).padStart(2, '0')}
                  </td>
                  <td>
                    <CaseIDPill id={c.case_id} size="sm" tone="ink" />
                  </td>
                  <td>{c.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
