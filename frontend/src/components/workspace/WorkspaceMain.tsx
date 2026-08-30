import React, { useState } from 'react';
import {
  FileUp,
  FolderPlus,
  Loader2,
  AlertCircle,
  RefreshCw,
  FileText,
  CheckCircle2,
  ShieldCheck,
  BookOpen,
  MessageSquare,
  Layers,
  Scale,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { DocumentReader } from './DocumentReader';
import { ChatInterface } from './ChatInterface';
import { EvidencePanel } from './EvidencePanel';
import type { WorkspaceItem } from './WorkspaceSidebar';
import type { DocumentItem, ChatMessage, Citation } from '../../types/docmind';

interface WorkspaceMainProps {
  activeWorkspace: WorkspaceItem | null;
  loadingWorkspaces: boolean;
  apiError: string | null;
  onRetry: () => void;
  onOpenCreateModal: () => void;
  documents?: DocumentItem[];
  activeDocumentId?: string | null;
  onUploadClick?: () => void;
  onDeleteDocument?: (docId: string, filename: string) => void;
  chatMessages?: ChatMessage[];
  onSendMessage?: (msg: ChatMessage) => void;
  onClearChat?: () => void;
  onOpenCompareModal?: () => void;
}

export const WorkspaceMain: React.FC<WorkspaceMainProps> = ({
  activeWorkspace,
  loadingWorkspaces,
  apiError,
  onRetry,
  onOpenCreateModal,
  documents = [],
  activeDocumentId,
  onUploadClick,
  onDeleteDocument,
  chatMessages = [],
  onSendMessage,
  onClearChat,
  onOpenCompareModal,
}) => {
  // Mobile Tab State: 'reader' | 'chat' | 'evidence'
  const [mobileTab, setMobileTab] = useState<'reader' | 'chat' | 'evidence'>('reader');

  // Reader & Citation states
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [activeCitationId, setActiveCitationId] = useState<string | null>(null);
  const [highlightedPageNumber, setHighlightedPageNumber] = useState<number | null>(null);

  const activeDocument = documents.find((d) => d.id === activeDocumentId) || documents[0] || null;

  // Extract all citations from chat history
  const allCitations: Citation[] = chatMessages.reduce((acc: Citation[], msg) => {
    if (msg.citations) {
      msg.citations.forEach((c) => {
        if (!acc.some((existing) => existing.id === c.id)) {
          acc.push(c);
        }
      });
    }
    return acc;
  }, []);

  const handleCitationClick = (citation: Citation) => {
    setActiveCitationId(citation.id);
    setHighlightedPageNumber(citation.page_number);
    setCurrentPage(citation.page_number);
    // On mobile, switch to reader tab to show the highlighted page
    setMobileTab('reader');
  };

  const handleJumpToPage = (pageNum: number) => {
    setHighlightedPageNumber(pageNum);
    setCurrentPage(pageNum);
    setMobileTab('reader');
  };

  // 1. Loading State
  if (loadingWorkspaces) {
    return (
      <main className="flex-1 flex flex-col items-center justify-center p-8 bg-[#F5F2EC] selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
        <div role="status" className="flex flex-col items-center gap-3 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-[#7C3AED]" />
          <p className="text-xs font-mono text-[#716B78]">Initializing research workstation...</p>
        </div>
      </main>
    );
  }

  // 2. API Error State
  if (apiError) {
    return (
      <main className="flex-1 p-6 sm:p-10 bg-[#F5F2EC] flex flex-col justify-center selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
        <div
          role="alert"
          className="max-w-xl mx-auto w-full p-6 bg-white border border-red-200 rounded-2xl shadow-sm text-left space-y-4"
        >
          <div className="flex items-center gap-3 text-red-700">
            <AlertCircle className="w-6 h-6 shrink-0" />
            <h2 className="text-base font-bold font-sans">Workspace Engine Failure</h2>
          </div>
          <p className="text-xs text-[#716B78] font-mono leading-relaxed bg-red-50 p-3 rounded-xl border border-red-100">
            {apiError}
          </p>
          <div className="pt-2 flex justify-end">
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              icon={<RefreshCw className="w-3.5 h-3.5" />}
              className="min-h-[44px]"
            >
              Retry Request
            </Button>
          </div>
        </div>
      </main>
    );
  }

  // 3. No Workspaces Exist State
  if (!activeWorkspace) {
    return (
      <main className="flex-1 p-6 sm:p-12 bg-[#F5F2EC] flex flex-col items-center justify-center selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
        <div className="max-w-lg w-full bg-white p-8 sm:p-10 rounded-2xl border border-[#1E1B24]/12 shadow-sm text-center space-y-6">
          <div className="w-12 h-12 rounded-2xl bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center mx-auto">
            <FolderPlus className="w-6 h-6" />
          </div>
          
          <div className="space-y-2">
            <h2 className="text-lg sm:text-xl font-bold text-[#1E1B24] font-sans">
              No Active Workspaces
            </h2>
            <p className="text-xs text-[#716B78] leading-relaxed max-w-sm mx-auto">
              Create a workspace to begin ingesting documents, extracting citations, and performing RAG research.
            </p>
          </div>

          <Button
            variant="primary"
            size="md"
            onClick={onOpenCreateModal}
            icon={<FolderPlus className="w-4 h-4" />}
            className="w-full sm:w-auto min-h-[44px] justify-center font-semibold"
          >
            Create Research Workspace
          </Button>
        </div>
      </main>
    );
  }

  // 4. Active Workspace with NO Documents: Show Academic Document Canvas & Upload CTA
  if (!activeDocument) {
    return (
      <main className="flex-1 bg-[#F5F2EC] flex flex-col selection:bg-[#EDE7FA] selection:text-[#5B21B6] overflow-y-auto">
        
        {/* Workspace Header Section */}
        <div className="bg-white border-b border-[#1E1B24]/10 px-6 sm:px-10 py-4 text-left">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2.5">
                <h1 className="text-lg sm:text-xl font-bold text-[#1E1B24] font-sans tracking-tight">
                  {activeWorkspace.name}
                </h1>
                <Badge variant="violet" size="sm">
                  Active Workspace
                </Badge>
              </div>
              <p className="text-[11px] text-[#716B78] font-mono">
                ID: {activeWorkspace.id} &bull; Created: {new Date(activeWorkspace.created_at).toLocaleDateString()}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#FAF8F5] border border-[#1E1B24]/08 text-[11px] text-[#716B78] font-mono">
                <span>Library:</span>
                <strong className="text-[#1E1B24] font-sans font-bold">{documents.length} files</strong>
              </div>

              {onOpenCompareModal && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onOpenCompareModal}
                  icon={<Scale className="w-3.5 h-3.5 text-[#7C3AED]" />}
                  className="min-h-[36px]"
                >
                  Compare Documents
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Central Composition: Paper Sheet Preview + Upload CTA */}
        <div className="flex-1 p-4 sm:p-8 lg:p-10 max-w-7xl w-full mx-auto flex flex-col justify-between space-y-8 text-left">
          
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            
            {/* Document Sheet Mockup - 7 cols desktop */}
            <div className="lg:col-span-7 bg-white rounded-xl border border-[#1E1B24]/15 shadow-md shadow-[#1E1B24]/05 p-6 sm:p-8 space-y-5 relative overflow-hidden select-none">
              <div className="flex items-center justify-between pb-3 border-b border-[#1E1B24]/10 text-[10px] font-mono text-[#716B78]">
                <div className="flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-[#7C3AED]" />
                  <span className="font-semibold text-[#1E1B24]">Vaswani_Attention_2017.pdf</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="bg-[#F8F7FC] px-2 py-0.5 rounded border border-[#1E1B24]/08">
                    PAGE 001 // SEC 1.2
                  </span>
                  <span className="text-[#15803D] font-bold flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> INDEXED
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <h3 className="text-base sm:text-lg font-bold text-[#1E1B24] font-sans tracking-tight leading-snug">
                  Attention Is All You Need — Multi-Head Self-Attention Ingestion
                </h3>
                <p className="text-[11px] text-[#716B78] font-mono">
                  Ashish Vaswani, Noam Shazeer et al. &bull; NeurIPS Research Archive
                </p>
              </div>

              <div className="p-3.5 bg-[#FAF8F5] rounded-lg border border-[#1E1B24]/08 space-y-2 text-left">
                <span className="text-[9px] font-mono uppercase tracking-widest text-[#716B78] font-bold block">
                  EXTRACTED PARAGRAPH EXCERPT
                </span>
                <p className="text-xs font-serif text-[#2D2A35] leading-relaxed italic">
                  &ldquo;We propose the Transformer, a model architecture eschewing recurrence and relying entirely on attention mechanisms to draw global dependencies between input and output.&rdquo;
                </p>
              </div>

              <div className="py-2.5 px-4 bg-[#F8F7FC] rounded-lg border border-[#7C3AED]/20 text-center font-mono text-xs text-[#1E1B24]">
                {"$$\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V$$"}
              </div>

              <div className="p-3 bg-[#EDE7FA]/80 rounded-r-lg border-l-4 border-[#7C3AED] text-xs text-[#5B21B6] space-y-1">
                <div className="flex items-center justify-between text-[10px] font-mono font-bold">
                  <span className="flex items-center gap-1 text-[#7C3AED]">
                    <ShieldCheck className="w-3.5 h-3.5" /> EVIDENCE HIGHLIGHT [1]
                  </span>
                  <span className="text-[#15803D]">RETRIEVAL SCORE: 0.942</span>
                </div>
                <p className="text-[11px] text-[#1E1B24] font-sans font-medium leading-normal">
                  Multi-Head Attention allows the model to jointly attend to information from different representation subspaces at different positions.
                </p>
              </div>

              <div className="pt-2 flex items-center justify-between text-[9px] font-mono text-[#716B78]/60 border-t border-[#1E1B24]/08">
                <span>DOCMIND-PARSER-V2 // VECTOR CHUNK #0412</span>
                <span>CONFIDENCE: 99.4%</span>
              </div>
            </div>

            {/* Upload Callout composition - 5 cols desktop */}
            <div className="lg:col-span-5 space-y-6 text-left pl-0 lg:pl-4">
              <div className="space-y-3">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#EDE7FA] text-[#5B21B6] text-xs font-semibold border border-[#7C3AED]/20">
                  <FileUp className="w-3.5 h-3.5 text-[#7C3AED]" />
                  <span>Document Analysis Engine</span>
                </div>

                <h2 className="text-2xl sm:text-3xl font-extrabold text-[#1E1B24] font-sans tracking-tight">
                  Start with a document
                </h2>

                <p className="text-xs sm:text-sm text-[#716B78] leading-relaxed">
                  Upload a research paper, technical report, or PDF to begin exploring its evidence, citations, and grounded answers.
                </p>
              </div>

              <div>
                <Button
                  variant="primary"
                  size="lg"
                  onClick={onUploadClick}
                  icon={<FileUp className="w-4 h-4" />}
                  className="w-full sm:w-auto px-7 py-3.5 text-sm font-semibold shadow-md shadow-[#7C3AED]/25 justify-center min-h-[48px]"
                >
                  Upload PDF Document
                </Button>
              </div>

              <div className="pt-4 border-t border-[#1E1B24]/10 space-y-2 text-xs text-[#716B78]">
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#7C3AED]" />
                  <span>Direct page-level citations &amp; bounding box highlighting</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#15803D]" />
                  <span>Zero-hallucination grounded RAG verification</span>
                </div>
              </div>
            </div>

          </div>

          {/* Engine Rail */}
          <div className="pt-6 border-t border-[#1E1B24]/12 space-y-3">
            <div className="flex items-center justify-between text-[10px] font-mono tracking-widest text-[#716B78] uppercase font-bold">
              <span>DOCUMENT INTELLIGENCE ENGINE</span>
              <span>SYSTEM STATUS: OPERATIONAL</span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 bg-white rounded-lg border border-[#1E1B24]/10 flex items-center justify-between">
                <span className="text-[11px] font-mono text-[#1E1B24] font-semibold">PDF PARSING</span>
                <span className="text-[10px] font-mono text-[#15803D] font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#15803D]" /> READY
                </span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-[#1E1B24]/10 flex items-center justify-between">
                <span className="text-[11px] font-mono text-[#1E1B24] font-semibold">EVIDENCE INDEX</span>
                <span className="text-[10px] font-mono text-[#15803D] font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#15803D]" /> READY
                </span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-[#1E1B24]/10 flex items-center justify-between">
                <span className="text-[11px] font-mono text-[#1E1B24] font-semibold">PAGE CONTEXT</span>
                <span className="text-[10px] font-mono text-[#15803D] font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#15803D]" /> READY
                </span>
              </div>
              <div className="p-3 bg-white rounded-lg border border-[#1E1B24]/10 flex items-center justify-between">
                <span className="text-[11px] font-mono text-[#1E1B24] font-semibold">GROUNDED OUTPUT</span>
                <span className="text-[10px] font-mono text-[#15803D] font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#15803D]" /> READY
                </span>
              </div>
            </div>
          </div>

        </div>
      </main>
    );
  }

  // 5. Active Document Workstation View (Split view on Desktop, Tabbed on Mobile)
  return (
    <main className="flex-1 bg-[#F5F2EC] flex flex-col selection:bg-[#EDE7FA] selection:text-[#5B21B6] overflow-hidden">
      
      {/* MOBILE TAB BAR (Only on screens below lg:) */}
      <div className="lg:hidden bg-white border-b border-[#1E1B24]/10 px-2 py-2 flex items-center justify-around text-xs font-semibold shrink-0">
        <button
          type="button"
          onClick={() => setMobileTab('reader')}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition-all min-h-[44px] ${
            mobileTab === 'reader'
              ? 'bg-[#7C3AED] text-white shadow-xs'
              : 'text-[#716B78] hover:text-[#1E1B24] hover:bg-[#FAF8F5]'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Reader</span>
        </button>

        <button
          type="button"
          onClick={() => setMobileTab('chat')}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition-all min-h-[44px] ${
            mobileTab === 'chat'
              ? 'bg-[#7C3AED] text-white shadow-xs'
              : 'text-[#716B78] hover:text-[#1E1B24] hover:bg-[#FAF8F5]'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>Chat</span>
        </button>

        <button
          type="button"
          onClick={() => setMobileTab('evidence')}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl transition-all min-h-[44px] ${
            mobileTab === 'evidence'
              ? 'bg-[#7C3AED] text-white shadow-xs'
              : 'text-[#716B78] hover:text-[#1E1B24] hover:bg-[#FAF8F5]'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Evidence ({allCitations.length})</span>
        </button>
      </div>

      {/* DESKTOP SPLIT VIEW & MOBILE TAB SWITCHING CONTAINER */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* LEFT / CENTER: DOCUMENT READER (Always visible on desktop, or when mobileTab === 'reader' on mobile) */}
        <div className={`flex-1 flex flex-col h-full min-w-0 ${mobileTab === 'reader' ? 'flex' : 'hidden lg:flex'}`}>
          <DocumentReader
            document={activeDocument}
            currentPage={currentPage}
            onPageChange={(page) => {
              setCurrentPage(page);
              setHighlightedPageNumber(null);
            }}
            highlightedPageNumber={highlightedPageNumber}
            highlightedCitationId={activeCitationId}
            onDeleteDocument={onDeleteDocument}
          />
        </div>

        {/* RIGHT COLUMN: CHAT & EVIDENCE PANEL (Desktop 40% width split, Mobile tab switching) */}
        <div
          className={`w-full lg:w-[420px] xl:w-[480px] shrink-0 border-l border-[#1E1B24]/10 flex flex-col h-full bg-white ${
            mobileTab !== 'reader' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {/* Mobile sub-tabs for Chat vs Evidence when in right panel */}
          <div className="hidden lg:flex items-center border-b border-[#1E1B24]/10 bg-[#FAF8F5] px-3 py-2 gap-2 text-xs font-semibold shrink-0">
            <button
              type="button"
              onClick={() => setMobileTab('chat')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg transition-colors min-h-[38px] ${
                mobileTab !== 'evidence'
                  ? 'bg-white text-[#5B21B6] border border-[#7C3AED]/20 shadow-2xs font-bold'
                  : 'text-[#716B78] hover:text-[#1E1B24]'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Grounded Chat</span>
            </button>

            <button
              type="button"
              onClick={() => setMobileTab('evidence')}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg transition-colors min-h-[38px] ${
                mobileTab === 'evidence'
                  ? 'bg-white text-[#5B21B6] border border-[#7C3AED]/20 shadow-2xs font-bold'
                  : 'text-[#716B78] hover:text-[#1E1B24]'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Evidence ({allCitations.length})</span>
            </button>
          </div>

          {/* CHAT INTERFACE AREA */}
          <div className={`flex-1 flex flex-col h-full ${mobileTab === 'evidence' ? 'hidden' : 'flex'}`}>
            <ChatInterface
              workspaceId={activeWorkspace.id}
              document={activeDocument}
              messages={chatMessages}
              onSendMessage={(msg) => onSendMessage && onSendMessage(msg)}
              onClearChat={() => onClearChat && onClearChat()}
              onCitationClick={handleCitationClick}
            />
          </div>

          {/* EVIDENCE PANEL AREA */}
          <div className={`flex-1 flex flex-col h-full ${mobileTab === 'evidence' ? 'flex' : 'hidden'}`}>
            <EvidencePanel
              citations={allCitations}
              activeCitationId={activeCitationId}
              onSelectCitation={handleCitationClick}
              onJumpToPage={handleJumpToPage}
            />
          </div>

        </div>

      </div>

    </main>
  );
};
