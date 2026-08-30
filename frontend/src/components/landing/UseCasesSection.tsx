import React from 'react';
import { GraduationCap, Microscope, FileCode2, BarChart3, Check } from 'lucide-react';
import { Badge } from '../ui/Badge';

export const UseCasesSection: React.FC = () => {
  const cases = [
    {
      title: 'Research Papers',
      audience: 'Academic Researchers & PhD Scholars',
      desc: 'Quickly synthesize methodologies, experimental setups, sample sizes, and empirical findings across literature reviews without missing subtle caveats.',
      icon: <Microscope className="w-6 h-6 text-[#7C3AED]" />,
      features: [
        'Methodology & Formula Extraction',
        'Document and citation references',
        'Evidence-backed claim verification',
      ],
    },
    {
      title: 'Study Material',
      audience: 'Students & University Coursework',
      desc: 'Transform 300-page course textbooks, lecture slides, and syllabus documents into document-grounded Q&A study companions before exams.',
      icon: <GraduationCap className="w-6 h-6 text-[#7C3AED]" />,
      features: [
        'Concept definition lookups',
        'Chapter page references',
        'Factual self-quizzing evidence',
      ],
    },
    {
      title: 'Technical Documents',
      audience: 'Engineers & System Architects',
      desc: 'Query dense API specifications, hardware whitepapers, and SDK documentation to locate parameters and syntax definitions.',
      icon: <FileCode2 className="w-6 h-6 text-[#7C3AED]" />,
      features: [
        'Configuration parameter lookups',
        'System architecture diagrams',
        'Protocol specification verification',
      ],
    },
    {
      title: 'Reports & Whitepapers',
      audience: 'Analysts & Consultants',
      desc: 'Extract key financial metrics, market analysis figures, and regulatory compliance disclosures from quarterly and annual corporate PDFs.',
      icon: <BarChart3 className="w-6 h-6 text-[#7C3AED]" />,
      features: [
        'Financial table data extraction',
        'Risk factor disclosures',
        'Executive summary grounding',
      ],
    },
  ];

  return (
    <section id="use-cases" className="py-24 lg:py-36 bg-[#F8F7FC] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center space-y-4">
          <Badge variant="violet" size="md">
            Target Domain Workspaces
          </Badge>
          <h2 className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-[#1E1B24] font-sans">
            Built for those who work with{' '}
            <span className="font-serif italic font-normal text-[#5B21B6]">serious documents.</span>
          </h2>
          <p className="text-base sm:text-lg text-[#716B78] leading-relaxed">
            Tailored retrieval workflows for researchers, students, engineers, and analysts who require document evidence behind an answer.
          </p>
        </div>

        {/* Spacious Domain Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-6xl mx-auto text-left">
          {cases.map((c) => (
            <div
              key={c.title}
              className="bg-white p-8 rounded-3xl border border-[#1E1B24]/10 space-y-6 hover:border-[#7C3AED]/40 transition-all duration-300 shadow-[0_4px_20px_-4px_rgba(30,27,36,0.04)]"
            >
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-2xl bg-[#EDE7FA] flex items-center justify-center">
                  {c.icon}
                </div>
                <span className="text-xs font-mono text-[#5B21B6] bg-[#EDE7FA] px-3 py-1 rounded-full font-bold">
                  {c.title}
                </span>
              </div>

              <div className="space-y-2">
                <span className="text-xs text-[#716B78] uppercase tracking-wider font-semibold font-mono">
                  {c.audience}
                </span>
                <h3 className="text-xl font-bold text-[#1E1B24]">{c.title}</h3>
                <p className="text-sm text-[#716B78] leading-relaxed font-normal">{c.desc}</p>
              </div>

              <ul className="space-y-2.5 pt-4 border-t border-[#1E1B24]/08 text-xs text-[#1E1B24]">
                {c.features.map((feat) => (
                  <li key={feat} className="flex items-center gap-2 font-medium">
                    <Check className="w-4 h-4 text-[#7C3AED] shrink-0" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
