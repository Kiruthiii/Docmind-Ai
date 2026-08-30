import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Loader2,
  Sparkles,
  RefreshCw,
  Trash2,
  AlertCircle,
  Bot,
  User,
  BookOpen,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import type { ChatMessage, Citation, DocumentItem } from '../../types/docmind';
import { chatApi, type BackendCitation } from '../../services/api';

interface ChatInterfaceProps {
  workspaceId: string;
  document: DocumentItem;
  messages: ChatMessage[];
  onSendMessage: (msg: ChatMessage) => void;
  onClearChat: () => void;
  onCitationClick: (citation: Citation) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  workspaceId,
  document,
  messages,
  onSendMessage,
  onClearChat,
  onCitationClick,
}) => {
  const [inputQuery, setInputQuery] = useState<string>('');
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [thinkingStep, setThinkingStep] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleSend = async (queryText?: string) => {
    const text = (queryText || inputQuery).trim();
    if (!text || isThinking) return;

    setErrorMsg(null);
    setInputQuery('');

    // 1. Add User Message
    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    onSendMessage(userMsg);

    // 2. Set Thinking state
    setIsThinking(true);
    setThinkingStep('Analyzing document context with Multi-Agent RAG pipeline...');

    try {
      const response = await chatApi.sendMessage({
        workspace_id: workspaceId,
        session_id: sessionId,
        question: text,
        show_sources: true,
      });

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      // Map Backend citations to Frontend Citation model
      const mappedCitations: Citation[] = (response.citations || []).map((c: BackendCitation, idx: number) => ({
        id: `cite-${c.document_id || document.id}-${c.page_number}-${idx}-${Date.now()}`,
        page_number: c.page_number,
        snippet: c.content_snippet || `Passage excerpt from Page ${c.page_number}`,
        document_id: c.document_id || document.id,
        document_name: c.document_name || document.filename,
        section_title: c.chunk_type ? `Type: ${c.chunk_type}` : undefined,
      }));

      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        sender: 'assistant',
        content: response.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: mappedCitations,
      };

      onSendMessage(assistantMsg);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate grounded RAG response. Please try again.');
    } finally {
      setIsThinking(false);
      setThinkingStep('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Helper to render message text with clickable [Page X] citation badges and evidence list
  const renderMessageContent = (msg: ChatMessage) => {
    if (msg.sender === 'user') {
      return <p className="whitespace-pre-wrap">{msg.content}</p>;
    }

    // Split message by [Page X] pattern
    const parts = msg.content.split(/(\[Page \d+\])/g);

    return (
      <div className="space-y-3">
        <p className="whitespace-pre-wrap leading-relaxed">
          {parts.map((part, idx) => {
            const match = part.match(/\[Page (\d+)\]/);
            if (match) {
              const pageNum = parseInt(match[1], 10);
              const relatedCitation = msg.citations?.find((c) => c.page_number === pageNum) || {
                id: `cite-${pageNum}`,
                page_number: pageNum,
                document_id: document.id,
                document_name: document.filename,
                snippet: `Passage excerpt from Page ${pageNum} of ${document.filename}`,
              };

              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => onCitationClick(relatedCitation)}
                  className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded bg-[#EDE7FA] hover:bg-[#7C3AED] text-[#5B21B6] hover:text-white font-mono text-[11px] font-bold border border-[#7C3AED]/30 transition-all cursor-pointer shadow-2xs focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]"
                  title={`Jump to Page ${pageNum}`}
                >
                  <BookOpen className="w-3 h-3" />
                  <span>Page {pageNum}</span>
                </button>
              );
            }
            return <span key={idx}>{part}</span>;
          })}
        </p>

        {msg.citations && msg.citations.length > 0 && (
          <div className="pt-2.5 border-t border-[#1E1B24]/10 space-y-1.5">
            <span className="text-[10px] font-mono text-[#716B78] uppercase tracking-wider font-bold block">
              GROUNDED EVIDENCE CITATIONS:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {msg.citations.map((cite) => (
                <button
                  key={cite.id}
                  type="button"
                  onClick={() => onCitationClick(cite)}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#EDE7FA] hover:bg-[#7C3AED] text-[#5B21B6] hover:text-white font-mono text-[11px] font-bold border border-[#7C3AED]/30 transition-all cursor-pointer shadow-2xs focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]"
                  title={cite.snippet || `Jump to Page ${cite.page_number}`}
                >
                  <BookOpen className="w-3 h-3 shrink-0" />
                  <span>{cite.document_name ? `${cite.document_name} — ` : ''}Page {cite.page_number}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const sampleQuestions = [
    'What is the main model architecture proposed?',
    'How does multi-head self-attention work?',
    'What hardware and training schedule were used?',
  ];

  return (
    <div className="flex-1 flex flex-col h-full bg-white selection:bg-[#EDE7FA] selection:text-[#5B21B6] text-left">
      
      {/* 1. CHAT HEADER */}
      <div className="bg-[#FAF8F5] border-b border-[#1E1B24]/10 px-4 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-[#1E1B24] font-sans">
              DocMind RAG Assistant
            </h3>
            <p className="text-[10px] text-[#716B78] font-mono truncate max-w-[180px] sm:max-w-xs">
              Context: {document.filename}
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            type="button"
            onClick={onClearChat}
            className="p-1.5 text-[#716B78] hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors min-h-[36px] min-w-[36px] flex items-center justify-center"
            title="Clear Chat History"
            aria-label="Clear Chat History"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* 2. CONVERSATION MESSAGES LIST AREA */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-[#F8F7FC]/30">
        
        {/* EMPTY STATE */}
        {messages.length === 0 && !isThinking && (
          <div className="py-8 text-center space-y-5 max-w-sm mx-auto">
            <div className="w-12 h-12 rounded-2xl bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center mx-auto shadow-xs">
              <Bot className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h4 className="text-sm font-bold text-[#1E1B24] font-sans">
                Ask questions about this paper
              </h4>
              <p className="text-xs text-[#716B78] leading-relaxed">
                DocMind locates evidence passages and provides grounded page citations.
              </p>
            </div>

            {/* Starter Prompt Cards */}
            <div className="space-y-2 text-left pt-2">
              <span className="text-[10px] font-mono text-[#716B78] uppercase tracking-wider font-bold block">
                SUGGESTED RESEARCH QUESTIONS:
              </span>
              {sampleQuestions.map((q, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(q)}
                  className="w-full p-3 bg-white hover:bg-[#EDE7FA]/40 border border-[#1E1B24]/10 hover:border-[#7C3AED]/40 rounded-xl text-xs text-[#1E1B24] text-left transition-all min-h-[44px] shadow-2xs font-sans"
                >
                  &ldquo;{q}&rdquo;
                </button>
              ))}
            </div>
          </div>
        )}

        {/* MESSAGES */}
        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          return (
            <div
              key={msg.id}
              className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
            >
              {/* Avatar Icon */}
              <div
                className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 font-bold text-xs ${
                  isUser
                    ? 'bg-[#1E1B24] text-white'
                    : 'bg-[#EDE7FA] text-[#7C3AED] border border-[#7C3AED]/20'
                }`}
              >
                {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              {/* Message Bubble */}
              <div
                className={`max-w-[85%] p-3.5 rounded-2xl text-xs shadow-2xs ${
                  isUser
                    ? 'bg-[#7C3AED] text-white rounded-tr-none'
                    : 'bg-white border border-[#1E1B24]/10 text-[#1E1B24] rounded-tl-none space-y-2'
                }`}
              >
                {renderMessageContent(msg)}

                <div
                  className={`text-[9px] font-mono mt-1 ${
                    isUser ? 'text-white/70 text-right' : 'text-[#716B78] text-left'
                  }`}
                >
                  {msg.timestamp}
                </div>
              </div>
            </div>
          );
        })}

        {/* THINKING STATE */}
        {isThinking && (
          <div className="flex items-start gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center shrink-0 border border-[#7C3AED]/20">
              <Bot className="w-3.5 h-3.5 animate-pulse" />
            </div>
            <div className="p-3.5 bg-white border border-[#7C3AED]/30 rounded-2xl rounded-tl-none shadow-2xs space-y-2">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#5B21B6]">
                <Loader2 className="w-3.5 h-3.5 animate-spin text-[#7C3AED]" />
                <span>{thinkingStep || 'Searching document context...'}</span>
              </div>
              <div className="w-32 h-1.5 bg-[#EDE7FA] rounded-full overflow-hidden">
                <div className="h-full bg-[#7C3AED] animate-pulse w-3/4" />
              </div>
            </div>
          </div>
        )}

        {/* ERROR MESSAGE & RETRY */}
        {errorMsg && (
          <div role="alert" className="p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 space-y-2">
            <div className="flex items-center gap-2 font-bold">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>Query Execution Failed</span>
            </div>
            <p className="font-mono text-[11px]">{errorMsg}</p>
            <div className="flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSend()}
                icon={<RefreshCw className="w-3 h-3" />}
                className="min-h-[36px]"
              >
                Retry Query
              </Button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 3. INPUT FORM AREA */}
      <div className="p-3 bg-white border-t border-[#1E1B24]/10 shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center gap-2"
        >
          <textarea
            ref={inputRef}
            rows={1}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about this document..."
            className="flex-1 p-3 bg-[#FAF8F5] border border-[#1E1B24]/12 rounded-xl text-xs focus:outline-none focus:border-[#7C3AED] focus:bg-white resize-none max-h-24 transition-all min-h-[44px]"
          />

          <Button
            type="submit"
            variant="primary"
            size="md"
            disabled={!inputQuery.trim() || isThinking}
            icon={<Send className="w-4 h-4" />}
            className="min-h-[44px] px-4 rounded-xl shrink-0"
            aria-label="Send question"
          >
            <span className="hidden sm:inline">Send</span>
          </Button>
        </form>

        <div className="flex items-center justify-between text-[9px] font-mono text-[#716B78] mt-2 px-1">
          <span>Press Enter to send, Shift+Enter for newline</span>
          <Badge variant="violet" size="sm" className="text-[9px] py-0 px-1.5">
            DocMind RAG Engine
          </Badge>
        </div>
      </div>

    </div>
  );
};
