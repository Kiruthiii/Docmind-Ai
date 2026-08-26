from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_workspace_crud():
    # 1. Create workspace
    create_res = client.post("/api/v1/workspaces", json={"name": "Test Science Workspace"})
    assert create_res.status_code == 201
    ws = create_res.json()
    ws_id = ws["id"]
    assert ws["name"] == "Test Science Workspace"

    # 2. Get workspace list
    list_res = client.get("/api/v1/workspaces")
    assert list_res.status_code == 200
    assert any(w["id"] == ws_id for w in list_res.json())

    # 3. Delete workspace
    del_res = client.delete(f"/api/v1/workspaces/{ws_id}")
    assert del_res.status_code == 204

def test_chat_message_endpoint():
    # Create workspace
    ws = client.post("/api/v1/workspaces", json={"name": "Chat Test WS"}).json()
    ws_id = ws["id"]

    # Send unanswerable question
    chat_res = client.post("/api/v1/chat/message", json={
        "workspace_id": ws_id,
        "question": "What is the capital of France?"
    })
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "I couldn't find sufficient evidence" in data["answer"]
    assert data["is_grounded"] is False

def test_json_control_character_handling():
    ws = client.post("/api/v1/workspaces", json={"name": "Control Char WS"}).json()
    ws_id = ws["id"]

    # Raw JSON payload with raw unescaped control character (newline in string)
    raw_payload = f'{{\n  "workspace_id": "{ws_id}",\n  "question": "tell about\\nwork experience?"\n}}'
    response = client.post(
        "/api/v1/chat/message",
        content=raw_payload.encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
