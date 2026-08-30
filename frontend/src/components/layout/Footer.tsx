import React from 'react';
import { BookOpen, ShieldCheck, ArrowUpRight } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[#1E1B24] text-white pt-16 pb-12 border-t border-[#1E1B24]/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 text-left">
          {/* Brand & Mission */}
          <div className="md:col-span-5 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center shadow-lg shadow-[#7C3AED]/30">
                <BookOpen className="w-4 h-4" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white font-sans">
                DocMind <span className="text-[#EDE7FA]">AI</span>
              </span>
            </div>
            <p className="text-sm text-[#716B78]/90 leading-relaxed max-w-sm">
              Understand Documents. Find the Evidence. Get Grounded Answers. Built for researchers, academic professionals, students, and technical analysts.
            </p>
            <div className="flex items-center gap-2 text-xs text-[#15803D] bg-[#F0FDF4]/10 border border-[#15803D]/30 px-3 py-1.5 rounded-full w-fit">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Grounded Evidence RAG Engine</span>
            </div>
          </div>

          {/* Links Column 1 */}
          <div className="md:col-span-2 space-y-3">
            <h4 className="text-xs font-semibold text-[#EDE7FA] uppercase tracking-wider font-mono">
              Product Story
            </h4>
            <ul className="space-y-2 text-sm text-[#716B78]">
              <li>
                <a href="#problem" className="hover:text-white transition-colors">
                  The Problem
                </a>
              </li>
              <li>
                <a href="#retrieval" className="hover:text-white transition-colors">
                  Retrieval Engine
                </a>
              </li>
              <li>
                <a href="#evidence" className="hover:text-white transition-colors">
                  Evidence Check
                </a>
              </li>
              <li>
                <a href="#grounded-answers" className="hover:text-white transition-colors">
                  Grounded Answers
                </a>
              </li>
            </ul>
          </div>

          {/* Links Column 2 */}
          <div className="md:col-span-2 space-y-3">
            <h4 className="text-xs font-semibold text-[#EDE7FA] uppercase tracking-wider font-mono">
              Use Cases
            </h4>
            <ul className="space-y-2 text-sm text-[#716B78]">
              <li>
                <a href="#use-cases" className="hover:text-white transition-colors">
                  Academic Papers
                </a>
              </li>
              <li>
                <a href="#use-cases" className="hover:text-white transition-colors">
                  Technical Docs
                </a>
              </li>
              <li>
                <a href="#use-cases" className="hover:text-white transition-colors">
                  Study Material
                </a>
              </li>
              <li>
                <a href="#use-cases" className="hover:text-white transition-colors">
                  Financial Reports
                </a>
              </li>
            </ul>
          </div>

          {/* Links Column 3 */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs font-semibold text-[#EDE7FA] uppercase tracking-wider font-mono">
              API & Integration
            </h4>
            <p className="text-xs text-[#716B78] leading-relaxed">
              DocMind AI connects directly to backend RAG services via REST contracts.
            </p>
            <div className="pt-1">
              <a
                href="#how-it-works"
                className="inline-flex items-center gap-1 text-xs text-[#EDE7FA] hover:text-white transition-colors font-medium border-b border-[#7C3AED] pb-0.5"
              >
                View Pipeline Architecture <ArrowUpRight className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between text-xs text-[#716B78] gap-4">
          <p>&copy; {new Date().getFullYear()} DocMind AI. All rights reserved.</p>
          <div className="flex items-center gap-6">
            <a href="#" className="hover:text-white transition-colors">
              Privacy Policy
            </a>
            <a href="#" className="hover:text-white transition-colors">
              Terms of Service
            </a>
            <a href="#" className="hover:text-white transition-colors">
              Security Overview
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};
