/**
 * Step 2 — Drafting.
 *
 * After the session is created, the agent calls the LLM. This step
 * subscribes to the WebSocket draft-stream for token-by-token rendering
 * (typewriter cursor primitive from theme.css), and falls back to the
 * buffered REST endpoint if the WS errors before any delta arrives.
 *
 * The page is intentionally calm — one big typewriter readout, no
 * spinners, restrained editorial framing.
 */

import { useEffect, useRef, useState } from 'react';
import { CaseIDPill } from '../components/CaseIDPill';
import { PageHeader } from '../components/PageHeader';
import { useDraft, useWebSocketDraft } from '../hooks/useDrafting';
import type { CaseDraftResponse } from '../types';
import type { WizardAction, WizardState } from './wizardState';

interface Step2Props {
  state: WizardState;
  dispatch: (action: WizardAction) => void;
}

const FIELD_LABELS: Partial<Record<keyof CaseDraftResponse, string>> = {
  clinical_notes: 'Clinical notes',
  guidelines_context: 'Guidelines context',
  clinical_rationale: 'Clinical rationale',
  judge_scoring_criteria: 'Judge scoring criteria',
};

export function Step2Drafting({ state, dispatch }: Step2Props) {
  const ws = useWebSocketDraft({
    onDone: (draft) => {
      dispatch({
        type: 'DRAFT_DONE',
        draft,
        allocatedCaseId: draft.case_id,
        recommendedFile: '', // backend recommends in the WS done event; pulled from ws.recommendedFile
      });
    },
    onError: () => {
      // If WS errored before any delta arrived, attempt REST fallback
      if (!fallbackTriedRef.current && !state.draft) {
        fallbackTriedRef.current = true;
        void tryRestFallback();
      }
    },
  });
  const rest = useDraft();
  const fallbackTriedRef = useRef(false);
  const [phase, setPhase] = useState<'idle' | 'streaming' | 'rest-fallback'>(
    'idle',
  );

  // Kick off the draft once we have a sessionId
  useEffect(() => {
    if (!state.sessionId) return;
    if (state.draft) return; // already drafted; user is just back-nav'd
    if (phase !== 'idle') return;

    dispatch({ type: 'DRAFT_PENDING' });
    setPhase('streaming');
    ws.connect(state.sessionId);
    // We intentionally don't re-trigger on every dispatch
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.sessionId]);

  // Sync the recommended_file out of the WS hook into the wizard state
  // when the 'done' event arrives.
  useEffect(() => {
    if (
      ws.status === 'done' &&
      ws.draft &&
      ws.recommendedFile !== null &&
      state.draft &&
      !state.recommendedFile
    ) {
      // The onDone callback already fired and set the draft; we patch
      // in the recommendedFile via a second dispatch to keep the
      // reducer's actions simple and serializable.
      dispatch({
        type: 'DRAFT_DONE',
        draft: ws.draft,
        allocatedCaseId: ws.allocatedCaseId ?? ws.draft.case_id,
        recommendedFile: ws.recommendedFile,
      });
    }
  }, [
    ws.status,
    ws.draft,
    ws.recommendedFile,
    ws.allocatedCaseId,
    state.draft,
    state.recommendedFile,
    dispatch,
  ]);

  async function tryRestFallback() {
    if (!state.sessionId) return;
    setPhase('rest-fallback');
    try {
      const res = await rest.run(state.sessionId);
      dispatch({
        type: 'DRAFT_DONE',
        draft: res.draft,
        allocatedCaseId: res.allocated_case_id,
        recommendedFile: res.recommended_file,
        routingReason: res.routing_reason,
      });
    } catch (err) {
      dispatch({
        type: 'DRAFT_FAILED',
        error: err instanceof Error ? err.message : 'Drafting failed',
      });
    }
  }

  const fields = Object.entries(ws.deltas).filter(
    ([, content]) => content.length > 0,
  );
  const currentlyStreaming = ws.status === 'drafting' || ws.status === 'authenticating';
  const usingFallback = phase === 'rest-fallback';

  return (
    <div className="sme-page-text">
      <PageHeader
        label="Step 2 of 6"
        title="Drafting"
        hint={
          state.allocatedCaseId
            ? undefined
            : 'The agent is composing a draft from your scenario. You will review and edit it next.'
        }
        actions={
          state.allocatedCaseId ? (
            <CaseIDPill id={state.allocatedCaseId} size="lg" />
          ) : undefined
        }
      />

      <div style={{ marginBottom: '2rem' }}>
        <div className="sme-label">Status</div>
        <p
          className="sme-mono"
          style={{
            marginTop: '0.5rem',
            color: 'var(--sme-deep-ink)',
            fontSize: '0.9375rem',
          }}
        >
          {usingFallback
            ? 'WebSocket unavailable — using buffered REST drafting…'
            : ws.status === 'connecting'
              ? 'opening drafting socket…'
              : ws.status === 'authenticating'
                ? 'authenticating session…'
                : ws.status === 'drafting'
                  ? 'drafting in progress…'
                  : ws.status === 'done'
                    ? 'draft complete'
                    : ws.status === 'error'
                      ? `error: ${ws.error}`
                      : 'preparing…'}
        </p>
      </div>

      {/* Streaming output */}
      <div
        className="sme-card"
        style={{
          marginBottom: '2rem',
          minHeight: '12rem',
          fontFamily: 'var(--sme-font-body)',
          fontSize: '1rem',
          lineHeight: 1.55,
          whiteSpace: 'pre-wrap',
        }}
      >
        {fields.length === 0 && (
          <p
            className="sme-mono"
            style={{
              color: 'var(--sme-muted)',
              fontSize: '0.875rem',
              fontStyle: 'italic',
              margin: 0,
            }}
          >
            waiting for first tokens…
          </p>
        )}
        {fields.map(([field, content], idx) => (
          <div key={field} style={{ marginBottom: '1rem' }}>
            <div className="sme-label" style={{ fontSize: '0.75rem' }}>
              {FIELD_LABELS[field as keyof CaseDraftResponse] ?? field}
            </div>
            <div
              style={{ marginTop: '0.25rem' }}
              className={
                currentlyStreaming && idx === fields.length - 1
                  ? 'sme-cursor'
                  : undefined
              }
            >
              {content}
            </div>
          </div>
        ))}
        {usingFallback && (
          <p className="sme-loading">
            (REST fallback in flight; the result will appear all at once)
          </p>
        )}
      </div>

      {state.error && (
        <div
          className="sme-card"
          style={{
            borderLeft: '4px solid var(--sme-deny)',
            marginBottom: '2rem',
          }}
        >
          <div className="sme-label sme-status-deny">Drafting failed</div>
          <p style={{ marginTop: '0.5rem', marginBottom: '0.75rem' }}>
            {state.error}
          </p>
          <button
            type="button"
            className="sme-button sme-button-secondary"
            onClick={() => {
              fallbackTriedRef.current = false;
              setPhase('idle');
              dispatch({ type: 'DRAFT_PENDING' });
              if (state.sessionId) ws.connect(state.sessionId);
            }}
          >
            Retry drafting
          </button>
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
          ← Back
        </button>
        <button
          type="button"
          className="sme-button"
          disabled={!state.draft}
          onClick={() => dispatch({ type: 'NEXT_STEP' })}
          style={{
            opacity: state.draft ? 1 : 0.45,
            cursor: state.draft ? 'pointer' : 'not-allowed',
          }}
        >
          Review the draft →
        </button>
      </div>
    </div>
  );
}
