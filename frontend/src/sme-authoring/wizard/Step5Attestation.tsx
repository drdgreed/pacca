/**
 * Step 5 — SME attestation.
 *
 * Per CASE_AUTHORING_GUIDE.md § 11, the SME must type ONE of:
 *
 *   1. The generic phrase (case-insensitive):
 *      "I attest this case is clinically accurate per my professional judgment"
 *
 *   2. A credential string of the form:
 *      "Dr. <Name>, <Degree>, board-certified <Specialty>"
 *
 * The backend validates the attestation format itself (the
 * `sme_attestation` field on CommitRequest has min_length=10). The
 * client surfaces a live indication of which format the typed text
 * looks like, so the SME knows the entry will be accepted.
 */

import { PageHeader } from '../components/PageHeader';
import type { WizardAction, WizardState } from './wizardState';

interface Step5Props {
  state: WizardState;
  dispatch: (action: WizardAction) => void;
}

const GENERIC_PHRASE_LOWER =
  'i attest this case is clinically accurate per my professional judgment';

const CREDENTIAL_REGEX =
  /^Dr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+,\s+[A-Z][.A-Za-z]+(?:,\s*[A-Z][.A-Za-z]+)*,\s+board-certified\s+[A-Z][a-z]+/i;

type AttestationKind = 'empty' | 'generic' | 'credentialed' | 'unrecognized';

function classifyAttestation(text: string): AttestationKind {
  const trimmed = text.trim();
  if (trimmed.length === 0) return 'empty';
  if (trimmed.toLowerCase().includes(GENERIC_PHRASE_LOWER)) return 'generic';
  if (CREDENTIAL_REGEX.test(trimmed)) return 'credentialed';
  return 'unrecognized';
}

export function Step5Attestation({ state, dispatch }: Step5Props) {
  const kind = classifyAttestation(state.attestation);
  const meetsMinLength = state.attestation.trim().length >= 10;
  const canContinue =
    meetsMinLength &&
    (kind === 'generic' || kind === 'credentialed');

  return (
    <div className="sme-page-text">
      <PageHeader
        label="Step 5 of 6"
        title="Attest your review"
        hint="Per CASE_AUTHORING_GUIDE § 11, your attestation goes into the audit trail next to the case."
      />

      <div className="sme-page-text">
        <p>
          Two formats are accepted. Type either one below — the agent
          will detect the format and pass it through to the audit record
          unchanged.
        </p>

        <div
          className="sme-card"
          style={{ marginBottom: '1.5rem' }}
        >
          <div className="sme-label">Format A — generic attestation</div>
          <p
            className="sme-mono"
            style={{
              marginTop: '0.5rem',
              marginBottom: 0,
              fontSize: '0.875rem',
              color: 'var(--sme-deep-ink)',
            }}
          >
            I attest this case is clinically accurate per my professional judgment
          </p>
        </div>

        <div className="sme-card" style={{ marginBottom: '2rem' }}>
          <div className="sme-label">Format B — credentialed</div>
          <p
            className="sme-mono"
            style={{
              marginTop: '0.5rem',
              marginBottom: 0,
              fontSize: '0.875rem',
              color: 'var(--sme-deep-ink)',
            }}
          >
            Dr. &lt;Name&gt;, &lt;Degree&gt;, board-certified &lt;Specialty&gt;
          </p>
        </div>

        <label
          htmlFor="attestation"
          className="sme-label"
          style={{ display: 'block', marginBottom: '0.5rem' }}
        >
          Your attestation
        </label>
        <textarea
          id="attestation"
          value={state.attestation}
          onChange={(e) =>
            dispatch({ type: 'SET_ATTESTATION', value: e.target.value })
          }
          rows={3}
          style={{
            width: '100%',
            fontFamily: 'var(--sme-font-body)',
            fontSize: '1rem',
            padding: '0.75rem',
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
            color:
              kind === 'generic' || kind === 'credentialed'
                ? 'var(--sme-approve)'
                : kind === 'unrecognized'
                  ? 'var(--sme-review)'
                  : 'var(--sme-muted)',
          }}
        >
          {kind === 'empty' && 'awaiting input'}
          {kind === 'generic' && '✓ generic attestation detected'}
          {kind === 'credentialed' && '✓ credentialed attestation detected'}
          {kind === 'unrecognized' &&
            'format not recognized — server will still accept if ≥10 chars; consider one of the two formats above'}
        </div>
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
          onClick={() => dispatch({ type: 'PREV_STEP' })}
        >
          ← Back to validation
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
          Proceed to commit →
        </button>
      </div>
    </div>
  );
}
