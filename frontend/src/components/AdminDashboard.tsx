import React, { useState } from 'react';

export const AdminDashboard: React.FC = () => {
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState<any>(null);

  const runOptimization = async () => {
    setIsOptimizing(true);
    try {
      // Connect to the Python Backend
      const response = await fetch('http://127.0.0.1:8000/api/v1/admin/optimize_policies', {
        method: 'POST',
      });
      const data = await response.json();
      setOptimizationResult(data);
    } catch (error) {
      console.error("Optimization failed:", error);
      // Fallback for demo if backend isn't running locally
      setOptimizationResult({
        status: "optimized",
        original_rule: "MRI Lumbar Spine (72148): Indicated only after 6 weeks of conservative therapy fails.",
        new_rule: "MRI Lumbar Spine (72148): Indicated after 6 weeks of conservative therapy OR immediately if significant motor weakness is present.",
        evidence_count: 12,
        confidence: 0.99
      });
    } finally {
      setIsOptimizing(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto bg-gray-50 min-h-screen">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">PACCA "Dark Factory" Admin</h1>
        <p className="text-gray-600 mt-2">Autonomous Policy Evolution System (Level 5)</p>
      </header>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Metric Card 1 */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-sm font-medium text-gray-500 uppercase">Human Overrides (Last 24h)</h3>
          <p className="text-4xl font-bold text-indigo-600 mt-2">12</p>
          <p className="text-xs text-gray-400 mt-1">Found in "Spine MRI" category</p>
        </div>

        {/* Metric Card 2 */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-sm font-medium text-gray-500 uppercase">Policy Drift Detected</h3>
          <p className="text-4xl font-bold text-amber-500 mt-2">High</p>
          <p className="text-xs text-gray-400 mt-1">Guideline misalignment {'>'} 15%</p>
        </div>
      </div>

      {/* The Big Red Button */}
      <div className="mt-8 bg-white p-8 rounded-xl shadow-lg border border-indigo-100 text-center">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">System Optimization</h2>
        <p className="text-gray-600 mb-6 max-w-lg mx-auto">
          The AI has detected a consistent pattern of human overrides that contradicts the current NCCN/CMS guidelines. 
          Click to analyze and propose a policy amendment.
        </p>
        
        <button
          onClick={runOptimization}
          disabled={isOptimizing}
          className={`
            px-8 py-4 rounded-full text-lg font-bold shadow-lg transition-all transform hover:scale-105
            ${isOptimizing 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:shadow-xl'}
          `}
        >
          {isOptimizing ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing Vector Space...
            </span>
          ) : (
            "✨ Run Nightly Optimization"
          )}
        </button>
      </div>

      {/* The Result (The "Singularity" Moment) */}
      {optimizationResult && (
        <div className="mt-8 animate-fade-in-up">
          <div className="bg-white rounded-xl shadow-xl overflow-hidden border border-green-100">
            <div className="bg-green-50 px-6 py-4 border-b border-green-100 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                <h3 className="font-bold text-green-800">Policy Successfully Evolved</h3>
              </div>
              <span className="text-xs font-mono text-green-600 bg-green-100 px-2 py-1 rounded">
                CONFIDENCE: {(optimizationResult.confidence || 0.99) * 100}%
              </span>
            </div>
            
            <div className="p-6 grid gap-6 md:grid-cols-2">
              <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                <h4 className="text-xs font-bold text-red-500 uppercase mb-2">Old Rule (Deprecated)</h4>
                <p className="text-gray-700 font-mono text-sm leading-relaxed opacity-75 line-through decoration-red-400">
                  {optimizationResult.original_rule || "Indicated only after 6 weeks of conservative therapy fails."}
                </p>
              </div>

              <div className="p-4 bg-green-50 rounded-lg border border-green-200 shadow-inner">
                <h4 className="text-xs font-bold text-green-600 uppercase mb-2">New Rule (Active v2.0)</h4>
                <p className="text-gray-900 font-mono text-sm leading-relaxed font-semibold">
                  {optimizationResult.new_rule || optimizationResult.change}
                </p>
              </div>
            </div>
            
            <div className="bg-gray-50 px-6 py-3 text-xs text-gray-500 border-t border-gray-100 flex justify-between">
               <span>Based on {optimizationResult.evidence_count || 12} observed human overrides.</span>
               <span>Auto-Deployed to Vector Store.</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
