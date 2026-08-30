import React from 'react';
import { CheckCircle2, AlertCircle } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const ProblemSection: React.FC = () => {
  return (
    <section id="problem" className="py-24 lg:py-36 bg-[#F5F2EC] border-y border-[#1E1B24]/10 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center space-y-4">
          <Badge variant="warm" size="md">
            The Document Information Bottleneck
          </Badge>
          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[#1E1B24] font-sans">
            Topically relevant isn&apos;t{' '}
            <span className="font-serif italic font-normal text-[#5B21B6]">always answerable.</span>
          </h2>
          <p className="text-base sm:text-lg text-[#716B78] leading-relaxed">
            Finding relevant text isn&apos;t enough. Retrieved evidence has to actually answer the question.
          </p>
        </div>

        {/* 2-Column Comparison Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 max-w-6xl mx-auto items-stretch">
          {/* Left Column — The Problem */}
          <div className="lg:col-span-6 bg-white p-8 rounded-3xl border border-[#1E1B24]/10 space-y-6 flex flex-col justify-between shadow-sm">
            <div className="space-y-4 text-left">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-red-600 bg-red-50 px-3 py-1 rounded-full">
                  Standard Topical Search
                </span>
                <span className="text-xs font-mono text-[#716B78]">Keyword Match</span>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-[#1E1B24]">
                Topical Relevance Without Factual Support
              </h3>
              <p className="text-xs sm:text-sm text-[#716B78] leading-relaxed">
                Traditional retrieval can find passages related to a question without finding the information the question actually asks for.
              </p>
            </div>

            <div className="bg-[#F8F7FC] p-4 rounded-2xl border border-red-200/80 space-y-3 text-left">
              <div className="flex items-center gap-2 text-xs text-red-700 font-semibold">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>Search returned related topic mentions without target formula</span>
              </div>
              <div className="p-3 bg-white rounded-xl border border-red-100 text-xs text-[#716B78] italic font-serif">
                &times; Found 14 occurrences of &quot;density&quot;, but failed to isolate the governing equation requested on Page 14.
              </div>
            </div>
          </div>

          {/* Right Column — The DocMind Solution */}
          <div className="lg:col-span-6 bg-white p-8 rounded-3xl border border-[#7C3AED]/30 space-y-6 flex flex-col justify-between shadow-editorial relative overflow-hidden text-left">
            <div className="absolute top-0 right-0 w-40 h-40 bg-[#EDE7FA]/60 rounded-full blur-3xl -z-10"></div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-[#5B21B6] bg-[#EDE7FA] px-3 py-1 rounded-full">
                  DocMind Evidence Validation
                </span>
                <Badge variant="grounded" size="sm">
                  Evidence Validated
                </Badge>
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-[#1E1B24]">
                Document-Supported Answers &amp; Citations
              </h3>
              <p className="text-xs sm:text-sm text-[#716B78] leading-relaxed">
                DocMind checks whether retrieved evidence supports the question before generating an answer, providing page-level citations.
              </p>
            </div>

            <div className="bg-[#F0FDF4] p-4 rounded-2xl border border-[#15803D]/25 space-y-3">
              <div className="flex items-center justify-between text-xs text-[#15803D] font-bold">
                <span className="flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-[#15803D]" /> Evidence Support Confirmed: Page 14, ¶3
                </span>
                <span className="font-mono text-[10px] bg-white px-2.5 py-0.5 rounded border border-[#15803D]/30">
                  Equation 4.2
                </span>
              </div>
              <p className="text-xs text-[#1E1B24] font-medium leading-relaxed bg-white p-3 rounded-xl border border-[#15803D]/20">
                &ldquo;Traffic density (&rho;) is defined as vehicle count N divided by segment length L (&rho; = N / L).&rdquo;
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
