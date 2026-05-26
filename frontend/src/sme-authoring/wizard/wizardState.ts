/**
 * Wizard state machine for the SME new-case authoring flow.
 *
 * 6 steps:
 *   1. Scenario       — SME types plain-English description + optional hints
 *   2. Drafting       — LLM call (REST or WS); typewriter cursor
 *   3. Draft review   — field-by-field SME edit of the LLM output
 *   4. Validators     — agent runs 6 validators; SME sees pass/fail/warn
 *   5. Attestation    — SME types the attestation per CASE_AUTHORING_GUIDE § 11
 *   6. Commit         — confirm + see PR template preview + fire commit
 *
 * Why a reducer:
 *   - The cross-step state is non-trivial (session + draft + validators +
 *     attestation + commit result + transient errors).
 *   - The wizard supports back-navigation; pure setState pyramids would
 *     leak state between steps.
 *   - A reducer's actions are testable in isolation and serializable —
 *     the active session_id + step number live in the URL so a refresh
 *     resumes correctly.
 *
 * Design discipline:
 *   - Reducer is pure: no fetches, no side effects. Components dispatch
 *     after an async hook resolves.
 *   - All field edits route through SET_SCENARIO_FIELD or
 *     EDIT_DRAFT_FIELD so the state stays consistent.
 *   - VALIDATE_DONE separates the report from the action that triggered it
 *     so re-validation works after field edits without re-firing the LLM.
 */

import type {
  CaseDraftResponse,
  CommitResponse,
  SMEScenario,
  ValidationReport,
} from '../types';

// =============================================================================
// State
// =============================================================================

export type WizardStep = 1 | 2 | 3 | 4 | 5 | 6 | 'done';

export interface WizardState {
  step: WizardStep;
  sessionId: string | null;
  mode: 'sandbox' | 'production';
  scenario: SMEScenario;
  draft: CaseDraftResponse | null;
  allocatedCaseId: string | null;
  recommendedFile: string | null;
  routingReason: string | null;
  validation: ValidationReport[];
  blockingCount: number;
  warningCount: number;
  passCount: number;
  attestation: string;
  commitResult: CommitResponse | null;
  /** Most recent transient error (network, API). Cleared on next step. */
  error: string | null;
  /** Async-in-flight indicators so step components can disable buttons. */
  inFlight: {
    creatingSession: boolean;
    drafting: boolean;
    validating: boolean;
    committing: boolean;
  };
}

export const EMPTY_SCENARIO: SMEScenario = {
  description: '',
  intended_specialty: null,
  intended_outcome: null,
  failure_mode_label: null,
};

export const initialWizardState: WizardState = {
  step: 1,
  sessionId: null,
  mode: 'sandbox',
  scenario: EMPTY_SCENARIO,
  draft: null,
  allocatedCaseId: null,
  recommendedFile: null,
  routingReason: null,
  validation: [],
  blockingCount: 0,
  warningCount: 0,
  passCount: 0,
  attestation: '',
  commitResult: null,
  error: null,
  inFlight: {
    creatingSession: false,
    drafting: false,
    validating: false,
    committing: false,
  },
};

// =============================================================================
// Actions
// =============================================================================

export type WizardAction =
  // Scenario step
  | { type: 'SET_SCENARIO_FIELD'; field: keyof SMEScenario; value: string | null }
  | { type: 'SET_MODE'; mode: 'sandbox' | 'production' }
  // Session creation (transitions step 1 → step 2)
  | { type: 'CREATE_SESSION_PENDING' }
  | { type: 'CREATE_SESSION_DONE'; sessionId: string }
  | { type: 'CREATE_SESSION_FAILED'; error: string }
  // Drafting
  | { type: 'DRAFT_PENDING' }
  | {
      type: 'DRAFT_DONE';
      draft: CaseDraftResponse;
      allocatedCaseId: string;
      recommendedFile: string;
      routingReason?: string;
    }
  | { type: 'DRAFT_FAILED'; error: string }
  // Draft review (step 3)
  | {
      type: 'EDIT_DRAFT_FIELD';
      field: keyof CaseDraftResponse;
      value: CaseDraftResponse[keyof CaseDraftResponse];
    }
  // Validation
  | { type: 'VALIDATE_PENDING' }
  | {
      type: 'VALIDATE_DONE';
      reports: ValidationReport[];
      blockingCount: number;
      warningCount: number;
      passCount: number;
    }
  | { type: 'VALIDATE_FAILED'; error: string }
  // Attestation
  | { type: 'SET_ATTESTATION'; value: string }
  // Commit
  | { type: 'COMMIT_PENDING' }
  | { type: 'COMMIT_DONE'; result: CommitResponse }
  | { type: 'COMMIT_FAILED'; error: string }
  // Navigation
  | { type: 'GO_TO_STEP'; step: WizardStep }
  | { type: 'NEXT_STEP' }
  | { type: 'PREV_STEP' }
  | { type: 'RESET' };

