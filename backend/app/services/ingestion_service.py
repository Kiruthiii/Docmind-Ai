import logging
import uuid
from typing import Dict, Any, List
from app.services.pdf_parser import PDFParser
from app.services.llm_service import LLMService
from app.db.supabase_client import get_supabase_client, _in_memory_db

logger = logging.getLogger("docmind")

class IngestionService:
    def __init__(self):
        self.parser = PDFParser()
        self.llm = LLMService()

    def process_pdf(self, workspace_id: str, filename: str, pdf_bytes: bytes, storage_path: str = "") -> Dict[str, Any]:
        """Orchestrates PDF parsing, chunking, embedding generation, and DB storage."""
        doc_id = str(uuid.uuid4())
        logger.info(f"Starting ingestion for document {filename} ({doc_id}) in workspace {workspace_id}")

        # 1. Store initial Document status
        doc_record = {
            "id": doc_id,
            "workspace_id": workspace_id,
            "filename": filename,
            "storage_path": storage_path or f"workspaces/{workspace_id}/{filename}",
            "status": "processing",
            "page_count": 0,
            "created_at": "2026-08-24T20:00:00Z"
        }

        client = get_supabase_client()
        if client:
            try:
                client.table("documents").insert(doc_record).execute()
            except Exception as e:
                logger.error(f"Error saving document record to Supabase: {e}")
        
        # Save to memory fallback
        _in_memory_db.documents[doc_id] = doc_record

        try:
            # 2. Parse PDF and extract text/tables
            parse_result = self.parser.parse_pdf_bytes(pdf_bytes, filename)
            doc_record["page_count"] = parse_result.page_count

            # 3. Generate embeddings & insert chunks
            chunks_to_insert = []
            for chunk in parse_result.chunks:
                chunk_id = str(uuid.uuid4())
                vector = self.llm.get_embedding(chunk.content)

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
                    # Strip extra non-db helper fields for Supabase RPC insert
                    db_payload = [{k: v for k, v in c.items() if k != "filename"} for c in chunks_to_insert]
                    client.table("document_chunks").insert(db_payload).execute()
                except Exception as e:
                    logger.error(f"Error inserting chunks to Supabase: {e}")

            # Always sync with in-memory fallback
            _in_memory_db.document_chunks.extend(chunks_to_insert)

            # 4. Mark status ready
            doc_record["status"] = "ready"
            doc_record["metadata"] = getattr(parse_result, "doc_metadata", {})
            if client:
                try:
                    client.table("documents").update({"status": "ready", "page_count": parse_result.page_count}).eq("id", doc_id).execute()
                except Exception as e:
                    logger.error(f"Error updating doc status in Supabase: {e}")

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
                    logger.error(f"Error updating failed status: {ex}")
            return {
                "document_id": doc_id,
                "filename": filename,
                "status": "failed",
                "error": str(e)
            }
