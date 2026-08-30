import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_missing_auth_header_returns_401():
    """Verify production behavior: Missing auth header strictly returns 401 Unauthorized."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False):
        res = client.get("/api/v1/workspaces")
        assert res.status_code == 401
        assert "Could not validate authentication credentials" in res.json()["detail"]

def test_malformed_auth_header_returns_401():
    """Verify production behavior: Non-Bearer auth header strictly returns 401 Unauthorized."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False):
        res = client.get("/api/v1/workspaces", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert res.status_code == 401

def test_invalid_bearer_token_returns_401():
    """Verify production behavior: Fake/Invalid Bearer token strictly returns 401 Unauthorized."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", False):
        res = client.get("/api/v1/workspaces", headers={"Authorization": "Bearer invalid_fake_token_12345"})
        assert res.status_code == 401

def test_dev_fallback_explicitly_enabled():
    """Verify development behavior: Fallback demo user permitted ONLY when AUTH_ALLOW_DEV_FALLBACK is True."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", True):
        res = client.get("/api/v1/workspaces")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

def test_workspace_creation_assigns_authenticated_user_id():
    """Verify workspace creation sets user_id to the verified authenticated identity."""
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", True):
        res = client.post("/api/v1/workspaces", json={"name": "Auth Security Test Workspace"})
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Auth Security Test Workspace"
        assert "user_id" in data
        assert data["user_id"] == "00000000-0000-0000-0000-000000000001"

def test_user_a_cannot_access_user_b_workspace():
    """Verify authorization: User A receiving 403 Forbidden when accessing User B's workspace."""
    from app.db.supabase_client import _in_memory_db
    
    user_b_ws_id = "ws-user-b-secret-uuid"
    _in_memory_db.workspaces[user_b_ws_id] = {
        "id": user_b_ws_id,
        "user_id": "11111111-1111-1111-1111-111111111111", # User B
        "name": "User B Secret Research",
        "created_at": "2026-08-29T00:00:00Z"
    }

    # Accessing as User A (or dev fallback user)
    with patch.object(settings, "AUTH_ALLOW_DEV_FALLBACK", True):
        res = client.get(f"/api/v1/workspaces/{user_b_ws_id}")
        assert res.status_code == 403
        assert "Not authorized to access this workspace" in res.json()["detail"]

def test_demo_fallback_disabled_by_default():
    """Verify production default: AUTH_ALLOW_DEV_FALLBACK is False by default."""
    assert settings.AUTH_ALLOW_DEV_FALLBACK is False
    res = client.get("/api/v1/workspaces")
    assert res.status_code == 401

def test_authenticated_supabase_user_allowed():
    """Verify authenticated user with valid token is permitted and assigned correct user_id."""
    class MockUser:
        id = "user-a-123"
        email = "usera@docmind.ai"
        user_metadata = {"full_name": "User A"}

    class MockUserResponse:
        user = MockUser()

    class MockAuth:
        def get_user(self, token):
            if token == "valid_token_user_a":
                return MockUserResponse()
            raise Exception("Invalid token")

    class MockSupabaseClient:
        auth = MockAuth()

    with patch("app.api.deps.get_supabase_client", return_value=MockSupabaseClient()):
        # 1. Access workspace list with valid Bearer token
        res = client.get("/api/v1/workspaces", headers={"Authorization": "Bearer valid_token_user_a"})
        assert res.status_code == 200

        # 2. Create workspace with valid Bearer token
        create_res = client.post(
            "/api/v1/workspaces",
            json={"name": "User A Private Workspace"},
            headers={"Authorization": "Bearer valid_token_user_a"}
        )
        assert create_res.status_code == 201
        assert create_res.json()["user_id"] == "user-a-123"

def test_user_a_cannot_access_or_delete_user_b_workspace():
    """Verify strict user isolation: User A receives 403 when attempting to GET or DELETE User B's workspace."""
    from app.db.supabase_client import _in_memory_db
    
    user_b_ws_id = "ws-user-b-strictly-private"
    _in_memory_db.workspaces[user_b_ws_id] = {
        "id": user_b_ws_id,
        "user_id": "user-b-456",
        "name": "User B Confidential Notes",
        "created_at": "2026-08-29T00:00:00Z"
    }

    class MockUserA:
        id = "user-a-123"
        email = "usera@docmind.ai"
        user_metadata = {}

    class MockUserAResponse:
        user = MockUserA()

    class MockAuth:
        def get_user(self, token):
            if token == "token_user_a":
                return MockUserAResponse()
            raise Exception("Invalid token")

    class MockSupabaseClient:
        auth = MockAuth()

    headers = {"Authorization": "Bearer token_user_a"}
    with patch("app.api.deps.get_supabase_client", return_value=MockSupabaseClient()):
        # Try GET
        get_res = client.get(f"/api/v1/workspaces/{user_b_ws_id}", headers=headers)
        assert get_res.status_code == 403
        assert "Not authorized to access this workspace" in get_res.json()["detail"]

        # Try DELETE
        del_res = client.delete(f"/api/v1/workspaces/{user_b_ws_id}", headers=headers)
        assert del_res.status_code == 403
        assert "Not authorized to delete this workspace" in del_res.json()["detail"]

def test_user_a_cannot_see_user_b_workspace_in_list():
    """Verify listing workspaces only returns workspaces owned by the authenticated user."""
    from app.db.supabase_client import _in_memory_db
    
    user_b_ws_id = "ws-user-b-hidden-from-list"
    _in_memory_db.workspaces[user_b_ws_id] = {
        "id": user_b_ws_id,
        "user_id": "user-b-456",
        "name": "User B Hidden Workspace",
        "created_at": "2026-08-29T00:00:00Z"
    }

    class MockUserA:
        id = "user-a-123"

    class MockUserAResponse:
        user = MockUserA()

    class MockAuth:
        def get_user(self, token):
            if token == "token_user_a":
                return MockUserAResponse()
            raise Exception("Invalid token")

    class MockSupabaseClient:
        auth = MockAuth()

    headers = {"Authorization": "Bearer token_user_a"}
    with patch("app.api.deps.get_supabase_client", return_value=MockSupabaseClient()):
        res = client.get("/api/v1/workspaces", headers=headers)
        assert res.status_code == 200
        ws_ids = [w["id"] for w in res.json()]
        assert user_b_ws_id not in ws_ids

