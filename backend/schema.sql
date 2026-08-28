-- Enable pgvector and UUID extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Workspaces table
CREATE TABLE IF NOT EXISTS public.workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents table
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'ready', 'failed')),
    page_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document Chunks table (with pgvector embedding)
CREATE TABLE IF NOT EXISTS public.document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL CHECK (page_number >= 1),
    chunk_type TEXT NOT NULL DEFAULT 'text' CHECK (chunk_type IN ('text', 'table', 'image_description')),
    content TEXT NOT NULL,
    section_path TEXT DEFAULT '',
    parent_section TEXT DEFAULT '',
    embedding vector(768) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chat Sessions table
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    title TEXT DEFAULT 'New Chat',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_documents_workspace ON public.documents(workspace_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_workspace ON public.document_chunks(workspace_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON public.document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_workspace ON public.chat_sessions(workspace_id);
CREATE INDEX IF NOT EXISTS idx_messages_session ON public.messages(session_id);

-- HNSW Vector Index for sub-millisecond Cosine Similarity Search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
ON public.document_chunks 
USING hnsw (embedding vector_cosine_ops);

-- Enable Row Level Security (RLS)
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Helper RPC Function for Vector Similarity Search with Metadata Filtering
CREATE OR REPLACE FUNCTION match_document_chunks (
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  filter_workspace_id uuid
)
RETURNS TABLE (
  id uuid,
  document_id uuid,
  workspace_id uuid,
  page_number int,
  chunk_type text,
  content text,
  section_path text,
  parent_section text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.document_id,
    dc.workspace_id,
    dc.page_number,
    dc.chunk_type,
    dc.content,
    dc.section_path,
    dc.parent_section,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM public.document_chunks dc
  WHERE dc.workspace_id = filter_workspace_id
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
