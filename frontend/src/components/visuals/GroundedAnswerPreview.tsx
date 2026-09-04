import React from 'react';

import { ShieldCheck, FileText, ExternalLink, Sparkles, CheckCircle2 } from 'lucide-react';

import { Badge } from '../ui/Badge';

export const GroundedAnswerPreview: React.FC = () => {
  return (
    <div className="w-full max-w-3xl mx-auto card-paper p-6 sm:p-8 space-y-6 text-left relative overflow-hidden">
      {/* Accent subtle background aura */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-[#EDE7FA]/40 rounded-full blur-3xl -z-10"></div>

      {/* Answer Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#1E1B24]/10 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center shadow-md shadow-[#7C3AED]/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#1E1B24] tracking-tight">DocMind Answer Engine</h3>
            <p className="text-xs text-[#716B78]">Synthesized from verified document evidence</p>
          </div>
        </div>

        {/* ONLY use green for grounded / verified states as requested by prompt! */}
        <Badge variant="grounded" icon={<ShieldCheck className="w-4 h-4" />}>
          Grounded in Document Evidence
        </Badge>
      </div>

      {/* User Question Bubble */}
      <div className="bg-[#F8F7FC] p-3.5 rounded-xl border border-[#1E1B24]/08 text-xs sm:text-sm text-[#1E1B24] font-medium flex items-start gap-3">
        <span className="font-mono text-[#7C3AED] font-bold shrink-0">Q:</span>
        <span>How is traffic density calculated in the provided research paper?</span>
      </div>

      {/* AI Grounded Response Content */}
      <div className="space-y-4 text-xs sm:text-sm text-[#1E1B24] leading-relaxed">
        <p>
          Based on <strong>Section 3.2 (Page 14)</strong> of <em>IEEE_Trans_Transportation_2025.pdf</em>, traffic density (&rho;) is calculated as the total number of vehicles (<em>N</em>) occupying a defined segment length (<em>L</em>) at an instantaneous sampling window:
        </p>

        {/* Formula Container */}
        <div className="p-4 bg-[#F5F2EC] rounded-xl border border-[#1E1B24]/10 font-mono text-xs text-[#1E1B24] space-y-1">
          <div className="text-[#5B21B6] font-bold">&rho; = N / L</div>
          <div className="text-[11px] text-[#716B78] font-sans">
            Where <em>N</em> = total vehicle count across segment length <em>L</em> (in km), normalized over 100-meter spatial intervals.
          </div>
        </div>

        <p>
          Unlike traditional stationary loop detectors which only measure point velocity, this formulation uses micro-tracking trajectories to ensure headway estimation remains accurate even under heavy traffic congestion{' '}
          <span className="inline-flex items-center gap-1 bg-[#EDE7FA] text-[#5B21B6] border border-[#7C3AED]/30 px-2 py-0.5 rounded font-mono text-xs cursor-pointer hover:bg-[#7C3AED] hover:text-white transition-colors">
            <FileText className="w-3 h-3" />
            [Doc 1, p. 14, ¶3]
          </span>.
        </p>
      </div>

      {/* Grounded Citation Cards Panel */}
      <div className="pt-4 border-t border-[#1E1B24]/10 space-y-3">
        <div className="flex items-center justify-between text-xs text-[#716B78] font-medium">
          <span>Supporting Citations (1 Verified Source)</span>
          <span className="text-[#7C3AED] hover:underline cursor-pointer flex items-center gap-1 font-sans">
            Inspect Source Page <ExternalLink className="w-3 h-3" />
          </span>
        </div>

        <div className="bg-[#F8F7FC] rounded-xl p-3.5 border border-[#7C3AED]/20 flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-lg bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center shrink-0 font-mono text-xs font-bold">
              p.14
            </div>
            <div className="text-xs space-y-1">
              <p className="font-semibold text-[#1E1B24]">IEEE_Trans_Transportation_2025.pdf</p>
              <p className="text-[#716B78] line-clamp-2 italic font-serif">
                &ldquo;Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length of lane at an instantaneous moment in time: &rho; = N / L...&rdquo;
              </p>
            </div>
          </div>
          <div className="shrink-0 flex items-center gap-1 text-[10px] font-semibold text-[#15803D] bg-[#F0FDF4] px-2.5 py-1 rounded-full border border-[#15803D]/20">
            <CheckCircle2 className="w-3 h-3" />
            Verified Grounding
          </div>
        </div>
      </div>
    </div>
  );
};
