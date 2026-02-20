import React, { useState } from 'react';

export const ProviderDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  
  // Default to the "Edge Case" that we just taught the AI to handle
  const [notes, setNotes] = useState(
    "Patient presents with acute lumbar pain (2 weeks duration). Physical exam reveals significant motor weakness in right leg. Requesting immediate MRI to rule out cauda equina."
  );

  // 1. The async wrapper is back!
  const submitCase = async () => {
    setLoading(true);
    setResult(null);

    // 2. The payload is back!
    const payload = {
      request_id: "demo_" + Date.now(),
      patient_id: "p_demo",
      provider_npi: "1234567890",
      clinical_case: {
        patient_id: "p_demo",
        primary_diagnosis_code: "M54.5", // Low back pain
        procedure_code: "72148",       // MRI Lumbar Spine
        evidence: [
          {
            id: "ev_1",
            source_type: "CLINICAL_NOTE",
            description: "Physician Notes",
            original_text: notes,
            confidence: 1.0
          }
        ]
      }
    };

    try {
      // Grab auth token
      const token = localStorage.getItem('token'); 

      const response = await fetch('http://127.0.0.1:8000/api/v1/authorizations/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      // Catch HTTP errors 
      if (!response.ok) {
        if (response.status === 401) {
          alert("You are not authorized. Please log in again.");
          return; 
        }
        throw new Error(`Server responded with status: ${response.status}`);
      }

      // Success
      const data = await response.json();
      setResult(data);

    } catch (error) {
      console.error(error);
      alert("Error submitting case. Ensure backend is running and you are logged in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        
        <div className="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">New Authorization Request</h2>
          <span className="text-sm font-mono text-gray-500">CPT: 72148 (MRI Lumbar Spine)</span>
        </div>

        <div className="p-6 space-y-6">
          {/* Form */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Clinical Notes / Evidence</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full h-32 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Enter clinical details..."
            />
            <p className="text-xs text-gray-400 mt-2">
              Tip: Try removing "motor weakness" to see the request fail, or keep it to see the AI apply the new rule.
            </p>
          </div>

          <button
            onClick={submitCase}
            disabled={loading}
            className={`w-full py-4 rounded-lg font-bold text-lg shadow-md transition-all
              ${loading 
                ? 'bg-gray-100 text-gray-400' 
                : 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-lg'}
            `}
          >
            {loading ? "Processing with AI..." : "Submit for Authorization"}
          </button>
        </div>

        {/* Results Area */}
        {result && (
          <div className="border-t border-gray-100 bg-gray-50 p-6 animate-fade-in">
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wide mb-4">AI Decision Output</h3>
            
            <div className="flex items-start gap-6">
              {/* Status Badge */}
              <div className={`
                px-6 py-3 rounded-xl border-2 font-bold text-xl flex-shrink-0
                ${result.status === 'AUTO_APPROVED' 
                  ? 'bg-green-50 border-green-200 text-green-700' 
                  : 'bg-amber-50 border-amber-200 text-amber-700'}
              `}>
                {result?.status ? result.status.replace("_", " ") : "Loading..."}
              </div>
              
              {/* Rationale */}
              <div className="flex-grow">
                <div className="mb-2">
                  <span className="text-xs font-semibold text-gray-400 uppercase">Rationale</span>
                  <p className="text-gray-800 leading-relaxed mt-1">
                    {result.rationale}
                  </p>
                </div>
                
                <div className="flex gap-4 mt-4 text-sm">
                   <div className="bg-white px-3 py-1 rounded border border-gray-200 text-gray-600">
                     Confidence: <strong>{(result.confidence_score * 100).toFixed(1)}%</strong>
                   </div>
                   <div className="bg-white px-3 py-1 rounded border border-gray-200 text-gray-600">
                     Review Tier: <strong>{result.review_tier_used}</strong>
                   </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};