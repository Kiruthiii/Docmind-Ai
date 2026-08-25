from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List

from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.ingestion_service import IngestionService
from app.db.supabase_client import get_supabase_client, _in_memory_db

router = APIRouter(tags=["Documents"])
ingestion_service = IngestionService()

@router.get("/workspaces/{workspace_id}/documents", response_model=List[DocumentResponse])
def list_workspace_documents(workspace_id: str):
    client = get_supabase_client()
    if client:
        try:
            res = client.table("documents").select("*").eq("workspace_id", workspace_id).execute()
            return res.data
        except Exception:
            pass

    # In-memory fallback
    docs = [d for d in _in_memory_db.documents.values() if d.get("workspace_id") == workspace_id]
    return docs

@router.post("/workspaces/{workspace_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(workspace_id: str, file: UploadFile = File(...)):
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

    # Ingest PDF
    result = ingestion_service.process_pdf(
        workspace_id=workspace_id,
        filename=file.filename,
        pdf_bytes=pdf_bytes
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

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str):
    if document_id in _in_memory_db.documents:
        del _in_memory_db.documents[document_id]
        _in_memory_db.document_chunks = [c for c in _in_memory_db.document_chunks if c.get("document_id") != document_id]

    client = get_supabase_client()
    if client:
        client.table("documents").delete().eq("id", document_id).execute()

    return None
