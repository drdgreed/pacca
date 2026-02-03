import { useEffect, useState } from 'react';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  FileText,
  User,
  Stethoscope,
  Brain,
  Shield,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useExplanation, useHumanReview, useAuthorization } from '../hooks/useApi';
import type { Authorization } from '../types';

interface AuthorizationDetailProps {
  authorization: Authorization;
  onBack: () => void;
}

export function AuthorizationDetail({
  authorization: initialAuth,
  onBack,
}: AuthorizationDetailProps) {
  const [auth, setAuth] = useState(initialAuth);
  const [showExplanation, setShowExplanation] = useState(false);
  const [reviewDecision, setReviewDecision] = useState<string>('');
  const [reviewNotes, setReviewNotes] = useState('');

  const { data: explanation, loading: loadingExplanation, fetch: fetchExplanation } =
    useExplanation(auth.request_id);
  const { loading: submittingReview, submitReview } = useHumanReview();
  const { fetch: refreshAuth } = useAuthorization(auth.request_id);

  useEffect(() => {
    if (showExplanation && !explanation) {
      fetchExplanation();
    }
  }, [showExplanation, explanation, fetchExplanation]);

  const handleSubmitReview = async () => {
    if (!reviewDecision) return;

    try {
      const result = await submitReview(auth.request_id, {
        decision: reviewDecision as 'approve' | 'deny' | 'approve_with_conditions',
        reviewer_id: 'DEMO_REVIEWER',
        reviewer_notes: reviewNotes || undefined,
      });
      setAuth(result);
    } catch (error) {
      console.error('Review submission failed:', error);
    }
  };

  const statusConfig = getStatusDisplay(auth.status, auth.decision);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to List
        </button>
        <span className="text-sm font-mono text-gray-500">{auth.request_id}</span>
      </div>

      {/* Status Banner */}
      <div className={`rounded-xl p-6 ${statusConfig.bgClass}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-full ${statusConfig.iconBgClass}`}>
              <statusConfig.icon className={`w-6 h-6 ${statusConfig.iconClass}`} />
            </div>
            <div>
              <h2 className={`text-xl font-bold ${statusConfig.textClass}`}>
                {statusConfig.title}
              </h2>
              {auth.confidence_score !== null && (
                <p className={`text-sm ${statusConfig.subtextClass}`}>
                  AI Confidence: {(auth.confidence_score * 100).toFixed(0)}%
                </p>
              )}
            </div>
          </div>
          {auth.decision_summary && (
            <p className={`text-sm max-w-md ${statusConfig.subtextClass}`}>
              {auth.decision_summary}
            </p>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Clinical Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Treatment Request */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <Stethoscope className="w-5 h-5 text-primary-600" />
              <h3 className="text-lg font-semibold text-gray-900">
                Treatment Request
              </h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-500">Requested Treatment</label>
                <p className="font-medium text-gray-900">
                  {auth.treatment_code} — {auth.treatment_description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-500">Primary Diagnosis</label>
                  <p className="font-medium text-gray-900">
                    {auth.diagnosis_code}
                  </p>
                  <p className="text-sm text-gray-600">
                    {auth.diagnosis_description}
                  </p>
                </div>
                <div>
                  <label className="text-sm text-gray-500">Urgency</label>
                  <p className="font-medium text-gray-900 capitalize">
                    {auth.urgency}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <button
              onClick={() => setShowExplanation(!showExplanation)}
              className="w-full flex items-center justify-between"
            >
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-purple-600" />
                <h3 className="text-lg font-semibold text-gray-900">
                  AI Decision Explanation
                </h3>
              </div>
              {showExplanation ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </button>

            {showExplanation && (
              <div className="mt-4 space-y-4">
                {loadingExplanation ? (
                  <div className="text-center py-8 text-gray-500">
                    Loading explanation...
                  </div>
                ) : explanation ? (
                  <>
                    <div>
                      <label className="text-sm text-gray-500">Summary</label>
                      <p className="text-gray-900">{explanation.summary}</p>
                    </div>

                    <div>
                      <label className="text-sm text-gray-500">
                        Detailed Reasoning
                      </label>
                      <p className="text-gray-700 whitespace-pre-line">
                        {explanation.detailed_reasoning}
                      </p>
                    </div>

                    {explanation.key_evidence_points.length > 0 && (
                      <div>
                        <label className="text-sm text-gray-500">
                          Key Evidence Points
                        </label>
                        <ul className="list-disc list-inside text-gray-700 space-y-1">
                          {explanation.key_evidence_points.map((point, i) => (
                            <li key={i}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {explanation.evidence_gaps.length > 0 && (
                      <div>
                        <label className="text-sm text-gray-500">
                          Evidence Gaps
                        </label>
                        <ul className="list-disc list-inside text-warning-600 space-y-1">
                          {explanation.evidence_gaps.map((gap, i) => (
                            <li key={i}>{gap}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {explanation.safety_concerns.length > 0 && (
                      <div>
                        <label className="text-sm text-gray-500">
                          Safety Concerns
                        </label>
                        <ul className="list-disc list-inside text-danger-600 space-y-1">
                          {explanation.safety_concerns.map((concern, i) => (
                            <li key={i}>{concern}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-gray-500">
                    No explanation available for this decision.
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Human Review Section */}
          {auth.requires_human_review && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-5 h-5 text-orange-600" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Human Review Required
                </h3>
              </div>

              {auth.escalation_reasons.length > 0 && (
                <div className="mb-4 p-3 bg-orange-50 rounded-lg">
                  <p className="text-sm font-medium text-orange-800 mb-2">
                    Escalation Reasons:
                  </p>
                  <ul className="list-disc list-inside text-sm text-orange-700">
                    {auth.escalation_reasons.map((reason, i) => (
                      <li key={i}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Your Decision
                  </label>
                  <div className="flex gap-3">
                    <button
                      onClick={() => setReviewDecision('approve')}
                      className={`flex-1 py-3 px-4 rounded-lg border-2 transition-colors ${
                        reviewDecision === 'approve'
                          ? 'border-success-500 bg-success-50 text-success-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <CheckCircle className="w-5 h-5 mx-auto mb-1" />
                      Approve
                    </button>
                    <button
                      onClick={() => setReviewDecision('deny')}
                      className={`flex-1 py-3 px-4 rounded-lg border-2 transition-colors ${
                        reviewDecision === 'deny'
                          ? 'border-danger-500 bg-danger-50 text-danger-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <XCircle className="w-5 h-5 mx-auto mb-1" />
                      Deny
                    </button>
                    <button
                      onClick={() => setReviewDecision('approve_with_conditions')}
                      className={`flex-1 py-3 px-4 rounded-lg border-2 transition-colors ${
                        reviewDecision === 'approve_with_conditions'
                          ? 'border-warning-500 bg-warning-50 text-warning-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <AlertTriangle className="w-5 h-5 mx-auto mb-1" />
                      Conditional
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Review Notes (Optional)
                  </label>
                  <textarea
                    value={reviewNotes}
                    onChange={(e) => setReviewNotes(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                    placeholder="Add any notes about your decision..."
                  />
                </div>

                <button
                  onClick={handleSubmitReview}
                  disabled={!reviewDecision || submittingReview}
                  className="w-full py-3 px-4 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {submittingReview ? 'Submitting...' : 'Submit Review Decision'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Metadata */}
        <div className="space-y-6">
          {/* Patient Info */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-gray-600" />
              <h3 className="text-lg font-semibold text-gray-900">Patient</h3>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-sm text-gray-500">Patient ID</label>
                <p className="font-mono text-gray-900">{auth.patient_id}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">Age</label>
                <p className="text-gray-900">{auth.patient_age} years</p>
              </div>
            </div>
          </div>

          {/* Classification */}
          {(auth.complexity || auth.specialty) && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="w-5 h-5 text-gray-600" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Classification
                </h3>
              </div>
              <div className="space-y-3">
                {auth.complexity && (
                  <div>
                    <label className="text-sm text-gray-500">Complexity</label>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-500 h-2 rounded-full"
                          style={{ width: `${(auth.complexity / 5) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700">
                        {auth.complexity}/5
                      </span>
                    </div>
                  </div>
                )}
                {auth.specialty && (
                  <div>
                    <label className="text-sm text-gray-500">Specialty</label>
                    <p className="text-gray-900 capitalize">{auth.specialty}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Conditions */}
          {auth.conditions.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Approval Conditions
              </h3>
              <ul className="space-y-2">
                {auth.conditions.map((condition, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-gray-700"
                  >
                    <CheckCircle className="w-4 h-4 text-success-500 flex-shrink-0 mt-0.5" />
                    {condition}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Timeline */}
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Timeline</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Submitted</span>
                <span className="text-gray-900">
                  {new Date(auth.submitted_at).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Last Updated</span>
                <span className="text-gray-900">
                  {new Date(auth.updated_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function getStatusDisplay(status: string, decision: string | null) {
  if (decision === 'approve' || status === 'approved') {
    return {
      icon: CheckCircle,
      title: 'Authorization Approved',
      bgClass: 'bg-success-50 border border-success-200',
      iconBgClass: 'bg-success-100',
      iconClass: 'text-success-600',
      textClass: 'text-success-800',
      subtextClass: 'text-success-600',
    };
  }

  if (decision === 'deny' || status === 'denied') {
    return {
      icon: XCircle,
      title: 'Authorization Denied',
      bgClass: 'bg-danger-50 border border-danger-200',
      iconBgClass: 'bg-danger-100',
      iconClass: 'text-danger-600',
      textClass: 'text-danger-800',
      subtextClass: 'text-danger-600',
    };
  }

  if (status === 'pending_review' || status === 'escalated') {
    return {
      icon: Clock,
      title: 'Pending Human Review',
      bgClass: 'bg-warning-50 border border-warning-200',
      iconBgClass: 'bg-warning-100',
      iconClass: 'text-warning-600',
      textClass: 'text-warning-800',
      subtextClass: 'text-warning-600',
    };
  }

  return {
    icon: Clock,
    title: 'Processing',
    bgClass: 'bg-blue-50 border border-blue-200',
    iconBgClass: 'bg-blue-100',
    iconClass: 'text-blue-600',
    textClass: 'text-blue-800',
    subtextClass: 'text-blue-600',
  };
}
