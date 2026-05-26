/**
 * NewCaseWizard — the 6-step shell that ties everything together.
 *
 * Responsibilities:
 *   - Owns the wizard state via useReducer.
 *   - Renders the StepIndicator above the active step component.
 *   - Wires the createSession action that transitions Step 1 → Step 2.
 *
 * State persistence: in v1.1 we keep the wizard purely in-memory.
 * Resume-mid-session is a v1.2 enhancement (would require restoring
 * the reducer state from sessionId via GET /sessions/{id}).
 */

import { useMemo, useReducer, useState } from 'react';
import { useCreateSession } from '../hooks/useSessions';
import { Step1Scenario } from '../wizard/Step1Scenario';
import { Step2Drafting } from '../wizard/Step2Drafting';
import { Step3DraftReview } from '../wizard/Step3DraftReview';
import { Step4Validators } from '../wizard/Step4Validators';
import { Step5Attestation } from '../wizard/Step5Attestation';
import { Step6Commit } from '../wizard/Step6Commit';
import { StepIndicator } from '../wizard/StepIndicator';
import {
  initialWizardState,
  wizardReducer,
  type WizardStep,
} from '../wizard/wizardState';

export function NewCaseWizard() {
  const [state, dispatch] = useReducer(wizardReducer, initialWizardState);
  const createSession = useCreateSession();
  const [visited, setVisited] = useState<Set<Exclude<WizardStep, 'done'>>>(
    new Set([1]),
  );

  // Track visited steps so the indicator allows back-jumping
  useMemo(() => {
    const s = state.step;
    if (s === 'done') return;
    setVisited((v) => {
      if (v.has(s)) return v;
      const next = new Set(v);
      next.add(s);
      return next;
    });
  }, [state.step]);

  // Transition: Step 1 → Step 2 via createSession
  const handleScenarioSubmit = async () => {
    dispatch({ type: 'CREATE_SESSION_PENDING' });
    try {
      const res = await createSession.create({
        scenario: state.scenario,
        mode: state.mode,
      });
      dispatch({
        type: 'CREATE_SESSION_DONE',
        sessionId: res.session.session_id,
      });
    } catch (err) {
      dispatch({
        type: 'CREATE_SESSION_FAILED',
        error:
          err instanceof Error ? err.message : 'Failed to create session',
      });
    }
  };

  const renderStep = () => {
    switch (state.step) {
      case 1:
        return (
          <Step1Scenario
            state={state}
            dispatch={dispatch}
            onSubmit={handleScenarioSubmit}
          />
        );
      case 2:
        return <Step2Drafting state={state} dispatch={dispatch} />;
      case 3:
        return <Step3DraftReview state={state} dispatch={dispatch} />;
      case 4:
        return <Step4Validators state={state} dispatch={dispatch} />;
      case 5:
        return <Step5Attestation state={state} dispatch={dispatch} />;
      case 6:
        return <Step6Commit state={state} dispatch={dispatch} />;
      case 'done':
        return <Step6Commit state={state} dispatch={dispatch} />;
    }
  };

  return (
    <div className="sme-page sme-page-enter sme-page-enter-active">
      <StepIndicator
        current={state.step}
        visited={visited}
        onJump={(s) => dispatch({ type: 'GO_TO_STEP', step: s })}
      />
      {renderStep()}
    </div>
  );
}
