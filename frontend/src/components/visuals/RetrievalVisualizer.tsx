import { useState } from 'react';
import { Search, ArrowRight, ShieldCheck, FileText, Check } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const RetrievalVisualizer: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(2);

  const steps = [
    { id: 1, label: 'Document Scanning', detail: '47 PDF Pages Parsed & Indexed' },
    { id: 2, label: 'Semantic Retrieval', detail: 'Locating Relevant Paragraphs' },
    { id: 3, label: 'Evidence Validation', detail: 'Grounded & Answerability Check' },
  ];

  return (
    <div className="w-full max-w-4xl mx-auto rounded-2xl bg-white border border-[#1E1B24]/10 shadow-editorial overflow-hidden">
      {/* Top Controller Bar */}
      <div className="bg-[#F8F7FC] border-b border-[#1E1B24]/10 px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#7C3AED]/40"></div>
          <div className="w-3 h-3 rounded-full bg-[#7C3AED]/70"></div>
          <div className="w-3 h-3 rounded-full bg-[#7C3AED]"></div>
          <span className="ml-2 text-xs font-mono font-semibold text-[#1E1B24]">
            DocMind RAG Visual Pipeline
          </span>
        </div>

        {/* Interactive Step Buttons */}
        <div className="flex items-center gap-1.5 bg-white p-1 rounded-xl border border-[#1E1B24]/10">
          {steps.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveStep(s.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeStep === s.id
                  ? 'bg-[#7C3AED] text-white shadow-sm'
                  : 'text-[#716B78] hover:text-[#1E1B24] hover:bg-[#F8F7FC]'
              }`}
            >
              Step {s.id}
            </button>
          ))}
        </div>
      </div>

      {/* Main Visualizer Stage */}
      <div className="p-6 sm:p-10 space-y-8">
        {/* User Question Bar */}
        <div className="bg-[#F5F2EC] rounded-xl p-4 border border-[#1E1B24]/10 flex items-center justify-between gap-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#EDE7FA] flex items-center justify-center text-[#5B21B6] shrink-0 font-semibold text-xs">
              Q
            </div>
            <div>
              <p className="text-xs text-[#716B78] font-medium">User Question</p>
              <p className="text-sm font-semibold text-[#1E1B24]">
                &ldquo;How is traffic density calculated in urban mobility models?&rdquo;
              </p>
            </div>
          </div>
          <Badge variant="violet" size="sm" icon={<Search className="w-3 h-3" />}>
            Searching PDF
          </Badge>
        </div>

        {/* Document Pages Grid vs Target Extraction */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          {/* Document pages column */}
          <div className="md:col-span-6 space-y-3">
            <div className="flex items-center justify-between text-xs text-[#716B78]">
              <span>Research Paper (47 Pages)</span>
              <span className="font-mono text-[11px]">Relevance Indexing: High</span>
            </div>

            <div className="grid grid-cols-4 gap-2">
              {[...Array(8)].map((_, i) => {
                const isTarget = i === 3; // Page 14 mock
                return (
                  <div
                    key={i}
                    className={`aspect-[3/4] rounded-lg border p-2 text-[8px] flex flex-col justify-between transition-all duration-500 ${
                      isTarget
                        ? 'border-[#7C3AED] bg-[#EDE7FA] ring-2 ring-[#7C3AED]/30 scale-105 shadow-md'
                        : activeStep >= 2
                        ? 'border-[#1E1B24]/10 bg-white/40 opacity-40'
                        : 'border-[#1E1B24]/10 bg-white'
                    }`}
                  >
                    <div className="flex justify-between items-center text-[7px] text-[#716B78]">
                      <FileText className="w-2.5 h-2.5" />
                      <span>p.{i * 6 + 2}</span>
                    </div>
                    <div className="space-y-1 my-auto">
                      <div className={`h-1 rounded ${isTarget ? 'bg-[#7C3AED]' : 'bg-[#1E1B24]/20'}`}></div>
                      <div className={`h-1 w-3/4 rounded ${isTarget ? 'bg-[#5B21B6]' : 'bg-[#1E1B24]/15'}`}></div>
                      <div className={`h-1 w-1/2 rounded ${isTarget ? 'bg-[#7C3AED]' : 'bg-[#1E1B24]/10'}`}></div>
                    </div>
                    {isTarget && (
                      <span className="bg-[#7C3AED] text-white font-semibold text-[7px] px-1 py-0.5 rounded text-center">
                        EVIDENCE
                      </span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Connection Arrow */}
          <div className="hidden md:flex md:col-span-1 justify-center">
            <div className="w-10 h-10 rounded-full bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center shadow-sm">
              <ArrowRight className="w-5 h-5" />
            </div>
          </div>

          {/* Extracted Evidence & Grounding Card */}
          <div className="md:col-span-5">
            <div className="bg-white rounded-xl border border-[#7C3AED]/30 p-5 shadow-editorial space-y-4">
              <div className="flex items-center justify-between">
                <Badge variant="grounded" size="sm" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
                  Answerable Evidence
                </Badge>
                <span className="text-[11px] font-mono text-[#716B78]">Page 14 &bull; Eq. 4.2</span>
              </div>

              <div className="p-3 bg-[#F8F7FC] rounded-lg border border-[#1E1B24]/08 text-xs text-[#1E1B24] leading-relaxed font-medium">
                &ldquo;Traffic density (&rho;) is defined as vehicle count N divided by segment length L (&rho; = N / L).&rdquo;
              </div>

              <div className="space-y-1.5 text-xs text-[#716B78]">
                <div className="flex items-center gap-2 text-[#15803D] font-medium">
                  <Check className="w-3.5 h-3.5" />
                  <span>Validation Agent: High Confidence</span>
                </div>
                <div className="flex items-center gap-2 text-[#15803D] font-medium">
                  <Check className="w-3.5 h-3.5" />
                  <span>Grounding Verification: Passed</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
