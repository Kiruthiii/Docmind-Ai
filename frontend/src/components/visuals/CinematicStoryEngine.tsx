import { useState, useEffect, useRef } from 'react';

import { Search, ShieldCheck, Sparkles, CheckCircle2, FileText, ExternalLink, Eye, Layers, ChevronDown } from 'lucide-react';

import { Badge } from '../ui/Badge';

export const CinematicStoryEngine: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = useState<number>(1);
  const [scrollProgress, setScrollProgress] = useState<number>(0);

  // Scroll listener to update story step as user scrolls through the sticky container
  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const totalScrollableHeight = rect.height - windowHeight;

      if (totalScrollableHeight <= 0) return;

      // Calculate progress from 0 to 1 when container is in view
      const currentScroll = Math.max(0, -rect.top);
      const progress = Math.min(1, Math.max(0, currentScroll / totalScrollableHeight));
      setScrollProgress(progress);

      // Map progress to steps 1..5
      if (progress < 0.2) {
        setActiveStep(1);
      } else if (progress < 0.4) {
        setActiveStep(2);
      } else if (progress < 0.6) {
        setActiveStep(3);
      } else if (progress < 0.8) {
        setActiveStep(4);
      } else {
        setActiveStep(5);
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const storySteps = [
    {
      step: 1,
      badge: 'Step 01 — Full Document',
      title: 'Dense PDF Parsing',
      subtitle: 'Multi-page academic research PDF loaded into memory.',
    },
    {
      step: 2,
      badge: 'Step 02 — User Question',
      title: 'Intent & Target Analysis',
      subtitle: 'Extracting question parameters, section targets, and entity scopes.',
    },
    {
      step: 3,
      badge: 'Step 03 — Semantic Retrieval',
      title: 'Noise Subduing & Focus',
      subtitle: 'Subduing irrelevant paragraphs to highlight target evidence coordinates.',
    },
    {
      step: 4,
      badge: 'Step 04 — Evidence Grounding',
      title: 'Answerability Verification',
      subtitle: 'Validating that extracted passage contains sufficient proof before generating.',
    },
    {
      step: 5,
      badge: 'Step 05 — Grounded Answer',
      title: 'Verifiable Synthesis',
      subtitle: 'Synthesizing factual output anchored to page-level citations.',
    },
  ];

  return (
    <div ref={containerRef} className="relative min-h-[220vh] w-full py-8">
      {/* Sticky Pinned Stage Container */}
      <div className="sticky top-20 z-30 max-w-5xl mx-auto px-4 sm:px-6">
        <div className="rounded-3xl bg-white border border-[#1E1B24]/12 shadow-[0_32px_64px_-16px_rgba(30,27,36,0.12)] overflow-hidden transition-all duration-500">
          
          {/* Top Control & Timeline Navigation Bar */}
          <div className="bg-[#1E1B24] text-white p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[#7C3AED] text-white flex items-center justify-center font-bold text-sm shadow-md shrink-0">
                <Layers className="w-5 h-5" />
              </div>
              <div className="text-left">
                <span className="text-[11px] font-mono font-bold text-[#EDE7FA] uppercase tracking-wider block">
                  Scroll-Driven Intelligence Engine
                </span>
                <h3 className="text-sm font-semibold text-white font-sans">
                  Document &rarr; Question &rarr; Retrieval &rarr; Evidence &rarr; Grounded Answer
                </h3>
              </div>
            </div>

            {/* Interactive Step Buttons */}
            <div className="flex items-center gap-1 bg-[#2D2937] p-1.5 rounded-2xl overflow-x-auto max-w-full">
              {storySteps.map((st) => (
                <button
                  key={st.step}
                  onClick={() => setActiveStep(st.step)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-all duration-300 cursor-pointer ${
                    activeStep === st.step
                      ? 'bg-[#7C3AED] text-white shadow-md font-semibold'
                      : 'text-[#716B78] hover:text-white hover:bg-white/10'
                  }`}
                  type="button"
                >
                  0{st.step}
                </button>
              ))}
            </div>
          </div>

          {/* Sticky Stage Active Progress Bar */}
          <div className="w-full bg-[#1E1B24]/10 h-1.5 overflow-hidden">
            <div
              className="bg-[#7C3AED] h-full transition-all duration-500 ease-out"
              style={{ width: `${Math.max(5, scrollProgress * 100)}%` }}
            ></div>
          </div>

          {/* Persistent Visual Stage Object Area */}
          <div className="p-6 sm:p-10 bg-[#F8F7FC] min-h-[460px] flex flex-col justify-between space-y-6 relative text-left">
            
            {/* Step Label Header */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1E1B24]/10 pb-4">
              <div>
                <span className="text-xs font-mono font-bold text-[#7C3AED] uppercase tracking-wider block">
                  {storySteps[activeStep - 1].badge}
                </span>
                <h4 className="text-lg sm:text-xl font-bold text-[#1E1B24]">
                  {storySteps[activeStep - 1].title}
                </h4>
              </div>
              <Badge variant={activeStep >= 4 ? 'grounded' : 'violet'} size="md">
                {activeStep === 5 ? 'Verified Output' : 'Live Scene Transformation'}
              </Badge>
            </div>

            {/* VISUAL TRANSFORMATION DISPLAY */}
            <div className="flex-1 transition-all duration-700 ease-in-out">
              
              {/* STEP 1: RAW FULL DOCUMENT */}
              {activeStep === 1 && (
                <div className="bg-white p-6 sm:p-8 rounded-2xl border border-[#1E1B24]/10 space-y-4 shadow-sm animate-in fade-in duration-500">
                  <div className="flex justify-between items-center text-xs text-[#716B78] font-mono border-b border-[#1E1B24]/08 pb-3">
                    <span className="flex items-center gap-2 text-[#1E1B24] font-semibold">
                      <FileText className="w-4 h-4 text-[#7C3AED]" /> IEEE_Trans_Transportation_2025.pdf
                    </span>
                    <span>Page 14 of 47</span>
                  </div>
                  <span className="text-[10px] uppercase font-mono tracking-widest text-[#7C3AED] bg-[#EDE7FA] px-2.5 py-0.5 rounded font-bold">
                    Section 3.2 — Traffic Dynamics
                  </span>
                  <h4 className="text-lg font-bold text-[#1E1B24] font-serif">
                    3.2 Empirical Density Calculation via Loop Sensors and Aerial Micro-Tracking
                  </h4>
                  <p className="text-xs text-[#716B78]">
                    Authors: Dr. A. Vance, Prof. M. K. Thorne &bull; IEEE Transactions on Transportation (2025)
                  </p>
                  <div className="space-y-2 text-xs text-[#1E1B24]/80 leading-relaxed font-sans pt-2">
                    <p>
                      Traditional macro-level traffic monitoring relied exclusively on stationary inductive loop sensors placed at fixed 500m intervals along urban freeways. While these sensors capture flow velocity <em>V</em> effectively, spatial headway estimation degrades rapidly under congestion conditions.
                    </p>
                    <p>
                      Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length of lane at an instantaneous moment in time: &rho; = N / L. Where <em>N</em> represents vehicle count over segment length <em>L</em>.
                    </p>
                  </div>
                </div>
              )}

              {/* STEP 2: QUESTION EMERGES & INTERACTS */}
              {activeStep === 2 && (
                <div className="space-y-4 animate-in fade-in duration-500">
                  <div className="bg-[#F5F2EC] p-5 rounded-2xl border border-[#7C3AED]/30 space-y-3 shadow-sm">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-md">
                        <Search className="w-4 h-4" />
                      </div>
                      <div>
                        <span className="text-[11px] font-mono text-[#7C3AED] uppercase font-bold">
                          User Question Prompt Detected
                        </span>
                        <h4 className="text-base sm:text-lg font-bold text-[#1E1B24]">
                          &ldquo;How is traffic density calculated in urban mobility models?&rdquo;
                        </h4>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-5 rounded-2xl border border-[#1E1B24]/10 text-xs text-[#716B78] space-y-2 opacity-80">
                    <div className="flex justify-between font-mono text-[11px] text-[#1E1B24] font-semibold">
                      <span>Scanning Document Coordinates...</span>
                      <span>Targeting Section: Methodology &amp; Equations</span>
                    </div>
                    <p className="italic font-serif">
                      Locating exact mathematical formulations matching query intent across 47 indexed pages...
                    </p>
                  </div>
                </div>
              )}

              {/* STEP 3: SEMANTIC RETRIEVAL & NOISE SUBDUING */}
              {activeStep === 3 && (
                <div className="bg-white p-6 sm:p-8 rounded-2xl border border-[#7C3AED]/40 space-y-4 shadow-editorial animate-in fade-in duration-500">
                  <div className="flex justify-between items-center text-xs font-mono text-[#5B21B6] font-bold border-b border-[#1E1B24]/08 pb-3">
                    <span className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-[#7C3AED]" /> Irrelevant Text Subdued
                    </span>
                    <span>Page 14 &bull; Paragraph 3</span>
                  </div>

                  <p className="text-xs text-[#716B78] opacity-30 filter blur-[0.3px] leading-relaxed select-none">
                    Traditional macro-level traffic monitoring relied exclusively on stationary inductive loop sensors placed at fixed 500m intervals along urban freeways...
                  </p>

                  <div className="p-4 bg-[#EDE7FA] border-l-4 border-[#7C3AED] rounded-r-2xl space-y-2 shadow-sm">
                    <div className="flex justify-between text-[11px] font-mono font-bold text-[#5B21B6]">
                      <span>RELEVANT EVIDENCE ISOLATED</span>
                      <span>Equation 4.2</span>
                    </div>
                    <p className="text-xs sm:text-sm font-bold text-[#1E1B24] leading-relaxed">
                      &ldquo;Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length of lane at an instantaneous moment in time: &rho; = N / L.&rdquo;
                    </p>
                  </div>

                  <p className="text-xs text-[#716B78] opacity-30 filter blur-[0.3px] leading-relaxed select-none">
                    In modern computer vision RAG pipelines, spatial density coordinates are verified against overhead footage...
                  </p>
                </div>
              )}

              {/* STEP 4: EVIDENCE EXTRACTION & ANSWERABILITY VALIDATION */}
              {activeStep === 4 && (
                <div className="bg-[#F0FDF4] p-6 sm:p-8 rounded-2xl border border-[#15803D]/30 space-y-4 shadow-grounded animate-in fade-in duration-500">
                  <div className="flex items-center justify-between">
                    <Badge variant="grounded" size="sm" icon={<ShieldCheck className="w-4 h-4" />}>
                      Answerability Validated
                    </Badge>
                    <span className="text-xs font-mono text-[#15803D] font-bold">
                      Chunk #14-3 &bull; Evidence Validated
                    </span>
                  </div>

                  <h4 className="text-base font-bold text-[#1E1B24]">
                    Validation Agent Result: Sufficient Evidence Support Verified
                  </h4>

                  <div className="bg-white p-4 rounded-xl border border-[#15803D]/20 text-xs sm:text-sm text-[#1E1B24] font-medium leading-relaxed">
                    &ldquo;The extracted passage explicitly contains the formula (&rho; = N / L) and normalizes vehicle count N over segment length L. Generating grounded answer.&rdquo;
                  </div>
                </div>
              )}

              {/* STEP 5: SYNTHESIZED GROUNDED ANSWER */}
              {activeStep === 5 && (
                <div className="bg-white p-6 sm:p-8 rounded-2xl border border-[#7C3AED]/40 space-y-5 shadow-editorial animate-in fade-in duration-500">
                  <div className="flex items-center justify-between border-b border-[#1E1B24]/10 pb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center shadow-md">
                        <Sparkles className="w-4 h-4" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-[#1E1B24]">DocMind Grounded Output</h4>
                        <p className="text-[11px] text-[#716B78]">Synthesized from verified document evidence</p>
                      </div>
                    </div>
                    <Badge variant="grounded" size="sm" icon={<CheckCircle2 className="w-3.5 h-3.5" />}>
                      Grounded Answer
                    </Badge>
                  </div>

                  <div className="space-y-3 text-xs sm:text-sm text-[#1E1B24] leading-relaxed">
                    <p>
                      Based on <strong>Section 3.2 (Page 14)</strong> of <em>IEEE_Trans_Transportation_2025.pdf</em>, traffic density (&rho;) is calculated as the total vehicle count (<em>N</em>) over segment length (<em>L</em>):
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
                        Inspect PDF <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </div>
              )}

            </div>

            {/* Bottom Scroll Cue Indicator */}
            <div className="pt-3 border-t border-[#1E1B24]/08 flex items-center justify-between text-xs text-[#716B78]">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#7C3AED]"></span>
                <span className="font-mono">Scroll down to advance visual story</span>
              </div>
              <div className="flex items-center gap-1 font-mono text-[11px] text-[#5B21B6] font-semibold">
                <span>Step {activeStep} of 5</span>
                <ChevronDown className="w-4 h-4 animate-bounce" />
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};
