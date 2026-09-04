import React, { useState, useRef, useEffect } from 'react';

import {
  FileUp,
  X,
  FileText,
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Trash2,
  UploadCloud,
  Sparkles,
} from 'lucide-react';

import type { DocumentItem } from '../../types/docmind';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { documentApi } from '../../services/api';

interface PdfUploadModalProps {
  isOpen: boolean;
  workspaceId: string | null;
  onClose: () => void;
  onUploadSuccess: (newDoc: DocumentItem) => void;
}

export const PdfUploadModal: React.FC<PdfUploadModalProps> = ({
  isOpen,
  workspaceId,
  onClose,
  onUploadSuccess,
}) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'success' | 'error'>('idle');
  const [progress, setProgress] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadedDoc, setUploadedDoc] = useState<DocumentItem | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (!isOpen) {
      setSelectedFile(null);
      setStatus('idle');
      setProgress(0);
      setErrorMessage(null);
      setUploadedDoc(null);
      setDragActive(false);
    }
  }, [isOpen]);

  // Keyboard Escape listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && status !== 'uploading' && status !== 'processing') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, status, onClose]);

  if (!isOpen) return null;

  const validateFile = (file: File): string | null => {
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      return 'Invalid file format. DocMind accepts PDF documents only (.pdf).';
    }
    const MAX_SIZE_BYTES = 25 * 1024 * 1024; // 25 MB
    if (file.size > MAX_SIZE_BYTES) {
      return `File size exceeds 25 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB). Please select a smaller file.`;
    }
    return null;
  };

  const handleFileSelection = (file: File) => {
    setErrorMessage(null);
    const error = validateFile(file);
    if (error) {
      setErrorMessage(error);
      setStatus('error');
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setStatus('idle');
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const startUpload = async () => {
    if (!selectedFile || !workspaceId) return;

    setStatus('uploading');
    setProgress(15);
    setErrorMessage(null);

    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          return 90;
        }
        const next = prev + 15;
        if (next >= 60) {
          setStatus('processing');
        }
        return next;
      });
    }, 180);

    try {
      const res = await documentApi.upload(workspaceId, selectedFile);
      clearInterval(progressTimer);
      setProgress(100);
      setStatus('success');

      const createdDoc: DocumentItem = {
        id: res.document_id,
        workspace_id: workspaceId,
        filename: res.filename,
        file_size: selectedFile.size,
        page_count: 0,
        status: 'ready',
        created_at: new Date().toISOString(),
      };
      setUploadedDoc(createdDoc);
      onUploadSuccess(createdDoc);
    } catch (err: any) {
      clearInterval(progressTimer);
      setErrorMessage(err.message || 'Failed to upload document. Please try again.');
      setStatus('error');
    }
  };


  const handleDone = () => {
    onClose();
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-[#1E1B24]/50 backdrop-blur-xs transition-opacity"
        onClick={() => {
          if (status !== 'uploading' && status !== 'processing') onClose();
        }}
        aria-hidden="true"
      />

      {/* Modal Dialog Box */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-modal-title"
        className="relative w-full max-w-lg bg-white rounded-2xl border border-[#1E1B24]/15 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 text-left"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1E1B24]/10 bg-[#FAF8F5]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center">
              <FileUp className="w-4 h-4" />
            </div>
            <div>
              <h2 id="upload-modal-title" className="text-base font-bold text-[#1E1B24] font-sans">
                Upload PDF Document
              </h2>
              <p className="text-[11px] text-[#716B78] font-mono">
                Ingest PDF for RAG index &amp; citation verification
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            disabled={status === 'uploading' || status === 'processing'}
            className="p-2 text-[#716B78] hover:text-[#1E1B24] hover:bg-[#EDE7FA]/60 rounded-xl transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5">
          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleInputChange}
            className="hidden"
            id="pdf-file-input"
          />

          {/* 1. IDLE / SELECTION STATE */}
          {(status === 'idle' || (status === 'error' && !selectedFile)) && (
            <div className="space-y-4">
              {/* Dropzone */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer flex flex-col items-center justify-center gap-3 min-h-[200px] ${
                  dragActive
                    ? 'border-[#7C3AED] bg-[#EDE7FA]/40 scale-[1.01]'
                    : 'border-[#1E1B24]/15 hover:border-[#7C3AED]/50 bg-[#FAF8F5]/80 hover:bg-white'
                }`}
              >
                <div className="w-12 h-12 rounded-2xl bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center shadow-xs">
                  <UploadCloud className="w-6 h-6" />
                </div>

                <div className="space-y-1">
                  <p className="text-sm font-semibold text-[#1E1B24]">
                    Drag and drop your PDF here, or <span className="text-[#7C3AED] underline underline-offset-2">browse files</span>
                  </p>
                  <p className="text-xs text-[#716B78] font-mono">
                    PDF files up to 25 MB supported
                  </p>
                </div>
              </div>

              {/* Error Box if any */}
              {errorMessage && (
                <div role="alert" className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700 flex items-start gap-2.5">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div className="space-y-0.5">
                    <p className="font-semibold">Upload Validation Error</p>
                    <p className="text-red-600 font-mono text-[11px]">{errorMessage}</p>
                  </div>
                </div>
              )}

              {/* Selected File Card if chosen */}
              {selectedFile && (
                <div className="p-4 bg-[#F8F7FC] border border-[#7C3AED]/25 rounded-xl flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-9 h-9 rounded-lg bg-[#EDE7FA] text-[#5B21B6] flex items-center justify-center shrink-0 font-mono font-bold text-xs">
                      <FileText className="w-4 h-4 text-[#7C3AED]" />
                    </div>
                    <div className="min-w-0 text-left">
                      <p className="text-xs font-bold text-[#1E1B24] truncate">
                        {selectedFile.name}
                      </p>
                      <p className="text-[10px] text-[#716B78] font-mono">
                        {formatFileSize(selectedFile.size)} &bull; PDF Document
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      setErrorMessage(null);
                    }}
                    className="p-2 text-[#716B78] hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                    aria-label="Remove selected file"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* 2. UPLOADING / PROCESSING STATE */}
          {(status === 'uploading' || status === 'processing') && (
            <div className="space-y-6 py-4 text-center">
              <div className="w-14 h-14 rounded-2xl bg-[#EDE7FA] text-[#7C3AED] flex items-center justify-center mx-auto relative">
                <Loader2 className="w-7 h-7 animate-spin" />
              </div>

              <div className="space-y-2">
                <h3 className="text-sm font-bold text-[#1E1B24] font-sans">
                  {status === 'uploading' ? 'Uploading PDF Document...' : 'Processing Layout & Vectorizing...'}
                </h3>
                <p className="text-xs text-[#716B78] font-mono">
                  {selectedFile?.name}
                </p>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5 max-w-sm mx-auto">
                <div className="w-full h-2 bg-[#1E1B24]/10 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[#7C3AED] transition-all duration-300 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[10px] font-mono text-[#716B78]">
                  <span>{status === 'uploading' ? 'Parsing PDF binary' : 'Generating text chunks'}</span>
                  <span>{progress}%</span>
                </div>
              </div>

              {/* Steps Indicator */}
              <div className="p-3 bg-[#FAF8F5] rounded-xl border border-[#1E1B24]/08 max-w-sm mx-auto text-left text-xs font-mono space-y-1 text-[#716B78]">
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${progress >= 30 ? 'bg-[#15803D]' : 'bg-[#716B78]'}`} />
                  <span>1. Validating document headers</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${progress >= 70 ? 'bg-[#15803D]' : 'bg-[#716B78]'}`} />
                  <span>2. Extracting layout pages &amp; equations</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full ${progress >= 95 ? 'bg-[#15803D]' : 'bg-[#716B78]'}`} />
                  <span>3. Preparing grounded RAG citation index</span>
                </div>
              </div>
            </div>
          )}

          {/* 3. SUCCESS STATE */}
          {status === 'success' && uploadedDoc && (
            <div className="space-y-5 text-center py-2">
              <div className="w-12 h-12 rounded-2xl bg-green-100 text-[#15803D] flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>

              <div className="space-y-1">
                <h3 className="text-base font-bold text-[#1E1B24] font-sans">
                  PDF Ingestion Complete
                </h3>
                <p className="text-xs text-[#716B78]">
                  Document has been indexed and added to your workspace library.
                </p>
              </div>

              <div className="p-4 bg-[#F0FDF4] border border-[#15803D]/20 rounded-xl text-left flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-[#15803D]" />
                  <div>
                    <p className="text-xs font-bold text-[#1E1B24] truncate max-w-[220px]">
                      {uploadedDoc.filename}
                    </p>
                    <p className="text-[10px] text-[#716B78] font-mono">
                      {uploadedDoc.page_count} pages &bull; Ready for RAG research
                    </p>
                  </div>
                </div>
                <Badge variant="grounded" size="sm">
                  READY
                </Badge>
              </div>
            </div>
          )}

          {/* 4. ERROR STATE WITH RETRY */}
          {status === 'error' && selectedFile && (
            <div className="space-y-4 py-2">
              <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-left space-y-3">
                <div className="flex items-center gap-2 text-red-700 font-bold text-sm">
                  <AlertCircle className="w-4 h-4" />
                  <span>Upload Operation Failed</span>
                </div>
                <p className="text-xs text-[#716B78] font-mono bg-white p-2.5 rounded-lg border border-red-100">
                  {errorMessage || 'An unexpected error occurred while processing the document.'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Modal Action Buttons Footer */}
        <div className="px-6 py-4 bg-[#FAF8F5] border-t border-[#1E1B24]/10 flex items-center justify-end gap-3">
          {status === 'idle' && (
            <>
              <Button
                variant="outline"
                size="md"
                onClick={onClose}
                className="min-h-[44px]"
              >
                Cancel
              </Button>

              <Button
                variant="primary"
                size="md"
                onClick={startUpload}
                disabled={!selectedFile}
                icon={<Sparkles className="w-4 h-4" />}
                className="min-h-[44px] font-semibold"
              >
                Ingest PDF
              </Button>
            </>
          )}

          {status === 'error' && (
            <>
              <Button
                variant="outline"
                size="md"
                onClick={onClose}
                className="min-h-[44px]"
              >
                Close
              </Button>

              <Button
                variant="primary"
                size="md"
                onClick={startUpload}
                icon={<RefreshCw className="w-4 h-4" />}
                className="min-h-[44px]"
              >
                Retry Ingestion
              </Button>
            </>
          )}

          {status === 'success' && (
            <Button
              variant="primary"
              size="md"
              onClick={handleDone}
              icon={<CheckCircle2 className="w-4 h-4" />}
              className="w-full sm:w-auto min-h-[44px] font-semibold"
            >
              Open Document Workstation
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