// =============================================================================
// Reducer
// =============================================================================

function nextStep(s: WizardStep): WizardStep {
  if (s === 'done') return 'done';
  if (s === 6) return 'done';
  return (s + 1) as WizardStep;
}

function prevStep(s: WizardStep): WizardStep {
  if (s === 'done') return 6;
  if (s === 1) return 1;
  return (s - 1) as WizardStep;
}

export function wizardReducer(
  state: WizardState,
  action: WizardAction,
): WizardState {
  switch (action.type) {
    case 'SET_SCENARIO_FIELD':
      return {
        ...state,
        scenario: { ...state.scenario, [action.field]: action.value },
      };
    case 'SET_MODE':
      return { ...state, mode: action.mode };

    case 'CREATE_SESSION_PENDING':
      return {
        ...state,
        error: null,
        inFlight: { ...state.inFlight, creatingSession: true },
      };
    case 'CREATE_SESSION_DONE':
      return {
        ...state,
        sessionId: action.sessionId,
        step: 2,
        inFlight: { ...state.inFlight, creatingSession: false },
      };
    case 'CREATE_SESSION_FAILED':
      return {
        ...state,
        error: action.error,
        inFlight: { ...state.inFlight, creatingSession: false },
      };

    case 'DRAFT_PENDING':
      return {
        ...state,
        error: null,
        inFlight: { ...state.inFlight, drafting: true },
      };
    case 'DRAFT_DONE':
      return {
        ...state,
        draft: action.draft,
        allocatedCaseId: action.allocatedCaseId,
        recommendedFile: action.recommendedFile,
        routingReason: action.routingReason ?? state.routingReason,
        step: 3,
        inFlight: { ...state.inFlight, drafting: false },
      };
    case 'DRAFT_FAILED':
      return {
        ...state,
        error: action.error,
        inFlight: { ...state.inFlight, drafting: false },
      };

    case 'EDIT_DRAFT_FIELD':
      if (!state.draft) return state;
      return {
        ...state,
        draft: { ...state.draft, [action.field]: action.value },
        // Editing invalidates the previous validation report
        validation: [],
        blockingCount: 0,
        warningCount: 0,
        passCount: 0,
      };

    case 'VALIDATE_PENDING':
      return {
        ...state,
        error: null,
        inFlight: { ...state.inFlight, validating: true },
      };
    case 'VALIDATE_DONE':
      return {
        ...state,
        validation: action.reports,
        blockingCount: action.blockingCount,
        warningCount: action.warningCount,
        passCount: action.passCount,
        step: 4,
        inFlight: { ...state.inFlight, validating: false },
      };
    case 'VALIDATE_FAILED':
      return {
        ...state,
        error: action.error,
        inFlight: { ...state.inFlight, validating: false },
      };

    case 'SET_ATTESTATION':
      return { ...state, attestation: action.value };

    case 'COMMIT_PENDING':
      return {
        ...state,
        error: null,
        inFlight: { ...state.inFlight, committing: true },
      };
    case 'COMMIT_DONE':
      return {
        ...state,
        commitResult: action.result,
        step: 'done',
        inFlight: { ...state.inFlight, committing: false },
      };
    case 'COMMIT_FAILED':
      return {
        ...state,
        error: action.error,
        inFlight: { ...state.inFlight, committing: false },
      };

    case 'GO_TO_STEP':
      return { ...state, step: action.step, error: null };
    case 'NEXT_STEP':
      return { ...state, step: nextStep(state.step), error: null };
    case 'PREV_STEP':
      return { ...state, step: prevStep(state.step), error: null };

    case 'RESET':
      return initialWizardState;
  }
}

// =============================================================================
// Step labels
// =============================================================================

export const STEP_LABELS: Record<WizardStep, string> = {
  1: 'Scenario',
  2: 'Drafting',
  3: 'Review',
  4: 'Validation',
  5: 'Attestation',
  6: 'Commit',
  done: 'Complete',
};
