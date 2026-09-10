import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import (APIRouter, Depends, File, HTTPException, Response, UploadFile,
                     status)

from app.api.deps import get_current_user
from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.ingestion_service import IngestionService

logger = logging.getLogger("docmind")
router = APIRouter(tags=["Documents"])
ingestion_service = IngestionService()

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
            logger.warning(f"Error checking workspace {workspace_id} in Supabase, checking in-memory DB: {e}")
            ws_item = _in_memory_db.workspaces.get(workspace_id)
    else:
        ws_item = _in_memory_db.workspaces.get(workspace_id)

    if not ws_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")

    if ws_item.get("user_id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this workspace")
    return ws_item

def get_document_record(document_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    client = get_supabase_client(token) if token else None
    if client:
        try:
            res = client.table("documents").select("*").eq("id", document_id).execute()
            if res.data:
                return res.data[0]
        except Exception as e:
            logger.error(f"Error fetching document {document_id} record: {e}")
    return _in_memory_db.documents.get(document_id)

@router.get("/workspaces/{workspace_id}/documents", response_model=List[DocumentResponse])
def list_workspace_documents(
    workspace_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    token = current_user.get("token")
    verify_workspace_ownership(workspace_id, current_user["id"], token)
    
    client = get_supabase_client(token) if token else None
    if client:
        try:
            res = client.table("documents").select("*").eq("workspace_id", workspace_id).execute()
            if res.data is not None:
                return res.data
        except Exception as e:
            logger.error(f"Error listing documents for workspace {workspace_id} from Supabase: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch workspace documents: {e}"
            )
    
    return [d for d in _in_memory_db.documents.values() if d.get("workspace_id") == workspace_id]

@router.post("/workspaces/{workspace_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    token = current_user.get("token")
    verify_workspace_ownership(workspace_id, current_user["id"], token)

    # Validate PDF content type / extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are supported."
        )

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded PDF file is empty. No readable content detected."
        )

    # Ingest PDF on worker thread to avoid blocking main event loop
    result = await asyncio.to_thread(
        ingestion_service.process_pdf,
        workspace_id=workspace_id,
        filename=file.filename,
        pdf_bytes=pdf_bytes,
        access_token=token
    )

    if result.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {result.get('error', 'Unknown parsing error')}"
        )

    return DocumentUploadResponse(
        document_id=result["document_id"],
        filename=result["filename"],
        status=result["status"],
        message=f"Successfully processed PDF ({result.get('page_count', 0)} pages, {result.get('chunk_count', 0)} searchable chunks)."
    )

@router.get("/documents/{document_id}/file")
def get_document_file(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Serves raw PDF binary stream from Supabase Storage for preview canvas."""
    token = current_user.get("token")
    doc_rec = get_document_record(document_id, token)
    if not doc_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF document record for ID {document_id} was not found on server."
        )

    workspace_id = doc_rec.get("workspace_id")
    verify_workspace_ownership(workspace_id, current_user["id"], token)

    storage_path = doc_rec.get("storage_path")
    filename = doc_rec.get("filename", "document.pdf")

    client = get_supabase_client(token) if token else None
    if client and storage_path:
        try:
            pdf_bytes = client.storage.from_("documents").download(storage_path)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f'inline; filename="{filename}"'}
            )
        except Exception as e:
            logger.warning(f"Error downloading PDF file {storage_path} from Supabase Storage: {e}. Checking in-memory fallback...")

    if document_id in _in_memory_db.pdf_bytes:
        return Response(
            content=_in_memory_db.pdf_bytes[document_id],
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"PDF document file for ID {document_id} was not found on server."
    )

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    token = current_user.get("token")
    doc_rec = get_document_record(document_id, token)
    if not doc_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    workspace_id = doc_rec.get("workspace_id")
    verify_workspace_ownership(workspace_id, current_user["id"], token)

    client = get_supabase_client(token) if token else None
    if client:
        try:
            # 1. Explicitly delete physical PDF from Supabase Storage
            storage_path = doc_rec.get("storage_path")
            if storage_path:
                try:
                    client.storage.from_("documents").remove([storage_path])
                except Exception as st_err:
                    logger.warning(f"Error deleting physical file {storage_path} from Supabase Storage: {st_err}")

            # 2. Delete document record in Supabase (PostgreSQL ON DELETE CASCADE handles chunks)
            client.table("documents").delete().eq("id", document_id).execute()
        except Exception as e:
            logger.error(f"Error deleting document {document_id} in Supabase: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete document from database: {e}"
            )
    else:
        if document_id in _in_memory_db.documents:
            del _in_memory_db.documents[document_id]
            _in_memory_db.document_chunks = [c for c in _in_memory_db.document_chunks if c.get("document_id") != document_id]
        if document_id in _in_memory_db.pdf_bytes:
            del _in_memory_db.pdf_bytes[document_id]

    return None


