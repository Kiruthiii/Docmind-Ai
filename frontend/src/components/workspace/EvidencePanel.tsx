import React from 'react';

import {
  ShieldCheck,
  ExternalLink,
  BookOpen,
  Sparkles,
  Layers,
} from 'lucide-react';

import type { Citation } from '../../types/docmind';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface EvidencePanelProps {
  citations: Citation[];
  activeCitationId: string | null;
  onSelectCitation: (citation: Citation) => void;
  onJumpToPage: (pageNum: number) => void;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({
  citations,
  activeCitationId,
  onSelectCitation,
  onJumpToPage,
}) => {
  return (
    <div className="flex-1 flex flex-col h-full bg-[#FAF8F5] selection:bg-[#EDE7FA] selection:text-[#5B21B6] text-left border-l border-[#1E1B24]/10 overflow-hidden">
      
      {/* 1. PANEL HEADER */}
      <div className="bg-white border-b border-[#1E1B24]/10 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-[#1E1B24] font-sans">
              Evidence &amp; Citation References
            </h3>
            <p className="text-[10px] text-[#716B78] font-mono">
              Grounding context passages
            </p>
          </div>
        </div>

        <Badge variant="violet" size="sm">
          {citations.length} References
        </Badge>
      </div>

      {/* 2. CITATIONS LIST AREA */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        
        {/* EMPTY STATE */}
        {citations.length === 0 ? (
          <div className="py-12 px-4 text-center space-y-4 max-w-xs mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center mx-auto shadow-xs">
              <Layers className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-bold text-[#1E1B24] font-sans">
                No active citations selected
              </h4>
              <p className="text-[11px] text-[#716B78] leading-relaxed">
                Ask a question in the chat interface to extract evidence references and source passages.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <span className="text-[10px] font-mono tracking-widest text-[#716B78] uppercase font-bold">
                EXTRACTED PASSAGES ({citations.length})
              </span>
            </div>

            {citations.map((cite) => {
              const isActive = cite.id === activeCitationId;
              const cleanSnippet = (cite.snippet || '')
                .replace(/\b([A-Za-z])\s+([a-z]{2,})\b/g, '$1$2')
                .replace(/\b([A-Z]{3,})\s+([A-Z])\b/g, '$1$2')
                .replace(/\s+/g, ' ')
                .trim();
              const cleanSection = cite.section_title
                ? cite.section_title
                    .replace(/\b([A-Za-z])\s+([a-z]{2,})\b/g, '$1$2')
                    .replace(/\b([A-Z]{3,})\s+([A-Z])\b/g, '$1$2')
                    .replace(/\s+/g, ' ')
                    .trim()
                : null;

              return (
                <div
                  key={cite.id}
                  onClick={() => onSelectCitation(cite)}
                  className={`group p-4 rounded-xl border transition-all text-left space-y-3 cursor-pointer ${
                    isActive
                      ? 'bg-white border-[#7C3AED] shadow-md shadow-[#7C3AED]/08 ring-1 ring-[#7C3AED]/20'
                      : 'bg-white/80 hover:bg-white border-[#1E1B24]/10 hover:border-[#7C3AED]/40'
                  }`}
                >
                  {/* Top Citation Tag & Page Badge */}
                  <div className="flex items-center justify-between border-b border-[#1E1B24]/08 pb-2 text-[10px] font-mono">
                    <div className="flex items-center gap-1.5 text-[#5B21B6] font-bold">
                      <BookOpen className="w-3.5 h-3.5 text-[#7C3AED]" />
                      <span>Page {cite.page_number}</span>
                    </div>

                    {cite.relevance_score && (
                      <span className="text-[#15803D] font-bold">
                        Relevance: {Math.round(cite.relevance_score * 100)}%
                      </span>
                    )}
                  </div>

                  {/* Section Title if available */}
                  {cleanSection && (
                    <div className="text-xs font-bold text-[#1E1B24] font-sans">
                      {cleanSection}
                    </div>
                  )}

                  {/* Evidence Snippet / Source Passage */}
                  <div className="p-3 bg-[#FAF8F5] rounded-lg border border-[#1E1B24]/08 space-y-1">
                    <span className="text-[9px] font-mono text-[#716B78] uppercase tracking-wider font-bold block">
                      SOURCE PASSAGE:
                    </span>
                    <p className="text-xs font-serif text-[#2D2A35] leading-relaxed italic">
                      &ldquo;{cleanSnippet}&rdquo;
                    </p>
                  </div>

                  {/* Document Source Metadata & Action */}
                  <div className="flex items-center justify-between pt-1 text-[10px] font-mono text-[#716B78]">
                    <span className="truncate max-w-[160px]" title={cite.document_name}>
                      {cite.document_name ? cite.document_name.replace(/\.pdf$/i, '').replace(/_/g, ' ') : ''}
                    </span>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onJumpToPage(cite.page_number);
                        onSelectCitation(cite);
                      }}
                      icon={<ExternalLink className="w-3 h-3" />}
                      className="min-h-[36px] px-2.5 py-1 text-[11px] font-semibold"
                    >
                      Jump to Page {cite.page_number}
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

      </div>

      {/* 3. PANEL FOOTER */}
      <div className="bg-white border-t border-[#1E1B24]/10 px-4 py-2.5 text-[10px] font-mono text-[#716B78] shrink-0 space-y-1">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-[#7C3AED]" />
          <span>Evidence reference index</span>
        </div>
        <p className="text-[9px] text-[#716B78]/70">
          Source passages linked to document layout pages.
        </p>
      </div>

    </div>
  );
};
