from unittest.mock import patch
import uuid
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.supabase_client import _in_memory_db
from app.main import app

client = TestClient(app)

def test_summary_and_whats_in_this_queries():
    """Verify that high-level queries like 'summarize', 'tell whats in this', and 'overview' trigger document overview intent and return grounded answers."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", True):
        # 1. Create workspace
        ws_res = client.post("/api/v1/workspaces", json={"name": "Summary Query Test WS"})
        assert ws_res.status_code == 201
        ws_id = ws_res.json()["id"]

        doc_id = str(uuid.uuid4())
        _in_memory_db.documents[doc_id] = {
            "id": doc_id,
            "workspace_id": ws_id,
            "filename": "Autonomous_Navigation.pdf",
            "page_count": 4,
            "status": "ready"
        }

        _in_memory_db.document_chunks.append({
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "content": "Autonomous navigation system uses LiDAR sensors and vision transformers for obstacle detection.",
            "chunk_type": "text",
            "document_position": "introduction",
            "section_path": "Introduction"
        })

        test_questions = [
            "summarize",
            "summarize this",
            "tell whats in this",
            "whats in this document",
            "overview of this file",
            "what is this document about"
        ]

        for q in test_questions:
            res = client.post("/api/v1/chat/message", json={
                "workspace_id": ws_id,
                "document_id": doc_id,
                "question": q
            })
            assert res.status_code == 200
            data = res.json()
            assert data["is_grounded"] is True, f"Failed grounding for query: {q}"
            assert len(data["citations"]) > 0, f"Missing citations for query: {q}"
            assert "Autonomous" in data["answer"] or "Summary" in data["answer"] or "describes" in data["answer"] or "LiDAR" in data["answer"] or "navigation" in data["answer"], f"Unexpected answer for query '{q}': {data['answer']}"
