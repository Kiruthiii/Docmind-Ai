import asyncio
from typing import List

from fastapi import (APIRouter, File, HTTPException, Response, UploadFile,
                     status)

from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.ingestion_service import IngestionService

router = APIRouter(tags=["Documents"])
ingestion_service = IngestionService()

@router.get("/workspaces/{workspace_id}/documents", response_model=List[DocumentResponse])
def list_workspace_documents(workspace_id: str):
    db_docs = []
    client = get_supabase_client()
    if client:
        try:
            res = client.table("documents").select("*").eq("workspace_id", workspace_id).execute()
            if res.data:
                db_docs = res.data
        except Exception:
            pass

    all_docs = {d["id"]: d for d in db_docs if "id" in d}
    for d_id, d_item in _in_memory_db.documents.items():
        if d_item.get("workspace_id") == workspace_id:
            all_docs[d_id] = d_item

    return list(all_docs.values())

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

    # Ingest PDF on worker thread to avoid blocking main event loop
    result = await asyncio.to_thread(
        ingestion_service.process_pdf,
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

@router.get("/documents/{document_id}/file")
def get_document_file(document_id: str):
    """Serves raw PDF binary stream for the frontend PDF reader preview canvas."""
    if document_id in _in_memory_db.pdf_bytes:
        pdf_bytes = _in_memory_db.pdf_bytes[document_id]
        doc_rec = _in_memory_db.documents.get(document_id, {})
        filename = doc_rec.get("filename", "document.pdf")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )

    client = get_supabase_client()
    if client:
        try:
            doc_res = client.table("documents").select("*").eq("id", document_id).execute()
            if doc_res.data:
                storage_path = doc_res.data[0].get("storage_path")
                if storage_path:
                    res = client.storage.from_("documents").download(storage_path)
                    return Response(
                        content=res,
                        media_type="application/pdf",
                        headers={"Content-Disposition": f'inline; filename="{doc_res.data[0].get("filename", "document.pdf")}"'}
                    )
        except Exception as e:
            pass

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"PDF document file for ID {document_id} was not found on server."
    )

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str):
    if document_id in _in_memory_db.documents:
        del _in_memory_db.documents[document_id]
        _in_memory_db.document_chunks = [c for c in _in_memory_db.document_chunks if c.get("document_id") != document_id]
    if document_id in _in_memory_db.pdf_bytes:
        del _in_memory_db.pdf_bytes[document_id]

    client = get_supabase_client()
    if client:
        client.table("documents").delete().eq("id", document_id).execute()

    return None
