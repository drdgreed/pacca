/**
 * DirectorQueue — Medical Director review queue.
 *
 * Reskinned in PR-UI-4 to the Editorial-Clinical aesthetic. Each
 * escalated case renders as a .sme-card-emphasis with a mustard top
 * border (signals "in review"). The two clinical actions
 * (override-and-approve vs confirm-denial) use .sme-button-approve
 * and .sme-button-deny.
 *
 * PHI scrub: the previous synthetic patient string included a titled
 * full name + a date-of-birth phrasing — the exact patterns CLAUDE.md
 * forbids in committed source even for demo data. Replaced with the
 * SME-authoring convention: opaque IDs + age representation (no name,
 * no DOB). See git history for the pre-scrub content.
 *
 * Bug fix: hardcoded `http://127.0.0.1:8000` URL replaced with
 * relative `/api/v1/...` (works through Vite proxy + nginx).
 *
 * Also fixes the last pre-existing tsc warning: unused `React`
 * import removed (React 18 + new JSX transform doesn't need it).
 */

import { useState } from 'react';
import { MonoChip } from './MonoChip';
import { StatusInk } from './StatusInk';
import { PageHeader } from '../sme-authoring/components/PageHeader';

interface DirectorCase {
  id: string;
  patient: string;
  diagnosis: string;
  procedure: string;
  clinical_notes: string;
  ai_status: string;
  ai_rationale: string;
}

// Synthetic demo case. NO real PHI. Patient identifier is opaque +
// age-only (no DOB, no full name). Per CLAUDE.md HIPAA rules.
const DEMO_QUEUE: DirectorCase[] = [
  {
    id: 'REQ-8842',
    patient: 'Patient DEMO-8842 · 47yo',
    diagnosis: 'M54.5 (Low back pain)',
    procedure: '72148 (MRI Lumbar Spine)',
    clinical_notes:
      'Acute lower back pain that started 2 weeks ago after lifting a heavy box. No numbness or weakness. Imaging requested.',
    ai_status: 'IN_REVIEW',
    ai_rationale:
      'Frontline agent confidence 0.82. Guidelines require 6 weeks of conservative therapy (PT, NSAIDs) for routine back pain without red flags; patient has had pain for only 2 weeks.',
  },
];

