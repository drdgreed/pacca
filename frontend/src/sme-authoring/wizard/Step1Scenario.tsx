/**
 * Step 1 — Scenario.
 *
 * The SME types a plain-English clinical scenario (1-3 sentences). They
 * may optionally hint specialty + intended outcome + failure mode to
 * bias the LLM draft.
 *
 * They also choose the mode:
 *   - sandbox     — drafts go to sandbox/cases/ (safe default)
 *   - production  — drafts commit to tests/clinical/ after attestation
 *
 * Client-side PHI scan runs on the textarea contents BEFORE the SME
 * proceeds. A detection blocks the "Continue" button until acknowledged.
 */

import { useMemo, useState } from 'react';
import { PageHeader } from '../components/PageHeader';
import { scanForPhiClient } from './phiClientScan';
import type { WizardAction, WizardState } from './wizardState';

interface Step1Props {
  state: WizardState;
  dispatch: (action: WizardAction) => void;
  /** Triggers the createSession + transition to step 2. */
  onSubmit: () => void | Promise<void>;
}

const SPECIALTY_OPTIONS = [
  'Oncology',
  'Cardiology',
  'Dermatology',
  'Rheumatology',
  'Endocrinology',
  'Pulmonology',
  'Gastroenterology',
  'Neurology',
  'Pediatrics',
  'Geriatrics',
];

const OUTCOME_OPTIONS = [
  { value: 'AUTO_APPROVED', label: 'Auto-approved' },
  { value: 'IN_REVIEW', label: 'In review' },
  { value: 'DENIED', label: 'Denied' },
  { value: 'PRE_FLIGHT_ESCALATE', label: 'Pre-flight escalate' },
  { value: 'INFORMATION_NEEDED', label: 'Information needed' },
] as const;

