/**
 * ProviderDashboard — single authorization-request submission surface.
 *
 * Reskinned in PR-UI-2 to the Editorial-Clinical aesthetic:
 *   - PageHeader for the section title
 *   - .sme-card-emphasis for the form container
 *   - .sme-input for the clinical-notes textarea
 *   - .sme-button for the primary action
 *   - StatusInk for the decision outcome
 *   - MonoChip for the CPT code + confidence value
 *   - PageHeader's right-aligned hint slot carries the CPT chip
 *
 * Bug fix included (same as Login): hardcoded `http://127.0.0.1:8000`
 * URL → relative `/api/v1/authorizations/`. Vite proxy + production
 * nginx both forward correctly.
 */

import { useState } from 'react';
import { MonoChip } from './MonoChip';
import { StatusInk, type StatusOutcome } from './StatusInk';
import { PageHeader } from '../sme-authoring/components/PageHeader';

interface DecisionResult {
  status: string;
  rationale: string;
  confidence_score: number;
  review_tier_used: string;
}

/** Map backend status strings to StatusInk outcome semantics. */
function outcomeFor(status: string): StatusOutcome {
  if (status === 'AUTO_APPROVED' || status === 'approved') return 'approved';
  if (status === 'DENIED' || status === 'denied') return 'denied';
  if (
    status === 'IN_REVIEW' ||
    status === 'pending_review' ||
    status === 'escalated' ||
    status === 'PRE_FLIGHT_ESCALATE'
  ) {
    return 'review';
  }
  return 'processing';
}

const DEFAULT_NOTES =
  'Patient presents with acute lumbar pain (2 weeks duration). Physical exam reveals significant motor weakness in right leg. Requesting immediate MRI to rule out cauda equina.';

export function ProviderDashboard() {
  const [notes, setNotes] = useState(DEFAULT_NOTES);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submitCase = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    const payload = {
      request_id: 'demo_' + Date.now(),
      patient_id: 'p_demo',
      // Synthetic demo NPI. Intentionally non-numeric so the PHI guard
      // doesn't flag it as a phone-shaped 10-digit literal.
      provider_npi: 'demo-npi-0001',
      clinical_case: {
        patient_id: 'p_demo',
        primary_diagnosis_code: 'M54.5', // Low back pain
        procedure_code: '72148', // MRI Lumbar Spine
        evidence: [
          {
            id: 'ev_1',
            source_type: 'CLINICAL_NOTE',
            description: 'Physician Notes',
            original_text: notes,
            confidence: 1.0,
          },
        ],
      },
    };

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/authorizations/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: token ? `Bearer ${token}` : '',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        if (response.status === 401) {
          setError('Your session has expired. Please sign in again.');
          return;
        }
        const body = await response.json().catch(() => ({}));
        setError(body.detail || `Server returned HTTP ${response.status}`);
        return;
      }

      const data = (await response.json()) as DecisionResult;
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Connection failed. Is the backend running on port 8000?',
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <PageHeader
        label="Provider"
        title="Submit authorization request"
        hint="Enter the clinical notes; the agent decides approve / deny / review and surfaces its rationale."
        actions={<MonoChip size="md" tone="muted">CPT 72148 · MRI lumbar</MonoChip>}
      />

      <div className="sme-page-text">
        <div className="sme-card-emphasis" style={{ marginBottom: '2rem' }}>
          <label
            htmlFor="provider-clinical-notes"
            className="sme-label"
            style={{ display: 'block', marginBottom: '0.5rem' }}
          >
            Clinical notes &middot; evidence
          </label>
          <textarea
            id="provider-clinical-notes"
            className="sme-input"
            rows={6}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Enter clinical details…"
            disabled={loading}
          />
          <div
            className="sme-mono"
            style={{
              marginTop: '0.5rem',
              fontSize: '0.75rem',
              color: 'var(--sme-muted)',
            }}
          >
            tip: removing &ldquo;motor weakness&rdquo; should flip the decision
            from approve to review.
          </div>
        </div>

        {error && (
          <div
            className="sme-card"
            style={{
              borderLeft: '4px solid var(--sme-deny)',
              marginBottom: '2rem',
            }}
          >
            <div className="sme-label sme-status-deny">Submission failed</div>
            <p style={{ marginTop: '0.5rem', marginBottom: 0 }}>{error}</p>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="button"
            className="sme-button"
            onClick={() => void submitCase()}
            disabled={loading || notes.trim().length === 0}
            style={{
              opacity: loading || notes.trim().length === 0 ? 0.6 : 1,
              cursor: loading || notes.trim().length === 0 ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? 'Processing…' : 'Submit for authorization'}
          </button>
        </div>

        {result && (
          <section style={{ marginTop: '3rem' }}>
            <hr className="sme-rule" />
            <div className="sme-label" style={{ marginBottom: '1rem' }}>
              Agent decision
            </div>

            <div
              className="sme-card-emphasis"
              style={{
                borderTopColor:
                  outcomeFor(result.status) === 'approved'
                    ? 'var(--sme-approve)'
                    : outcomeFor(result.status) === 'denied'
                      ? 'var(--sme-deny)'
                      : 'var(--sme-review)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: '1.5rem',
                  marginBottom: '1.5rem',
                  flexWrap: 'wrap',
                }}
              >
                <StatusInk
                  outcome={outcomeFor(result.status)}
                  style={{
                    fontSize: '1.5rem',
                    fontVariant: 'small-caps',
                    letterSpacing: '0.04em',
                  }}
                >
                  {result.status?.replace(/_/g, ' ').toLowerCase()}
                </StatusInk>
                <div
                  className="sme-mono"
                  style={{
                    fontSize: '0.875rem',
                    color: 'var(--sme-muted)',
                  }}
                >
                  confidence{' '}
                  <MonoChip size="sm" tone="ink">
                    {(result.confidence_score * 100).toFixed(1)}%
                  </MonoChip>
                  {' · '}tier{' '}
                  <MonoChip size="sm" tone="ink">
                    {result.review_tier_used}
                  </MonoChip>
                </div>
              </div>

              <div className="sme-label" style={{ fontSize: '0.6875rem' }}>
                Rationale
              </div>
              <p
                style={{
                  marginTop: '0.5rem',
                  marginBottom: 0,
                  color: 'var(--sme-ink-soft)',
                  lineHeight: 1.6,
                }}
              >
                {result.rationale}
              </p>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
