import React, { useState, useEffect } from 'react';

import { Search, ShieldCheck, Sparkles, CheckCircle2, FileText, ExternalLink, ArrowRight, Eye, Layers } from 'lucide-react';

import { Badge } from '../ui/Badge';

export const InteractiveDocumentStage: React.FC = () => {
  const [activeStage, setActiveStage] = useState<number>(1);

  const stages = [
    { id: 1, title: '01. Raw Document', label: 'PDF Upload & Layout Parsing' },
    { id: 2, title: '02. Question Focus', label: 'Intent & Entity Extraction' },
    { id: 3, title: '03. Semantic Retrieval', label: 'Noise Subduing & Chunk Indexing' },
    { id: 4, title: '04. Evidence Grounding', label: 'Answerability Verification' },
    { id: 5, title: '05. Grounded Answer', label: 'Synthesized Answer + Page Citations' },
  ];

  // Auto-play through stages if user prefers passive viewing
  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStage((prev) => (prev % 5) + 1);
    }, 8000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="w-full max-w-5xl mx-auto rounded-3xl bg-white border border-[#1E1B24]/12 shadow-[0_24px_48px_-12px_rgba(30,27,36,0.08)] overflow-hidden transition-all duration-500">
      {/* Interactive Story Header Navigation Bar */}
      <div className="bg-[#1E1B24] text-white p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center font-bold text-sm shadow-md">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-mono font-bold text-[#EDE7FA] uppercase tracking-wider block">
              DocMind Story Pipeline
            </span>
            <h3 className="text-sm font-semibold text-white font-sans">
              Interactive Document &rarr; Evidence Grounding Workflow
            </h3>
          </div>
        </div>

        {/* Stage Selector Pills */}
        <div className="flex items-center gap-1 bg-[#2D2937] p-1.5 rounded-2xl overflow-x-auto max-w-full">
          {stages.map((st) => (
            <button
              key={st.id}
              onClick={() => setActiveStage(st.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all duration-300 cursor-pointer ${
                activeStage === st.id
                  ? 'bg-[#7C3AED] text-white shadow-md font-semibold'
                  : 'text-[#716B78] hover:text-white hover:bg-white/10'
              }`}
              type="button"
            >
              {st.title}
            </button>
          ))}
        </div>
      </div>

      {/* Main Interactive Stage Stage View */}
      <div className="p-6 sm:p-10 bg-[#F8F7FC] min-h-[480px] flex flex-col justify-between space-y-8 relative">
        {/* Stage Progress Bar Indicator */}
        <div className="w-full bg-[#1E1B24]/10 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-[#7C3AED] h-full transition-all duration-700 ease-out"
            style={{ width: `${(activeStage / 5) * 100}%` }}
          ></div>
        </div>

        {/* Stage Content Renderers */}
        <div className="flex-1 space-y-6">
          {/* STAGE 1: RAW DOCUMENT */}
          {activeStage === 1 && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1E1B24]/10 pb-3">
                <div className="flex items-center gap-2 text-xs font-mono text-[#716B78]">
                  <FileText className="w-4 h-4 text-[#7C3AED]" />
                  <span className="font-semibold text-[#1E1B24]">IEEE_Trans_Transportation_2025.pdf</span>
                  <span>(47 Pages indexed)</span>
                </div>
                <Badge variant="violet" size="sm">
                  Stage 1: Document Uploaded
                </Badge>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-[#1E1B24]/10 space-y-3 shadow-sm">
                <span className="text-[10px] uppercase font-mono tracking-widest text-[#7C3AED] bg-[#EDE7FA] px-2.5 py-1 rounded-md font-bold">
                  Document View — Page 14
                </span>
                <h4 className="text-lg font-bold text-[#1E1B24] font-serif">
                  3.2 Empirical Density Calculation via Loop Sensors and Aerial Micro-Tracking
                </h4>
                <p className="text-xs text-[#716B78] leading-relaxed">
                  Authors: Dr. A. Vance &amp; Prof. M. K. Thorne &bull; IEEE Transactions on Transportation (2025)
                </p>
                <p className="text-xs text-[#1E1B24]/80 leading-relaxed font-sans pt-2">
                  Traditional macro-level traffic monitoring relied exclusively on stationary inductive loop sensors placed at fixed 500m intervals along urban freeways. While these sensors capture flow velocity <em>V</em> effectively, spatial headway estimation degrades under heavy congestion...
                </p>
              </div>
            </div>
          )}

          {/* STAGE 2: QUESTION FOCUS */}
          {activeStage === 2 && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1E1B24]/10 pb-3">
                <div className="flex items-center gap-2 text-xs font-mono text-[#7C3AED] font-semibold">
                  <Search className="w-4 h-4" />
                  <span>Question Intent: Methodology &amp; Formula Retrieval</span>
                </div>
                <Badge variant="violet" size="sm">
                  Stage 2: User Question
                </Badge>
              </div>

              <div className="bg-[#F5F2EC] p-5 rounded-2xl border border-[#1E1B24]/10 space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#7C3AED] text-white flex items-center justify-center font-bold text-xs">
                    Q
                  </div>
                  <p className="text-base font-bold text-[#1E1B24]">
                    &ldquo;How is traffic density calculated in urban mobility models?&rdquo;
                  </p>
                </div>
                <div className="pl-11 text-xs text-[#716B78] flex items-center gap-3">
                  <span className="bg-white px-2.5 py-1 rounded border border-[#1E1B24]/10 font-mono">
                    Target Section: Methodology
                  </span>
                  <span className="bg-white px-2.5 py-1 rounded border border-[#1E1B24]/10 font-mono">
                    Entities: [&quot;traffic density&quot;, &quot;equation&quot;]
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* STAGE 3: SEMANTIC RETRIEVAL & SUBDUING */}
          {activeStage === 3 && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1E1B24]/10 pb-3">
                <div className="flex items-center gap-2 text-xs font-mono text-[#5B21B6] font-semibold">
                  <Eye className="w-4 h-4" />
                  <span>Noise Subdued &bull; Evidence Isolated</span>
                </div>
                <Badge variant="violet" size="sm">
                  Stage 3: Retrieval
                </Badge>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-[#7C3AED]/30 space-y-4 shadow-sm">
                <p className="text-xs text-[#716B78] opacity-40 blur-[0.2px] leading-relaxed">
                  Traditional macro-level traffic monitoring relied exclusively on stationary inductive loop sensors...
                </p>

                <div className="p-4 bg-[#EDE7FA] border-l-4 border-[#7C3AED] rounded-r-xl space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-mono font-bold text-[#5B21B6]">
                    <span>Extracted Passage Candidate (Page 14, ¶3)</span>
                    <span>Relevance: High</span>
                  </div>
                  <p className="text-xs sm:text-sm font-semibold text-[#1E1B24] leading-relaxed">
                    &ldquo;Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length of lane at an instantaneous moment in time: &rho; = N / L.&rdquo;
                  </p>
                </div>

                <p className="text-xs text-[#716B78] opacity-40 blur-[0.2px] leading-relaxed">
                  In modern computer vision RAG pipelines, spatial density coordinates are verified against overhead footage...
                </p>
              </div>
            </div>
          )}

          {/* STAGE 4: EVIDENCE GROUNDING */}
          {activeStage === 4 && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1E1B24]/10 pb-3">
                <div className="flex items-center gap-2 text-xs font-mono text-[#15803D] font-semibold">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Answerability Verification: Passed</span>
                </div>
                <Badge variant="grounded" size="sm">
                  Stage 4: Validation
                </Badge>
              </div>

              <div className="bg-[#F0FDF4] p-6 rounded-2xl border border-[#15803D]/30 space-y-4 shadow-sm">
                <div className="flex items-center justify-between text-xs text-[#15803D] font-bold">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Factual Claim Support Confirmed
                  </span>
                  <span className="font-mono text-[11px] bg-white px-2.5 py-0.5 rounded border border-[#15803D]/30">
                    Chunk ID: #14-3
                  </span>
                </div>

                <p className="text-xs sm:text-sm text-[#1E1B24] font-medium leading-relaxed bg-white p-4 rounded-xl border border-[#15803D]/20">
                  The document explicitly provides the mathematical definition (&rho; = N / L) and spatial normalization parameters (100m intervals). The question is supported by document evidence.
                </p>
              </div>
            </div>
          )}

          {/* STAGE 5: GROUNDED ANSWER */}
          {activeStage === 5 && (
            <div className="space-y-4 animate-in fade-in duration-500">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#1E1B24]/10 pb-3">
                <div className="flex items-center gap-2 text-xs font-mono text-[#7C3AED] font-semibold">
                  <Sparkles className="w-4 h-4" />
                  <span>DocMind Grounded Output</span>
                </div>
                <Badge variant="grounded" size="sm">
                  Stage 5: Synthesized Answer
                </Badge>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-[#7C3AED]/30 space-y-4 shadow-md text-left">
                <p className="text-xs sm:text-sm text-[#1E1B24] leading-relaxed font-medium">
                  Based on <strong>Section 3.2 (Page 14)</strong> of <em>IEEE_Trans_Transportation_2025.pdf</em>, traffic density (&rho;) is calculated as total vehicle count <em>N</em> over segment length <em>L</em>:
                </p>

                <div className="p-3.5 bg-[#F5F2EC] rounded-xl border border-[#1E1B24]/10 font-mono text-xs text-[#5B21B6] font-bold">
                  &rho; = N / L
                </div>

                <div className="flex items-center justify-between text-xs pt-2 border-t border-[#1E1B24]/08">
                  <span className="text-[#5B21B6] font-mono flex items-center gap-1 font-semibold">
                    <FileText className="w-3.5 h-3.5 text-[#7C3AED]" />
                    Cited: [IEEE_Trans_Transportation_2025.pdf, p. 14, ¶3]
                  </span>
                  <span className="text-[#7C3AED] font-semibold hover:underline cursor-pointer flex items-center gap-1">
                    Inspect PDF Page <ExternalLink className="w-3 h-3" />
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Control Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-[#1E1B24]/10 text-xs text-[#716B78]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#7C3AED]"></span>
            <span>Current Scene: {stages.find((s) => s.id === activeStage)?.label}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveStage((prev) => (prev > 1 ? prev - 1 : 5))}
              className="px-3 py-1.5 bg-white border border-[#1E1B24]/10 rounded-xl hover:bg-[#F8F7FC] transition-colors cursor-pointer"
              type="button"
            >
              Previous Scene
            </button>
            <button
              onClick={() => setActiveStage((prev) => (prev < 5 ? prev + 1 : 1))}
              className="px-4 py-1.5 bg-[#7C3AED] text-white rounded-xl hover:bg-[#5B21B6] transition-colors font-semibold flex items-center gap-1.5 cursor-pointer"
              type="button"
            >
              Next Scene <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
