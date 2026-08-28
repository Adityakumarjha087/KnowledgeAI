"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { api } from "@/lib/api";

interface Metrics {
  total_users: number;
  total_documents: number;
  total_questions: number;
  average_response_time_sec: number;
  average_retrieval_time_sec: number;
  total_tokens_used: number;
  total_estimated_cost_usd: number;
  total_feedback_submissions: number;
  helpfulness_rating_percent: number;
  error_rate_percent: number;
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const data = await api.get<Metrics>("/metrics");
        setMetrics(data);
      } catch (err: any) {
        setError(err.message || "Failed to load metrics dashboard.");
      } finally {
        setLoading(false);
      }
    }
    fetchMetrics();
  }, []);

  return (
    <Sidebar>
      <div className="flex flex-col flex-1 max-w-6xl mx-auto w-full space-y-8">
        {/* Page Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md border border-white/15 bg-white/5 text-white/70 text-[10px] font-mono uppercase tracking-wider mb-2">
              <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
              Live Observability
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Dashboard
            </h1>
            <p className="text-white/50 mt-1 text-xs font-normal">
              Real-time system telemetry, latency tracking, and cost metrics for your knowledge repository
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-3 py-1.5 rounded-lg border border-white/15 bg-[#0a0a0a] text-xs font-mono text-white/80 font-medium flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Operational
            </span>
          </div>
        </div>

        {loading ? (
          <div className="flex flex-1 items-center justify-center min-h-[300px]">
            <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl border border-red-500/30 bg-red-500/10 text-red-300 text-xs font-medium max-w-lg">
            {error}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Grid of Key Metrics Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Card 1: Documents */}
              <div className="black-card p-6 rounded-xl space-y-2">
                <span className="text-white/50 text-[11px] font-mono uppercase tracking-wider block">Indexed Documents</span>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  {metrics?.total_documents}
                </h2>
                <p className="text-[11px] text-white/40 font-normal">PDF, DOCX, TXT, and Markdown</p>
              </div>

              {/* Card 2: Questions */}
              <div className="black-card p-6 rounded-xl space-y-2">
                <span className="text-white/50 text-[11px] font-mono uppercase tracking-wider block">Queries Answered</span>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  {metrics?.total_questions}
                </h2>
                <p className="text-[11px] text-white/40 font-normal">Processed with session memory</p>
              </div>

              {/* Card 3: Response Time */}
              <div className="black-card p-6 rounded-xl space-y-2">
                <span className="text-white/50 text-[11px] font-mono uppercase tracking-wider block">Avg Latency</span>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  {metrics?.average_response_time_sec}s
                </h2>
                <p className="text-[11px] text-white/40 font-normal">
                  Retrieval: {metrics?.average_retrieval_time_sec}s
                </p>
              </div>

              {/* Card 4: Estimated Cost */}
              <div className="black-card p-6 rounded-xl space-y-2">
                <span className="text-white/50 text-[11px] font-mono uppercase tracking-wider block">Token Spend</span>
                <h2 className="text-3xl font-extrabold text-white tracking-tight">
                  ${metrics?.total_estimated_cost_usd.toFixed(4)}
                </h2>
                <p className="text-[11px] text-white/40 font-normal">
                  Tokens: {metrics?.total_tokens_used.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Performance & Quality Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Box 1: Helpful Ratings */}
              <div className="black-card p-6 rounded-xl space-y-3">
                <h3 className="text-sm font-bold text-white">Helpfulness Feedback</h3>
                <div className="flex items-center gap-5">
                  <div className="text-4xl font-extrabold text-white">
                    {metrics?.helpfulness_rating_percent}%
                  </div>
                  <div className="flex-1 space-y-1.5">
                    <p className="text-xs text-white/60 font-normal leading-relaxed">
                      Percentage of generated answers rated as <strong className="text-white font-semibold">helpful</strong> by users.
                    </p>
                    <div className="w-full bg-white/10 border border-white/10 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-white h-full rounded-full transition-all duration-500" 
                        style={{ width: `${metrics?.helpfulness_rating_percent || 0}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Box 2: Error Rates */}
              <div className="black-card p-6 rounded-xl space-y-3">
                <h3 className="text-sm font-bold text-white">RAG Error Rate</h3>
                <div className="flex items-center gap-5">
                  <div className={`text-4xl font-extrabold ${metrics && metrics.error_rate_percent > 5 ? "text-red-400" : "text-white/60"}`}>
                    {metrics?.error_rate_percent}%
                  </div>
                  <div className="flex-1 space-y-1.5">
                    <p className="text-xs text-white/60 font-normal leading-relaxed">
                      Percentage of retrieval or inference operations encountering issues.
                    </p>
                    <div className="w-full bg-white/10 border border-white/10 h-2 rounded-full overflow-hidden">
                      <div 
                        className="bg-white/40 h-full rounded-full transition-all duration-500" 
                        style={{ width: `${metrics?.error_rate_percent || 0}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Sidebar>
  );
}
