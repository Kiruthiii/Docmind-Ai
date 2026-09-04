import React, { useState, useEffect, useRef } from 'react';

import { Search, ShieldCheck, Sparkles, CheckCircle2, FileText, ExternalLink, ArrowRight, Eye } from 'lucide-react';

import { Badge } from '../ui/Badge';

export const MasterDocumentStage: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeState, setActiveState] = useState<number>(1);
  const [scrollProgress, setScrollProgress] = useState<number>(0);

  // Scroll listener for sticky cinematic transformations
  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const totalScrollableHeight = rect.height - windowHeight;

      if (totalScrollableHeight <= 0) return;

      const currentScroll = Math.max(0, -rect.top);
      const progress = Math.min(1, Math.max(0, currentScroll / totalScrollableHeight));
      setScrollProgress(progress);

      // Map progress smoothly across 9 states
      const step = Math.min(9, Math.max(1, Math.floor(progress * 9) + 1));
      setActiveState(step);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const statesList = [
    { id: 1, label: '01. Raw Document', title: 'Full Academic PDF Loaded' },
    { id: 2, label: '02. Question Prompt', title: 'User Asks Question' },
    { id: 3, label: '03. Laser Scanning', title: 'Scanning Page Coordinates' },
    { id: 4, label: '04. Noise Subduing', title: 'Irrelevant Text Fades' },
    { id: 5, label: '05. Evidence Highlight', title: 'Target Paragraph Lit Up' },
    { id: 6, label: '06. Evidence Extraction', title: 'Passage Extracted' },
    { id: 7, label: '07. Answerability Check', title: 'Evidence Support Verified' },
    { id: 8, label: '08. Grounded Synthesis', title: 'Answer + Citations Formed' },
    { id: 9, label: '09. Product Workspace', title: 'Full DocMind Interface' },
  ];

  return (
    <div ref={containerRef} className="relative min-h-[160vh] w-full py-6">
      {/* Sticky Pinned Cinematic Stage Container */}
      <div className="sticky top-16 z-30 max-w-6xl mx-auto px-4 sm:px-6">
        <div className="rounded-3xl bg-white border border-[#1E1B24]/15 shadow-[0_32px_80px_-16px_rgba(30,27,36,0.16)] overflow-hidden transition-all duration-500 relative">
          
          {/* Top Control Bar & State Nav */}
          <div className="bg-[#1E1B24] text-white p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#7C3AED] text-white flex items-center justify-center font-bold text-sm shadow-md shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div className="text-left">
                <span className="text-[11px] font-mono font-bold text-[#EDE7FA] uppercase tracking-wider block">
                  The Protagonist: Physical PDF Document Stage
                </span>
                <h3 className="text-sm font-semibold text-white font-sans flex items-center gap-2">
                  IEEE_Trans_Transportation_2025.pdf
                  <span className="text-xs text-[#716B78] font-mono font-normal">(Page 14 of 47)</span>
                </h3>
              </div>
            </div>

            {/* State Step Tabs */}
            <div className="flex items-center gap-1.5 bg-[#2D2937] p-1.5 rounded-2xl overflow-x-auto max-w-full">
              {statesList.map((st) => (
                <button
                  key={st.id}
                  onClick={() => setActiveState(st.id)}
                  className={`px-2.5 py-1.5 rounded-xl text-xs font-mono font-medium transition-all duration-300 cursor-pointer ${
                    activeState === st.id
                      ? 'bg-[#7C3AED] text-white shadow-md font-bold scale-105'
                      : 'text-[#716B78] hover:text-white hover:bg-white/10'
                  }`}
                  type="button"
                  title={st.title}
                >
                  0{st.id}
                </button>
              ))}
            </div>
          </div>

          {/* Interactive Progress Line */}
          <div className="w-full bg-[#1E1B24]/10 h-1.5 overflow-hidden">
            <div
              className="bg-[#7C3AED] h-full transition-all duration-500 ease-out"
              style={{ width: `${Math.max(5, scrollProgress * 100)}%` }}
            ></div>
          </div>

          {/* MAIN PROTAGONIST DOCUMENT STAGE CANVAS */}
          <div className="p-6 sm:p-10 bg-[#F8F7FC] min-h-[520px] flex flex-col justify-between space-y-6 relative text-left overflow-hidden">
            
            {/* Stage Indicator Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1E1B24]/10 pb-4">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#7C3AED]"></span>
                <span className="text-xs font-mono font-bold text-[#7C3AED] uppercase tracking-wider">
                  {statesList[activeState - 1].label} — {statesList[activeState - 1].title}
                </span>
              </div>
              <Badge variant={activeState >= 7 ? 'grounded' : 'violet'} size="md">
                {activeState === 9 ? 'Full Workspace Active' : activeState >= 7 ? 'Verified Evidence' : 'Document Analysis Active'}
              </Badge>
            </div>

            {/* STAGE DISPLAY ENGINE */}
            <div className="flex-1 transition-all duration-700 ease-in-out relative">
              
              {/* STATE 01: RAW PHYSICAL DOCUMENT */}
              {activeState === 1 && (
                <div className="bg-white p-8 rounded-2xl border border-[#1E1B24]/12 shadow-sm space-y-4 animate-in fade-in zoom-in-95 duration-500 relative overflow-hidden">
                  <div className="flex justify-between items-center text-xs font-mono text-[#716B78] border-b border-[#1E1B24]/08 pb-3">
                    <span className="font-semibold text-[#1E1B24]">Section 3.2 — Traffic Dynamics &amp; Empirical Models</span>
                    <span>Document ID: #47-14</span>
                  </div>
                  <h4 className="text-xl sm:text-2xl font-bold text-[#1E1B24] font-serif tracking-tight">
                    3.2 Empirical Density Calculation via Loop Sensors and Aerial Video Micro-Tracking
                  </h4>
                  <p className="text-xs text-[#716B78]">
                    Authors: Dr. A. Vance &amp; Prof. M. K. Thorne &bull; Published IEEE Transactions (2025)
                  </p>
                  <div className="space-y-3 text-xs sm:text-sm text-[#1E1B24]/85 leading-relaxed font-sans pt-2">
                    <p>
                      Traditional macro-level traffic monitoring relied exclusively on stationary inductive loop sensors placed at fixed 500m intervals along urban freeways. While these sensors capture flow velocity <em>V</em> effectively, spatial headway estimation degrades rapidly under congestion conditions.
                    </p>
                    <p className="p-3 bg-[#F8F7FC] rounded-xl border border-[#1E1B24]/08 font-mono text-xs">
                      Equation 4.2: &rho; = N / L = (1 / L) &times; &sum;<sub>i=1</sub><sup>N</sup> 1
                    </p>
                    <p>
                      Where <em>N</em> represents total vehicle count recorded over segment length <em>L</em> (in kilometers), with spatial sampling rates normalized to 100-meter intervals.
                    </p>
                  </div>
                </div>
              )}

              {/* STATE 02: QUESTION EMERGES */}
              {activeState === 2 && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-4 duration-500">
                  <div className="bg-[#F5F2EC] p-6 rounded-2xl border border-[#7C3AED]/40 shadow-sm space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-md">
                        <Search className="w-5 h-5" />
                      </div>
                      <div>
                        <span className="text-[11px] font-mono text-[#7C3AED] uppercase font-bold tracking-wide">
                          User Question Intent Detected
                        </span>
                        <h4 className="text-lg sm:text-xl font-bold text-[#1E1B24]">
                          &ldquo;How is traffic density calculated in urban mobility models?&rdquo;
                        </h4>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-2xl border border-[#1E1B24]/10 text-xs text-[#716B78] space-y-2 opacity-80">
                    <div className="flex justify-between font-mono text-[11px] text-[#1E1B24] font-semibold">
                      <span>Query Parameters Target: Formula &amp; Methodology</span>
                      <span>Targeting Page 14</span>
                    </div>
                    <p className="italic font-serif">
                      Ready to execute semantic scanning across 47 pages...
                    </p>
                  </div>
                </div>
              )}

              {/* STATE 03: LASER SCANNING */}
              {activeState === 3 && (
                <div className="bg-white p-8 rounded-2xl border border-[#7C3AED]/40 space-y-4 shadow-editorial relative overflow-hidden animate-in fade-in duration-500">
                  {/* Laser Scan Line Overlay */}
                  <div className="absolute top-0 left-0 right-0 h-1 bg-[#7C3AED] shadow-[0_0_15px_#7C3AED] animate-pulse"></div>

                  <div className="flex justify-between items-center text-xs font-mono text-[#7C3AED] font-bold border-b border-[#1E1B24]/08 pb-3">
                    <span className="flex items-center gap-2">
                      <Eye className="w-4 h-4" /> Scanning Document Coordinates...
                    </span>
                    <span>Page 14 &bull; Paragraph 3</span>
                  </div>

                  <div className="space-y-3 text-xs sm:text-sm text-[#1E1B24] leading-relaxed">
                    <p className="opacity-60">Traditional macro-level traffic monitoring relied on loop sensors...</p>
                    <div className="p-4 bg-[#EDE7FA]/80 rounded-xl border border-[#7C3AED] font-semibold text-[#1E1B24]">
                      &ldquo;Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length of lane at an instantaneous moment in time: &rho; = N / L.&rdquo;
                    </div>
                    <p className="opacity-60">Where N represents vehicle count over segment length L...</p>
                  </div>
                </div>
              )}

              {/* STATE 04: NOISE SUBDUING */}
              {activeState === 4 && (
                <div className="bg-white p-8 rounded-2xl border border-[#7C3AED]/40 space-y-4 shadow-editorial animate-in fade-in duration-500">
                  <div className="flex justify-between items-center text-xs font-mono text-[#5B21B6] font-bold border-b border-[#1E1B24]/08 pb-3">
                    <span>IRRELEVANT TEXT SUBDUED (15% OPACITY)</span>
                    <span>TARGET ISOLATED</span>
                  </div>

                  <p className="text-xs text-[#716B78] opacity-20 filter blur-[0.4px] select-none">
                    Traditional macro-level traffic monitoring relied exclusively on stationary inductive loop sensors placed at fixed 500m intervals along urban freeways...
                  </p>

                  <div className="p-5 bg-[#EDE7FA] border-l-4 border-[#7C3AED] rounded-r-2xl space-y-2 shadow-md">
                    <span className="text-[10px] font-mono font-bold text-[#5B21B6] uppercase">Isolated Target Snippet</span>
                    <p className="text-sm sm:text-base font-bold text-[#1E1B24] leading-relaxed">
                      &ldquo;Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length of lane at an instantaneous moment in time: &rho; = N / L.&rdquo;
                    </p>
                  </div>

                  <p className="text-xs text-[#716B78] opacity-20 filter blur-[0.4px] select-none">
                    In modern computer vision RAG pipelines, spatial density coordinates are verified against visual bounding boxes...
                  </p>
                </div>
              )}

              {/* STATE 05: EVIDENCE HIGHLIGHT */}
              {activeState === 5 && (
                <div className="bg-white p-8 rounded-2xl border-2 border-[#7C3AED] space-y-4 shadow-editorial animate-in fade-in duration-500 relative">
                  <div className="absolute -top-3 right-6 bg-[#7C3AED] text-white text-[10px] uppercase tracking-wider font-bold px-3 py-1 rounded-full shadow-sm">
                    Evidence Passage Highlighted
                  </div>

                  <div className="p-6 bg-[#EDE7FA] rounded-2xl border border-[#7C3AED]/40 space-y-3">
                    <span className="text-xs font-mono text-[#5B21B6] font-bold">Page 14 &bull; Paragraph 3 &bull; Eq. 4.2</span>
                    <p className="text-base sm:text-lg font-bold text-[#1E1B24] leading-relaxed">
                      &ldquo;Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length of lane at an instantaneous moment in time: &rho; = N / L.&rdquo;
                    </p>
                  </div>
                </div>
              )}

              {/* STATE 06: EVIDENCE EXTRACTION */}
              {activeState === 6 && (
                <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="text-xs font-mono text-[#7C3AED] font-bold uppercase">
                    Extracted Evidence Passage
                  </div>
                  <div className="bg-white p-6 rounded-2xl border border-[#7C3AED]/40 shadow-xl space-y-3 transform scale-105">
                    <div className="flex items-center justify-between text-xs text-[#5B21B6] font-mono">
                      <span>Source: IEEE_Trans_Transportation_2025.pdf</span>
                      <span>Page 14</span>
                    </div>
                    <p className="text-sm sm:text-base font-bold text-[#1E1B24] leading-relaxed">
                      &ldquo;Traffic density (&rho;) is formally defined as: &rho; = N / L.&rdquo;
                    </p>
                  </div>
                </div>
              )}

              {/* STATE 07: ANSWERABILITY CHECK */}
              {activeState === 7 && (
                <div className="bg-[#F0FDF4] p-8 rounded-2xl border border-[#15803D]/40 space-y-4 shadow-grounded animate-in fade-in duration-500">
                  <div className="flex items-center justify-between">
                    <Badge variant="grounded" size="md" icon={<ShieldCheck className="w-4 h-4" />}>
                      Answerability Validated
                    </Badge>
                    <span className="text-xs font-mono text-[#15803D] font-bold">Validation Agent: Evidence Support Confirmed</span>
                  </div>

                  <h4 className="text-lg font-bold text-[#1E1B24]">
                    Validation Agent Confirmation: Sufficient Evidence Present
                  </h4>

                  <p className="text-xs sm:text-sm text-[#1E1B24] bg-white p-4 rounded-xl border border-[#15803D]/25 font-medium leading-relaxed">
                    The extracted paragraph contains supporting mathematical formulation and spatial normalization parameters. Proceeding to answer synthesis.
                  </p>
                </div>
              )}

              {/* STATE 08: GROUNDED SYNTHESIS */}
              {activeState === 8 && (
                <div className="bg-white p-8 rounded-2xl border border-[#7C3AED]/40 space-y-5 shadow-editorial animate-in fade-in duration-500 text-left">
                  <div className="flex items-center justify-between border-b border-[#1E1B24]/10 pb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center shadow-md">
                        <Sparkles className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-[#1E1B24]">DocMind Grounded Output</h4>
                        <p className="text-xs text-[#716B78]">Synthesized from verified document evidence</p>
                      </div>
                    </div>
                    <Badge variant="grounded" size="sm" icon={<CheckCircle2 className="w-3.5 h-3.5" />}>
                      Verified Answer
                    </Badge>
                  </div>

                  <div className="space-y-3 text-xs sm:text-sm text-[#1E1B24] leading-relaxed">
                    <p>
                      Based on <strong>Section 3.2 (Page 14)</strong> of <em>IEEE_Trans_Transportation_2025.pdf</em>, traffic density (&rho;) is calculated as total vehicle count <em>N</em> over segment length <em>L</em>:
                    </p>

                    <div className="p-3.5 bg-[#F5F2EC] rounded-xl border border-[#1E1B24]/10 font-mono text-xs font-bold text-[#5B21B6]">
                      &rho; = N / L
                    </div>

                    <div className="pt-3 border-t border-[#1E1B24]/08 flex items-center justify-between text-xs">
                      <span className="text-[#5B21B6] font-mono font-semibold flex items-center gap-1">
                        <FileText className="w-3.5 h-3.5 text-[#7C3AED]" />
                        Cited: [IEEE_Trans_Transportation_2025.pdf, p. 14, ¶3]
                      </span>
                      <span className="text-[#7C3AED] font-semibold hover:underline cursor-pointer flex items-center gap-1">
                        Inspect Source <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* STATE 09: FULL PRODUCT WORKSPACE SEAMLESS TRANSITION */}
              {activeState === 9 && (
                <div className="bg-[#1E1B24] text-white p-6 sm:p-8 rounded-2xl border border-white/20 shadow-2xl space-y-6 animate-in fade-in zoom-in-95 duration-500">
                  <div className="flex items-center justify-between border-b border-white/10 pb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-[#7C3AED] text-white flex items-center justify-center font-bold text-xs">
                        DM
                      </div>
                      <span className="text-sm font-bold text-white font-sans">
                        DocMind AI Workspace Interface
                      </span>
                    </div>
                    <Badge variant="grounded" size="sm">
                      Active Workspace Session
                    </Badge>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-12 gap-4 text-xs text-left">
                    <div className="md:col-span-4 bg-white/05 p-3.5 rounded-xl border border-white/10 space-y-2">
                      <span className="text-[10px] font-mono text-[#EDE7FA] uppercase font-bold">Document Reader</span>
                      <p className="text-white font-semibold">IEEE_Trans_Transportation_2025.pdf</p>
                      <p className="text-[#716B78] text-[11px]">Page 14 selected &bull; Section 3.2</p>
                    </div>
                    <div className="md:col-span-8 bg-white/10 p-4 rounded-xl border border-white/15 space-y-2">
                      <span className="text-[10px] font-mono text-[#4ADE80] font-bold">Grounded Chat &amp; Citations</span>
                      <p className="text-xs text-[#EDE7FA] leading-relaxed">
                        &ldquo;Traffic density (&rho;) is calculated as &rho; = N / L [Doc 1, p.14, ¶3].&rdquo;
                      </p>
                    </div>
                  </div>
                </div>
              )}

            </div>

            {/* Bottom Scroll Cue Indicator Bar */}
            <div className="pt-3 border-t border-[#1E1B24]/08 flex items-center justify-between text-xs text-[#716B78]">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#7C3AED]"></span>
                <span className="font-mono">Scroll down to advance visual transformation</span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveState((prev) => (prev > 1 ? prev - 1 : 9))}
                  className="px-3 py-1.5 bg-white border border-[#1E1B24]/10 rounded-xl hover:bg-[#F8F7FC] transition-colors cursor-pointer text-xs"
                  type="button"
                >
                  Prev
                </button>
                <button
                  onClick={() => setActiveState((prev) => (prev < 9 ? prev + 1 : 1))}
                  className="px-4 py-1.5 bg-[#7C3AED] text-white rounded-xl hover:bg-[#5B21B6] transition-colors font-semibold flex items-center gap-1 cursor-pointer text-xs"
                  type="button"
                >
                  Next <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};
