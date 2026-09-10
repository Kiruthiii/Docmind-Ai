import logging
import uuid
from typing import Any, Dict, List, Optional

from supabase import Client, create_client

from app.core.config import settings

logger = logging.getLogger("docmind")

class InMemoryDatabase:
    """In-memory database fallback for development and testing without active Supabase credentials."""
    def __init__(self):
        self.workspaces: Dict[str, Dict[str, Any]] = {}
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.pdf_bytes: Dict[str, bytes] = {}
        self.document_chunks: List[Dict[str, Any]] = []
        self.chat_sessions: Dict[str, Dict[str, Any]] = {}
        self.messages: List[Dict[str, Any]] = []
        logger.info("Initialized In-Memory DB fallback mode.")

_in_memory_db = InMemoryDatabase()
_supabase_client_instance: Optional[Client] = None

def get_supabase_client(access_token: Optional[str] = None) -> Optional[Client]:
    """
    Returns a Supabase client.
    If access_token is provided, configures headers with the authenticated user's Bearer JWT
    so PostgREST executes queries in Postgres under the authenticated user's scope (enforcing RLS).
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "your-project" in settings.SUPABASE_URL:
        return None

    try:
        if access_token:
            if access_token.count(".") != 2:
                return None
            client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            client.postgrest.auth(access_token)
            return client

        global _supabase_client_instance
        if _supabase_client_instance is not None:
            return _supabase_client_instance

        _supabase_client_instance = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return _supabase_client_instance
    except Exception as e:
        logger.warning(f"Failed to connect to Supabase: {e}")
        return None

