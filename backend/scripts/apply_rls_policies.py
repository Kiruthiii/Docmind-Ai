import os
import sys
import logging

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.supabase_client import get_supabase_client
from app.core.config import settings

logger = logging.getLogger("docmind")

SQL_POLICIES = """
-- Enable Row Level Security (RLS)
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Workspaces policy
DROP POLICY IF EXISTS "Users manage own workspaces" ON public.workspaces;
CREATE POLICY "Users manage own workspaces" ON public.workspaces
FOR ALL TO authenticated
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Documents policy
DROP POLICY IF EXISTS "Users manage documents in own workspaces" ON public.documents;
CREATE POLICY "Users manage documents in own workspaces" ON public.documents
FOR ALL TO authenticated
USING (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()))
WITH CHECK (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()));

-- Document Chunks policy
DROP POLICY IF EXISTS "Users manage document chunks in own workspaces" ON public.document_chunks;
CREATE POLICY "Users manage document chunks in own workspaces" ON public.document_chunks
FOR ALL TO authenticated
USING (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()))
WITH CHECK (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()));

-- Chat Sessions policy
DROP POLICY IF EXISTS "Users manage chat sessions in own workspaces" ON public.chat_sessions;
CREATE POLICY "Users manage chat sessions in own workspaces" ON public.chat_sessions
FOR ALL TO authenticated
USING (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()))
WITH CHECK (workspace_id IN (SELECT id FROM public.workspaces WHERE user_id = auth.uid()));

-- Messages policy (Strengthened RLS)
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
"""

def main():
    print("=====================================================")
    print("DocMind AI — Supabase RLS Policy & Connection Check")
    print("=====================================================")
    client = get_supabase_client()
    if not client:
        print("❌ Error: Could not initialize Supabase client. Check SUPABASE_URL and SUPABASE_KEY.")
        sys.exit(1)

    print("✅ Supabase client active for URL:", settings.SUPABASE_URL)
    
    # Test table visibility
    tables = ["workspaces", "documents", "document_chunks", "chat_sessions", "messages"]
    for table in tables:
        try:
            res = client.table(table).select("id").limit(1).execute()
            print(f"  • Table '{table}': OK")
        except Exception as e:
            print(f"  • Table '{table}': {e}")

    print("\n--- Required SQL Policies for Supabase SQL Editor ---")
    print(SQL_POLICIES)
    print("=====================================================")

if __name__ == "__main__":
    main()

