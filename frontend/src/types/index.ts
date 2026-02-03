// API Types for PACCA Frontend

export type AuthorizationStatus =
  | 'submitted'
  | 'validating'
  | 'evidence_gathering'
  | 'classifying'
  | 'evaluating'
  | 'pending_review'
  | 'in_review'
  | 'escalated'
  | 'approved'
  | 'denied'
  | 'approved_with_conditions'
  | 'withdrawn'
  | 'expired'
  | 'failed'
  | 'incomplete';

export type DecisionOutcome =
  | 'approve'
  | 'deny'
  | 'approve_with_conditions'
  | 'request_more_info'
  | 'escalate'
  | 'unable_to_determine';

export type UrgencyLevel = 'routine' | 'expedited' | 'urgent' | 'emergent';

export type ComplexityLevel = 1 | 2 | 3 | 4 | 5;

export interface Authorization {
  request_id: string;
  status: AuthorizationStatus;
  submitted_at: string;
  updated_at: string;
  patient_id: string;
  patient_age: number;
  diagnosis_code: string;
  diagnosis_description: string;
  treatment_code: string;
  treatment_description: string;
  complexity: ComplexityLevel | null;
  specialty: string | null;
  urgency: UrgencyLevel;
  decision: DecisionOutcome | null;
  confidence_score: number | null;
  decision_summary: string | null;
  conditions: string[];
  requires_human_review: boolean;
  escalation_reasons: string[];
}

export interface AuthorizationListResponse {
  items: Authorization[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExplanationResponse {
  request_id: string;
  decision: string;
  confidence_score: number;
  summary: string;
  detailed_reasoning: string;
  key_evidence_points: string[];
  evidence_gaps: string[];
  clinical_risks: string[];
  safety_concerns: string[];
  guideline_alignment: string | null;
}

export interface PatientInput {
  id: string;
  date_of_birth: string;
  gender: string;
  zip_code?: string;
}

export interface DiagnosisInput {
  code: string;
  description: string;
  is_primary?: boolean;
  onset_date?: string;
}

export interface TreatmentInput {
  code: string;
  code_type: string;
  description: string;
  category: string;
  quantity?: number;
  estimated_cost?: number;
}

export interface ProviderInput {
  provider_id: string;
  provider_name: string;
  specialty?: string;
  facility_name?: string;
}

export interface PayerInput {
  payer_id: string;
  payer_name: string;
  member_id: string;
  plan_name?: string;
}

export interface AuthorizationSubmission {
  patient: PatientInput;
  diagnosis: DiagnosisInput;
  secondary_diagnoses?: DiagnosisInput[];
  treatment: TreatmentInput;
  provider: ProviderInput;
  payer: PayerInput;
  clinical_notes?: string;
  urgency?: UrgencyLevel;
}

export interface HumanReviewInput {
  decision: 'approve' | 'deny' | 'approve_with_conditions';
  reviewer_id: string;
  reviewer_notes?: string;
  conditions?: string[];
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  environment: string;
  timestamp: string;
  checks: Record<string, unknown>;
}

export interface MetricsResponse {
  uptime_seconds: number;
  requests_total: number;
  authorizations_processed: number;
  autonomous_decisions: number;
  escalated_decisions: number;
  average_processing_time_ms: number;
}
