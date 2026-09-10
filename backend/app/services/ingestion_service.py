import logging
import uuid
from typing import Any, Dict, List, Optional

from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.services.llm_service import LLMService
from app.services.pdf_parser import PDFParser

logger = logging.getLogger("docmind")

class IngestionService:
    def __init__(self):
        self.parser = PDFParser()
        self.llm = LLMService()

    def process_pdf(
        self,
        workspace_id: str,
        filename: str,
        pdf_bytes: bytes,
        storage_path: str = "",
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Orchestrates PDF storage, parsing, chunking, embedding generation, and DB storage."""
        doc_id = str(uuid.uuid4())
        logger.info(f"Starting ingestion for document {filename} ({doc_id}) in workspace {workspace_id}")

        actual_storage_path = storage_path or f"workspaces/{workspace_id}/{doc_id}.pdf"
        client = get_supabase_client(access_token)

        # 1. Upload PDF file binary to Supabase Storage (with auto-bucket creation & fallback)
        if client:
            try:
                # Attempt to create documents bucket if it does not exist
                try:
                    client.storage.get_bucket("documents")
                except Exception:
                    try:
                        client.storage.create_bucket("documents", options={"public": True})
                    except Exception as b_err:
                        logger.warning(f"Could not auto-create Supabase Storage bucket 'documents': {b_err}")

                # Store PDF in Supabase Storage documents bucket
                client.storage.from_("documents").upload(
                    actual_storage_path,
                    pdf_bytes,
                    file_options={"content-type": "application/pdf", "upsert": "true"}
                )
            except Exception as e:
                logger.warning(
                    f"Error uploading PDF file {filename} to Supabase Storage: {e}. "
                    f"Caching binary in fallback memory storage for PDF preview."
                )
                _in_memory_db.pdf_bytes[doc_id] = pdf_bytes

        # 2. Store initial Document status in database
        doc_record = {
            "id": doc_id,
            "workspace_id": workspace_id,
            "filename": filename,
            "storage_path": actual_storage_path,
            "status": "processing",
            "page_count": 0,
            "created_at": "2026-08-24T20:00:00Z"
        }

        if client:
            try:
                client.table("documents").insert(doc_record).execute()
            except Exception as e:
                logger.error(f"Error saving document record to Supabase: {e}")
                return {
                    "document_id": doc_id,
                    "filename": filename,
                    "status": "failed",
                    "error": f"Database insert failed: {e}"
                }
        else:
            _in_memory_db.documents[doc_id] = doc_record
            _in_memory_db.pdf_bytes[doc_id] = pdf_bytes

        try:
            # 3. Parse PDF and extract text/tables
            parse_result = self.parser.parse_pdf_bytes(pdf_bytes, filename)
            doc_record["page_count"] = parse_result.page_count

            # 4. Generate embeddings in batch & insert chunks
            chunks_to_insert = []
            chunk_contents = [chunk.content for chunk in parse_result.chunks]
            embeddings = self.llm.get_embeddings_batch(chunk_contents) if chunk_contents else []

            for idx, chunk in enumerate(parse_result.chunks):
                chunk_id = str(uuid.uuid4())
                vector = embeddings[idx] if idx < len(embeddings) else self.llm._mock_embedding(chunk.content)

                chunk_record = {
                    "id": chunk_id,
                    "document_id": doc_id,
                    "workspace_id": workspace_id,
                    "page_number": chunk.page_number,
                    "chunk_type": chunk.chunk_type,
                    "content_type": getattr(chunk, "content_type", "text"),
                    "document_position": getattr(chunk, "document_position", "general"),
                    "section_hierarchy": getattr(chunk, "section_hierarchy", []),
                    "content": chunk.content,
                    "section_path": getattr(chunk, "section_path", ""),
                    "parent_section": getattr(chunk, "parent_section", ""),
                    "embedding": vector,
                    "filename": filename,
                    "metadata": getattr(chunk, "metadata", {}) or {
                        "filename": filename,
                        "page_number": chunk.page_number,
                        "parent_section": getattr(chunk, "parent_section", ""),
                        "content_type": getattr(chunk, "content_type", "text"),
                        "document_position": getattr(chunk, "document_position", "general"),
                        "section_hierarchy": getattr(chunk, "section_hierarchy", [])
                    }
                }

                chunks_to_insert.append(chunk_record)

            if client and chunks_to_insert:
                try:
                    # Strip non-db helper fields for Supabase table insert
                    db_payload = [{k: v for k, v in c.items() if k != "filename"} for c in chunks_to_insert]
                    client.table("document_chunks").insert(db_payload).execute()
                except Exception as e:
                    logger.error(f"Error inserting chunks to Supabase: {e}")
                    if "metadata" in str(e) or "PGRST204" in str(e):
                        logger.warning("Retrying document_chunks insert without 'metadata' column...")
                        try:
                            db_payload_no_meta = [{k: v for k, v in c.items() if k not in ("filename", "metadata")} for c in chunks_to_insert]
                            client.table("document_chunks").insert(db_payload_no_meta).execute()
                        except Exception as retry_err:
                            logger.error(f"Retry without metadata also failed: {retry_err}")
                            raise retry_err
                    else:
                        raise e
            else:
                _in_memory_db.document_chunks.extend(chunks_to_insert)

            # 5. Mark document status ready
            doc_record["status"] = "ready"
            if client:
                client.table("documents").update({"status": "ready", "page_count": parse_result.page_count}).eq("id", doc_id).execute()

            logger.info(f"Successfully processed {len(chunks_to_insert)} chunks for {filename}")
            return {
                "document_id": doc_id,
                "filename": filename,
                "status": "ready",
                "page_count": parse_result.page_count,
                "chunk_count": len(chunks_to_insert)
            }

        except Exception as e:
            logger.error(f"Ingestion failed for {filename}: {e}", exc_info=True)
            doc_record["status"] = "failed"
            if client:
                try:
                    client.table("documents").update({"status": "failed"}).eq("id", doc_id).execute()
                except Exception as ex:
                    logger.error(f"Error updating failed status in Supabase: {ex}")
            return {
                "document_id": doc_id,
                "filename": filename,
                "status": "failed",
                "error": str(e)
            }

