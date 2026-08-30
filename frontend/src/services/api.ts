import { supabase } from '../lib/supabaseClient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

  const customHeaders = options.headers instanceof Headers
    ? Object.fromEntries(options.headers.entries())
    : (options.headers as Record<string, string> || {});

  const headers: Record<string, string> = {
    ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...customHeaders,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = `API Request failed with status ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      // JSON parse error, use default message
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

export const workspaceApi = {
  list: () => apiFetch<Array<{ id: string; user_id: string; name: string; created_at: string }>>('/workspaces'),
  create: (name: string) => apiFetch<{ id: string; user_id: string; name: string; created_at: string }>('/workspaces', {
    method: 'POST',
    body: JSON.stringify({ name }),
  }),
  get: (workspaceId: string) => apiFetch<{ id: string; user_id: string; name: string; created_at: string }>(`/workspaces/${workspaceId}`),
  delete: (workspaceId: string) => apiFetch<void>(`/workspaces/${workspaceId}`, {
    method: 'DELETE',
  }),
};

export interface BackendDocumentResponse {
  id: string;
  workspace_id: string;
  filename: string;
  storage_path: string;
  status: string;
  page_count: number;
  created_at: string;
}

export interface BackendDocumentUploadResponse {
  document_id: string;
  filename: string;
  status: string;
  message: string;
}

export const documentApi = {
  list: (workspaceId: string) =>
    apiFetch<BackendDocumentResponse[]>(`/workspaces/${workspaceId}/documents`),

  upload: (workspaceId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiFetch<BackendDocumentUploadResponse>(`/workspaces/${workspaceId}/documents`, {
      method: 'POST',
      body: formData,
    });
  },

  getFileUrl: (documentId: string) => `${API_BASE_URL}/documents/${documentId}/file`,

  delete: (documentId: string) =>
    apiFetch<void>(`/documents/${documentId}`, {
      method: 'DELETE',
    }),
};

export interface ComparisonRequestPayload {
  workspace_id: string;
  document_ids?: string[] | null;
  categories?: string[];
}

export interface ComparisonCitation {
  document_id: string;
  document_name: string;
  page_number: number;
  content_snippet: string;
  chunk_type: string;
}

export interface ComparisonResponseData {
  workspace_id: string;
  markdown_matrix: string;
  potential_contradictions: string[];
  citations: ComparisonCitation[];
}

export interface BackendCitation {
  document_id: string;
  document_name: string;
  page_number: number;
  content_snippet: string;
  chunk_type: string;
}

export interface ChatMessageRequest {
  workspace_id: string;
  session_id?: string;
  question: string;
  show_sources?: boolean;
}

export interface ChatMessageResponse {
  session_id: string;
  question: string;
  answer: string;
  is_grounded: boolean;
  citations: BackendCitation[];
}

export const chatApi = {
  sendMessage: (payload: ChatMessageRequest) =>
    apiFetch<ChatMessageResponse>('/chat/message', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getHistory: (sessionId: string) =>
    apiFetch<Array<any>>(`/chat/${sessionId}/messages`),
  compare: (payload: ComparisonRequestPayload) =>
    apiFetch<ComparisonResponseData>('/chat/compare', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};


