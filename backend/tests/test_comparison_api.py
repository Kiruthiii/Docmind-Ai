from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_chat_compare_endpoint():
    payload = {
        "workspace_id": "test-ws-123",
        "document_ids": ["doc-1", "doc-2"],
        "categories": ["Summary", "Methodology", "Results"]
    }
    response = client.post("/api/v1/chat/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "workspace_id" in data
    assert "markdown_matrix" in data
    assert "potential_contradictions" in data
    assert "citations" in data
    assert data["workspace_id"] == "test-ws-123"

def test_chat_compare_endpoint_all_docs():
    payload = {
        "workspace_id": "test-ws-456",
        "document_ids": None,
        "categories": ["Summary", "Limitations"]
    }
    response = client.post("/api/v1/chat/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == "test-ws-456"
