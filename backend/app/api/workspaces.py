import logging
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse

logger = logging.getLogger("docmind")
router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    token = current_user.get("token")
    is_dev_user = (user_id == "00000000-0000-0000-0000-000000000001")
    client = get_supabase_client(token) if (token and not is_dev_user) else None
    
    db_items: List[Dict[str, Any]] = []
    if client:
        try:
            res = client.table("workspaces").select("*").eq("user_id", user_id).execute()
            if res.data is not None:
                db_items = res.data
        except Exception as e:
            logger.warning(f"Error listing workspaces from Supabase, falling back to in-memory: {e}")
            client = None
            db_items = [v for v in _in_memory_db.workspaces.values() if v.get("user_id") == user_id]
    else:
        # Development / test fallback mode if token is missing or dev user
        db_items = [v for v in _in_memory_db.workspaces.values() if v.get("user_id") == user_id]

    # Auto-provision default "My Workspace" for new users if 0 workspaces exist
    if not db_items:
        ws_id = str(uuid.uuid4())
        default_ws = {
            "id": ws_id,
            "user_id": user_id,
            "name": "My Workspace",
            "created_at": "2026-08-24T20:00:00Z"
        }
        if client:
            try:
                res = client.table("workspaces").insert(default_ws).execute()
                if res.data:
                    default_ws = res.data[0]
            except Exception as e:
                logger.warning(f"Error creating default workspace in Supabase: {e}. Falling back to in-memory DB.")
                _in_memory_db.workspaces[ws_id] = default_ws
        else:
            _in_memory_db.workspaces[ws_id] = default_ws

        db_items = [default_ws]

    return db_items

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    token = current_user.get("token")
    is_dev_user = (user_id == "00000000-0000-0000-0000-000000000001")
    ws_id = str(uuid.uuid4())
    ws_record = {
        "id": ws_id,
        "user_id": user_id,
        "name": payload.name,
        "created_at": "2026-08-24T20:00:00Z"
    }

    client = get_supabase_client(token) if (token and not is_dev_user) else None
    if client:
        try:
            res = client.table("workspaces").insert(ws_record).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.warning(f"Error creating workspace in Supabase: {e}. Falling back to in-memory DB.")

    _in_memory_db.workspaces[ws_id] = ws_record
    return ws_record

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    token = current_user.get("token")
    is_dev_user = (user_id == "00000000-0000-0000-0000-000000000001")
    client = get_supabase_client(token) if (token and not is_dev_user) else None

    ws_item = None
    if client:
        try:
            res = client.table("workspaces").select("*").eq("id", workspace_id).execute()
            if res.data:
                ws_item = res.data[0]
            else:
                ws_item = _in_memory_db.workspaces.get(workspace_id)
        except Exception as e:
            logger.warning(f"Error fetching workspace {workspace_id} from Supabase, checking in-memory DB: {e}")
            ws_item = _in_memory_db.workspaces.get(workspace_id)
    else:
        ws_item = _in_memory_db.workspaces.get(workspace_id)

    if not ws_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    # Authorize workspace ownership
    if ws_item.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this workspace")

    return ws_item

@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user["id"]
    token = current_user.get("token")
    is_dev_user = (user_id == "00000000-0000-0000-0000-000000000001")
    client = get_supabase_client(token) if (token and not is_dev_user) else None

    ws_item = get_workspace(workspace_id, current_user)

    if client:
        try:
            # 1. Fetch all documents in workspace to get storage paths for physical PDF removal
            docs_res = client.table("documents").select("storage_path").eq("workspace_id", workspace_id).execute()
            storage_paths = []
            if docs_res.data:
                storage_paths = [d["storage_path"] for d in docs_res.data if d.get("storage_path")]

            # 2. Explicitly remove physical PDF files from Supabase Storage bucket
            if storage_paths:
                try:
                    client.storage.from_("documents").remove(storage_paths)
                except Exception as st_err:
                    logger.warning(f"Error deleting physical storage files for workspace {workspace_id}: {st_err}")

            # 3. Delete workspace record (PostgreSQL ON DELETE CASCADE deletes dependent DB rows)
            client.table("workspaces").delete().eq("id", workspace_id).execute()
        except Exception as e:
            logger.error(f"Error deleting workspace {workspace_id} in Supabase: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete workspace from database: {e}"
            )
    else:
        if workspace_id in _in_memory_db.workspaces:
            del _in_memory_db.workspaces[workspace_id]
        _in_memory_db.documents = {k: v for k, v in _in_memory_db.documents.items() if v.get("workspace_id") != workspace_id}
        _in_memory_db.document_chunks = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") != workspace_id]

    return None


