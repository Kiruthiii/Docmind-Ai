from supabase import create_client, Client
from app.core.config import settings
import logging
import uuid
from typing import Dict, List, Any, Optional

logger = logging.getLogger("docmind")

class InMemoryDatabase:
    """In-memory database fallback for development and testing without active Supabase credentials."""
    def __init__(self):
        self.workspaces: Dict[str, Dict[str, Any]] = {}
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.document_chunks: List[Dict[str, Any]] = []
        self.chat_sessions: Dict[str, Dict[str, Any]] = {}
        self.messages: List[Dict[str, Any]] = []
        logger.info("Initialized In-Memory DB fallback mode.")

_in_memory_db = InMemoryDatabase()

def get_supabase_client() -> Optional[Client]:
    if settings.SUPABASE_URL and settings.SUPABASE_KEY and "your-project" not in settings.SUPABASE_URL:
        try:
            return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        except Exception as e:
            logger.warning(f"Failed to connect to Supabase: {e}. Falling back to in-memory mode.")
            return None
    return None
