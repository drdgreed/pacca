import { useState } from 'react';
import { ArrowLeft, Send, AlertCircle } from 'lucide-react';
import { useSubmitAuthorization } from '../hooks/useApi';
import type { Authorization, AuthorizationSubmission } from '../types';

interface NewAuthorizationFormProps {
  onSubmitted: (auth: Authorization) => void;
  onCancel: () => void;
}

const TREATMENT_CATEGORIES = [
  { value: 'medication', label: 'Medication' },
  { value: 'procedure', label: 'Procedure' },
  { value: 'imaging', label: 'Imaging' },
  { value: 'lab_test', label: 'Lab Test' },
  { value: 'dme', label: 'Durable Medical Equipment' },
  { value: 'rehabilitation', label: 'Rehabilitation' },
];

const URGENCY_LEVELS = [
  { value: 'routine', label: 'Routine (24-48 hours)' },
  { value: 'expedited', label: 'Expedited (4-24 hours)' },
  { value: 'urgent', label: 'Urgent (Same day)' },
  { value: 'emergent', label: 'Emergent (Immediate)' },
];

export function NewAuthorizationForm({
  onSubmitted,
  onCancel,
}: NewAuthorizationFormProps) {
  const { loading, error, submit } = useSubmitAuthorization();

  // Form state
  const [formData, setFormData] = useState({
    // Patient
    patientId: '',
    patientDob: '',
    patientGender: 'M',

    // Diagnosis
    diagnosisCode: '',
    diagnosisDescription: '',

    // Treatment
    treatmentCode: '',
    treatmentDescription: '',
    treatmentCategory: 'medication',
    estimatedCost: '',

    // Provider
    providerId: '',
    providerName: '',
    facilityName: '',

    // Payer
    payerId: '',
    payerName: '',
    memberId: '',

    // Additional
    clinicalNotes: '',
    urgency: 'routine',
  });

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const submission: AuthorizationSubmission = {
      patient: {
        id: formData.patientId,
        date_of_birth: formData.patientDob,
        gender: formData.patientGender,
      },
      diagnosis: {
        code: formData.diagnosisCode,
        description: formData.diagnosisDescription,
        is_primary: true,
      },
      treatment: {
        code: formData.treatmentCode,
        code_type: 'HCPCS',
        description: formData.treatmentDescription,
        category: formData.treatmentCategory,
        estimated_cost: formData.estimatedCost
          ? parseFloat(formData.estimatedCost)
          : undefined,
      },
      provider: {
        provider_id: formData.providerId,
        provider_name: formData.providerName,
        facility_name: formData.facilityName || undefined,
      },
      payer: {
        payer_id: formData.payerId,
        payer_name: formData.payerName,
        member_id: formData.memberId,
      },
      clinical_notes: formData.clinicalNotes || undefined,
      urgency: formData.urgency as 'routine' | 'expedited' | 'urgent' | 'emergent',
    };

    try {
      const result = await submit(submission);
      onSubmitted(result);
    } catch {
      // Error is handled by the hook
    }
  };

  const loadDemoData = () => {
    setFormData({
      patientId: 'P-DEMO-001',
      patientDob: '1966-05-15',
      patientGender: 'M',
      diagnosisCode: 'C34.1',
      diagnosisDescription: 'Malignant neoplasm of upper lobe, bronchus or lung',
      treatmentCode: 'J9271',
      treatmentDescription: 'Pembrolizumab (Keytruda) 200mg IV infusion',
      treatmentCategory: 'medication',
      estimatedCost: '15000',
      providerId: '1234567890',
      providerName: 'Dr. Michael Chen',
      facilityName: 'Regional Cancer Center',
      payerId: 'BCBS001',
      payerName: 'Blue Cross Blue Shield',
      memberId: 'MEM123456789',
      clinicalNotes:
        'Patient with stage IIIA non-small cell lung cancer (adenocarcinoma). PD-L1 TPS 65% (high expression). EGFR/ALK negative. ECOG performance status 1. Requesting first-line pembrolizumab monotherapy per NCCN guidelines.',
      urgency: 'expedited',
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={onCancel}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Cancel
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              New Authorization Request
            </h2>
            <p className="text-gray-500 mt-1">
              Submit a prior authorization for AI-assisted evaluation
            </p>
          </div>
        </div>
        <button
          onClick={loadDemoData}
          className="px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 transition-colors"
        >
          Load Demo Data
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-danger-50 border border-danger-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-danger-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-danger-800">Submission Failed</p>
            <p className="text-sm text-danger-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Patient Information */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Patient Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Patient ID *
              </label>
              <input
                type="text"
                name="patientId"
                value={formData.patientId}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="P-12345"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date of Birth *
              </label>
              <input
                type="date"
                name="patientDob"
                value={formData.patientDob}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Gender *
              </label>
              <select
                name="patientGender"
                value={formData.patientGender}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
              </select>
            </div>
          </div>
        </div>

        {/* Diagnosis */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Primary Diagnosis
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                ICD-10 Code *
              </label>
              <input
                type="text"
                name="diagnosisCode"
                value={formData.diagnosisCode}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="C34.1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <input
                type="text"
                name="diagnosisDescription"
                value={formData.diagnosisDescription}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Diagnosis description"
              />
            </div>
          </div>
        </div>

        {/* Treatment */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Requested Treatment
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Treatment Code *
              </label>
              <input
                type="text"
                name="treatmentCode"
                value={formData.treatmentCode}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="J9271"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category *
              </label>
              <select
                name="treatmentCategory"
                value={formData.treatmentCategory}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                {TREATMENT_CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description *
              </label>
              <input
                type="text"
                name="treatmentDescription"
                value={formData.treatmentDescription}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Treatment description"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estimated Cost ($)
              </label>
              <input
                type="number"
                name="estimatedCost"
                value={formData.estimatedCost}
                onChange={handleChange}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="15000"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Urgency *
              </label>
              <select
                name="urgency"
                value={formData.urgency}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                {URGENCY_LEVELS.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Provider */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Requesting Provider
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider NPI *
              </label>
              <input
                type="text"
                name="providerId"
                value={formData.providerId}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="1234567890"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider Name *
              </label>
              <input
                type="text"
                name="providerName"
                value={formData.providerName}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Dr. Jane Smith"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Facility Name
              </label>
              <input
                type="text"
                name="facilityName"
                value={formData.facilityName}
                onChange={handleChange}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="City Medical Center"
              />
            </div>
          </div>
        </div>

        {/* Payer */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Insurance Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payer ID *
              </label>
              <input
                type="text"
                name="payerId"
                value={formData.payerId}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="BCBS001"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Payer Name *
              </label>
              <input
                type="text"
                name="payerName"
                value={formData.payerName}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Blue Cross Blue Shield"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Member ID *
              </label>
              <input
                type="text"
                name="memberId"
                value={formData.memberId}
                onChange={handleChange}
                required
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="MEM123456789"
              />
            </div>
          </div>
        </div>

        {/* Clinical Notes */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Clinical Notes
          </h3>
          <textarea
            name="clinicalNotes"
            value={formData.clinicalNotes}
            onChange={handleChange}
            rows={5}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500"
            placeholder="Provide clinical context, relevant history, and rationale for the requested treatment..."
          />
          <p className="text-sm text-gray-500 mt-2">
            Include relevant clinical history, test results, and medical
            necessity justification.
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-3 border rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Processing...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Submit Authorization Request
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
