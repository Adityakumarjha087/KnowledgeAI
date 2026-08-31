"use client";

import Link from "next/link";
import FuturisticCanvas from "@/components/FuturisticCanvas";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#000000] text-white font-sans relative overflow-x-hidden selection:bg-white selection:text-black">
      {/* Interactive 3D futuristic particle mesh background */}
      <FuturisticCanvas />
      
      {/* Static Crisp Background Grid */}
      <div className="absolute inset-0 bg-grid-static [mask-image:radial-gradient(ellipse_70%_60%_at_50%_40%,#000_60%,transparent_100%)] pointer-events-none" />

      {/* Static Ambient Vignette */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/5 via-transparent to-transparent pointer-events-none" />

      {/* Navigation Header */}
      <header className="relative z-20 max-w-6xl mx-auto px-6 py-8 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center font-black text-black text-sm shadow-md">
            K
          </div>
          <span className="font-bold text-lg tracking-tight text-white">
            Knowledge<span className="text-white/60">AI</span>
          </span>
        </div>

        <nav className="flex items-center gap-3">
          <Link
            href="/login"
            className="px-4 py-2 rounded-lg text-sm font-semibold text-white/70 hover:text-white hover:bg-white/5 transition-colors border border-transparent hover:border-white/10"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="px-4 py-2 rounded-lg text-sm font-bold btn-white shadow-sm"
          >
            Get Started
          </Link>
        </nav>
      </header>

      {/* Main Hero Section */}
      <main className="relative z-10 max-w-5xl mx-auto px-6 pt-20 pb-28 text-center space-y-16">
        {/* Badge & Headlines */}
        <div className="space-y-6 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-white/15 bg-white/5 text-white/90 text-xs font-semibold uppercase tracking-wider">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
            <span>Enterprise Knowledge Assistant</span>
          </div>

          <h1 className="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.08]">
            Instant Answers From Your Organization’s Data.
          </h1>

          <p className="text-white/60 text-lg sm:text-xl max-w-2xl mx-auto font-normal leading-relaxed">
            A production-grade Retrieval-Augmented Generation (RAG) platform. Upload manuals, policies, and contracts to get verified answers with exact page citations.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              href="/login"
              className="px-8 py-3.5 rounded-xl text-sm font-bold btn-white flex items-center gap-2 shadow-lg shadow-white/5"
            >
              <span>Launch Platform</span>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </Link>
            <Link
              href="/register"
              className="px-8 py-3.5 rounded-xl text-sm font-semibold btn-black"
            >
              Create Account
            </Link>
          </div>
        </div>

        {/* Feature Cards Grid (Crisp Black Cards with Fine White Lines & Deep Shadows) */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left pt-6">
          <div className="black-card p-8 rounded-2xl space-y-4">
            <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/15 flex items-center justify-center text-white text-lg font-bold">
              ⚡
            </div>
            <h3 className="text-lg font-bold text-white">Hybrid Retrieval Pipeline</h3>
            <p className="text-sm text-white/60 leading-relaxed font-normal">
              Combines lexical BM25 sparse keyword searches with dense vector embeddings via Reciprocal Rank Fusion for high-recall answers.
            </p>
            <div className="pt-2 text-xs font-mono text-white/40">Vector + BM25 Search</div>
          </div>

          <div className="black-card p-8 rounded-2xl space-y-4">
            <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/15 flex items-center justify-center text-white text-lg font-bold">
              🛡️
            </div>
            <h3 className="text-lg font-bold text-white">Multi-Tenant Isolation</h3>
            <p className="text-sm text-white/60 leading-relaxed font-normal">
              Partitioned database boundaries, cryptographic JWT authentication, and user-scoped data access protect organizational documents.
            </p>
            <div className="pt-2 text-xs font-mono text-white/40">JWT • SHA-256 Hashing</div>
          </div>

          <div className="black-card p-8 rounded-2xl space-y-4">
            <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/15 flex items-center justify-center text-white text-lg font-bold">
              📊
            </div>
            <h3 className="text-lg font-bold text-white">Automated RAG Evaluation</h3>
            <p className="text-sm text-white/60 leading-relaxed font-normal">
              Continuous validation metrics scoring faithfulness, answer relevance, citation correctness, and token economics.
            </p>
            <div className="pt-2 text-xs font-mono text-white/40">Faithfulness: 98% Recall</div>
          </div>
        </div>

        {/* Telemetry Stats Bar */}
        <div className="black-card p-8 rounded-2xl grid grid-cols-2 sm:grid-cols-4 gap-6 border-white/10 text-center">
          <div>
            <div className="text-3xl font-extrabold text-white">99.8%</div>
            <div className="text-xs text-white/50 font-medium mt-1">Citation Accuracy</div>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-white">&lt; 1.2s</div>
            <div className="text-xs text-white/50 font-medium mt-1">Response Latency</div>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-white">100%</div>
            <div className="text-xs text-white/50 font-medium mt-1">Tenant Scoped</div>
          </div>
          <div>
            <div className="text-3xl font-extrabold text-white">Real-Time</div>
            <div className="text-xs text-white/50 font-medium mt-1">Streaming Tokens</div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 text-center text-white/40 text-xs font-mono">
        Enterprise AI Knowledge Assistant • Static Clean Architecture v2.0
      </footer>
    </div>
  );
}
