/**
 * Step 3 — Draft review.
 *
 * Field-by-field editor over the LLM's CaseDraftResponse. The SME
 * adjusts any field that needs clinical correction. Each edit
 * invalidates the prior validation result (handled by the reducer),
 * so they re-validate in step 4.
 *
 * Field rendering rules:
 *   - case_id is read-only (allocated by the agent).
 *   - String fields use textarea for >40 chars typical (clinical notes,
 *     rationale, etc.), input for short fields (title, codes).
 *   - List fields (reasoning_must_include / _not_include /
 *     prior_denial_codes) use a multi-line textarea with one item per
 *     line — simpler than per-item add/remove UI and good enough at SME
 *     throughput.
 */

import { CaseIDPill } from '../components/CaseIDPill';
import { PageHeader } from '../components/PageHeader';
import type { CaseDraftResponse } from '../types';
import type { WizardAction, WizardState } from './wizardState';

interface Step3Props {
  state: WizardState;
  dispatch: (action: WizardAction) => void;
}

interface FieldDef {
  field: keyof CaseDraftResponse;
  label: string;
  hint?: string;
  kind: 'input' | 'textarea' | 'string-list';
  rows?: number;
}

const FIELDS: FieldDef[] = [
  { field: 'title', label: 'Title', kind: 'input', hint: '10–120 chars; descriptive' },
  { field: 'diagnosis_code', label: 'Diagnosis code (ICD-10)', kind: 'input' },
  {
    field: 'diagnosis_description',
    label: 'Diagnosis description',
    kind: 'input',
  },
  {
    field: 'procedure_code',
    label: 'Procedure code (CPT / HCPCS / J-code)',
    kind: 'input',
  },
  {
    field: 'procedure_description',
    label: 'Procedure description',
    kind: 'input',
  },
  {
    field: 'clinical_notes',
    label: 'Clinical notes',
    hint: '3–8 sentences. PHI-free, synthetic only.',
    kind: 'textarea',
    rows: 6,
  },
  {
    field: 'guidelines_context',
    label: 'Guidelines context',
    hint: 'Cite a real authoritative body (NCCN, ACR, AAD, ACC/AHA, etc.).',
    kind: 'textarea',
    rows: 4,
  },
  {
    field: 'expected_outcome',
    label: 'Expected outcome',
    hint: 'AUTO_APPROVED / IN_REVIEW / DENIED / PRE_FLIGHT_ESCALATE / INFORMATION_NEEDED',
    kind: 'input',
  },
  {
    field: 'expected_branch',
    label: 'Expected branch',
    hint: 'BRANCH_1_AUTO_APPROVE … BRANCH_7_PRIOR_DENIAL, or NONE',
    kind: 'input',
  },
  {
    field: 'reasoning_must_include',
    label: 'Reasoning must include',
    hint: 'One phrase per line. At least one required.',
    kind: 'string-list',
    rows: 3,
  },
  {
    field: 'reasoning_must_not_include',
    label: 'Reasoning must not include (hallucination markers)',
    hint: 'One phrase per line. Empty is fine for routine coverage cases.',
    kind: 'string-list',
    rows: 3,
  },
  {
    field: 'prior_denial_codes',
    label: 'Prior denial codes',
    hint: 'One code per line. Empty if no prior denial.',
    kind: 'string-list',
    rows: 2,
  },
  {
    field: 'clinical_rationale',
    label: 'Clinical rationale',
    hint: 'Human-expert justification, 2–5 sentences (≥2 periods).',
    kind: 'textarea',
    rows: 4,
  },
  {
    field: 'judge_scoring_criteria',
    label: 'Judge scoring criteria',
    hint: 'Non-generic. What should the LLM-as-judge specifically evaluate here?',
    kind: 'textarea',
    rows: 4,
  },
];