export function Step1Scenario({ state, dispatch, onSubmit }: Step1Props) {
  const [acknowledgedPhi, setAcknowledgedPhi] = useState(false);
  const description = state.scenario.description;

  const phiHits = useMemo(
    () => scanForPhiClient(description),
    [description],
  );

  const minLengthMet = description.trim().length >= 20;
  const phiBlocking = phiHits.length > 0 && !acknowledgedPhi;
  const canContinue =
    minLengthMet && !phiBlocking && !state.inFlight.creatingSession;

  const handleField = (field: 'description' | 'intended_specialty' | 'intended_outcome' | 'failure_mode_label') =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const raw = e.target.value;
      const value = field === 'description' ? raw : (raw === '' ? null : raw);
      dispatch({
        type: 'SET_SCENARIO_FIELD',
        field,
        value,
      });
      // PHI re-check resets the ack on every keystroke
      if (field === 'description') setAcknowledgedPhi(false);
    };

  return (
    <div className="sme-page-text">
      <PageHeader
        label="Step 1 of 6"
        title="Describe the clinical scenario"
        hint="One to three sentences. The agent uses this as input; the SME (you) reviews everything it generates."
      />

      {/* Mode banner */}
      <div
        className="sme-card-emphasis"
        style={{
          marginBottom: '2rem',
          borderTopColor:
            state.mode === 'production'
              ? 'var(--sme-deny)'
              : 'var(--sme-deep-ink)',
        }}
      >
        <div className="sme-label">Authoring mode</div>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '1rem' }}>
          <label
            style={{
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'baseline',
              gap: '0.5rem',
            }}
          >
            <input
              type="radio"
              name="mode"
              value="sandbox"
              checked={state.mode === 'sandbox'}
              onChange={() => dispatch({ type: 'SET_MODE', mode: 'sandbox' })}
            />
            <span>
              <strong>Sandbox</strong>{' '}
              <span style={{ color: 'var(--sme-muted)' }}>
                — drafts go to <code>sandbox/cases/</code>; nothing touches production
              </span>
            </span>
          </label>
          <label
            style={{
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'baseline',
              gap: '0.5rem',
            }}
          >
            <input
              type="radio"
              name="mode"
              value="production"
              checked={state.mode === 'production'}
              onChange={() =>
                dispatch({ type: 'SET_MODE', mode: 'production' })
              }
            />
            <span>
              <strong className="sme-status-deny">Production</strong>{' '}
              <span style={{ color: 'var(--sme-muted)' }}>
                — commits to <code>tests/clinical/</code> after attestation
              </span>
            </span>
          </label>
        </div>
      </div>

      {/* Scenario textarea */}
      <div style={{ marginBottom: '2rem' }}>
        <label
          htmlFor="scenario-description"
          className="sme-label"
          style={{ display: 'block', marginBottom: '0.5rem' }}
        >
          Scenario
        </label>
        <textarea
          id="scenario-description"
          value={description}
          onChange={handleField('description')}
          placeholder="e.g. 65yo male with stage IV NSCLC, PD-L1 70%, no EGFR/ALK mutations, requesting first-line pembrolizumab."
          rows={5}
          style={{
            width: '100%',
            fontFamily: 'var(--sme-font-body)',
            fontSize: '1.0625rem',
            padding: '1rem',
            backgroundColor: 'var(--sme-paper)',
            border: '1px solid var(--sme-rule-soft)',
            borderTop: '2px solid var(--sme-rule)',
            color: 'var(--sme-ink)',
            lineHeight: 1.5,
            resize: 'vertical',
          }}
        />
        <div
          className="sme-mono"
          style={{
            marginTop: '0.5rem',
            fontSize: '0.75rem',
            color: minLengthMet ? 'var(--sme-muted)' : 'var(--sme-deny)',
          }}
        >
          {description.trim().length} chars · minimum 20 ·{' '}
          {minLengthMet ? 'ready' : 'needs more detail'}
        </div>
      </div>

      {/* PHI warning */}
      {phiHits.length > 0 && (
        <div
          className="sme-card"
          style={{
            marginBottom: '2rem',
            borderLeft: '4px solid var(--sme-deny)',
          }}
        >
          <div className="sme-label sme-status-deny">PHI-shaped patterns detected</div>
          <p style={{ marginTop: '0.5rem', marginBottom: '0.75rem' }}>
            The text appears to contain real-patient identifiers. Per PACCA's
            synthetic-only policy, you must remove them before continuing.
            False positives can be acknowledged below.
          </p>
          <ul style={{ marginTop: 0, marginBottom: '1rem' }}>
            {phiHits.map((hit) => (
              <li key={hit} className="sme-mono" style={{ fontSize: '0.875rem' }}>
                {hit}
              </li>
            ))}
          </ul>
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
              checked={acknowledgedPhi}
              onChange={(e) => setAcknowledgedPhi(e.target.checked)}
            />
            <span style={{ fontSize: '0.95rem' }}>
              I confirm this is a false positive (synthetic data only; no real
              patient information).
            </span>
          </label>
        </div>
      )}

      {/* Optional hints */}
      <div style={{ marginBottom: '2rem' }}>
        <div className="sme-label" style={{ marginBottom: '0.75rem' }}>
          Optional hints
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1rem',
          }}
        >
          <div>
            <label
              htmlFor="hint-specialty"
              style={{
                display: 'block',
                fontSize: '0.875rem',
                color: 'var(--sme-muted)',
                marginBottom: '0.25rem',
              }}
            >
              Specialty
            </label>
            <select
              id="hint-specialty"
              value={state.scenario.intended_specialty ?? ''}
              onChange={handleField('intended_specialty')}
              style={{
                width: '100%',
                fontFamily: 'var(--sme-font-body)',
                fontSize: '0.9375rem',
                padding: '0.5rem',
                backgroundColor: 'var(--sme-paper)',
                border: '1px solid var(--sme-rule-soft)',
              }}
            >
              <option value="">— let agent infer —</option>
              {SPECIALTY_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label
              htmlFor="hint-outcome"
              style={{
                display: 'block',
                fontSize: '0.875rem',
                color: 'var(--sme-muted)',
                marginBottom: '0.25rem',
              }}
            >
              Intended outcome
            </label>
            <select
              id="hint-outcome"
              value={state.scenario.intended_outcome ?? ''}
              onChange={handleField('intended_outcome')}
              style={{
                width: '100%',
                fontFamily: 'var(--sme-font-body)',
                fontSize: '0.9375rem',
                padding: '0.5rem',
                backgroundColor: 'var(--sme-paper)',
                border: '1px solid var(--sme-rule-soft)',
              }}
            >
              <option value="">— let agent propose —</option>
              {OUTCOME_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {state.error && (
        <p className="sme-status-deny" style={{ fontStyle: 'italic' }}>
          {state.error}
        </p>
      )}

      <div
        style={{
          marginTop: '2.5rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid var(--sme-rule-soft)',
          display: 'flex',
          justifyContent: 'flex-end',
        }}
      >
        <button
          type="button"
          className="sme-button"
          disabled={!canContinue}
          onClick={() => void onSubmit()}
          style={{
            opacity: canContinue ? 1 : 0.45,
            cursor: canContinue ? 'pointer' : 'not-allowed',
          }}
        >
          {state.inFlight.creatingSession ? 'Creating session…' : 'Begin drafting →'}
        </button>
      </div>
    </div>
  );
}
