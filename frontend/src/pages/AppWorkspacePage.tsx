import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { workspaceApi, documentApi } from '../services/api';
import { AppHeader } from '../components/workspace/AppHeader';
import { WorkspaceSidebar, type WorkspaceItem } from '../components/workspace/WorkspaceSidebar';
import { WorkspaceMain } from '../components/workspace/WorkspaceMain';
import { CreateWorkspaceModal } from '../components/workspace/CreateWorkspaceModal';
import { PdfUploadModal } from '../components/workspace/PdfUploadModal';
import { ComparisonModal } from '../components/workspace/ComparisonModal';
import type { DocumentItem, ChatMessage } from '../types/docmind';

export const AppWorkspacePage: React.FC = () => {
  const { user, signOut } = useAuth();

  // Workspaces state
  const [workspaces, setWorkspaces] = useState<WorkspaceItem[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [loadingWorkspaces, setLoadingWorkspaces] = useState<boolean>(true);
  const [apiError, setApiError] = useState<string | null>(null);

  // Documents state (mapped per workspace ID)
  const [workspaceDocs, setWorkspaceDocs] = useState<Record<string, DocumentItem[]>>({});
  const [activeDocIdMap, setActiveDocIdMap] = useState<Record<string, string | null>>({});
  const [loadingDocuments, setLoadingDocuments] = useState<boolean>(false);

  // Chat messages state (mapped per document ID)
  const [chatMessagesMap, setChatMessagesMap] = useState<Record<string, ChatMessage[]>>({});

  // Modal Visibility states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [isCreating, setIsCreating] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [isCompareModalOpen, setIsCompareModalOpen] = useState<boolean>(false);
  const [isMobileDrawerOpen, setIsMobileDrawerOpen] = useState<boolean>(false);

  // Fetch workspaces from backend API on mount
  const loadWorkspaces = useCallback(async () => {
    setLoadingWorkspaces(true);
    setApiError(null);
    try {
      const data = await workspaceApi.list();
      setWorkspaces(data);
      if (data.length > 0) {
        setActiveWorkspaceId((prev) => (prev && data.some((w) => w.id === prev) ? prev : data[0].id));
      } else {
        setActiveWorkspaceId(null);
      }
    } catch (err: any) {
      setApiError(err.message || 'Failed to fetch user workspaces from server.');
    } finally {
      setLoadingWorkspaces(false);
    }
  }, []);

  useEffect(() => {
    loadWorkspaces();
  }, [loadWorkspaces]);

  // Fetch documents for active workspace from real FastAPI backend
  const fetchWorkspaceDocuments = useCallback(async (wsId: string) => {
    setLoadingDocuments(true);
    try {
      const backendDocs = await documentApi.list(wsId);
      const mappedDocs: DocumentItem[] = backendDocs.map((d) => ({
        id: d.id,
        workspace_id: d.workspace_id,
        filename: d.filename,
        file_size: 0,
        page_count: d.page_count || 0,
        status: d.status === 'failed' ? 'error' : (d.status as any) || 'ready',
        created_at: d.created_at,
      }));

      setWorkspaceDocs((prev) => ({ ...prev, [wsId]: mappedDocs }));

      if (mappedDocs.length > 0) {
        setActiveDocIdMap((prev) => ({
          ...prev,
          [wsId]: prev[wsId] && mappedDocs.some((doc) => doc.id === prev[wsId]) ? prev[wsId] : mappedDocs[0].id,
        }));
      } else {
        setActiveDocIdMap((prev) => ({ ...prev, [wsId]: null }));
      }
    } catch (err) {
      console.error('Failed to load workspace documents from backend:', err);
    } finally {
      setLoadingDocuments(false);
    }
  }, []);

  // Load documents when activeWorkspaceId changes
  useEffect(() => {
    if (!activeWorkspaceId) return;
    fetchWorkspaceDocuments(activeWorkspaceId);
  }, [activeWorkspaceId, fetchWorkspaceDocuments]);

  // Create Workspace handler
  const handleCreateWorkspace = async (name: string) => {
    setIsCreating(true);
    setCreateError(null);
    try {
      const created = await workspaceApi.create(name);
      setWorkspaces((prev) => [created, ...prev]);
      setActiveWorkspaceId(created.id);
      setIsCreateModalOpen(false);
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create workspace. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleSignOut = async () => {
    await signOut();
  };

  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId) || null;
  const currentDocs = activeWorkspaceId ? workspaceDocs[activeWorkspaceId] || [] : [];
  const currentActiveDocId = activeWorkspaceId ? activeDocIdMap[activeWorkspaceId] || null : null;
  const activeDocument = currentDocs.find((d) => d.id === currentActiveDocId) || currentDocs[0] || null;

  // Handle successful upload: update active doc and refresh library from FastAPI backend
  const handleUploadSuccess = async (newDoc: DocumentItem) => {
    if (!activeWorkspaceId) return;
    setWorkspaceDocs((prev) => {
      const existing = prev[activeWorkspaceId] || [];
      const exists = existing.some((d) => d.id === newDoc.id);
      return {
        ...prev,
        [activeWorkspaceId]: exists ? existing : [newDoc, ...existing],
      };
    });
    setActiveDocIdMap((prev) => ({
      ...prev,
      [activeWorkspaceId]: newDoc.id,
    }));
    await fetchWorkspaceDocuments(activeWorkspaceId);
  };

  // Handle document deletion using real FastAPI DELETE endpoint
  const handleDeleteDocument = async (docId: string, filename: string) => {
    if (!activeWorkspaceId) return;
    const confirmed = window.confirm(`Are you sure you want to remove "${filename}" from this workspace?`);
    if (!confirmed) return;

    try {
      await documentApi.delete(docId);
      await fetchWorkspaceDocuments(activeWorkspaceId);
    } catch (err: any) {
      console.error('Failed to delete document from backend:', err);
      alert(err.message || 'Failed to delete document from backend server.');
    }
  };


  // Chat message handlers
  const currentChatMessages = activeDocument ? chatMessagesMap[activeDocument.id] || [] : [];

  const handleSendMessage = (msg: ChatMessage) => {
    if (!activeDocument) return;
    setChatMessagesMap((prev) => ({
      ...prev,
      [activeDocument.id]: [...(prev[activeDocument.id] || []), msg],
    }));
  };

  const handleClearChat = () => {
    if (!activeDocument) return;
    setChatMessagesMap((prev) => ({
      ...prev,
      [activeDocument.id]: [],
    }));
  };

  return (
    <div className="min-h-screen bg-[#F8F7FC] flex flex-col font-sans overflow-x-hidden selection:bg-[#EDE7FA] selection:text-[#5B21B6]">
      {/* Top Application Header */}
      <AppHeader
        user={user}
        activeWorkspaceName={activeWorkspace?.name}
        onSignOut={handleSignOut}
        isMobileDrawerOpen={isMobileDrawerOpen}
        onToggleMobileDrawer={() => setIsMobileDrawerOpen((prev) => !prev)}
      />

      {/* Main Layout: Workspace Sidebar + Workstation Canvas */}
      <div className="flex-1 flex overflow-hidden">
        <WorkspaceSidebar
          workspaces={workspaces}
          activeWorkspaceId={activeWorkspaceId}
          onSelectWorkspace={(id) => setActiveWorkspaceId(id)}
          onOpenCreateModal={() => {
            setCreateError(null);
            setIsCreateModalOpen(true);
          }}
          loadingWorkspaces={loadingWorkspaces}
          documents={currentDocs}
          activeDocumentId={activeDocument?.id}
          onSelectDocument={(docId) => {
            if (activeWorkspaceId) {
              setActiveDocIdMap((prev) => ({ ...prev, [activeWorkspaceId]: docId }));
            }
          }}
          onDeleteDocument={handleDeleteDocument}
          loadingDocuments={loadingDocuments}
          isOpen={isMobileDrawerOpen}
          onCloseMobileDrawer={() => setIsMobileDrawerOpen(false)}
          onAddDocument={() => setIsUploadModalOpen(true)}
          onOpenCompareModal={() => setIsCompareModalOpen(true)}
        />

        <WorkspaceMain
          activeWorkspace={activeWorkspace}
          loadingWorkspaces={loadingWorkspaces}
          apiError={apiError}
          onRetry={loadWorkspaces}
          onOpenCreateModal={() => {
            setCreateError(null);
            setIsCreateModalOpen(true);
          }}
          documents={currentDocs}
          activeDocumentId={activeDocument?.id}
          onUploadClick={() => setIsUploadModalOpen(true)}
          onDeleteDocument={handleDeleteDocument}
          chatMessages={currentChatMessages}
          onSendMessage={handleSendMessage}
          onClearChat={handleClearChat}
          onOpenCompareModal={() => setIsCompareModalOpen(true)}
        />
      </div>

      {/* Create Workspace Modal */}
      <CreateWorkspaceModal
        isOpen={isCreateModalOpen}
        onClose={() => {
          if (!isCreating) {
            setIsCreateModalOpen(false);
            setCreateError(null);
          }
        }}
        onCreate={handleCreateWorkspace}
        isCreating={isCreating}
        error={createError}
      />

      {/* PDF Upload Modal */}
      <PdfUploadModal
        isOpen={isUploadModalOpen}
        workspaceId={activeWorkspaceId}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Multi-Document Comparison Modal */}
      <ComparisonModal
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        workspaceId={activeWorkspaceId}
        documents={currentDocs}
      />
    </div>
  );
};