function inputBaseStyle(): React.CSSProperties {
  return {
    width: '100%',
    fontFamily: 'var(--sme-font-body)',
    fontSize: '0.9375rem',
    padding: '0.625rem 0.75rem',
    backgroundColor: 'var(--sme-paper)',
    border: '1px solid var(--sme-rule-soft)',
    color: 'var(--sme-ink)',
    lineHeight: 1.5,
  };
}

export function Step3DraftReview({ state, dispatch }: Step3Props) {
  if (!state.draft) {
    return (
      <div className="sme-page-text">
        <PageHeader label="Step 3 of 6" title="Draft review" />
        <p className="sme-empty">
          No draft loaded. Step back to drafting to generate one.
        </p>
      </div>
    );
  }
  const draft = state.draft;

  const setField = (
    field: keyof CaseDraftResponse,
    value: CaseDraftResponse[keyof CaseDraftResponse],
  ) => {
    dispatch({ type: 'EDIT_DRAFT_FIELD', field, value });
  };

  return (
    <div>
      <div className="sme-page-text">
        <PageHeader
          label="Step 3 of 6"
          title="Review the draft"
          hint="Read each field. Edit anything that's clinically off — small adjustments compound."
          actions={<CaseIDPill id={draft.case_id} size="lg" />}
        />
      </div>

      <div className="sme-page-text">
        {state.recommendedFile && (
          <div
            className="sme-card"
            style={{ marginBottom: '2rem' }}
          >
            <div className="sme-label">Routing</div>
            <p style={{ marginTop: '0.5rem', marginBottom: 0 }}>
              The agent will write this case to{' '}
              <code>{state.recommendedFile}</code>.
              {state.routingReason && (
                <>
                  {' '}
                  <span style={{ color: 'var(--sme-muted)' }}>
                    ({state.routingReason})
                  </span>
                </>
              )}
            </p>
          </div>
        )}

        {FIELDS.map(({ field, label, hint, kind, rows }) => {
          const value = draft[field];
          return (
            <div key={field} style={{ marginBottom: '1.5rem' }}>
              <label
                htmlFor={`field-${field}`}
                className="sme-label"
                style={{ display: 'block', marginBottom: '0.25rem' }}
              >
                {label}
              </label>
              {hint && (
                <div
                  style={{
                    fontSize: '0.8125rem',
                    color: 'var(--sme-muted)',
                    marginBottom: '0.375rem',
                  }}
                >
                  {hint}
                </div>
              )}
              {kind === 'input' && (
                <input
                  id={`field-${field}`}
                  type="text"
                  value={typeof value === 'string' ? value : ''}
                  onChange={(e) => setField(field, e.target.value)}
                  style={inputBaseStyle()}
                />
              )}
              {kind === 'textarea' && (
                <textarea
                  id={`field-${field}`}
                  value={typeof value === 'string' ? value : ''}
                  onChange={(e) => setField(field, e.target.value)}
                  rows={rows ?? 4}
                  style={{ ...inputBaseStyle(), resize: 'vertical' }}
                />
              )}
              {kind === 'string-list' && (
                <textarea
                  id={`field-${field}`}
                  value={Array.isArray(value) ? value.join('\n') : ''}
                  onChange={(e) =>
                    setField(
                      field,
                      e.target.value
                        .split('\n')
                        .map((s) => s.trim())
                        .filter((s) => s.length > 0),
                    )
                  }
                  rows={rows ?? 3}
                  style={{
                    ...inputBaseStyle(),
                    fontFamily: 'var(--sme-font-mono)',
                    fontSize: '0.875rem',
                    resize: 'vertical',
                  }}
                />
              )}
            </div>
          );
        })}
      </div>

      <div
        className="sme-page-text"
        style={{
          marginTop: '2rem',
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
          ← Back to drafting
        </button>
        <button
          type="button"
          className="sme-button"
          onClick={() => dispatch({ type: 'NEXT_STEP' })}
        >
          Run validators →
        </button>
      </div>
    </div>
  );
}
