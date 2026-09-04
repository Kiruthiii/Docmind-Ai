import { useState } from 'react';

import { FileText, Plus, Send, ShieldCheck, Sparkles, ChevronRight } from 'lucide-react';

import { Badge } from '../ui/Badge';

export const ProductRevealSection: React.FC = () => {
  const [selectedDoc, setSelectedDoc] = useState<string>('IEEE_Trans_Transportation_2025.pdf');

  const documents = [
    { id: '1', name: 'IEEE_Trans_Transportation_2025.pdf', pages: 47, active: true },
    { id: '2', name: 'Quantum_Decoherence_Model_v3.pdf', pages: 32, active: false },
    { id: '3', name: 'Autonomous_Nav_SLAM_Report.pdf', pages: 84, active: false },
  ];

  return (
    <section id="product-reveal" className="py-20 md:py-28 bg-[#F5F2EC] border-y border-[#1E1B24]/08 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center space-y-4">
          <Badge variant="violet" size="md">
            Product Interface Preview
          </Badge>
          <h2 className="text-3xl sm:text-5xl font-bold tracking-tight text-[#1E1B24] font-sans">
            The DocMind Workspace.{' '}
            <span className="font-serif italic font-normal text-[#5B21B6]">Focus built for depth.</span>
          </h2>
          <p className="text-base sm:text-lg text-[#716B78] leading-relaxed">
            Experience the actual document intelligence application. Clean multi-document sidebars, grounded chat threads, and live side-by-side evidence inspectors.
          </p>
        </div>

        {/* Polished Realistic Workspace Preview Mockup */}
        <div className="max-w-6xl mx-auto card-paper rounded-2xl overflow-hidden border-[#1E1B24]/10 shadow-editorial text-left bg-white">
          {/* Top Window Bar */}
          <div className="bg-[#1E1B24] text-white px-6 py-3.5 flex items-center justify-between border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <span className="font-mono text-xs font-semibold text-[#EDE7FA] ml-3">
                DocMind AI Workspace &bull; Workspace ID: ws-research-409
              </span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs bg-[#15803D]/20 text-[#4ADE80] border border-[#15803D]/40 px-2.5 py-1 rounded-full font-mono flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" /> Evidence-aware RAG Active
              </span>
            </div>
          </div>

          {/* Main App Grid (Sidebar + Chat Area + Evidence Inspector) */}
          <div className="grid grid-cols-1 md:grid-cols-12 min-h-[500px]">
            {/* Sidebar (Documents List) */}
            <div className="md:col-span-3 bg-[#F8F7FC] border-r border-[#1E1B24]/08 p-4 space-y-6">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#1E1B24] uppercase tracking-wider font-mono">
                  Document Library
                </span>
                <button
                  className="w-7 h-7 rounded-lg bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center hover:bg-[#7C3AED] hover:text-white transition-colors cursor-pointer"
                  title="Upload New PDF"
                  id="workspace-preview-upload-btn"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    onClick={() => setSelectedDoc(doc.name)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                      selectedDoc === doc.name
                        ? 'bg-white border-[#7C3AED] shadow-sm ring-1 ring-[#7C3AED]/20 font-semibold'
                        : 'bg-transparent border-transparent hover:bg-white/60 text-[#716B78]'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <FileText className={`w-4 h-4 shrink-0 ${selectedDoc === doc.name ? 'text-[#7C3AED]' : 'text-[#716B78]'}`} />
                      <span className="truncate text-[#1E1B24]">{doc.name}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-[#716B78] font-mono pl-6">
                      <span>{doc.pages} Pages</span>
                      {selectedDoc === doc.name && <span className="text-[#5B21B6]">Active PDF</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Central Chat Interface */}
            <div className="md:col-span-6 p-6 flex flex-col justify-between space-y-6 bg-white">
              {/* Thread Header */}
              <div className="flex items-center justify-between border-b border-[#1E1B24]/08 pb-3">
                <div>
                  <h4 className="text-xs font-mono text-[#7C3AED] uppercase font-semibold">Current Session</h4>
                  <p className="text-sm font-bold text-[#1E1B24] truncate">
                    {selectedDoc}
                  </p>
                </div>
                <Badge variant="violet" size="sm">
                  1 Session Active
                </Badge>
              </div>

              {/* Chat Messages */}
              <div className="space-y-4 text-xs sm:text-sm">
                {/* User Message */}
                <div className="flex justify-end">
                  <div className="bg-[#EDE7FA] text-[#1E1B24] p-3.5 rounded-2xl rounded-tr-none max-w-md font-medium">
                    What equation is used to compute instantaneous vehicle traffic density?
                  </div>
                </div>

                {/* AI Grounded Response */}
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-xl bg-[#7C3AED] text-white flex items-center justify-center shrink-0 shadow-sm">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div className="space-y-3 bg-[#F8F7FC] p-4 rounded-2xl rounded-tl-none border border-[#7C3AED]/20 max-w-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono text-[#5B21B6] font-bold">DocMind Grounded Answer</span>
                      <span className="text-[10px] bg-[#F0FDF4] text-[#15803D] border border-[#15803D]/30 px-2 py-0.5 rounded-full font-semibold">
                        Grounded
                      </span>
                    </div>

                    <p className="text-[#1E1B24] leading-relaxed">
                      Instantaneous traffic density (&rho;) is computed as total vehicle count <em>N</em> over segment length <em>L</em>:
                    </p>

                    <div className="bg-white p-2.5 rounded-lg border border-[#7C3AED]/30 font-mono text-xs text-[#5B21B6]">
                      &rho; = N / L
                    </div>

                    <p className="text-[#716B78] text-xs">
                      Cited: <em>IEEE_Trans_Transportation_2025.pdf</em> [Page 14, Eq 4.2]
                    </p>
                  </div>
                </div>
              </div>

              {/* Input Box */}
              <div className="pt-3 border-t border-[#1E1B24]/08">
                <div className="relative flex items-center">
                  <input
                    type="text"
                    readOnly
                    value="Ask follow-up question regarding parameters..."
                    className="w-full bg-[#F8F7FC] border border-[#1E1B24]/10 rounded-xl py-3 pl-4 pr-12 text-xs text-[#716B78] focus:outline-none cursor-not-allowed"
                    id="preview-chat-input-field"
                  />
                  <button
                    className="absolute right-2 p-2 bg-[#7C3AED] text-white rounded-lg hover:bg-[#5B21B6] transition-colors"
                    id="preview-send-chat-btn"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Right Evidence Inspector Sidebar */}
            <div className="md:col-span-3 bg-[#F8F7FC] border-l border-[#1E1B24]/08 p-4 space-y-4 text-xs">
              <div className="flex items-center justify-between border-b border-[#1E1B24]/08 pb-3">
                <span className="font-mono font-bold text-[#1E1B24] uppercase">Evidence Panel</span>
                <span className="text-[10px] text-[#15803D] font-mono bg-[#F0FDF4] px-2 py-0.5 rounded">
                  Match 98%
                </span>
              </div>

              <div className="bg-white p-3.5 rounded-xl border border-[#7C3AED]/30 space-y-2 shadow-sm">
                <div className="flex items-center justify-between font-mono text-[11px] text-[#5B21B6] font-bold">
                  <span>Chunk #14-3</span>
                  <span>Page 14</span>
                </div>
                <p className="text-[#716B78] italic font-serif leading-relaxed text-[11px]">
                  &ldquo;Traffic density (&rho;) is formally defined as the number of vehicles occupying a given length...&rdquo;
                </p>
                <div className="pt-2 border-t border-[#1E1B24]/08 flex items-center justify-between text-[10px] text-[#716B78]">
                  <span>Status: Verified</span>
                  <span className="text-[#7C3AED] font-semibold flex items-center">
                    Jump to PDF <ChevronRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
