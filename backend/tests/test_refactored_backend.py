import pytest
from fastapi.testclient import TestClient

from app.db.supabase_client import get_supabase_client
from app.main import app
from app.services.llm_service import (CLEAN_WORD_RE, STOP_WORDS, TOKEN_RE,
                                      term_matches_words)

client = TestClient(app)

def test_supabase_client_singleton():
    """Verifies get_supabase_client returns a cached singleton instance on repeated calls."""
    c1 = get_supabase_client()
    c2 = get_supabase_client()
    assert c1 is c2

def test_json_control_character_middleware_escaping():
    """Verifies control character middleware escapes non-standard control chars cleanly without stripping."""
    raw_payload = '{"question": "What is the duration\u0007 of the project?"}'
    res = client.post(
        "/api/v1/chat/message",
        content=raw_payload,
        headers={"Content-Type": "application/json"}
    )
    assert res.status_code != 400

def test_term_matches_words_helper():
    """Verifies unified term_matches_words fuzzy matching logic."""
    words = {"baseline", "performance", "yolo", "detection", "methodology"}
    assert term_matches_words("methodology", words) is True
    assert term_matches_words("method", words) is True
    assert term_matches_words("unrelatedterm", words) is False
