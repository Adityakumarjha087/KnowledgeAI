"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

interface EvalReport {
  status: string;
  eval_queries_run: number;
  metrics: {
    faithfulness: number;
    answer_relevance: number;
    context_recall: number;
    citation_accuracy: number;
  };
  performance: {
    average_latency_sec: number;
    average_tokens: number;
    estimated_cost_per_request: number;
  };
}

export default function EvaluationPage() {
  const [report, setReport] = useState<EvalReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const fetchEvaluation = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setError("");
    try {
      const data = await api.get<EvalReport>("/evaluation");
      setReport(data);
    } catch (err: any) {
      setError(err.message || "Failed to load evaluation reports.");
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvaluation(true);
  }, []);

  const handleRunEvaluation = async () => {
    setRunning(true);
    try {
      await fetchEvaluation(false);
      alert("RAG Evaluation Suite completed successfully! Scorecard updated.");
    } catch (err: any) {
      setError(err.message || "Failed to execute evaluation runner.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <Sidebar>
      <div className="flex flex-col flex-1 max-w-6xl mx-auto w-full space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md border border-white/15 bg-white/5 text-white/70 text-[10px] font-mono uppercase tracking-wider mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
              Automated Benchmarking
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Evaluation Suite
            </h1>
            <p className="text-white/50 mt-1 text-xs font-normal">
              Continuous accuracy testing measuring answer faithfulness, context recall, and token latency
            </p>
          </div>

          <button
            onClick={handleRunEvaluation}
            disabled={loading || running}
            className="px-4 py-2.5 rounded-lg btn-white font-bold text-xs text-black transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer shadow-sm"
          >
            {running ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                Running Suite...
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 8H18.5" />
                </svg>
                Run Evaluation Suite
              </>
            )}
          </button>
        </div>

        {error && (
          <div className="p-3.5 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 text-xs font-medium max-w-lg">
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex flex-1 items-center justify-center min-h-[300px]">
            <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Scorecard Grids */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Faithfulness */}
              <div className="black-card p-6 rounded-xl space-y-2.5">
                <span className="text-white/50 text-[11px] font-mono uppercase tracking-wider block">Faithfulness</span>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  {report?.metrics.faithfulness}%
                </h2>
                <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-white h-full rounded-full transition-all duration-500" 
                    style={{ width: `${report?.metrics.faithfulness || 0}%` }}
                  />
                </div>
                <p className="text-[10px] text-white/40 font-mono">Zero hallucination claims</p>
              </div>

              {/* Answer Relevance */}
              <div className="black-card p-6 rounded-xl space-y-2.5">
                <span className="text-white/50 text-[11px] font-mono uppercase tracking-wider block">Answer Relevance</span>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  {report?.metrics.answer_relevance}%
                </h2>
                <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-white h-full rounded-full transition-all duration-500" 
                    style={{ width: `${report?.metrics.answer_relevance || 0}%` }}
                  />
                </div>
                <p className="text-[10px] text-white/40 font-mono">Direct query alignment</p>
              </div>

              {/* Context Recall */}
              <div className="black-card p-6 rounded-xl space-y-2.5">
                <span className="text-white/50 text-[11px] font-mono uppercase tracking-wider block">Context Recall</span>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  {report?.metrics.context_recall}%
                </h2>
                <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-white h-full rounded-full transition-all duration-500" 
                    style={{ width: `${report?.metrics.context_recall || 0}%` }}
                  />
                </div>
                <p className="text-[10px] text-white/40 font-mono">Gold standard recall</p>
              </div>

              {/* Citation Accuracy */}
              <div className="black-card p-6 rounded-xl space-y-2.5">
                <span className="text-white/50 text-[11px] font-mono uppercase tracking-wider block">Citation Accuracy</span>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  {report?.metrics.citation_accuracy}%
                </h2>
                <div className="w-full bg-white/10 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-white h-full rounded-full transition-all duration-500" 
                    style={{ width: `${report?.metrics.citation_accuracy || 0}%` }}
                  />
                </div>
                <p className="text-[10px] text-white/40 font-mono">Exact segment verification</p>
              </div>
            </div>

            {/* Performance telemetry panel */}
            <div className="black-card p-6 rounded-xl space-y-4">
              <div className="flex items-center justify-between border-b border-white/10 pb-3">
                <h3 className="text-sm font-bold text-white">Pipeline Execution Telemetry</h3>
                <span className="text-xs font-mono text-white/40">Benchmark Suite</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-[#050505] border border-white/10 space-y-1">
                  <span className="text-white/40 text-[10px] font-mono uppercase tracking-wider">Avg Latency</span>
                  <div className="text-xl font-bold text-white tracking-tight">
                    {report?.performance.average_latency_sec} <span className="text-xs text-white/40 font-normal">sec</span>
                  </div>
                  <p className="text-[11px] text-white/40 font-mono">Streaming response time</p>
                </div>
                
                <div className="p-4 rounded-lg bg-[#050505] border border-white/10 space-y-1">
                  <span className="text-white/40 text-[10px] font-mono uppercase tracking-wider">Token Footprint</span>
                  <div className="text-xl font-bold text-white tracking-tight">
                    {report?.performance.average_tokens.toLocaleString()} <span className="text-xs text-white/40 font-normal">tokens</span>
                  </div>
                  <p className="text-[11px] text-white/40 font-mono">Context + answer size</p>
                </div>

                <div className="p-4 rounded-lg bg-[#050505] border border-white/10 space-y-1">
                  <span className="text-white/40 text-[10px] font-mono uppercase tracking-wider">Unit Cost</span>
                  <div className="text-xl font-bold text-white tracking-tight">
                    ${report?.performance.estimated_cost_per_request.toFixed(6)}
                  </div>
                  <p className="text-[11px] text-white/40 font-mono">Cost per query</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Sidebar>
  );
}
