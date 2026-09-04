from typing import List

from fastapi import APIRouter, HTTPException, status

from app.db.supabase_client import _in_memory_db
from app.schemas.chat import (ChatMessageRequest, ChatMessageResponse,
                              ComparisonRequest, ComparisonResponse)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["Chat & Grounded RAG"])
rag_service = RAGService()

@router.post("/message", response_model=ChatMessageResponse)
def send_chat_message(payload: ChatMessageRequest):
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
def compare_documents(payload: ComparisonRequest):
    response = rag_service.compare_documents(
        workspace_id=payload.workspace_id,
        document_ids=payload.document_ids,
        categories=payload.categories
    )

    return response

@router.get("/{session_id}/messages")
def get_chat_history(session_id: str):
    msgs = [m for m in _in_memory_db.messages if m.get("session_id") == session_id]
    return msgs
