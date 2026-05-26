/**
 * Step 4 — Validators.
 *
 * Auto-runs validation on first mount (and whenever the draft has
 * changed since the last run). Shows the 6 deterministic validators'
 * reports as a hairline-separated list. Blocking failures gate the
 * "Continue to attestation" button.
 *
 * Outcomes use ink color, not filled badges:
 *   - pass → muted (default)
 *   - warn → mustard (sme-status-review)
 *   - fail → oxblood (sme-status-deny)
 */

import { useEffect, useRef } from 'react';
import { PageHeader } from '../components/PageHeader';
import { useValidate } from '../hooks/useDrafting';
import type { ValidationReport } from '../types';
import type { WizardAction, WizardState } from './wizardState';

interface Step4Props {
  state: WizardState;
  dispatch: (action: WizardAction) => void;
}

const VALIDATOR_LABELS: Record<string, string> = {
  phi_scan: 'PHI scan',
  guideline_citation: 'Guideline citation',
  schema_completeness: 'Schema completeness',
  outcome_branch_consistency: 'Outcome ↔ branch consistency',
  reasoning_specificity: 'Reasoning specificity',
  judge_criteria_specificity: 'Judge criteria specificity',
};

function ValidatorRow({ report }: { report: ValidationReport }) {
  const toneClass =
    report.outcome === 'fail'
      ? 'sme-status-deny'
      : report.outcome === 'warn'
        ? 'sme-status-review'
        : 'sme-status-approve';

  return (
    <div
      style={{
        padding: '1rem 0',
        borderTop: '1px solid var(--sme-rule-soft)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'baseline',
          gap: '1rem',
        }}
      >
        <div style={{ fontWeight: 600 }}>
          {VALIDATOR_LABELS[report.validator] ?? report.validator}
        </div>
        <div
          className={`sme-label ${toneClass}`}
          style={{ fontSize: '0.8125rem' }}
        >
          {report.outcome}
        </div>
      </div>
      {report.reason && (
        <p
          style={{
            marginTop: '0.5rem',
            marginBottom: 0,
            color: 'var(--sme-muted)',
            fontSize: '0.9375rem',
          }}
        >
          {report.reason}
        </p>
      )}
      {report.field_path && (
        <p
          className="sme-mono"
          style={{
            marginTop: '0.25rem',
            marginBottom: 0,
            fontSize: '0.75rem',
            color: 'var(--sme-muted)',
          }}
        >
          {report.field_path}
        </p>
      )}
    </div>
  );
}

export function Step4Validators({ state, dispatch }: Step4Props) {
  const validate = useValidate();
  const didFetch = useRef(false);

  // Auto-run validation when this step mounts (or when validation
  // was invalidated by a draft edit and we have a draft).
  useEffect(() => {
    if (didFetch.current) return;
    if (!state.sessionId) return;
    if (!state.draft) return;
    if (state.validation.length > 0) return;
    didFetch.current = true;

    dispatch({ type: 'VALIDATE_PENDING' });
    void validate
      .run(state.sessionId, { draft: state.draft })
      .then((res) => {
        dispatch({
          type: 'VALIDATE_DONE',
          reports: res.reports,
          blockingCount: res.blocking_count,
          warningCount: res.warning_count,
          passCount: res.pass_count,
        });
      })
      .catch((err) => {
        dispatch({
          type: 'VALIDATE_FAILED',
          error: err instanceof Error ? err.message : 'Validation failed',
        });
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.sessionId, state.draft, state.validation.length]);

  const rerun = () => {
    if (!state.sessionId || !state.draft) return;
    didFetch.current = false;
    // Reset the existing reports so the effect re-fires
    dispatch({ type: 'VALIDATE_PENDING' });
    void validate
      .run(state.sessionId, { draft: state.draft })
      .then((res) => {
        dispatch({
          type: 'VALIDATE_DONE',
          reports: res.reports,
          blockingCount: res.blocking_count,
          warningCount: res.warning_count,
          passCount: res.pass_count,
        });
      })
      .catch((err) => {
        dispatch({
          type: 'VALIDATE_FAILED',
          error: err instanceof Error ? err.message : 'Validation failed',
        });
      });
  };

  const blocked = state.blockingCount > 0;
  const canContinue =
    state.validation.length > 0 && !blocked && !state.inFlight.validating;

  return (
    <div className="sme-page-text">
      <PageHeader
        label="Step 4 of 6"
        title="Validation"
        hint="Six deterministic checks run against the draft. Pass all to continue; fix any blocking failures and step back to revise."
      />

      <div
        style={{
          display: 'flex',
          gap: '2rem',
          marginBottom: '1.5rem',
        }}
      >
        <div>
          <div className="sme-label">Pass</div>
          <div
            className="sme-mono sme-status-approve"
            style={{ fontSize: '1.875rem', fontVariantNumeric: 'tabular-nums' }}
          >
            {state.passCount}
          </div>
        </div>
        <div>
          <div className="sme-label">Warn</div>
          <div
            className="sme-mono sme-status-review"
            style={{ fontSize: '1.875rem', fontVariantNumeric: 'tabular-nums' }}
          >
            {state.warningCount}
          </div>
        </div>
        <div>
          <div className="sme-label">Fail</div>
          <div
            className="sme-mono sme-status-deny"
            style={{ fontSize: '1.875rem', fontVariantNumeric: 'tabular-nums' }}
          >
            {state.blockingCount}
          </div>
        </div>
      </div>

      {state.inFlight.validating && (
        <p className="sme-loading">running validators…</p>
      )}

      {state.error && (
        <div
          className="sme-card"
          style={{
            borderLeft: '4px solid var(--sme-deny)',
            marginBottom: '1.5rem',
          }}
        >
          <div className="sme-label sme-status-deny">Validation error</div>
          <p style={{ marginTop: '0.5rem', marginBottom: '0.75rem' }}>
            {state.error}
          </p>
          <button
            type="button"
            className="sme-button sme-button-secondary"
            onClick={rerun}
          >
            Retry
          </button>
        </div>
      )}

      {state.validation.length > 0 && (
        <div style={{ borderBottom: '1px solid var(--sme-rule-soft)' }}>
          {state.validation.map((r) => (
            <ValidatorRow key={r.validator} report={r} />
          ))}
        </div>
      )}

      {blocked && (
        <div
          className="sme-card"
          style={{
            marginTop: '1.5rem',
            borderLeft: '4px solid var(--sme-deny)',
          }}
        >
          <div className="sme-label sme-status-deny">Blocked</div>
          <p style={{ marginTop: '0.5rem', marginBottom: 0 }}>
            {state.blockingCount} blocking{' '}
            {state.blockingCount === 1 ? 'failure' : 'failures'}. Step back
            to revise the affected fields, then return to re-run validation.
          </p>
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
          ← Back to review
        </button>
        <button
          type="button"
          className="sme-button"
          disabled={!canContinue}
          onClick={() => dispatch({ type: 'NEXT_STEP' })}
          style={{
            opacity: canContinue ? 1 : 0.45,
            cursor: canContinue ? 'pointer' : 'not-allowed',
          }}
        >
          Continue to attestation →
        </button>
      </div>
    </div>
  );
}
