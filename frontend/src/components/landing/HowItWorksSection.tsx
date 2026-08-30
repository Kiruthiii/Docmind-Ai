import React from 'react';
import { Brain, FileSearch, ShieldCheck, Cpu, CheckCircle, Award } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const HowItWorksSection: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Understand',
      desc: 'Parses complex user questions into structured search intents, section targets, and entity parameters.',
      icon: <Brain className="w-5 h-5 text-[#7C3AED]" />,
    },
    {
      num: '02',
      title: 'Retrieve',
      desc: 'Executes hybrid dense vector and semantic keyword retrieval across uploaded PDF page chunks.',
      icon: <FileSearch className="w-5 h-5 text-[#7C3AED]" />,
    },
    {
      num: '03',
      title: 'Validate',
      desc: 'Validates evidence before generating to help reduce unsupported or hallucinated answers.',
      icon: <ShieldCheck className="w-5 h-5 text-[#7C3AED]" />,
    },
    {
      num: '04',
      title: 'Generate',
      desc: 'Synthesizes clear responses conditioned on validated document evidence passages.',
      icon: <Cpu className="w-5 h-5 text-[#7C3AED]" />,
    },
    {
      num: '05',
      title: 'Verify',
      desc: 'Cross-verifies claim statements against extracted snippet IDs to ensure alignment.',
      icon: <CheckCircle className="w-5 h-5 text-[#7C3AED]" />,
    },
    {
      num: '06',
      title: 'Ground',
      desc: 'Attaches page-level citations to synthesized responses for easy verification.',
      icon: <Award className="w-5 h-5 text-[#15803D]" />,
      isGrounded: true,
    },
  ];

  return (
    <section id="how-it-works" className="py-24 lg:py-36 bg-[#F5F2EC] border-y border-[#1E1B24]/10 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center space-y-4">
          <Badge variant="violet" size="md">
            Pipeline Architecture
          </Badge>
          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[#1E1B24] font-sans">
            How DocMind finds{' '}
            <span className="font-serif italic font-normal text-[#5B21B6]">answers worth trusting.</span>
          </h2>
          <p className="text-base sm:text-lg text-[#716B78] leading-relaxed">
            A multi-stage evidence pipeline designed to keep answers grounded in your uploaded documents.
          </p>
        </div>

        {/* Continuous Step Pipeline Timeline */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 text-left">
          {steps.map((step, idx) => (
            <div
              key={step.num}
              className={`bg-white p-7 rounded-3xl border transition-all duration-300 relative flex flex-col justify-between ${
                step.isGrounded
                  ? 'border-[#15803D]/40 shadow-grounded'
                  : 'border-[#1E1B24]/10 shadow-[0_4px_20px_-4px_rgba(30,27,36,0.04)] hover:shadow-md'
              }`}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-11 h-11 rounded-2xl bg-[#EDE7FA] flex items-center justify-center">
                    {step.icon}
                  </div>
                  <span className="font-mono text-xs font-bold text-[#5B21B6] bg-[#EDE7FA] px-3 py-1 rounded-full">
                    STEP {step.num}
                  </span>
                </div>

                <div className="space-y-2">
                  <h3 className="text-xl font-bold text-[#1E1B24] flex items-center gap-2">
                    {step.title}
                    {step.isGrounded && (
                      <span className="text-[10px] bg-[#F0FDF4] text-[#15803D] border border-[#15803D]/30 px-2.5 py-0.5 rounded-full font-sans font-semibold">
                        Grounded Output
                      </span>
                    )}
                  </h3>
                  <p className="text-xs sm:text-sm text-[#716B78] leading-relaxed font-normal">{step.desc}</p>
                </div>
              </div>

              {/* Connected node line */}
              <div className="pt-4 mt-4 border-t border-[#1E1B24]/08 flex items-center justify-between text-[11px] font-mono text-[#716B78]">
                <span>Phase {idx + 1} of 6</span>
                <span className="text-[#7C3AED] font-semibold">&rarr;</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
