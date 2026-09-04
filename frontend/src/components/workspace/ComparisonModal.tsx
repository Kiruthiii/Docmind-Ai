import React, { useState, useEffect, useCallback } from 'react';

import {
  X,
  Scale,
  Loader2,
  AlertCircle,
  AlertTriangle,
  Check,
  Plus,
  Copy,
  BookOpen,
  FileText,
  CheckSquare,
  Square,
  RefreshCw,
} from 'lucide-react';

import type { DocumentItem } from '../../types/docmind';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { chatApi, type ComparisonResponseData } from '../../services/api';

interface ComparisonModalProps {
  isOpen: boolean;
  onClose: () => void;
  workspaceId: string | null;
  documents: DocumentItem[];
}

const DEFAULT_CATEGORIES = ['Summary', 'Methodology', 'Results', 'Advantages', 'Limitations'];

export const ComparisonModal: React.FC<ComparisonModalProps> = ({
  isOpen,
  onClose,
  workspaceId,
  documents = [],
}) => {
  // Selected Document IDs state
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  // Categories state
  const [categories, setCategories] = useState<string[]>(DEFAULT_CATEGORIES);
  const [newCategoryInput, setNewCategoryInput] = useState<string>('');

  // API Call Execution State
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResponseData | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  // Initialize/Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setError(null);
      setComparisonResult(null);
      setCopied(false);
      setCategories(DEFAULT_CATEGORIES);
      setNewCategoryInput('');

      // Pre-select all documents by default
      if (documents.length > 0) {
        setSelectedDocIds(documents.map((d) => d.id));
      } else {
        setSelectedDocIds([]);
      }
    }
  }, [isOpen, documents]);

  // Keyboard Escape listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isLoading) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, onClose]);

  // Category Management Handlers
  const handleAddCategory = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = newCategoryInput.trim();
    if (trimmed && !categories.some((c) => c.toLowerCase() === trimmed.toLowerCase())) {
      setCategories((prev) => [...prev, trimmed]);
      setNewCategoryInput('');
    }
  };

  const handleRemoveCategory = (catToRemove: string) => {
    setCategories((prev) => prev.filter((c) => c !== catToRemove));
  };

  // Toggle Document Selection
  const toggleDocSelection = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedDocIds.length === documents.length) {
      setSelectedDocIds([]);
    } else {
      setSelectedDocIds(documents.map((d) => d.id));
    }
  };

  // Execute Real API Request
  const handleExecuteComparison = useCallback(async () => {
    if (!workspaceId) {
      setError('No active workspace selected.');
      return;
    }
    if (selectedDocIds.length < 2) {
      setError('Please select at least 2 documents to compare.');
      return;
    }
    if (categories.length === 0) {
      setError('Please specify at least 1 comparison category.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await chatApi.compare({
        workspace_id: workspaceId,
        document_ids: selectedDocIds,
        categories: categories,
      });

      setComparisonResult(response);
    } catch (err: any) {
      console.error('Comparison API error:', err);
      setError(err.message || 'Failed to compare documents. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, selectedDocIds, categories]);

  // Copy Markdown Matrix to Clipboard
  const handleCopyMatrix = () => {
    if (comparisonResult?.markdown_matrix) {
      navigator.clipboard.writeText(comparisonResult.markdown_matrix);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen) return null;

  // Helper to parse and render Markdown matrix text/tables into structured HTML
  const renderMarkdownContent = (markdown: string) => {
    if (!markdown || !markdown.trim()) {
      return (
        <div className="p-6 text-center text-xs text-[#716B78] font-mono bg-white rounded-xl border border-[#1E1B24]/10">
          No comparison table output returned from server.
        </div>
      );
    }

    const lines = markdown.split('\n');
    const elements: React.ReactNode[] = [];
    let currentTableRows: string[][] = [];
    let inTable = false;
    let tableKeyCounter = 0;

    const flushTable = () => {
      if (currentTableRows.length > 0) {
        // Filter out divider row (e.g. | --- | --- |)
        const headerRow = currentTableRows[0];
        const bodyRows = currentTableRows.slice(1).filter(
          (row) => !row.every((cell) => /^[\s:-]+$/.test(cell))
        );

        elements.push(
          <div
            key={`table-${tableKeyCounter++}`}
            className="my-4 overflow-x-auto rounded-xl border border-[#1E1B24]/12 bg-white shadow-xs"
          >
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#FAF8F5] border-b border-[#1E1B24]/12">
                  {headerRow.map((cell, cIdx) => (
                    <th
                      key={cIdx}
                      className="p-3 sm:p-3.5 font-sans font-bold text-[#1E1B24] border-r border-[#1E1B24]/08 last:border-r-0 tracking-tight"
                    >
                      {cell.replace(/\*\*/g, '').trim()}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E1B24]/08 font-sans">
                {bodyRows.map((row, rIdx) => (
                  <tr
                    key={rIdx}
                    className="hover:bg-[#F8F7FC]/60 transition-colors odd:bg-white even:bg-[#F8F7FC]/30"
                  >
                    {row.map((cell, cIdx) => {
                      const text = cell.trim();
                      const isHeaderCol = cIdx === 0;
                      return (
                        <td
                          key={cIdx}
                          className={`p-3 sm:p-3.5 border-r border-[#1E1B24]/08 last:border-r-0 text-[#1E1B24] leading-relaxed align-top ${
                            isHeaderCol ? 'font-semibold text-[#5B21B6] bg-[#EDE7FA]/20' : ''
                          }`}
                        >
                          {text.split('**').map((part, pIdx) =>
                            pIdx % 2 === 1 ? (
                              <strong key={pIdx} className="font-bold text-[#1E1B24]">
                                {part}
                              </strong>
                            ) : (
                              <span key={pIdx}>{part}</span>
                            )
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        currentTableRows = [];
        inTable = false;
      }
    };

    lines.forEach((line, idx) => {
      const trimmed = line.trim();

      // Check if line is part of a markdown table (starts and ends with '|' or contains multiple '|')
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        inTable = true;
        const cells = trimmed
          .split('|')
          .slice(1, -1)
          .map((c) => c.trim());
        currentTableRows.push(cells);
      } else {
        if (inTable) {
          flushTable();
        }

        if (trimmed.startsWith('### ')) {
          elements.push(
            <h4
              key={`h3-${idx}`}
              className="text-sm font-bold text-[#1E1B24] font-sans pt-3 pb-1 flex items-center gap-2"
            >
              <span className="w-2 h-2 rounded-full bg-[#7C3AED]" />
              {trimmed.replace('### ', '')}
            </h4>
          );
        } else if (trimmed.startsWith('## ')) {
          elements.push(
            <h3
              key={`h2-${idx}`}
              className="text-base font-extrabold text-[#1E1B24] font-sans pt-4 pb-1"
            >
              {trimmed.replace('## ', '')}
            </h3>
          );
        } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          elements.push(
            <li key={`li-${idx}`} className="text-xs text-[#1E1B24] leading-relaxed ml-4 list-disc my-1">
              {trimmed.substring(2)}
            </li>
          );
        } else if (trimmed.length > 0) {
          elements.push(
            <p key={`p-${idx}`} className="text-xs text-[#1E1B24] leading-relaxed my-2">
              {trimmed}
            </p>
          );
        }
      }
    });

    if (inTable) {
      flushTable();
    }

    return <div className="space-y-1 text-left">{elements}</div>;
  };

  const isFormInvalid = selectedDocIds.length < 2 || categories.length === 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#1E1B24]/40 backdrop-blur-xs transition-opacity"
        onClick={() => {
          if (!isLoading) onClose();
        }}
        aria-hidden="true"
      />

      {/* Modal Dialog Container */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="comparison-modal-title"
        className="relative w-full max-w-4xl max-h-[90vh] bg-[#F8F7FC] rounded-2xl border border-[#1E1B24]/12 shadow-2xl flex flex-col overflow-hidden animate-in fade-in-50 zoom-in-95 duration-150 text-left"
      >
        {/* MODAL HEADER */}
        <div className="bg-white border-b border-[#1E1B24]/10 px-5 sm:px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center shrink-0 border border-[#7C3AED]/20">
              <Scale className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="comparison-modal-title" className="text-base sm:text-lg font-bold text-[#1E1B24] font-sans">
                  Multi-Document Comparison Matrix
                </h2>
                <Badge variant="violet" size="sm" className="hidden sm:inline-flex">
                  DocMind RAG Engine
                </Badge>
              </div>
              <p className="text-xs text-[#716B78]">
                Compare facts, methodologies, and findings across multiple workspace papers.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
            aria-label="Close modal"
            className="p-2 rounded-xl text-[#716B78] hover:text-[#1E1B24] hover:bg-[#F8F7FC] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] min-h-[44px] min-w-[44px] flex items-center justify-center transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* MODAL BODY (Scrollable) */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-6">

          {/* 1. SELECTION & CONFIGURATION SECTION */}
          {!comparisonResult && !isLoading && (
            <div className="space-y-6">

              {/* Document Selection Box */}
              <div className="p-4 bg-white rounded-xl border border-[#1E1B24]/10 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-[#7C3AED]" />
                    <span className="text-xs font-bold text-[#1E1B24] font-sans">
                      Select Documents to Compare ({selectedDocIds.length}/{documents.length})
                    </span>
                  </div>

                  {documents.length >= 2 && (
                    <button
                      type="button"
                      onClick={toggleSelectAll}
                      className="text-[11px] font-mono text-[#7C3AED] hover:underline font-semibold flex items-center gap-1"
                    >
                      {selectedDocIds.length === documents.length ? (
                        <>
                          <CheckSquare className="w-3.5 h-3.5" /> Deselect All
                        </>
                      ) : (
                        <>
                          <Square className="w-3.5 h-3.5" /> Select All ({documents.length})
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* Document Selection Grid */}
                {documents.length < 2 ? (
                  <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-amber-800 text-xs flex items-center gap-2 font-mono">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>
                      At least 2 documents are required in the workspace to perform cross-document comparison. Please upload more files.
                    </span>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {documents.map((doc) => {
                      const isChecked = selectedDocIds.includes(doc.id);
                      return (
                        <div
                          key={doc.id}
                          onClick={() => toggleDocSelection(doc.id)}
                          className={`flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer select-none text-xs min-h-[44px] ${
                            isChecked
                              ? 'bg-[#EDE7FA]/40 border-[#7C3AED]/40 text-[#5B21B6] font-semibold'
                              : 'bg-[#F8F7FC] border-[#1E1B24]/08 text-[#716B78] hover:bg-white'
                          }`}
                        >
                          <div className="flex items-center gap-2.5 min-w-0">
                            <div
                              className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors ${
                                isChecked
                                  ? 'bg-[#7C3AED] border-[#7C3AED] text-white'
                                  : 'border-[#716B78]/40 bg-white'
                              }`}
                            >
                              {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                            </div>
                            <span className="truncate">{doc.filename}</span>
                          </div>

                          <span className="text-[10px] font-mono text-[#716B78] shrink-0 ml-2">
                            {doc.page_count} pages
                          </span>
                        </div>
                      );
                    })}
                  </div>
                )}

                {selectedDocIds.length < 2 && documents.length >= 2 && (
                  <p className="text-[11px] text-amber-700 font-mono flex items-center gap-1.5 pt-1">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>Select at least 2 documents to enable matrix comparison.</span>
                  </p>
                )}
              </div>

              {/* Comparison Categories Configuration */}
              <div className="p-4 bg-white rounded-xl border border-[#1E1B24]/10 space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-[#1E1B24] font-sans flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-[#7C3AED]" />
                    Comparison Categories ({categories.length})
                  </span>
                  <span className="text-[10px] font-mono text-[#716B78]">
                    Customizable criteria tags
                  </span>
                </div>

                {/* Categories Tags */}
                <div className="flex flex-wrap gap-2">
                  {categories.map((cat) => (
                    <span
                      key={cat}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#EDE7FA] text-[#5B21B6] text-xs font-semibold border border-[#7C3AED]/20"
                    >
                      <span>{cat}</span>
                      <button
                        type="button"
                        onClick={() => handleRemoveCategory(cat)}
                        className="text-[#7C3AED] hover:text-red-600 rounded p-0.5 transition-colors"
                        title={`Remove category "${cat}"`}
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>

                {/* Add Custom Category Form */}
                <form onSubmit={handleAddCategory} className="flex items-center gap-2 pt-1">
                  <input
                    type="text"
                    value={newCategoryInput}
                    onChange={(e) => setNewCategoryInput(e.target.value)}
                    placeholder="Add custom criteria (e.g. Model Size, Dataset, Dataset Size)..."
                    className="flex-1 min-h-[38px] bg-[#F8F7FC] border border-[#1E1B24]/15 rounded-xl px-3 text-xs text-[#1E1B24] placeholder-[#716B78] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#7C3AED] transition-all"
                  />
                  <Button
                    type="submit"
                    variant="outline"
                    size="sm"
                    disabled={!newCategoryInput.trim()}
                    icon={<Plus className="w-3.5 h-3.5" />}
                    className="min-h-[38px] px-3 shrink-0"
                  >
                    Add
                  </Button>
                </form>

                {categories.length === 0 && (
                  <p className="text-[11px] text-red-600 font-mono flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>Please add at least one category to run comparison.</span>
                  </p>
                )}
              </div>

            </div>
          )}

          {/* 2. LOADING STATE */}
          {isLoading && (
            <div className="py-12 bg-white rounded-xl border border-[#7C3AED]/20 p-8 text-center space-y-4 shadow-sm">
              <div className="w-12 h-12 rounded-2xl bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center mx-auto animate-bounce">
                <Scale className="w-6 h-6" />
              </div>

              <div className="space-y-1">
                <h3 className="text-sm font-bold text-[#1E1B24] font-sans flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-[#7C3AED]" />
                  <span>Synthesizing Multi-Document Matrix...</span>
                </h3>
                <p className="text-xs text-[#716B78] font-mono">
                  Fetching workspace vector chunks and analyzing cross-document findings.
                </p>
              </div>

              <div className="w-48 h-1.5 bg-[#EDE7FA] rounded-full overflow-hidden mx-auto">
                <div className="h-full bg-[#7C3AED] animate-pulse w-3/4" />
              </div>
            </div>
          )}

          {/* 3. ERROR NOTIFICATION */}
          {error && !isLoading && (
            <div
              role="alert"
              className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs space-y-3"
            >
              <div className="flex items-center gap-2 font-bold text-sm">
                <AlertCircle className="w-4.5 h-4.5 shrink-0 text-red-600" />
                <span>Comparison Analysis Failed</span>
              </div>
              <p className="font-mono text-xs leading-relaxed bg-white/60 p-2.5 rounded-lg border border-red-100">
                {error}
              </p>
              <div className="flex justify-end pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExecuteComparison}
                  icon={<RefreshCw className="w-3.5 h-3.5" />}
                  className="min-h-[36px]"
                >
                  Retry Comparison
                </Button>
              </div>
            </div>
          )}

          {/* 4. COMPARISON RESULTS VIEW */}
          {comparisonResult && !isLoading && (
            <div className="space-y-6">

              {/* Header Action Bar for Results */}
              <div className="flex items-center justify-between bg-white p-3.5 rounded-xl border border-[#1E1B24]/10">
                <div className="flex items-center gap-2">
                  <Badge variant="grounded" size="sm">
                    Comparison Complete
                  </Badge>
                  <span className="text-xs text-[#716B78] font-mono">
                    Workspace ID: {comparisonResult.workspace_id}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopyMatrix}
                    icon={copied ? <Check className="w-3.5 h-3.5 text-[#15803D]" /> : <Copy className="w-3.5 h-3.5" />}
                    className="min-h-[36px] text-xs font-semibold"
                  >
                    {copied ? 'Copied Matrix!' : 'Copy Matrix'}
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setComparisonResult(null)}
                    icon={<RefreshCw className="w-3.5 h-3.5" />}
                    className="min-h-[36px] text-xs"
                  >
                    Configure Again
                  </Button>
                </div>
              </div>

              {/* Rendered Markdown Matrix Table */}
              <div className="p-5 bg-white rounded-xl border border-[#1E1B24]/10 shadow-xs space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#716B78] font-mono">
                  COMPARATIVE MATRIX
                </h3>

                {renderMarkdownContent(comparisonResult.markdown_matrix)}
              </div>

              {/* Potential Contradictions Alert Card */}
              {comparisonResult.potential_contradictions &&
                comparisonResult.potential_contradictions.length > 0 && (
                  <div className="p-4 bg-amber-50/80 rounded-xl border border-amber-200 text-amber-900 space-y-2">
                    <div className="flex items-center gap-2 font-bold text-xs text-amber-800">
                      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                      <span>Potential Contradictions Detected</span>
                    </div>

                    <ul className="space-y-1 pl-5 list-disc text-xs font-sans">
                      {comparisonResult.potential_contradictions.map((item, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

              {/* Citations List */}
              {comparisonResult.citations && comparisonResult.citations.length > 0 && (
                <div className="p-4 bg-white rounded-xl border border-[#1E1B24]/10 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#716B78] font-mono flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-[#7C3AED]" />
                      Referenced Document Evidence ({comparisonResult.citations.length})
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {comparisonResult.citations.map((cite, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-[#F8F7FC] rounded-lg border border-[#1E1B24]/08 space-y-1 text-xs"
                      >
                        <div className="flex items-center justify-between font-semibold text-[#5B21B6]">
                          <span className="truncate">{cite.document_name}</span>
                          <span className="font-mono text-[10px] bg-[#EDE7FA] px-1.5 py-0.5 rounded">
                            Page {cite.page_number}
                          </span>
                        </div>
                        <p className="text-[11px] text-[#716B78] line-clamp-2 leading-relaxed font-sans italic">
                          &ldquo;{cite.content_snippet}&rdquo;
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}

        </div>

        {/* MODAL FOOTER */}
        <div className="bg-white border-t border-[#1E1B24]/10 px-5 sm:px-6 py-4 flex items-center justify-between shrink-0">
          <span className="text-[10px] font-mono text-[#716B78]">
            {!comparisonResult ? 'Step 1 of 2: Configure Comparison' : 'Step 2 of 2: Matrix View'}
          </span>

          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="outline"
              size="md"
              onClick={onClose}
              disabled={isLoading}
              className="min-h-[44px]"
            >
              {comparisonResult ? 'Done' : 'Cancel'}
            </Button>

            {!comparisonResult && (
              <Button
                type="button"
                variant="primary"
                size="md"
                onClick={handleExecuteComparison}
                disabled={isLoading || isFormInvalid}
                icon={
                  isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Scale className="w-4 h-4" />
                  )
                }
                className="min-h-[44px] font-semibold"
              >
                {isLoading ? 'Comparing...' : 'Compare Documents'}
              </Button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
