import React, { useState } from 'react';

export function DirectorQueue() {
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  
  // For the portfolio demo, we hardcode a "gray area" case that the AI flagged for review.
  const [queue, setQueue] = useState([
    {
      id: "REQ-8842",
      patient: "Jane Doe (DOB: 04/12/1978)",
      diagnosis: "M54.5 (Low back pain)",
      procedure: "72148 (MRI Lumbar Spine)",
      clinical_notes: "Patient presents with acute lower back pain that started 2 weeks ago after lifting a heavy box. No numbness or weakness. Requesting MRI to see what is wrong.",
      ai_status: "IN_REVIEW",
      ai_rationale: "Frontline Nurse Agent Confidence: 0.82. The guidelines explicitly require 6 weeks of conservative therapy (PT, NSAIDs) for routine back pain without red flags. Patient has only had pain for 2 weeks."
    }
  ]);

  const handleOverride = async (caseItem: any) => {
    setStatusMessage("Injecting human override into Vector Database...");
    
    // The rationale the human doctor provides for overriding the AI
    const humanRationale = "Medical Director Override: Patient is a manual laborer and primary earner. Delaying imaging risks long-term structural damage that could permanently prevent return to work. Approved as an exception.";

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/authorizations/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // If you secured the feedback route, it will use this token:
          'Authorization': `Bearer ${localStorage.getItem('token')}` 
        },
        body: JSON.stringify({
          case_summary: caseItem.clinical_notes,
          decision: "APPROVED",
          rationale: humanRationale
        })
      });

      if (response.ok) {
        setStatusMessage("✅ Success! The AI has learned this precedent. It will reference this decision for future cases.");
        // Remove the case from the UI queue
        setQueue(queue.filter(c => c.id !== caseItem.id));
      } else {
        setStatusMessage("❌ Failed to submit override.");
      }
    } catch (error) {
      setStatusMessage(`❌ Connection error. Is the backend running?`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-800">Medical Director Queue</h2>
        <p className="text-gray-600 mt-2">Review complex cases escalated by the AI Orchestrator.</p>
      </div>

      {statusMessage && (
        <div className="mb-6 p-4 bg-indigo-50 border border-indigo-200 text-indigo-800 rounded-md shadow-sm font-medium">
          {statusMessage}
        </div>
      )}

      {queue.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-lg shadow border border-gray-200">
          <p className="text-xl text-gray-500">🎉 The queue is empty. Great job!</p>
        </div>
      ) : (
        queue.map((caseItem) => (
          <div key={caseItem.id} className="bg-white rounded-lg shadow-md border-l-4 border-amber-500 overflow-hidden mb-6">
            <div className="bg-gray-50 px-6 py-4 border-b flex justify-between items-center">
              <div>
                <span className="text-sm font-bold text-gray-500 uppercase tracking-wider">Case ID: {caseItem.id}</span>
                <h3 className="text-lg font-bold text-gray-800 mt-1">{caseItem.patient}</h3>
              </div>
              <span className="px-3 py-1 bg-amber-100 text-amber-800 font-semibold rounded-full text-sm">
                {caseItem.ai_status}
              </span>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-500 font-semibold">Diagnosis</p>
                  <p className="text-gray-800">{caseItem.diagnosis}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 font-semibold">Requested Procedure</p>
                  <p className="text-gray-800">{caseItem.procedure}</p>
                </div>
              </div>

              <div className="mb-6">
                <p className="text-sm text-gray-500 font-semibold mb-1">Clinical Notes</p>
                <div className="p-3 bg-gray-50 rounded border border-gray-200 text-gray-700 text-sm">
                  {caseItem.clinical_notes}
                </div>
              </div>

              <div className="mb-6">
                <p className="text-sm text-amber-600 font-bold mb-1">AI Escalation Rationale</p>
                <div className="p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded text-sm italic">
                  "{caseItem.ai_rationale}"
                </div>
              </div>

              <div className="flex gap-4 border-t pt-4">
                <button 
                  onClick={() => handleOverride(caseItem)}
                  className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-bold rounded transition-colors shadow-sm"
                >
                  Override & Approve (Teach AI)
                </button>
                <button 
                  onClick={() => setQueue(queue.filter(c => c.id !== caseItem.id))}
                  className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white font-bold rounded transition-colors shadow-sm"
                >
                  Confirm Denial
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}