import React from 'react';

import { ArrowRight, Play, ShieldCheck, FileText, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export const HeroSection: React.FC = () => {
  return (
    <section className="relative pt-16 pb-20 lg:pt-28 lg:pb-32 overflow-hidden bg-[#F8F7FC]">
      {/* Academic PDF Coordinate Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e1b240a_1px,transparent_1px),linear-gradient(to_bottom,#1e1b240a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none -z-10"></div>
      
      {/* Ambient Lighting Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#EDE7FA]/60 rounded-full blur-3xl -z-10 pointer-events-none"></div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-10">
        {/* Architecture Badge */}
        <div className="inline-flex items-center gap-2">
          <Badge variant="violet" size="md" icon={<ShieldCheck className="w-4 h-4" />}>
            Evidence-Grounded Document Intelligence
          </Badge>
        </div>

        {/* Imposing Editorial Headline */}
        <div className="max-w-4xl mx-auto space-y-6">
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-[#1E1B24] leading-[1.08] font-sans">
            Ask your documents.{' '}
            <span className="font-serif italic font-normal text-[#5B21B6] border-b-2 border-[#7C3AED]/40 pb-1">
              Find the evidence.
            </span>
          </h1>

          <p className="text-base sm:text-xl text-[#716B78] leading-relaxed max-w-2xl mx-auto font-normal">
            Find answers inside research papers, technical reports, and academic PDFs — with document evidence showing where the answer came from.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <Link to="/signup">
            <Button variant="primary" size="lg" icon={<ArrowRight className="w-5 h-5" />}>
              Get Started Free
            </Button>
          </Link>
          <a href="#document-stage">
            <Button variant="outline" size="lg" icon={<Play className="w-4 h-4 fill-current text-[#7C3AED]" />}>
              See Interactive Document Story
            </Button>
          </a>
        </div>

        {/* Visual Preview Frame of the Document Hero Object */}
        <div className="pt-8 max-w-4xl mx-auto">
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-[#1E1B24]/12 shadow-[0_20px_50px_-10px_rgba(30,27,36,0.08)] text-left space-y-4">
            <div className="flex items-center justify-between border-b border-[#1E1B24]/08 pb-3">
              <div className="flex items-center gap-2 text-xs font-mono font-semibold text-[#1E1B24]">
                <FileText className="w-4 h-4 text-[#7C3AED]" />
                <span>IEEE_Trans_Transportation_2025.pdf</span>
                <span className="text-[#716B78] font-normal">(Page 14 of 47)</span>
              </div>
              <Badge variant="grounded" size="sm" icon={<CheckCircle2 className="w-3.5 h-3.5" />}>
                Evidence Support Checked
              </Badge>
            </div>
            
            <p className="text-xs text-[#716B78] font-serif italic">
              &ldquo;3.2 Empirical Density Calculation via Loop Sensors and Aerial Micro-Tracking... Traffic density (&rho;) is formally defined as: &rho; = N / L.&rdquo;
            </p>

            <div className="flex items-center justify-between text-[11px] font-mono text-[#7C3AED] font-semibold pt-1">
              <span>[Cited: Page 14, ¶3]</span>
              <a href="#document-stage" className="hover:underline flex items-center gap-1">
                Scroll to interactive stage &rarr;
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
