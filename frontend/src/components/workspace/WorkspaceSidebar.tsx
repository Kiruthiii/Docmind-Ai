import React, { useEffect } from 'react';

import { Plus, Folder, FolderCheck, Loader2, FileUp, Scale } from 'lucide-react';

import type { DocumentItem } from '../../types/docmind';
import { DocumentList } from './DocumentList';

export interface WorkspaceItem {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
}

interface WorkspaceSidebarProps {
  workspaces: WorkspaceItem[];
  activeWorkspaceId: string | null;
  onSelectWorkspace: (id: string) => void;
  onOpenCreateModal: () => void;
  loadingWorkspaces: boolean;
  documents?: DocumentItem[];
  activeDocumentId?: string | null;
  onSelectDocument?: (docId: string) => void;
  onDeleteDocument?: (docId: string, filename: string) => void;
  loadingDocuments?: boolean;
  isOpen: boolean;
  onCloseMobileDrawer: () => void;
  onAddDocument?: () => void;
  onOpenCompareModal?: () => void;
}

export const WorkspaceSidebar: React.FC<WorkspaceSidebarProps> = ({
  workspaces,
  activeWorkspaceId,
  onSelectWorkspace,
  onOpenCreateModal,
  loadingWorkspaces,
  documents = [],
  activeDocumentId,
  onSelectDocument,
  onDeleteDocument,
  loadingDocuments = false,
  isOpen,
  onCloseMobileDrawer,
  onAddDocument,
  onOpenCompareModal,
}) => {
  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId);

  // Keyboard Escape listener for mobile drawer
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onCloseMobileDrawer();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCloseMobileDrawer]);

  const sidebarContent = (
    <div className="h-full flex flex-col justify-between p-4 space-y-6 text-left selection:bg-[#EDE7FA] selection:text-[#5B21B6] overflow-y-auto">
      <div className="space-y-6">
        
        {/* WORKSPACES SECTION */}
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] tracking-widest text-[#716B78] uppercase font-mono font-bold">
              WORKSPACES
            </span>
            <span className="text-[10px] font-mono text-[#716B78]">
              {workspaces.length} total
            </span>
          </div>

          {/* Workspaces List */}
          {loadingWorkspaces ? (
            <div className="p-4 text-center text-xs text-[#716B78] flex items-center justify-center gap-2 font-mono">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#7C3AED]" />
              <span>Fetching...</span>
            </div>
          ) : workspaces.length === 0 ? (
            <div className="p-3 text-xs text-[#716B78] bg-white border border-dashed border-[#1E1B24]/12 rounded-xl text-center">
              No workspaces found.
            </div>
          ) : (
            <div className="space-y-1" role="group" aria-label="Workspaces list">
              {workspaces.map((ws) => {
                const isActive = ws.id === activeWorkspaceId;
                return (
                  <button
                    key={ws.id}
                    type="button"
                    onClick={() => {
                      onSelectWorkspace(ws.id);
                      onCloseMobileDrawer();
                    }}
                    className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition-all text-left min-h-[44px] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED] ${
                      isActive
                        ? 'bg-white text-[#5B21B6] font-semibold border border-[#7C3AED]/25 shadow-sm'
                        : 'text-[#1E1B24] hover:bg-white/80 hover:text-[#5B21B6] border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {isActive ? (
                        <span className="w-2 h-2 rounded-full bg-[#7C3AED] shrink-0 animate-pulse" />
                      ) : (
                        <Folder className="w-3.5 h-3.5 text-[#716B78] shrink-0" />
                      )}
                      <span className="truncate">{ws.name}</span>
                    </div>

                    {isActive && (
                      <span className="text-[10px] font-mono bg-[#EDE7FA] text-[#5B21B6] px-1.5 py-0.5 rounded shrink-0">
                        Active
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* New Workspace Action Button */}
          <button
            type="button"
            onClick={onOpenCreateModal}
            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold text-[#7C3AED] bg-[#EDE7FA]/60 hover:bg-[#EDE7FA] border border-[#7C3AED]/20 hover:border-[#7C3AED]/40 transition-all min-h-[44px] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>+ New workspace</span>
          </button>
        </div>

        {/* DOCUMENTS SECTION */}
        <div className="space-y-3 pt-4 border-t border-[#1E1B24]/08">
          <div className="flex items-center justify-between px-1">
            <span className="text-[10px] tracking-widest text-[#716B78] uppercase font-mono font-bold">
              DOCUMENTS
            </span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-[#716B78]">
                {documents.length} files
              </span>
              {onAddDocument && (
                <button
                  type="button"
                  onClick={onAddDocument}
                  className="p-1 text-[#7C3AED] hover:bg-[#EDE7FA] rounded-md transition-colors min-h-[32px] min-w-[32px] flex items-center justify-center"
                  title="Upload Document"
                  aria-label="Upload Document"
                >
                  <FileUp className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Compare Documents CTA Button */}
          {onOpenCompareModal && (
            <button
              type="button"
              onClick={() => {
                onOpenCompareModal();
                onCloseMobileDrawer();
              }}
              className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold text-[#5B21B6] bg-[#EDE7FA] hover:bg-[#D8D3E6] border border-[#7C3AED]/30 hover:border-[#7C3AED]/60 transition-all min-h-[42px] shadow-2xs focus:outline-none focus-visible:ring-2 focus-visible:ring-[#7C3AED]"
            >
              <Scale className="w-3.5 h-3.5 text-[#7C3AED]" />
              <span>Compare Documents ({documents.length})</span>
            </button>
          )}

          <DocumentList
            documents={documents}
            activeDocumentId={activeDocumentId}
            onSelectDocument={(id) => {
              if (onSelectDocument) onSelectDocument(id);
              onCloseMobileDrawer();
            }}
            onDeleteDocument={onDeleteDocument}
            onAddDocument={onAddDocument}
            loadingDocuments={loadingDocuments}
          />
        </div>

      </div>

      {/* Sidebar Footer Metadata */}
      <div className="pt-4 border-t border-[#1E1B24]/08 text-[10px] text-[#716B78] font-mono space-y-1">
        <div className="flex items-center gap-1.5">
          <FolderCheck className="w-3 h-3 text-[#15803D]" />
          <span>{activeWorkspace ? activeWorkspace.name : 'Workspace'}: Ready</span>
        </div>
        <p className="text-[9px] text-[#716B78]/80">DocMind AI Research Standard</p>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:block w-64 xl:w-72 bg-[#F8F7FC] border-r border-[#1E1B24]/10 shrink-0">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-[#1E1B24]/40 backdrop-blur-xs transition-opacity"
            onClick={onCloseMobileDrawer}
            aria-hidden="true"
          />

          {/* Drawer Content */}
          <div
            id="mobile-sidebar-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Workspace Navigation Drawer"
            className="relative w-4/5 max-w-xs bg-[#F8F7FC] h-full shadow-2xl border-r border-[#1E1B24]/10 animate-in slide-in-from-left duration-200"
          >
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
};
