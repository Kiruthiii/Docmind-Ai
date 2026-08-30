import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ShieldCheck, FileText, CheckCircle2, Sparkles } from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

export const FinalCTASection: React.FC = () => {
  return (
    <section className="py-24 lg:py-36 bg-[#1E1B24] text-white relative overflow-hidden border-t border-white/10">
      {/* Background Academic Grid Pattern & Ambient Lighting */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff08_1px,transparent_1px),linear-gradient(to_bottom,#ffffff08_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none -z-10"></div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#7C3AED]/20 rounded-full blur-3xl pointer-events-none -z-10"></div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-12 relative z-10">
        
        {/* Narrative Resolution Pipeline Chain */}
        <div className="flex flex-wrap items-center justify-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-2 bg-white/10 text-[#EDE7FA] px-3.5 py-1.5 rounded-full border border-white/15">
            <FileText className="w-3.5 h-3.5 text-[#7C3AED]" />
            <span>01. PDF DOCUMENT</span>
          </div>
          <span className="text-[#7C3AED] font-bold">&rarr;</span>
          <div className="flex items-center gap-2 bg-white/10 text-[#EDE7FA] px-3.5 py-1.5 rounded-full border border-white/15">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#15803D]" />
            <span>02. VALIDATED EVIDENCE</span>
          </div>
          <span className="text-[#7C3AED] font-bold">&rarr;</span>
          <div className="flex items-center gap-2 bg-[#7C3AED] text-white px-3.5 py-1.5 rounded-full shadow-lg shadow-[#7C3AED]/30 font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>03. GROUNDED ANSWER</span>
          </div>
        </div>

        {/* Closing Narrative Headlines */}
        <div className="space-y-6 max-w-3xl mx-auto">
          <h2 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-white font-sans leading-[1.08]">
            Find the answers hiding inside{' '}
            <span className="font-serif italic font-normal text-[#EDE7FA] border-b-2 border-[#7C3AED]/60 pb-1">
              your documents.
            </span>
          </h2>

          <p className="text-base sm:text-xl text-[#716B78]/90 font-sans font-normal leading-relaxed max-w-xl mx-auto">
            DocMind AI helps you ask questions, validate supporting passages, and generate answers backed by document evidence.
          </p>
        </div>

        {/* Resolved Grounded Document Snippet Card */}
        <div className="max-w-2xl mx-auto bg-white/05 backdrop-blur-md rounded-2xl border border-white/15 p-6 text-left space-y-3 shadow-2xl">
          <div className="flex items-center justify-between text-xs text-[#EDE7FA] font-mono">
            <span className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#7C3AED]" /> IEEE_Trans_Transportation_2025.pdf
            </span>
            <Badge variant="grounded" size="sm" icon={<ShieldCheck className="w-3 h-3" />}>
              Evidence Validated
            </Badge>
          </div>
          <p className="text-xs text-[#716B78] italic font-serif">
            &ldquo;Traffic density (&rho;) is formally defined as vehicle count N divided by segment length L: &rho; = N / L.&rdquo;
          </p>
          <div className="text-[11px] text-[#7C3AED] font-mono font-semibold pt-2 border-t border-white/10 flex justify-between">
            <span>[Cited: Page 14, ¶3]</span>
            <span>DocMind Evidence Verification Active</span>
          </div>
        </div>

        {/* Primary Action Button */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/signup">
            <Button variant="primary" size="lg" className="px-9 py-4 text-base shadow-xl shadow-[#7C3AED]/30" icon={<ArrowRight className="w-5 h-5" />}>
              Get Started Free
            </Button>
          </Link>
        </div>

        <div className="pt-2 text-xs text-[#716B78] font-mono">
          Free tier available &bull; No credit card required &bull; Works with academic PDFs &amp; technical reports
        </div>
      </div>
    </section>
  );
};
