/**
 * SessionDetail — drill-down for one session.
 *
 * Shows everything the agent has captured: scenario, draft (if any),
 * last validation report, attestation, and last step reached. The
 * delete action permanently removes the session from disk.
 *
 * "Resume" intentionally surfaces a link to /sme-author/new in v1.1
 * (wizard state isn't re-hydrated from session yet — that's v1.2).
 * The session record is preserved for audit either way.
 */

import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { CaseIDPill } from '../components/CaseIDPill';
import { PageHeader } from '../components/PageHeader';
import { useDeleteSession, useSession } from '../hooks/useSessions';
import { formatRelative, formatTimestamp } from '../lib/format';
import type { ValidationReport } from '../types';

const VALIDATOR_LABELS: Record<string, string> = {
  phi_scan: 'PHI scan',
  guideline_citation: 'Guideline citation',
  schema_completeness: 'Schema completeness',
  outcome_branch_consistency: 'Outcome ↔ branch consistency',
  reasoning_specificity: 'Reasoning specificity',
  judge_criteria_specificity: 'Judge criteria specificity',
};

function outcomeClass(o: ValidationReport['outcome']) {
  if (o === 'fail') return 'sme-status-deny';
  if (o === 'warn') return 'sme-status-review';
  return 'sme-status-approve';
}

interface MetaRowProps {
  label: string;
  children: React.ReactNode;
}

function MetaRow({ label, children }: MetaRowProps) {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '180px 1fr',
        gap: '1rem',
        padding: '0.5rem 0',
        borderBottom: '1px solid var(--sme-rule-soft)',
        alignItems: 'baseline',
      }}
    >
      <div className="sme-label">{label}</div>
      <div>{children}</div>
    </div>
  );
}

