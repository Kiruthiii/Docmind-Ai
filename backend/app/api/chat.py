from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.schemas.chat import (ChatMessageRequest, ChatMessageResponse,
                              ComparisonRequest, ComparisonResponse)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["Chat & Grounded RAG"])
rag_service = RAGService()

def verify_workspace_ownership(workspace_id: str, user_id: str) -> Dict[str, Any]:
    ws_item = None
    if workspace_id in _in_memory_db.workspaces:
        ws_item = _in_memory_db.workspaces[workspace_id]
    else:
        client = get_supabase_client()
        if client:
            try:
                res = client.table("workspaces").select("*").eq("id", workspace_id).execute()
                if res.data:
                    ws_item = res.data[0]
            except Exception:
                pass

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
    verify_workspace_ownership(payload.workspace_id, current_user["id"])

    if not payload.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question text cannot be empty."
        )

    response = rag_service.query_workspace(
        workspace_id=payload.workspace_id,
        question=payload.question,
        session_id=payload.session_id,
        show_sources=payload.show_sources
    )

    return response

@router.post("/compare", response_model=ComparisonResponse)
def compare_documents(
    payload: ComparisonRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    verify_workspace_ownership(payload.workspace_id, current_user["id"])

    response = rag_service.compare_documents(
        workspace_id=payload.workspace_id,
        document_ids=payload.document_ids,
        categories=payload.categories
    )

    return response

@router.get("/{session_id}/messages")
def get_chat_history(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    session_item = None
    if session_id in _in_memory_db.chat_sessions:
        session_item = _in_memory_db.chat_sessions[session_id]
    else:
        client = get_supabase_client()
        if client:
            try:
                res = client.table("chat_sessions").select("*").eq("id", session_id).execute()
                if res.data:
                    session_item = res.data[0]
            except Exception:
                pass

    if session_item:
        verify_workspace_ownership(session_item.get("workspace_id"), current_user["id"])
    else:
        # If session_id not explicitly tracked in sessions table, check messages for workspace verification
        sample_msg = next((m for m in _in_memory_db.messages if m.get("session_id") == session_id), None)
        if sample_msg and "workspace_id" in sample_msg:
            verify_workspace_ownership(sample_msg["workspace_id"], current_user["id"])

    msgs = [m for m in _in_memory_db.messages if m.get("session_id") == session_id]
    if not msgs:
        client = get_supabase_client()
        if client:
            try:
                res = client.table("messages").select("*").eq("session_id", session_id).execute()
                if res.data:
                    msgs = res.data
            except Exception:
                pass
    return msgs