export function DirectorQueue() {
  const [queue, setQueue] = useState<DirectorCase[]>(DEMO_QUEUE);
  const [status, setStatus] = useState<{
    tone: 'approved' | 'denied' | 'info';
    message: string;
  } | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  const handleOverride = async (caseItem: DirectorCase) => {
    setPending(caseItem.id);
    setStatus({ tone: 'info', message: 'Injecting human override into vector store…' });

    const humanRationale =
      'Medical Director override: patient is a manual laborer and primary earner. Delaying imaging risks long-term structural damage that could prevent return to work. Approved as exception.';

    try {
      const response = await fetch('/api/v1/authorizations/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token') ?? ''}`,
        },
        body: JSON.stringify({
          case_summary: caseItem.clinical_notes,
          decision: 'APPROVED',
          rationale: humanRationale,
        }),
      });
      if (response.ok) {
        setStatus({
          tone: 'approved',
          message: 'Precedent recorded. The agent will reference this decision for future cases.',
        });
        setQueue((q) => q.filter((c) => c.id !== caseItem.id));
      } else {
        setStatus({ tone: 'denied', message: `Failed to submit override (HTTP ${response.status}).` });
      }
    } catch {
      setStatus({
        tone: 'denied',
        message: 'Connection error. Is the backend running on port 8000?',
      });
    } finally {
      setPending(null);
    }
  };

  const handleConfirmDenial = (caseItem: DirectorCase) => {
    setQueue((q) => q.filter((c) => c.id !== caseItem.id));
    setStatus({ tone: 'denied', message: `${caseItem.id} denial confirmed.` });
  };

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Director"
        title="Medical Director queue"
        hint="Review complex cases the agent escalated. Override-and-approve teaches the AI; confirm-denial leaves the AI's decision intact."
      />

      {status && (
        <div
          className="sme-card"
          style={{
            borderLeft: `4px solid ${
              status.tone === 'approved'
                ? 'var(--sme-approve)'
                : status.tone === 'denied'
                  ? 'var(--sme-deny)'
                  : 'var(--sme-info)'
            }`,
            marginBottom: '2rem',
          }}
        >
          <StatusInk outcome={status.tone === 'info' ? 'info' : status.tone}>
            {status.message}
          </StatusInk>
        </div>
      )}

      {queue.length === 0 ? (
        <div className="sme-empty">
          Queue empty. No cases pending Medical Director review.
        </div>
      ) : (
        queue.map((caseItem) => (
          <article
            key={caseItem.id}
            className="sme-card-emphasis"
            style={{
              borderTopColor: 'var(--sme-review)',
              marginBottom: '2rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                gap: '1rem',
                marginBottom: '1rem',
                flexWrap: 'wrap',
              }}
            >
              <div>
                <div className="sme-label">Case</div>
                <div
                  style={{
                    fontFamily: 'var(--sme-font-display)',
                    fontSize: '1.375rem',
                    fontWeight: 600,
                    color: 'var(--sme-deep-ink)',
                    marginTop: '0.25rem',
                  }}
                >
                  {caseItem.patient}
                </div>
                <MonoChip size="sm" tone="muted">
                  {caseItem.id}
                </MonoChip>
              </div>
              <StatusInk
                outcome="review"
                style={{
                  fontSize: '0.9375rem',
                  fontVariant: 'small-caps',
                  letterSpacing: '0.04em',
                }}
              >
                {caseItem.ai_status.toLowerCase().replace(/_/g, ' ')}
              </StatusInk>
            </div>

            <hr className="sme-rule-soft" />

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '1.5rem',
                marginBottom: '1.5rem',
              }}
            >
              <div>
                <div className="sme-label">Diagnosis</div>
                <p style={{ marginTop: '0.25rem', marginBottom: 0 }}>{caseItem.diagnosis}</p>
              </div>
              <div>
                <div className="sme-label">Requested procedure</div>
                <p style={{ marginTop: '0.25rem', marginBottom: 0 }}>{caseItem.procedure}</p>
              </div>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <div className="sme-label">Clinical notes</div>
              <p
                style={{
                  marginTop: '0.25rem',
                  color: 'var(--sme-ink-soft)',
                  lineHeight: 1.55,
                }}
              >
                {caseItem.clinical_notes}
              </p>
            </div>

            <div
              style={{
                borderLeft: '2px solid var(--sme-review)',
                paddingLeft: '0.75rem',
                marginBottom: '2rem',
              }}
            >
              <div className="sme-label sme-status-review">Agent escalation rationale</div>
              <p
                style={{
                  marginTop: '0.25rem',
                  marginBottom: 0,
                  fontStyle: 'italic',
                  color: 'var(--sme-ink-soft)',
                }}
              >
                {caseItem.ai_rationale}
              </p>
            </div>

            <div
              style={{
                display: 'flex',
                gap: '0.75rem',
                paddingTop: '1rem',
                borderTop: '1px solid var(--sme-rule-soft)',
              }}
            >
              <button
                type="button"
                className="sme-button sme-button-approve"
                onClick={() => void handleOverride(caseItem)}
                disabled={pending === caseItem.id}
                style={{
                  opacity: pending === caseItem.id ? 0.6 : 1,
                  cursor: pending === caseItem.id ? 'not-allowed' : 'pointer',
                }}
              >
                {pending === caseItem.id ? 'Submitting…' : 'Override · teach AI'}
              </button>
              <button
                type="button"
                className="sme-button sme-button-deny"
                onClick={() => handleConfirmDenial(caseItem)}
                disabled={pending === caseItem.id}
                style={{
                  opacity: pending === caseItem.id ? 0.6 : 1,
                  cursor: pending === caseItem.id ? 'not-allowed' : 'pointer',
                }}
              >
                Confirm denial
              </button>
            </div>
          </article>
        ))
      )}
    </div>
  );
}
