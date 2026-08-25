from fastapi import APIRouter, HTTPException, status
from typing import List
import uuid

from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from app.db.supabase_client import get_supabase_client, _in_memory_db

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(user_id: str = "demo-student-user"):
    client = get_supabase_client()
    if client:
        try:
            res = client.table("workspaces").select("*").eq("user_id", user_id).execute()
            return res.data
        except Exception:
            pass
    
    # In-memory fallback
    return list(_in_memory_db.workspaces.values())

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceCreate):
    ws_id = str(uuid.uuid4())
    ws_record = {
        "id": ws_id,
        "user_id": payload.user_id or "demo-student-user",
        "name": payload.name,
        "created_at": "2026-08-24T20:00:00Z"
    }

    client = get_supabase_client()
    if client:
        try:
            res = client.table("workspaces").insert(ws_record).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database insert error: {e}")

    _in_memory_db.workspaces[ws_id] = ws_record
    return ws_record

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace_id: str):
    if workspace_id in _in_memory_db.workspaces:
        return _in_memory_db.workspaces[workspace_id]
    
    client = get_supabase_client()
    if client:
        res = client.table("workspaces").select("*").eq("id", workspace_id).execute()
        if res.data:
            return res.data[0]

    raise HTTPException(status_code=404, detail="Workspace not found")

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: str):
    if workspace_id in _in_memory_db.workspaces:
        del _in_memory_db.workspaces[workspace_id]

    client = get_supabase_client()
    if client:
        client.table("workspaces").delete().eq("id", workspace_id).execute()
    return None
