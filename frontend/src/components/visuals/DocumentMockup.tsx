import React from 'react';

import { FileText, Bookmark, CheckCircle2, Search } from 'lucide-react';

interface DocumentMockupProps {
  highlightedSection?: boolean;
  activeEvidenceId?: string;
  className?: string;
}

export const DocumentMockup: React.FC<DocumentMockupProps> = ({
  highlightedSection = false,
  activeEvidenceId,
  className = '',
}) => {
  return (
    <div className={`card-paper p-6 sm:p-8 font-sans text-left relative transition-all duration-500 ${className}`}>
      {/* Document Header Bar */}
      <div className="flex items-center justify-between border-b border-[#1E1B24]/10 pb-4 mb-6 text-xs text-[#716B78]">
        <div className="flex items-center gap-2 font-mono">
          <FileText className="w-4 h-4 text-[#7C3AED]" />
          <span>IEEE_Trans_Transportation_2025.pdf</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="bg-[#EDE7FA] text-[#5B21B6] px-2 py-0.5 rounded font-mono font-semibold">
            Page 14 of 47
          </span>
          <Bookmark className="w-3.5 h-3.5 text-[#716B78] cursor-pointer hover:text-[#7C3AED]" />
        </div>
      </div>

      {/* Academic Paper Title & Metadata */}
      <div className="space-y-3 mb-6">
        <span className="text-[10px] uppercase tracking-widest font-semibold text-[#7C3AED] bg-[#EDE7FA] px-2 py-0.5 rounded">
          Section 3.2 — Traffic Dynamics & Empirical Models
        </span>
        <h4 className="text-base sm:text-lg font-bold text-[#1E1B24] tracking-tight leading-snug font-serif">
          3.2 Empirical Density Calculation via Loop Sensors and Aerial Video Micro-Tracking
        </h4>
        <p className="text-xs text-[#716B78]">
          Authors: Dr. A. Vance, Prof. M. K. Thorne &bull; IEEE Transactions on Transportation (2025)
        </p>
      </div>

      {/* Non-relevant paragraph (Subdued) */}
      <div className={`transition-opacity duration-500 text-xs sm:text-sm text-[#716B78] leading-relaxed mb-4 ${
        highlightedSection ? 'opacity-40 filter blur-[0.3px]' : 'opacity-80'
      }`}>
        Traditional macro-level traffic monitoring relied exclusively on stationary inductive loop sensors placed at fixed 500m intervals along urban freeways. While these sensors capture flow velocity <em>V</em> effectively, spatial headway estimation degrades rapidly under congestion conditions.
      </div>

      {/* Relevant Evidence Paragraph (Highlighted when active) */}
      <div className={`p-4 rounded-xl transition-all duration-700 relative border ${
        highlightedSection || activeEvidenceId
          ? 'bg-[#EDE7FA]/80 border-[#7C3AED] shadow-sm ring-1 ring-[#7C3AED]/20'
          : 'bg-transparent border-transparent opacity-80'
      }`}>
        {(highlightedSection || activeEvidenceId) && (
          <div className="absolute -top-3 right-4 bg-[#7C3AED] text-white text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm">
            <CheckCircle2 className="w-3 h-3 text-white" />
            Verified Evidence (Page 14, ¶3)
          </div>
        )}
        <p className="text-xs sm:text-sm font-medium text-[#1E1B24] leading-relaxed">
          <mark className={`bg-transparent ${highlightedSection ? 'text-[#1E1B24] font-semibold' : ''}`}>
            Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length of lane at an instantaneous moment in time:
          </mark>
        </p>
        <div className="my-3 py-2 px-4 bg-white/90 border border-[#7C3AED]/20 rounded-lg font-mono text-xs text-[#5B21B6] flex items-center justify-between">
          <span>&rho; = N / L = (1 / L) &times; &sum;<sub>i=1</sub><sup>N</sup> 1</span>
          <span className="text-[10px] text-[#716B78] font-sans">[Eq. 4.2]</span>
        </div>
        <p className="text-xs sm:text-sm text-[#1E1B24] leading-relaxed font-medium">
          Where <em>N</em> represents total vehicle count recorded over segment length <em>L</em> (in kilometers), with spatial sampling rates normalized to 100-meter intervals.
        </p>
      </div>

      {/* Subsequent paragraph */}
      <div className={`transition-opacity duration-500 text-xs sm:text-sm text-[#716B78] leading-relaxed mt-4 ${
        highlightedSection ? 'opacity-40 filter blur-[0.3px]' : 'opacity-80'
      }`}>
        In modern computer vision RAG pipelines, spatial density coordinates are verified against visual bounding box trajectories extracted from overhead drone footage...
      </div>

      {/* Footer watermark */}
      <div className="mt-6 pt-4 border-t border-[#1E1B24]/05 flex items-center justify-between text-[11px] text-[#716B78]">
        <div className="flex items-center gap-1.5 font-mono">
          <Search className="w-3.5 h-3.5 text-[#7C3AED]" />
          <span>DocMind Evidence Index #47-14</span>
        </div>
        <span className="font-mono text-[#15803D] font-semibold">Status: Verified Evidence Paragraph</span>
      </div>
    </div>
  );
};
