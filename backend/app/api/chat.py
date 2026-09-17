import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.schemas.chat import (ChatMessageRequest, ChatMessageResponse,
                               ComparisonRequest, ComparisonResponse)
from app.services.rag_service import RAGService

logger = logging.getLogger("docmind")
router = APIRouter(prefix="/chat", tags=["Chat & Grounded RAG"])
rag_service = RAGService()

def verify_workspace_ownership(workspace_id: str, user_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    ws_item = None
    is_dev_user = (user_id == "00000000-0000-0000-0000-000000000001")
    client = get_supabase_client(token) if (token and not is_dev_user) else None
    if client:
        try:
            res = client.table("workspaces").select("*").eq("id", workspace_id).execute()
            if res.data:
                ws_item = res.data[0]
            else:
                ws_item = _in_memory_db.workspaces.get(workspace_id)
        except Exception as e:
            logger.warning(f"Error checking workspace ownership for {workspace_id} in Supabase, checking in-memory DB: {e}")
            ws_item = _in_memory_db.workspaces.get(workspace_id)
    else:
        ws_item = _in_memory_db.workspaces.get(workspace_id)

    if not ws_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    if ws_item.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this workspace")
    return ws_item

@router.post("/message", response_model=ChatMessageResponse)
def send_chat_message(
    payload: ChatMessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    token = current_user.get("token")
    verify_workspace_ownership(payload.workspace_id, current_user["id"], token)

    if not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question text cannot be empty."
        )

    response = rag_service.query_workspace(
        workspace_id=payload.workspace_id,
        question=payload.question,
        session_id=payload.session_id,
        show_sources=payload.show_sources,
        access_token=token,
        document_id=payload.document_id,
        document_ids=payload.document_ids
    )

    return response

@router.post("/compare", response_model=ComparisonResponse)
def compare_documents(
    payload: ComparisonRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    token = current_user.get("token")
    verify_workspace_ownership(payload.workspace_id, current_user["id"], token)

    response = rag_service.compare_documents(
        workspace_id=payload.workspace_id,
        document_ids=payload.document_ids,
        categories=payload.categories,
        access_token=token
    )

    return response

@router.get("/{session_id}/messages")
def get_chat_history(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    token = current_user.get("token")
    client = get_supabase_client(token) if token else None

    session_item = None
    if client:
        try:
            res = client.table("chat_sessions").select("*").eq("id", session_id).execute()
            if res.data:
                session_item = res.data[0]
        except Exception as e:
            logger.error(f"Error fetching chat session {session_id}: {e}")
    else:
        session_item = _in_memory_db.chat_sessions.get(session_id)

    if session_item:
        verify_workspace_ownership(session_item.get("workspace_id"), current_user["id"], token)

    msgs = []
    if client:
        try:
            res = client.table("messages").select("*").eq("session_id", session_id).order("created_at").execute()
            if res.data:
                msgs = res.data
        except Exception as e:
            logger.error(f"Error fetching messages for session {session_id}: {e}")
    else:
        msgs = [m for m in _in_memory_db.messages if m.get("session_id") == session_id]

    return msgs


