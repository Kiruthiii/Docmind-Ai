import io
import uuid
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.supabase_client import _in_memory_db
from app.main import app
from app.services.rag_service import RAGService

client = TestClient(app)

# Helper mock users for testing
USER_A = {
    "id": "11111111-1111-1111-1111-111111111111",
    "email": "usera@docmind.ai",
    "user_metadata": {"full_name": "User A"}
}

USER_B = {
    "id": "22222222-2222-2222-2222-222222222222",
    "email": "userb@docmind.ai",
    "user_metadata": {"full_name": "User B"}
}

VALID_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
    b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    b"4 0 obj << /Length 120 >> stream\n"
    b"BT\n"
    b"/F1 12 Tf\n"
    b"100 700 Td\n"
    b"(User A Secret Document Content) Tj\n"
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
    b"00000000420 00000 n \n"
    b"trailer << /Size 6 /Root 1 0 R >>\n"
    b"startxref\n"
    b"490\n"
    b"%%EOF\n"
)

@pytest.fixture(autouse=True)
def reset_in_memory_db():
    _in_memory_db.workspaces.clear()
    _in_memory_db.documents.clear()
    _in_memory_db.document_chunks.clear()
    _in_memory_db.chat_sessions.clear()
    _in_memory_db.messages.clear()
    _in_memory_db.pdf_bytes.clear()
    yield

def get_auth_headers(token_str: str) -> dict:
    return {"Authorization": f"Bearer {token_str}"}

def mock_supabase_for_user(user_dict):
    class MockUser:
        id = user_dict["id"]
        email = user_dict["email"]
        user_metadata = user_dict["user_metadata"]

    class MockUserResponse:
        user = MockUser()

    class MockAuth:
        def get_user(self, token):
            return MockUserResponse()

    class MockSupabaseClient:
        auth = MockAuth()

    return MockSupabaseClient()


def test_1_workspace_provisioning():
    """Test 1: New user gets auto-created 'My Workspace'. Subsequent calls are idempotent."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_A)):
        
        # 1. First list workspaces for User A
        res1 = client.get("/api/v1/workspaces", headers=get_auth_headers("token_user_a"))
        assert res1.status_code == 200
        data1 = res1.json()
        assert len(data1) == 1
        assert data1[0]["name"] == "My Workspace"
        assert data1[0]["user_id"] == USER_A["id"]
        ws_id = data1[0]["id"]

        # 2. Call again: verify idempotency (no duplicate workspace created)
        res2 = client.get("/api/v1/workspaces", headers=get_auth_headers("token_user_a"))
        assert res2.status_code == 200
        data2 = res2.json()
        assert len(data2) == 1
        assert data2[0]["id"] == ws_id


def test_2_document_isolation():
    """Test 2: User A's uploaded document is isolated from User B."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False):
        # Setup User A workspace
        with patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_A)):
            ws_a_res = client.get("/api/v1/workspaces", headers=get_auth_headers("token_user_a"))
            ws_a_id = ws_a_res.json()[0]["id"]

            # User A uploads a valid PDF
            files = {"file": ("UserA_Secret.pdf", io.BytesIO(VALID_PDF_BYTES), "application/pdf")}
            up_res = client.post(
                f"/api/v1/workspaces/{ws_a_id}/documents",
                files=files,
                headers=get_auth_headers("token_user_a")
            )
            assert up_res.status_code == 201

        # User B attempts to list User A's workspace documents -> 403 Forbidden
        with patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_B)):
            res_b_access_a = client.get(
                f"/api/v1/workspaces/{ws_a_id}/documents",
                headers=get_auth_headers("token_user_b")
            )
            assert res_b_access_a.status_code == 403

            # User B lists their own workspace documents -> 0 documents
            ws_b_res = client.get("/api/v1/workspaces", headers=get_auth_headers("token_user_b"))
            ws_b_id = ws_b_res.json()[0]["id"]
            docs_b = client.get(
                f"/api/v1/workspaces/{ws_b_id}/documents",
                headers=get_auth_headers("token_user_b")
            )
            assert docs_b.status_code == 200
            assert len(docs_b.json()) == 0


def test_3_direct_document_access():
    """Test 3: User B direct file download of User A's document returns 403 Forbidden."""
    doc_id = str(uuid.uuid4())
    ws_a_id = str(uuid.uuid4())

    _in_memory_db.workspaces[ws_a_id] = {
        "id": ws_a_id,
        "user_id": USER_A["id"],
        "name": "User A Private Workspace",
        "created_at": "2026-08-24T20:00:00Z"
    }
    _in_memory_db.documents[doc_id] = {
        "id": doc_id,
        "workspace_id": ws_a_id,
        "filename": "Confidential.pdf"
    }
    _in_memory_db.pdf_bytes[doc_id] = b"%PDF-1.4 Secret Data"

    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_B)):
        res = client.get(f"/api/v1/documents/{doc_id}/file", headers=get_auth_headers("token_user_b"))
        assert res.status_code == 403
        assert "Not authorized" in res.json()["detail"]


