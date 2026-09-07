from unittest.mock import patch
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.supabase_client import _in_memory_db
from app.main import app

client = TestClient(app)

DEV_USER_ID = "00000000-0000-0000-0000-000000000001"

def test_chat_compare_endpoint():
    _in_memory_db.workspaces["test-ws-123"] = {
        "id": "test-ws-123",
        "user_id": DEV_USER_ID,
        "name": "Test Workspace 123",
        "created_at": "2026-08-24T20:00:00Z"
    }

    payload = {
        "workspace_id": "test-ws-123",
        "document_ids": ["doc-1", "doc-2"],
        "categories": ["Summary", "Methodology", "Results"]
    }
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", True):
        response = client.post("/api/v1/chat/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "workspace_id" in data
        assert "markdown_matrix" in data
        assert "potential_contradictions" in data
        assert "citations" in data
        assert data["workspace_id"] == "test-ws-123"

def test_chat_compare_endpoint_all_docs():
    _in_memory_db.workspaces["test-ws-456"] = {
        "id": "test-ws-456",
        "user_id": DEV_USER_ID,
        "name": "Test Workspace 456",
        "created_at": "2026-08-24T20:00:00Z"
    }

    payload = {
        "workspace_id": "test-ws-456",
        "document_ids": None,
        "categories": ["Summary", "Limitations"]
    }
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", True):
        response = client.post("/api/v1/chat/compare", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["workspace_id"] == "test-ws-456"
