import io
import uuid
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.supabase_client import _in_memory_db
from app.main import app
from app.services.rag_service import RAGService

client = TestClient(app)

USER_1 = {
    "id": "11111111-2222-3333-4444-555555555555",
    "email": "user1@docmind.ai",
    "user_metadata": {"full_name": "Test User One"},
    "token": "bearer_token_user_1"
}

USER_2 = {
    "id": "99999999-8888-7777-6666-555555555555",
    "email": "user2@docmind.ai",
    "user_metadata": {"full_name": "Test User Two"},
    "token": "bearer_token_user_2"
}

VALID_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
    b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    b"4 0 obj << /Length 100 >> stream\n"
    b"BT\n"
    b"/F1 12 Tf\n"
    b"100 700 Td\n"
    b"(DocMind Persistence Verification Document) Tj\n"
    b"ET\n"
    b"endstream\n"
    b"endobj\n"
    b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    b"xref\n"
    b"0 6\n"
    b"0000000000 65535 f \n"
    b"0000000010 00000 n \n"
    b"0000000060 00000 n \n"
    b"00000000117 00000 n \n"
    b"00000000250 00000 n \n"
    b"00000000400 00000 n \n"
    b"trailer << /Size 6 /Root 1 0 R >>\n"
    b"startxref\n"
    b"470\n"
    b"%%EOF\n"
)

@pytest.fixture(autouse=True)
def reset_db_state():
    _in_memory_db.workspaces.clear()
    _in_memory_db.documents.clear()
    _in_memory_db.document_chunks.clear()
    _in_memory_db.chat_sessions.clear()
    _in_memory_db.messages.clear()
    _in_memory_db.pdf_bytes.clear()
    yield

def get_auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

def create_mock_supabase(user_dict):
    class MockUser:
        id = user_dict["id"]
        email = user_dict["email"]
        user_metadata = user_dict["user_metadata"]

    class MockUserResponse:
        user = MockUser()

    class MockAuth:
        def get_user(self, token):
            return MockUserResponse()

    class MockSupabase:
        auth = MockAuth()

    return MockSupabase()

def test_workspace_creation_and_scoping():
    """Test workspace creation and listing scoping in Supabase context."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=create_mock_supabase(USER_1)), \
         patch("app.api.workspaces.get_supabase_client") as mock_get_client:

        mock_db_client = MagicMock()
        mock_get_client.return_value = mock_db_client

        # Mock workspaces table select & insert
        ws_id = str(uuid.uuid4())
        mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_db_client.table.return_value.insert.return_value.execute.return_value.data = [{
            "id": ws_id,
            "user_id": USER_1["id"],
            "name": "My Workspace",
            "created_at": "2026-08-24T20:00:00Z"
        }]

        res = client.get("/api/v1/workspaces", headers=get_auth_headers(USER_1["token"]))
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Workspace"
        assert data[0]["user_id"] == USER_1["id"]

def test_explicit_storage_file_deletion_on_document_delete():
    """Test explicit physical PDF deletion from Supabase Storage when document is deleted."""
    doc_id = str(uuid.uuid4())
    ws_id = str(uuid.uuid4())
    storage_path = f"workspaces/{ws_id}/{doc_id}.pdf"

    mock_db_client = MagicMock()
    mock_db_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
        "id": ws_id,
        "user_id": USER_1["id"],
        "name": "User 1 WS"
    }]

    # Return document record on query
    def mock_table(name):
        t_mock = MagicMock()
        if name == "documents":
            t_mock.select.return_value.eq.return_value.execute.return_value.data = [{
                "id": doc_id,
                "workspace_id": ws_id,
                "filename": "TestDoc.pdf",
                "storage_path": storage_path
            }]
            t_mock.delete.return_value.eq.return_value.execute.return_value.data = None
        elif name == "workspaces":
            t_mock.select.return_value.eq.return_value.execute.return_value.data = [{
                "id": ws_id,
                "user_id": USER_1["id"],
                "name": "User 1 WS"
            }]
        return t_mock

    mock_db_client.table.side_effect = mock_table

    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=create_mock_supabase(USER_1)), \
         patch("app.api.documents.get_supabase_client", return_value=mock_db_client):

        del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=get_auth_headers(USER_1["token"]))
        assert del_res.status_code == 204

        # Verify physical file removal was explicitly called on Supabase Storage
        mock_db_client.storage.from_.assert_called_with("documents")
        mock_db_client.storage.from_("documents").remove.assert_called_with([storage_path])

def test_explicit_storage_file_deletion_on_workspace_delete():
    """Test explicit physical PDF file cleanup for all documents in workspace when deleting workspace."""
    ws_id = str(uuid.uuid4())
    doc_1_path = f"workspaces/{ws_id}/doc1.pdf"
    doc_2_path = f"workspaces/{ws_id}/doc2.pdf"

    mock_db_client = MagicMock()

    def mock_table(name):
        t_mock = MagicMock()
        if name == "workspaces":
            t_mock.select.return_value.eq.return_value.execute.return_value.data = [{
                "id": ws_id,
                "user_id": USER_1["id"],
                "name": "Workspace To Delete"
            }]
            t_mock.delete.return_value.eq.return_value.execute.return_value.data = None
        elif name == "documents":
            t_mock.select.return_value.eq.return_value.execute.return_value.data = [
                {"storage_path": doc_1_path},
                {"storage_path": doc_2_path}
            ]
        return t_mock

    mock_db_client.table.side_effect = mock_table

    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=create_mock_supabase(USER_1)), \
         patch("app.api.workspaces.get_supabase_client", return_value=mock_db_client):

        del_res = client.delete(f"/api/v1/workspaces/{ws_id}", headers=get_auth_headers(USER_1["token"]))
        assert del_res.status_code == 204

        # Verify both storage paths were explicitly deleted from Supabase Storage
        mock_db_client.storage.from_("documents").remove.assert_called_with([doc_1_path, doc_2_path])

def test_chat_history_persistence_and_scoping():
    """Test chat sessions and chat messages persistence in Supabase."""
    ws_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    mock_db_client = MagicMock()

    def mock_table(name):
        t_mock = MagicMock()
        if name == "workspaces":
            t_mock.select.return_value.eq.return_value.execute.return_value.data = [{
                "id": ws_id,
                "user_id": USER_1["id"],
                "name": "Chat WS"
            }]
        elif name == "chat_sessions":
            t_mock.select.return_value.eq.return_value.execute.return_value.data = [{
                "id": session_id,
                "workspace_id": ws_id,
                "title": "Persistent Chat"
            }]
        elif name == "messages":
            t_mock.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
                {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "role": "user",
                    "content": "What is in the document?",
                    "created_at": "2026-08-24T20:00:00Z"
                },
                {
                    "id": str(uuid.uuid4()),
                    "session_id": session_id,
                    "role": "assistant",
                    "content": "Here is the grounded answer.",
                    "created_at": "2026-08-24T20:01:00Z"
                }
            ]
        return t_mock

    mock_db_client.table.side_effect = mock_table

    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=create_mock_supabase(USER_1)), \
         patch("app.api.chat.get_supabase_client", return_value=mock_db_client):

        res = client.get(f"/api/v1/chat/{session_id}/messages", headers=get_auth_headers(USER_1["token"]))
        assert res.status_code == 200
        msgs = res.json()
        assert len(msgs) == 2
        assert msgs[0]["content"] == "What is in the document?"
        assert msgs[1]["content"] == "Here is the grounded answer."
