/**
 * TypeScript types for the SME Case Authoring Web UI.
 *
 * Mirrors the Pydantic wire-format models in
 * `src/pacca/api/models/sme_authoring.py`.
 *
 * Hand-maintained (no OpenAPI codegen yet). When the backend contract
 * changes, this file must be updated in lock-step. The `kind`
 * discriminator field on response envelopes enables exhaustive
 * narrowing in the React layer.
 */

// =============================================================================
// Primitives — mirror src/pacca/agents/sme_authoring/models.py
// =============================================================================

export type ValidationOutcome = 'pass' | 'fail' | 'warn';

export type ValidatorName =
  | 'phi_scan'
  | 'guideline_citation'
  | 'schema_completeness'
  | 'outcome_branch_consistency'
  | 'reasoning_specificity'
  | 'judge_criteria_specificity';

export interface ValidationReport {
  validator: ValidatorName;
  outcome: ValidationOutcome;
  reason: string;
  field_path: string | null;
}

export type IntendedOutcome =
  | 'AUTO_APPROVED'
  | 'IN_REVIEW'
  | 'DENIED'
  | 'PRE_FLIGHT_ESCALATE'
  | 'INFORMATION_NEEDED';

export interface SMEScenario {
  description: string;
  intended_specialty: string | null;
  intended_outcome: IntendedOutcome | null;
  failure_mode_label: string | null;
}

export interface CaseDraftResponse {
  case_id: string;
  title: string;
  diagnosis_code: string;
  diagnosis_description: string;
  procedure_code: string;
  procedure_description: string;
  clinical_notes: string;
  guidelines_context: string;
  expected_outcome: string;
  expected_branch: string;
  reasoning_must_include: string[];
  reasoning_must_not_include: string[];
  prior_denial_codes: string[];
  clinical_rationale: string;
  judge_scoring_criteria: string;
}

export type SessionMode = 'sandbox' | 'production' | 'git_worktree';

export interface SessionState {
  session_id: string;
  created_at: string;
  last_updated_at: string;
  mode: SessionMode;
  sme_attestation: string | null;
  scenario: SMEScenario | null;
  draft: CaseDraftResponse | null;
  last_validation_report: ValidationReport[];
  last_step: string;
}

// =============================================================================
// Request/Response envelopes — mirror api/models/sme_authoring.py
// =============================================================================

export interface CreateSessionRequest {
  scenario: SMEScenario;
  mode?: 'sandbox' | 'production';
}

export interface SessionResponse {
  kind: 'session';
  session: SessionState;
}

export interface SessionListResponse {
  kind: 'session_list';
  sessions: SessionState[];
  total: number;
}

export interface DraftResponse {
  kind: 'draft';
  draft: CaseDraftResponse;
  allocated_case_id: string;
  recommended_file: string;
  routing_reason: string;
}

export interface ValidateRequest {
  draft?: CaseDraftResponse;
}

export interface ValidateResponse {
  kind: 'validation';
  reports: ValidationReport[];
  blocking_count: number;
  warning_count: number;
  pass_count: number;
}

export interface CommitRequest {
  sme_attestation: string;
  draft?: CaseDraftResponse;
  confirm_production_write?: boolean;
}

export interface CommitResponse {
  kind: 'commit';
  written: boolean;
  target_file: string;
  case_id: string;
  pr_title: string;
  pr_body: string;
  integrity_test_passed: boolean;
  integrity_test_summary: string;
}

export interface ListCount {
  list_name: string;
  file: string;
  count: number;
  id_range: string;
}

export interface GapItem {
  category: string;
  label: string;
  current_count: number;
  target_count: number;
  cases_needed: number;
  priority: number;
  description: string;
}

export interface StatusResponse {
  kind: 'status';
  total_cases: number;
  per_list_counts: ListCount[];
  milestone_gaps: GapItem[];
  coverage_parsed_ok: boolean;
  coverage_parse_error: string;
}

export interface BatchCaseItem {
  case_id: string;
  description: string;
}

export interface BatchItem {
  batch_id: string;
  name: string;
  case_count: number;
  id_range: string;
  target_file: string;
  is_new_file: boolean;
  cases: BatchCaseItem[];
}

export interface BatchListResponse {
  kind: 'batch_list';
  batches: BatchItem[];
  total: number;
}

export interface BatchResponse {
  kind: 'batch';
  batch: BatchItem;
}

export interface GapListResponse {
  kind: 'gap_list';
  gaps: GapItem[];
  total: number;
}

// =============================================================================
// WebSocket event union — typewriter-style streaming for /draft-stream
// =============================================================================

export interface WSDeltaEvent {
  type: 'delta';
  field: string;
  content: string;
}

export interface WSDoneEvent {
  type: 'done';
  draft: CaseDraftResponse;
  allocated_case_id: string;
  recommended_file: string;
}

export interface WSErrorEvent {
  type: 'error';
  message: string;
  recoverable: boolean;
}

export interface WSHeartbeatEvent {
  type: 'heartbeat';
  timestamp: string;
}

export type WSEvent =
  | WSDeltaEvent
  | WSDoneEvent
  | WSErrorEvent
  | WSHeartbeatEvent;

// =============================================================================
// Error envelope
// =============================================================================

export interface ApiError {
  detail: string;
}