export function SessionDetail() {
  const { sessionId = '' } = useParams<{ sessionId: string }>();
  const session = useSession(sessionId);
  const del = useDeleteSession();
  const navigate = useNavigate();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const data = session.data?.session;

  const handleDelete = async () => {
    try {
      await del.remove(sessionId);
      navigate('/sme-author/sessions');
    } catch {
      // Error surfaces via the hook's `error` state
    }
  };

  if (session.loading) {
    return (
      <div className="sme-page sme-page-enter sme-page-enter-active">
        <PageHeader label="Session" title="Loading…" />
        <p className="sme-loading">loading session…</p>
      </div>
    );
  }

  if (session.error || !data) {
    return (
      <div className="sme-page sme-page-enter sme-page-enter-active">
        <PageHeader
          label="Session"
          title="Not found"
          actions={
            <Link to="/sme-author/sessions" className="sme-button sme-button-secondary">
              ← Back to list
            </Link>
          }
        />
        <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
          {session.error ?? 'Session could not be loaded.'}
        </p>
      </div>
    );
  }

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Session"
        title={`Session ${data.session_id.slice(0, 8)}`}
        hint={`Last activity ${formatRelative(data.last_updated_at)} · step "${data.last_step}"`}
        actions={
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Link
              to="/sme-author/sessions"
              className="sme-button sme-button-secondary"
            >
              ← Back
            </Link>
            <Link to="/sme-author/new" className="sme-button">
              New case
            </Link>
          </div>
        }
      />

      {/* Meta */}
      <section style={{ marginBottom: '2.5rem' }}>
        <MetaRow label="Session ID">
          <code style={{ fontSize: '0.9375rem' }}>{data.session_id}</code>
        </MetaRow>
        <MetaRow label="Mode">
          <span
            className={
              data.mode === 'production'
                ? 'sme-status-deny sme-label'
                : data.mode === 'git_worktree'
                  ? 'sme-status-info sme-label'
                  : 'sme-label'
            }
          >
            {data.mode}
          </span>
        </MetaRow>
        <MetaRow label="Created">
          <span className="sme-mono" style={{ fontSize: '0.875rem' }}>
            {formatTimestamp(data.created_at)}
          </span>
        </MetaRow>
        <MetaRow label="Last updated">
          <span className="sme-mono" style={{ fontSize: '0.875rem' }}>
            {formatTimestamp(data.last_updated_at)}
          </span>
        </MetaRow>
        <MetaRow label="Last step">
          <span className="sme-table-mono">{data.last_step}</span>
        </MetaRow>
        {data.draft && (
          <MetaRow label="Allocated case ID">
            <CaseIDPill id={data.draft.case_id} size="md" tone="ink" />
          </MetaRow>
        )}
        <MetaRow label="Attestation">
          {data.sme_attestation ? (
            <span className="sme-status-approve">✓ attested</span>
          ) : (
            <span style={{ color: 'var(--sme-muted)', fontStyle: 'italic' }}>
              not attested
            </span>
          )}
        </MetaRow>
      </section>

      {/* Scenario */}
      {data.scenario && (
        <section style={{ marginBottom: '2.5rem' }}>
          <div className="sme-label" style={{ marginBottom: '0.5rem' }}>
            Scenario
          </div>
          <div className="sme-card">
            <p style={{ marginBottom: '1rem' }}>{data.scenario.description}</p>
            {(data.scenario.intended_specialty ||
              data.scenario.intended_outcome ||
              data.scenario.failure_mode_label) && (
              <div
                className="sme-mono"
                style={{
                  fontSize: '0.8125rem',
                  color: 'var(--sme-muted)',
                }}
              >
                {data.scenario.intended_specialty && (
                  <span>specialty: {data.scenario.intended_specialty}</span>
                )}
                {data.scenario.intended_outcome && (
                  <span style={{ marginLeft: '1rem' }}>
                    intended: {data.scenario.intended_outcome}
                  </span>
                )}
                {data.scenario.failure_mode_label && (
                  <span style={{ marginLeft: '1rem' }}>
                    failure-mode: {data.scenario.failure_mode_label}
                  </span>
                )}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Draft preview */}
      {data.draft && (
        <section style={{ marginBottom: '2.5rem' }}>
          <div className="sme-label" style={{ marginBottom: '0.5rem' }}>
            Draft preview
          </div>
          <div className="sme-card">
            <p style={{ marginBottom: '0.5rem' }}>
              <strong>{data.draft.title}</strong>
            </p>
            <p
              className="sme-mono"
              style={{
                fontSize: '0.8125rem',
                color: 'var(--sme-muted)',
                marginBottom: '1rem',
              }}
            >
              {data.draft.diagnosis_code} · {data.draft.procedure_code} ·{' '}
              {data.draft.expected_outcome} · {data.draft.expected_branch}
            </p>
            <div className="sme-label" style={{ fontSize: '0.6875rem' }}>
              Clinical notes
            </div>
            <p
              style={{
                marginTop: '0.25rem',
                fontSize: '0.9375rem',
                color: 'var(--sme-ink-soft)',
              }}
            >
              {data.draft.clinical_notes}
            </p>
          </div>
        </section>
      )}

      {/* Last validation report */}
      {data.last_validation_report.length > 0 && (
        <section style={{ marginBottom: '2.5rem' }}>
          <div className="sme-label" style={{ marginBottom: '0.5rem' }}>
            Last validation
          </div>
          <div style={{ borderTop: '1px solid var(--sme-rule-soft)' }}>
            {data.last_validation_report.map((r) => (
              <div
                key={r.validator}
                style={{
                  padding: '0.75rem 0',
                  borderBottom: '1px solid var(--sme-rule-soft)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'baseline',
                  gap: '1rem',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600 }}>
                    {VALIDATOR_LABELS[r.validator] ?? r.validator}
                  </div>
                  {r.reason && (
                    <div
                      style={{
                        fontSize: '0.875rem',
                        color: 'var(--sme-muted)',
                      }}
                    >
                      {r.reason}
                    </div>
                  )}
                </div>
                <div className={`sme-label ${outcomeClass(r.outcome)}`}>
                  {r.outcome}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Attestation text */}
      {data.sme_attestation && (
        <section style={{ marginBottom: '2.5rem' }}>
          <div className="sme-label" style={{ marginBottom: '0.5rem' }}>
            SME attestation
          </div>
          <div className="sme-card">
            <p style={{ marginBottom: 0 }}>{data.sme_attestation}</p>
          </div>
        </section>
      )}

      {/* Delete affordance */}
      <section
        style={{
          marginTop: '3rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid var(--sme-rule-soft)',
        }}
      >
        <div className="sme-label" style={{ marginBottom: '0.5rem' }}>
          Danger zone
        </div>
        {!confirmDelete ? (
          <button
            type="button"
            className="sme-button sme-button-secondary"
            onClick={() => setConfirmDelete(true)}
          >
            Delete session
          </button>
        ) : (
          <div className="sme-card" style={{ borderLeft: '4px solid var(--sme-deny)' }}>
            <p style={{ marginTop: 0 }}>
              This permanently removes the session record from disk. The case
              file in <code>tests/clinical/</code> or <code>sandbox/cases/</code>
              is <strong>not</strong> deleted — only the in-progress session
              metadata.
            </p>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                type="button"
                className="sme-button sme-button-deny"
                onClick={() => void handleDelete()}
                disabled={del.loading}
              >
                {del.loading ? 'Deleting…' : 'Yes, delete'}
              </button>
              <button
                type="button"
                className="sme-button sme-button-secondary"
                onClick={() => setConfirmDelete(false)}
                disabled={del.loading}
              >
                Cancel
              </button>
            </div>
            {del.error && (
              <p
                className="sme-status-deny"
                style={{ fontStyle: 'italic', marginTop: '0.75rem', marginBottom: 0 }}
              >
                {del.error}
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
