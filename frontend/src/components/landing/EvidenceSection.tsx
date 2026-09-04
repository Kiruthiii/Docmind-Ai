import { ShieldCheck, CheckCircle2 } from 'lucide-react';

import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';

export const EvidenceSection: React.FC = () => {
  return (
    <section id="evidence" className="py-20 md:py-28 bg-[#F5F2EC] border-y border-[#1E1B24]/08 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center space-y-4">
          <Badge variant="violet" size="md" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
            Evidence Validation Layer
          </Badge>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-[#1E1B24] font-sans">
            Not just relevant.{' '}
            <span className="font-serif italic font-normal text-[#5B21B6]">Actually answerable.</span>
          </h2>
          <p className="text-base sm:text-lg text-[#716B78] leading-relaxed">
            Standard RAG returns text that merely mentions similar keywords. DocMind&apos;s multi-agent system verifies whether the retrieved passage contains sufficient, factual evidence before generating an answer.
          </p>
        </div>

        {/* 3-Step Flow Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto text-left">
          {/* Step 1: User Question */}
          <Card variant="paper" className="p-6 space-y-4 bg-white relative">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-full bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center font-bold text-xs font-mono">
                01
              </span>
              <span className="text-[11px] font-mono text-[#716B78] uppercase">Question Intent</span>
            </div>
            <h3 className="text-lg font-bold text-[#1E1B24]">1. User Asks Question</h3>
            <p className="text-xs text-[#716B78] leading-relaxed">
              Extract query intent, target section preferences, entities, and temporal context.
            </p>
            <div className="p-3 bg-[#F8F7FC] rounded-lg border border-[#1E1B24]/08 text-xs font-medium text-[#1E1B24]">
              &ldquo;What is the experimental sample size used in Trial B?&rdquo;
            </div>
          </Card>

          {/* Step 2: Answerability Validation */}
          <Card variant="paper" className="p-6 space-y-4 bg-white border-[#7C3AED]/40 shadow-editorial relative">
            <div className="absolute -top-3 left-6 bg-[#7C3AED] text-white text-[10px] uppercase tracking-wider font-semibold px-2.5 py-0.5 rounded-full">
              DocMind Verification Step
            </div>
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-full bg-[#7C3AED] text-white flex items-center justify-center font-bold text-xs font-mono shadow-sm">
                02
              </span>
              <Badge variant="grounded" size="sm" icon={<CheckCircle2 className="w-3 h-3" />}>
                Answerable: True
              </Badge>
            </div>
            <h3 className="text-lg font-bold text-[#1E1B24]">2. Validate Evidence</h3>
            <p className="text-xs text-[#716B78] leading-relaxed">
              Validation Agent inspects extracted chunks to ensure claims are grounded in document facts.
            </p>
            <div className="p-3 bg-[#F0FDF4] rounded-lg border border-[#15803D]/25 text-xs text-[#15803D] font-medium space-y-1">
              <div className="font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Sufficient Evidence Verified
              </div>
              <p className="text-[11px] text-[#1E1B24]">Page 22, Table 4: N = 1,420 randomized participants.</p>
            </div>
          </Card>

          {/* Step 3: Grounded Generation */}
          <Card variant="paper" className="p-6 space-y-4 bg-white relative">
            <div className="flex items-center justify-between">
              <span className="w-8 h-8 rounded-full bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center font-bold text-xs font-mono">
                03
              </span>
              <span className="text-[11px] font-mono text-[#716B78] uppercase">Final Output</span>
            </div>
            <h3 className="text-lg font-bold text-[#1E1B24]">3. Grounded Answer</h3>
            <p className="text-xs text-[#716B78] leading-relaxed">
              Generate precise answer linked to verifiable page citations. If evidence is lacking, state explicitly.
            </p>
            <div className="p-3 bg-[#F8F7FC] rounded-lg border border-[#1E1B24]/08 text-xs font-medium text-[#1E1B24] space-y-1">
              <p>&ldquo;Trial B evaluated N = 1,420 participants [Doc 1, p. 22].&rdquo;</p>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
};
