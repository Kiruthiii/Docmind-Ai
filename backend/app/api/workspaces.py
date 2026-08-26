from fastapi import APIRouter, HTTPException, status
from typing import List
import uuid

from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from app.db.supabase_client import get_supabase_client, _in_memory_db

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(user_id: str = "00000000-0000-0000-0000-000000000001"):
    db_items = []
    client = get_supabase_client()
    if client:
        try:
            res = client.table("workspaces").select("*").eq("user_id", user_id).execute()
            if res.data:
                db_items = res.data
        except Exception:
            pass
    
    all_items = {w["id"]: w for w in db_items}
    for k, v in _in_memory_db.workspaces.items():
        all_items[k] = v
    return list(all_items.values())

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceCreate):
    ws_id = str(uuid.uuid4())
    ws_record = {
        "id": ws_id,
        "user_id": payload.user_id or "00000000-0000-0000-0000-000000000001",
        "name": payload.name,
        "created_at": "2026-08-24T20:00:00Z"
    }

    client = get_supabase_client()
    if client:
        try:
            res = client.table("workspaces").insert(ws_record).execute()
            if res.data:
                _in_memory_db.workspaces[ws_id] = res.data[0]
                return res.data[0]
        except Exception:
            pass

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
