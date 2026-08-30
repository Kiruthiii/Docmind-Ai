import React from 'react';
import { FileText, Plus, FileCode2, CheckCircle2, Clock, AlertCircle, Loader2, Trash2 } from 'lucide-react';
import { Badge } from '../ui/Badge';
import type { DocumentItem } from '../../types/docmind';

interface DocumentListProps {
  documents?: DocumentItem[];
  activeDocumentId?: string | null;
  onSelectDocument?: (docId: string) => void;
  onDeleteDocument?: (docId: string, filename: string) => void;
  onAddDocument?: () => void;
  loadingDocuments?: boolean;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents = [],
  activeDocumentId,
  onSelectDocument,
  onDeleteDocument,
  onAddDocument,
  loadingDocuments = false,
}) => {
  if (loadingDocuments) {
    return (
      <div className="py-6 px-3 text-center text-xs text-[#716B78] flex items-center justify-center gap-2 font-mono bg-white/50 rounded-xl border border-[#1E1B24]/08">
        <Loader2 className="w-4 h-4 animate-spin text-[#7C3AED]" />
        <span>Loading library...</span>
      </div>
    );
  }

  if (!documents || documents.length === 0) {
    return (
      <div className="py-5 px-4 text-left space-y-3 border border-[#1E1B24]/10 rounded-xl bg-white/80 shadow-xs">
        <div className="flex items-center gap-2 text-[#716B78]">
          <FileText className="w-4 h-4 text-[#7C3AED]" />
          <span className="text-xs font-bold text-[#1E1B24]">No documents yet</span>
        </div>
        
        <p className="text-[11px] text-[#716B78] leading-relaxed">
          Upload a PDF paper or technical document to start RAG research.
        </p>

        {onAddDocument && (
          <button
            type="button"
            onClick={onAddDocument}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl text-xs font-semibold text-[#7C3AED] bg-[#EDE7FA] hover:bg-[#D8D3E6] border border-[#7C3AED]/20 transition-all min-h-[44px] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Upload PDF Document</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-2" role="group" aria-label="Documents library list">
      {documents.map((doc) => {
        const isActive = doc.id === activeDocumentId;
        return (
          <div
            key={doc.id}
            onClick={() => onSelectDocument && onSelectDocument(doc.id)}
            className={`w-full group flex items-center justify-between p-3 rounded-xl transition-all cursor-pointer text-left min-h-[48px] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] ${
              isActive
                ? 'bg-white text-[#5B21B6] border border-[#7C3AED]/30 shadow-md shadow-[#7C3AED]/05 ring-1 ring-[#7C3AED]/10'
                : 'bg-white/70 hover:bg-white border border-[#1E1B24]/08 text-[#1E1B24]'
            }`}
          >
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${
                  isActive ? 'bg-[#7C3AED] text-white' : 'bg-[#EDE7FA] text-[#5B21B6]'
                }`}
              >
                <FileCode2 className="w-4 h-4" />
              </div>

              <div className="min-w-0 flex-1">
                <p className={`text-xs font-bold truncate ${isActive ? 'text-[#5B21B6]' : 'text-[#1E1B24]'}`}>
                  {doc.filename}
                </p>
                <div className="flex items-center gap-2 text-[10px] text-[#716B78] font-mono mt-0.5">
                  <span>{doc.page_count} pages</span>
                  {doc.created_at && (
                    <span>&bull; {new Date(doc.created_at).toLocaleDateString()}</span>
                  )}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1.5 shrink-0 ml-2">
              {doc.status && (
                <Badge
                  variant={
                    doc.status === 'ready'
                      ? 'grounded'
                      : doc.status === 'error'
                      ? 'warm'
                      : 'violet'
                  }
                  size="sm"
                  icon={
                    doc.status === 'ready' ? (
                      <CheckCircle2 className="w-3 h-3" />
                    ) : doc.status === 'error' ? (
                      <AlertCircle className="w-3 h-3 text-red-600" />
                    ) : (
                      <Clock className="w-3 h-3 animate-spin" />
                    )
                  }
                  className="text-[10px]"
                >
                  {doc.status}
                </Badge>
              )}

              {/* Delete Document Button */}
              {onDeleteDocument && (
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteDocument(doc.id, doc.filename);
                  }}
                  className="p-1 text-[#716B78] hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors min-h-[28px] min-w-[28px] flex items-center justify-center"
                  title={`Remove ${doc.filename}`}
                  aria-label={`Remove ${doc.filename}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};
