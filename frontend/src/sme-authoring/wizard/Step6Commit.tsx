/**
 * Step 6 — Commit.
 *
 * Final review + commit. Sandbox commits go through unconditionally;
 * production commits require the explicit `confirm_production_write`
 * interlock from the backend.
 *
 * After commit, the PR template preview is the SME's hand-off
 * artifact — copy-to-clipboard for pasting into `gh pr create` or the
 * GitHub web UI.
 */

import { useState } from 'react';
import { CaseIDPill } from '../components/CaseIDPill';
import { PageHeader } from '../components/PageHeader';
import { useCommit } from '../hooks/useDrafting';
import type { WizardAction, WizardState } from './wizardState';

interface Step6Props {
  state: WizardState;
  dispatch: (action: WizardAction) => void;
}

export function Step6Commit({ state, dispatch }: Step6Props) {
  const commit = useCommit();
  const [confirmProd, setConfirmProd] = useState(false);
  const [copied, setCopied] = useState<'title' | 'body' | null>(null);

  const isProduction = state.mode === 'production';
  const productionConfirmRequired = isProduction;
  const canCommit =
    !state.inFlight.committing &&
    state.draft !== null &&
    state.attestation.trim().length >= 10 &&
    (!productionConfirmRequired || confirmProd);

  const fire = () => {
    if (!state.sessionId || !state.draft) return;
    dispatch({ type: 'COMMIT_PENDING' });
    void commit
      .run(state.sessionId, {
        sme_attestation: state.attestation,
        draft: state.draft,
        confirm_production_write: isProduction ? confirmProd : false,
      })
      .then((res) => {
        dispatch({ type: 'COMMIT_DONE', result: res });
      })
      .catch((err) => {
        dispatch({
          type: 'COMMIT_FAILED',
          error: err instanceof Error ? err.message : 'Commit failed',
        });
      });
  };

  const copyToClipboard = async (text: string, which: 'title' | 'body') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(which);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      // Older browsers; fall back to a textarea trick. For v1.1 we
      // surface the failure silently and let the SME select manually.
    }
  };

  // -------------------------------------------------------------------------
  // Post-commit state — show result + PR template preview
  // -------------------------------------------------------------------------
  if (state.commitResult) {
    const r = state.commitResult;
    return (
      <div className="sme-page-text">
        <PageHeader
          label="Complete"
          title={r.written ? 'Case committed' : 'Commit attempted'}
          actions={<CaseIDPill id={r.case_id} size="lg" />}
        />

        <div
          className="sme-card-emphasis"
          style={{
            marginBottom: '2rem',
            borderTopColor: r.written
              ? 'var(--sme-approve)'
              : 'var(--sme-deny)',
          }}
        >
          <div
            className={`sme-label ${r.written ? 'sme-status-approve' : 'sme-status-deny'}`}
          >
            {r.written ? 'Written successfully' : 'Not written'}
          </div>
          <p style={{ marginTop: '0.75rem', marginBottom: 0 }}>
            <strong>Target file:</strong>{' '}
            <code>{r.target_file}</code>
            <br />
            <strong>Integrity tests:</strong>{' '}
            <span
              className={
                r.integrity_test_passed
                  ? 'sme-status-approve'
                  : 'sme-status-deny'
              }
            >
              {r.integrity_test_passed ? 'passed' : 'failed'}
            </span>
            {r.integrity_test_summary && (
              <>
                <br />
                <span style={{ color: 'var(--sme-muted)', fontSize: '0.9375rem' }}>
                  {r.integrity_test_summary}
                </span>
              </>
            )}
          </p>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
              marginBottom: '0.5rem',
            }}
          >
            <div className="sme-label">PR title</div>
            <button
              type="button"
              className="sme-button sme-button-secondary"
              onClick={() => void copyToClipboard(r.pr_title, 'title')}
              style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}
            >
              {copied === 'title' ? '✓ copied' : 'copy'}
            </button>
          </div>
          <code
            style={{
              display: 'block',
              padding: '0.75rem',
              backgroundColor: 'var(--sme-paper-deep)',
              border: '1px solid var(--sme-rule-soft)',
              fontSize: '0.875rem',
            }}
          >
            {r.pr_title}
          </code>
        </div>

        <div style={{ marginBottom: '2rem' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'baseline',
              marginBottom: '0.5rem',
            }}
          >
            <div className="sme-label">PR body</div>
            <button
              type="button"
              className="sme-button sme-button-secondary"
              onClick={() => void copyToClipboard(r.pr_body, 'body')}
              style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}
            >
              {copied === 'body' ? '✓ copied' : 'copy'}
            </button>
          </div>
          <pre
            style={{
              padding: '1rem',
              backgroundColor: 'var(--sme-paper-deep)',
              border: '1px solid var(--sme-rule-soft)',
              fontSize: '0.8125rem',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: 'var(--sme-font-mono)',
              maxHeight: '24rem',
              overflowY: 'auto',
            }}
          >
            {r.pr_body}
          </pre>
        </div>

        <div
          style={{
            marginTop: '2.5rem',
            paddingTop: '1.5rem',
            borderTop: '1px solid var(--sme-rule-soft)',
            display: 'flex',
            justifyContent: 'space-between',
          }}
        >
          <button
            type="button"
            className="sme-button sme-button-secondary"
            onClick={() => dispatch({ type: 'RESET' })}
          >
            Author another case
          </button>
          <a href="/sme-author" className="sme-button">
            Back to dashboard
          </a>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------------
  // Pre-commit state — confirmation
  // -------------------------------------------------------------------------
  return (
    <div className="sme-page-text">
      <PageHeader
        label="Step 6 of 6"
        title="Confirm and commit"
        hint="Last check. After this, the case is written and the integrity tests run."
        actions={
          state.allocatedCaseId ? (
            <CaseIDPill id={state.allocatedCaseId} size="lg" />
          ) : undefined
        }
      />

      <div className="sme-card" style={{ marginBottom: '2rem' }}>
        <div className="sme-label">Summary</div>
        <p style={{ marginTop: '0.75rem', marginBottom: 0 }}>
          <strong>Mode:</strong>{' '}
          <span
            className={isProduction ? 'sme-status-deny' : 'sme-status-approve'}
          >
            {state.mode}
          </span>
          <br />
          <strong>Target file:</strong>{' '}
          <code>{state.recommendedFile ?? '— pending —'}</code>
          <br />
          <strong>Case ID:</strong>{' '}
          {state.allocatedCaseId ? (
            <CaseIDPill id={state.allocatedCaseId} size="sm" tone="ink" />
          ) : (
            '—'
          )}
          <br />
          <strong>Validation:</strong>{' '}
          <span className="sme-status-approve">{state.passCount} pass</span> ·{' '}
          <span className="sme-status-review">{state.warningCount} warn</span> ·{' '}
          <span className="sme-status-deny">{state.blockingCount} fail</span>
        </p>
      </div>

      {isProduction && (
        <div
          className="sme-card"
          style={{
            marginBottom: '2rem',
            borderLeft: '4px solid var(--sme-deny)',
          }}
        >
          <div className="sme-label sme-status-deny">Production write</div>
          <p style={{ marginTop: '0.5rem' }}>
            This commit writes to <code>tests/clinical/</code>, runs the
            integrity tests, and appends to the audit trail. Sandbox is the
            default for experimentation; production is irreversible without
            a follow-up commit.
          </p>
          <label
            style={{
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'baseline',
              gap: '0.5rem',
            }}
          >
            <input
              type="checkbox"
              checked={confirmProd}
              onChange={(e) => setConfirmProd(e.target.checked)}
            />
            <span>
              I confirm this case should be written to production now.
            </span>
          </label>
        </div>
      )}

      {state.error && (
        <div
          className="sme-card"
          style={{
            marginBottom: '2rem',
            borderLeft: '4px solid var(--sme-deny)',
          }}
        >
          <div className="sme-label sme-status-deny">Commit failed</div>
          <p style={{ marginTop: '0.5rem', marginBottom: 0 }}>{state.error}</p>
        </div>
      )}

      <div
        style={{
          marginTop: '2.5rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid var(--sme-rule-soft)',
          display: 'flex',
          justifyContent: 'space-between',
        }}
      >
        <button
          type="button"
          className="sme-button sme-button-secondary"
          onClick={() => dispatch({ type: 'PREV_STEP' })}
        >
          ← Back to attestation
        </button>
        <button
          type="button"
          className={`sme-button ${isProduction ? 'sme-button-deny' : 'sme-button-approve'}`}
          disabled={!canCommit}
          onClick={fire}
          style={{
            opacity: canCommit ? 1 : 0.45,
            cursor: canCommit ? 'pointer' : 'not-allowed',
          }}
        >
          {state.inFlight.committing
            ? 'Committing…'
            : isProduction
              ? 'Commit to production'
              : 'Commit to sandbox'}
        </button>
      </div>
    </div>
  );
}
