from unittest.mock import patch
import uuid
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.supabase_client import _in_memory_db
from app.main import app

client = TestClient(app)

def test_chat_message_scoped_to_selected_document():
    """Verify that chat responses and citations are strictly filtered to the user-selected document_id."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", True):
        # 1. Create a workspace
        ws_res = client.post("/api/v1/workspaces", json={"name": "Scoped Doc Test WS"})
        assert ws_res.status_code == 201
        ws_id = ws_res.json()["id"]

        doc_a_id = str(uuid.uuid4())
        doc_b_id = str(uuid.uuid4())

        # Setup Document A
        _in_memory_db.documents[doc_a_id] = {
            "id": doc_a_id,
            "workspace_id": ws_id,
            "filename": "Quantum_Physics.pdf",
            "page_count": 5,
            "status": "ready"
        }
        # Setup Document B
        _in_memory_db.documents[doc_b_id] = {
            "id": doc_b_id,
            "workspace_id": ws_id,
            "filename": "Gourmet_Recipes.pdf",
            "page_count": 3,
            "status": "ready"
        }

        # Setup Chunks for Document A
        _in_memory_db.document_chunks.append({
            "id": str(uuid.uuid4()),
            "document_id": doc_a_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "content": "Quantum physics uses qubits to process information in superposition state.",
            "chunk_type": "text",
            "document_position": "introduction",
            "section_path": "Introduction > Overview"
        })

        # Setup Chunks for Document B
        _in_memory_db.document_chunks.append({
            "id": str(uuid.uuid4()),
            "document_id": doc_b_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "content": "Quantum chocolate baking requires preheating oven to 350 degrees Fahrenheit.",
            "chunk_type": "text",
            "document_position": "introduction",
            "section_path": "Baking > Quantum Chocolate"
        })

        # Query specifying Document A ID
        res_a = client.post("/api/v1/chat/message", json={
            "workspace_id": ws_id,
            "document_id": doc_a_id,
            "question": "What does quantum physics use to process information?"
        })
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert data_a["is_grounded"] is True
        for citation in data_a["citations"]:
            assert citation["document_id"] == doc_a_id
            assert citation["document_name"] == "Quantum_Physics.pdf"

        # Query specifying Document B ID
        res_b = client.post("/api/v1/chat/message", json={
            "workspace_id": ws_id,
            "document_id": doc_b_id,
            "question": "What oven temperature is required for baking quantum chocolate?"
        })
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["is_grounded"] is True
        for citation in data_b["citations"]:
            assert citation["document_id"] == doc_b_id
            assert citation["document_name"] == "Gourmet_Recipes.pdf"