def test_4_document_deletion():
    """Test 4: User B attempting to delete User A's document returns 403 Forbidden."""
    doc_id = str(uuid.uuid4())
    ws_a_id = str(uuid.uuid4())

    _in_memory_db.workspaces[ws_a_id] = {
        "id": ws_a_id,
        "user_id": USER_A["id"],
        "name": "User A Workspace",
        "created_at": "2026-08-24T20:00:00Z"
    }
    _in_memory_db.documents[doc_id] = {
        "id": doc_id,
        "workspace_id": ws_a_id,
        "filename": "Important.pdf"
    }

    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_B)):
        res = client.delete(f"/api/v1/documents/{doc_id}", headers=get_auth_headers("token_user_b"))
        assert res.status_code == 403
        # Ensure document was NOT deleted
        assert doc_id in _in_memory_db.documents


def test_5_chat_isolation():
    """Test 5: User B attempting to send message or fetch chat history for User A's session/workspace returns 403."""
    ws_a_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    _in_memory_db.workspaces[ws_a_id] = {
        "id": ws_a_id,
        "user_id": USER_A["id"],
        "name": "User A Workspace",
        "created_at": "2026-08-24T20:00:00Z"
    }
    _in_memory_db.chat_sessions[session_id] = {
        "id": session_id,
        "workspace_id": ws_a_id,
        "title": "User A Chat"
    }

    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_B)):
        
        # User B sends message to Workspace A -> 403
        msg_res = client.post(
            "/api/v1/chat/message",
            json={"workspace_id": ws_a_id, "question": "What are your secrets?"},
            headers=get_auth_headers("token_user_b")
        )
        assert msg_res.status_code == 403

        # User B fetches history for Session A -> 403
        hist_res = client.get(f"/api/v1/chat/{session_id}/messages", headers=get_auth_headers("token_user_b"))
        assert hist_res.status_code == 403


def test_6_chat_persistence():
    """Test 6: Chat messages created by User A persist and can be reloaded."""
    ws_a_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    _in_memory_db.workspaces[ws_a_id] = {
        "id": ws_a_id,
        "user_id": USER_A["id"],
        "name": "User A Workspace",
        "created_at": "2026-08-24T20:00:00Z"
    }
    _in_memory_db.chat_sessions[session_id] = {
        "id": session_id,
        "workspace_id": ws_a_id,
        "title": "Persistent Chat"
    }
    _in_memory_db.messages.append({
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "role": "user",
        "content": "Hello DocMind!"
    })

    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False), \
         patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_A)):
        res = client.get(f"/api/v1/chat/{session_id}/messages", headers=get_auth_headers("token_user_a"))
        assert res.status_code == 200
        msgs = res.json()
        assert len(msgs) == 1
        assert msgs[0]["content"] == "Hello DocMind!"


def test_7_user_isolation_after_relogin():
    """Test 7: User A data is preserved on relogin and completely invisible to User B."""
    ws_a_id = str(uuid.uuid4())
    doc_a_id = str(uuid.uuid4())

    _in_memory_db.workspaces[ws_a_id] = {
        "id": ws_a_id,
        "user_id": USER_A["id"],
        "name": "User A Workspace",
        "created_at": "2026-08-24T20:00:00Z"
    }
    _in_memory_db.documents[doc_a_id] = {
        "id": doc_a_id,
        "workspace_id": ws_a_id,
        "filename": "UserA_Data.pdf",
        "storage_path": "workspaces/usera/UserA_Data.pdf",
        "status": "ready",
        "page_count": 1,
        "created_at": "2026-08-24T20:00:00Z"
    }

    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False):
        # 1. User B logs in -> sees only B's workspace and 0 documents from User A
        with patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_B)):
            b_ws = client.get("/api/v1/workspaces", headers=get_auth_headers("token_user_b")).json()
            assert len(b_ws) == 1
            assert b_ws[0]["user_id"] == USER_B["id"]
            
            b_docs = client.get(f"/api/v1/workspaces/{b_ws[0]['id']}/documents", headers=get_auth_headers("token_user_b")).json()
            assert len(b_docs) == 0

        # 2. User A relogs in -> sees User A's workspace and document intact
        with patch("app.api.deps.get_supabase_client", return_value=mock_supabase_for_user(USER_A)):
            a_ws = client.get("/api/v1/workspaces", headers=get_auth_headers("token_user_a")).json()
            assert any(w["id"] == ws_a_id for w in a_ws)

            a_docs = client.get(f"/api/v1/workspaces/{ws_a_id}/documents", headers=get_auth_headers("token_user_a")).json()
            assert len(a_docs) == 1
            assert a_docs[0]["filename"] == "UserA_Data.pdf"


def test_8_rag_vector_search_isolation():
    """Test 8: Critical RAG isolation — User B query in Workspace B cannot retrieve User A's document chunks."""
    ws_a_id = str(uuid.uuid4())
    ws_b_id = str(uuid.uuid4())
    doc_a_id = str(uuid.uuid4())

    rag = RAGService()

    # User A chunk containing secret information
    _in_memory_db.document_chunks.append({
        "id": str(uuid.uuid4()),
        "document_id": doc_a_id,
        "workspace_id": ws_a_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Secret Project Alpha Strategy: Launch date is set for Q4 2026.",
        "section_path": "Executive Summary",
        "parent_section": "Executive Summary",
        "embedding": rag.llm.get_embedding("Secret Project Alpha Strategy Launch date Q4 2026")
    })

    # User B queries RAG in Workspace B for "Project Alpha Strategy"
    res_b = rag.query_workspace(
        workspace_id=ws_b_id,
        question="What is the launch date for Secret Project Alpha Strategy?"
    )

    # RAG candidate search in Workspace B must NOT retrieve User A's chunks
    assert "Q4 2026" not in res_b.answer
    assert len(res_b.citations) == 0
