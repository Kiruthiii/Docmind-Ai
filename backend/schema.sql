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
    chunk_type TEXT NOT NULL DEFAULT 'text' CHECK (chunk_type IN ('text', 'table', 'image_description', 'figure_caption', 'reference', 'header')),
    content_type TEXT NOT NULL DEFAULT 'text',
    document_position TEXT NOT NULL DEFAULT 'general',
    section_hierarchy JSONB DEFAULT '[]'::jsonb,
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

-- Row Level Security Policies for Authenticated Users
DROP POLICY IF EXISTS "Users manage own workspaces" ON public.workspaces;
CREATE POLICY "Users manage own workspaces" ON public.workspaces
FOR ALL TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users manage documents in own workspaces" ON public.documents;
CREATE POLICY "Users manage documents in own workspaces" ON public.documents
FOR ALL TO authenticated
USING (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()))
WITH CHECK (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Users manage document chunks in own workspaces" ON public.document_chunks;
CREATE POLICY "Users manage document chunks in own workspaces" ON public.document_chunks
FOR ALL TO authenticated
USING (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()))
WITH CHECK (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Users manage chat sessions in own workspaces" ON public.chat_sessions;
CREATE POLICY "Users manage chat sessions in own workspaces" ON public.chat_sessions
FOR ALL TO authenticated
USING (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()))
WITH CHECK (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Users manage messages in own workspaces" ON public.messages;
CREATE POLICY "Users manage messages in own workspaces" ON public.messages
FOR ALL TO authenticated
USING (session_id IN (
    SELECT cs.id FROM public.chat_sessions cs
    JOIN public.workspaces w ON cs.workspace_id = w.id
    WHERE w.user_id = auth.uid()
))
WITH CHECK (session_id IN (
    SELECT cs.id FROM public.chat_sessions cs
    JOIN public.workspaces w ON cs.workspace_id = w.id
    WHERE w.user_id = auth.uid()
));

-- Helper RPC Function for Vector Similarity Search with Metadata & Workspace Isolation Filtering
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
  content_type text,
  document_position text,
  section_hierarchy jsonb,
  content text,
  section_path text,
  parent_section text,
  similarity float
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.document_id,
    dc.workspace_id,
    dc.page_number,
    dc.chunk_type,
    dc.content_type,
    dc.document_position,
    dc.section_hierarchy,
    dc.content,
    dc.section_path,
    dc.parent_section,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM public.document_chunks dc
  JOIN public.workspaces w ON dc.workspace_id = w.id
  WHERE dc.workspace_id = filter_workspace_id
    AND (w.user_id = auth.uid() OR auth.uid() IS NULL)
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create Storage Bucket 'documents' for PDF files if not already existing
INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', true)
ON CONFLICT (id) DO NOTHING;

-- Storage Policies for 'documents' bucket
DROP POLICY IF EXISTS "Allow public access on documents storage" ON storage.objects;
CREATE POLICY "Allow public access on documents storage" ON storage.objects
FOR ALL USING (bucket_id = 'documents') WITH CHECK (bucket_id = 'documents');
