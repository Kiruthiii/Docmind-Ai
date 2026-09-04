import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
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
        if v.get("user_id") == user_id:
            all_items[k] = v
    return list(all_items.values())

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    ws_id = str(uuid.uuid4())
    ws_record = {
        "id": ws_id,
        "user_id": user_id,
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
def get_workspace(workspace_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    ws_item = None

    if workspace_id in _in_memory_db.workspaces:
        ws_item = _in_memory_db.workspaces[workspace_id]
    else:
        client = get_supabase_client()
        if client:
            res = client.table("workspaces").select("*").eq("id", workspace_id).execute()
            if res.data:
                ws_item = res.data[0]

    if not ws_item:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Authorize workspace ownership
    if ws_item.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this workspace")

    return ws_item

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    ws_item = None

    if workspace_id in _in_memory_db.workspaces:
        ws_item = _in_memory_db.workspaces[workspace_id]
    else:
        client = get_supabase_client()
        if client:
            res = client.table("workspaces").select("*").eq("id", workspace_id).execute()
            if res.data:
                ws_item = res.data[0]

    if not ws_item:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if ws_item.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this workspace")

    if workspace_id in _in_memory_db.workspaces:
        del _in_memory_db.workspaces[workspace_id]

    client = get_supabase_client()
    if client:
        client.table("workspaces").delete().eq("id", workspace_id).execute()
    return None
