import React from 'react';
import { GroundedAnswerPreview } from '../visuals/GroundedAnswerPreview';
import { Badge } from '../ui/Badge';
import { Sparkles } from 'lucide-react';

export const AnswerSection: React.FC = () => {
  return (
    <section id="grounded-answers" className="py-20 md:py-28 bg-[#F8F7FC] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Title */}
        <div className="max-w-3xl mx-auto text-center space-y-4">
          <Badge variant="violet" size="md" icon={<Sparkles className="w-3.5 h-3.5" />}>
            The Grounded Output Interface
          </Badge>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-[#1E1B24] font-sans">
            Answers that lead back to{' '}
            <span className="font-serif italic font-normal text-[#5B21B6]">the truth.</span>
          </h2>
          <p className="text-base sm:text-lg text-[#716B78] leading-relaxed">
            DocMind responses are anchored to verifiable document evidence. Inspect page-level citations with a single click.
          </p>
        </div>

        {/* Answer visual preview */}
        <div className="max-w-4xl mx-auto">
          <GroundedAnswerPreview />
        </div>
      </div>
    </section>
  );
};
