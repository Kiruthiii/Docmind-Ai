export type DocumentStatus = 'uploading' | 'processing' | 'ready' | 'error';

export interface DocumentSection {
  heading: string;
  body: string;
}

export interface DocumentPage {
  page_number: number;
  title?: string;
  content: string;
  excerpt?: string;
  sections?: DocumentSection[];
}

export interface DocumentItem {
  id: string;
  workspace_id: string;
  filename: string;
  file_size: number;
  page_count: number;
  status: DocumentStatus;
  upload_progress?: number;
  error_message?: string;
  created_at: string;
  pages?: DocumentPage[];
  file_url?: string;
  file_data?: string | ArrayBuffer;
}

export interface Citation {
  id: string;
  page_number: number;
  snippet: string;
  document_id: string;
  document_name: string;
  relevance_score?: number;
  section_title?: string;
  bounding_box?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: Citation[];
  error?: boolean;
}

export interface UploadState {
  file: File | null;
  progress: number;
  status: 'idle' | 'uploading' | 'processing' | 'success' | 'error';
  errorMessage: string | null;
}

export interface DocumentReaderState {
  currentPage: number;
  zoomLevel: number; // 0.5 to 2.0
  searchQuery: string;
  activeMatchIndex: number;
  highlightedCitationId: string | null;
  highlightedPageNumber: number | null;
}
