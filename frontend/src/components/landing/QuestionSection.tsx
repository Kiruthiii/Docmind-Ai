import React, { useState } from 'react';

import { Search, Eye, Filter, ArrowDown } from 'lucide-react';

import { Badge } from '../ui/Badge';
import { DocumentMockup } from '../visuals/DocumentMockup';

export const QuestionSection: React.FC = () => {
  const [retrievalActive, setRetrievalActive] = useState<boolean>(true);

  return (
    <section id="retrieval" className="py-24 lg:py-36 bg-[#F8F7FC] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center space-y-4">
          <Badge variant="violet" size="md" icon={<Filter className="w-3.5 h-3.5" />}>
            Semantic Document Scanning
          </Badge>
          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[#1E1B24] font-sans">
            Question meet document.{' '}
            <span className="font-serif italic font-normal text-[#5B21B6]">Focus meet evidence.</span>
          </h2>
          <p className="text-base sm:text-lg text-[#716B78] leading-relaxed">
            Watch how DocMind automatically subdues noise across multi-page research documents to pull relevant methodology passages into sharp focus.
          </p>
        </div>

        {/* Interactive Story Block */}
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Question Focus Bar */}
          <div className="bg-white p-6 rounded-3xl border border-[#7C3AED]/30 shadow-editorial flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4 text-left w-full sm:w-auto">
              <div className="w-11 h-11 rounded-2xl bg-[#7C3AED] text-white flex items-center justify-center font-bold text-sm shrink-0 shadow-md shadow-[#7C3AED]/25">
                <Search className="w-5 h-5" />
              </div>
              <div>
                <span className="text-[11px] font-mono text-[#7C3AED] uppercase font-bold tracking-wide">
                  Query Intent Detected: Methodology Calculation
                </span>
                <h3 className="text-base sm:text-xl font-bold text-[#1E1B24]">
                  &ldquo;How is traffic density calculated?&rdquo;
                </h3>
              </div>
            </div>

            {/* Toggle Control */}
            <button
              onClick={() => setRetrievalActive(!retrievalActive)}
              className="w-full sm:w-auto px-4 py-2.5 bg-[#EDE7FA] hover:bg-[#D8D3E6] text-[#5B21B6] rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer border border-[#7C3AED]/20"
              id="toggle-retrieval-focus-btn"
              type="button"
            >
              <Eye className="w-4 h-4 text-[#7C3AED]" />
              {retrievalActive ? 'Subdue Irrelevant Content (Active)' : 'Show Full Raw Page'}
            </button>
          </div>

          <div className="flex justify-center text-[#7C3AED]">
            <div className="flex items-center gap-2 bg-[#EDE7FA] px-4 py-1.5 rounded-full text-xs font-mono font-semibold text-[#5B21B6] border border-[#7C3AED]/25 shadow-sm">
              <ArrowDown className="w-3.5 h-3.5 text-[#7C3AED]" />
              <span>Scanning Page 14 Coordinates</span>
            </div>
          </div>

          {/* Render Document Mockup */}
          <DocumentMockup highlightedSection={retrievalActive} activeEvidenceId="eq-4.2" />
        </div>
      </div>
    </section>
  );
};
