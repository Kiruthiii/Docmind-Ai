import logging
import uuid
from typing import Any, Dict, List, Optional

from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.services.agents.document_agent import DocumentIntelligenceAgent
from app.services.llm_service import LLMService
from app.services.pdf_parser import PDFParser

logger = logging.getLogger("docmind")


class IngestionService:
    def __init__(self):
        self.parser = PDFParser()
        self.llm = LLMService()
        self.document_agent = DocumentIntelligenceAgent(self.llm)

    def process_pdf(
        self,
        workspace_id: str,
        filename: str,
        pdf_bytes: bytes,
        storage_path: str = "",
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Orchestrates PDF storage, parsing, classification, chunking, embedding generation, and DB storage."""
        doc_id = str(uuid.uuid4())
        logger.info(f"Starting ingestion for document {filename} ({doc_id}) in workspace {workspace_id}")

        actual_storage_path = storage_path or f"workspaces/{workspace_id}/{doc_id}.pdf"
        client = get_supabase_client(access_token)

        # 1. Upload PDF file binary to Supabase Storage (with auto-bucket creation & fallback)
        if client:
            try:
                try:
                    client.storage.get_bucket("documents")
                except Exception:
                    try:
                        client.storage.create_bucket("documents", options={"public": True})
                    except Exception as b_err:
                        logger.warning(f"Could not auto-create Supabase Storage bucket 'documents': {b_err}")

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
            "document_type": "General Document",
            "document_type_confidence": 1.0,
            "classification_method": "default",
            "created_at": "2026-08-24T20:00:00Z"
        }

        # Always register in in-memory DB fallback
        _in_memory_db.documents[doc_id] = doc_record
        _in_memory_db.pdf_bytes[doc_id] = pdf_bytes

        if client:
            try:
                client.table("documents").insert(doc_record).execute()
            except Exception as e:
                logger.warning(f"Error saving document record to Supabase: {e}")
                if "PGRST204" in str(e) or "column" in str(e).lower():
                    logger.warning("Retrying initial documents insert without classification columns for schema compatibility...")
                    try:
                        base_doc_rec = {k: v for k, v in doc_record.items() if k not in ("document_type", "document_type_confidence", "classification_method")}
                        client.table("documents").insert(base_doc_rec).execute()
                    except Exception as retry_err:
                        logger.error(f"Retry documents insert also failed: {retry_err}")

        try:
            # 3. Parse PDF and extract text/tables
            parse_result = self.parser.parse_pdf_bytes(pdf_bytes, filename)
            doc_record["page_count"] = parse_result.page_count

            # 4. Perform Document Type Classification (Non-blocking)
            chunks_dicts = [c.model_dump() if hasattr(c, "model_dump") else dict(c) for c in parse_result.chunks]
            try:
                cls_result = self.document_agent.classify_document(chunks_dicts, filename)
            except Exception as cls_err:
                logger.warning(f"Classification error during ingestion for {filename}: {cls_err}. Falling back to General Document.")
                cls_result = {
                    "document_type": "General Document",
                    "confidence": 0.5,
                    "method": "default"
                }

            doc_cat = cls_result.get("document_category", "General")
            doc_type = cls_result.get("document_type", "General Document")
            doc_conf = float(cls_result.get("confidence", 0.5))
            doc_method = str(cls_result.get("method", "default"))
            doc_evidence = cls_result.get("evidence", [])

            doc_record["document_category"] = doc_cat
            doc_record["document_type"] = doc_type
            doc_record["document_type_confidence"] = doc_conf
            doc_record["classification_method"] = doc_method
            doc_record["evidence"] = doc_evidence

            # 5. Generate embeddings in batch & insert chunks
            chunks_to_insert = []
            chunk_contents = [
                getattr(c, "content", c.get("content") if isinstance(c, dict) else "")
                for c in parse_result.chunks
            ]
            embeddings = self.llm.get_embeddings_batch(chunk_contents) if chunk_contents else []

            for idx, chunk in enumerate(parse_result.chunks):
                chunk_id = str(uuid.uuid4())
                content_text = getattr(chunk, "content", chunk.get("content") if isinstance(chunk, dict) else "")
                vector = embeddings[idx] if idx < len(embeddings) else self.llm._mock_embedding(content_text)

                page_num = getattr(chunk, "page_number", chunk.get("page_number", 1) if isinstance(chunk, dict) else 1)
                chunk_type = getattr(chunk, "chunk_type", chunk.get("chunk_type", "text") if isinstance(chunk, dict) else "text")
                content_type = getattr(chunk, "content_type", chunk.get("content_type", "text") if isinstance(chunk, dict) else "text")
                doc_pos = getattr(chunk, "document_position", chunk.get("document_position", "general") if isinstance(chunk, dict) else "general")
                sec_hier = getattr(chunk, "section_hierarchy", chunk.get("section_hierarchy", []) if isinstance(chunk, dict) else [])
                sec_path = getattr(chunk, "section_path", chunk.get("section_path", "") if isinstance(chunk, dict) else "")
                parent_sec = getattr(chunk, "parent_section", chunk.get("parent_section", "") if isinstance(chunk, dict) else "")

                chunk_meta = getattr(chunk, "metadata", chunk.get("metadata", {}) if isinstance(chunk, dict) else {}) or {}
                chunk_meta.update({
                    "filename": filename,
                    "page_number": page_num,
                    "parent_section": parent_sec,
                    "content_type": content_type,
                    "document_position": doc_pos,
                    "section_hierarchy": sec_hier,
                    "document_type": doc_type,
                    "document_type_confidence": doc_conf,
                    "classification_method": doc_method
                })

                chunk_record = {
                    "id": chunk_id,
                    "document_id": doc_id,
                    "workspace_id": workspace_id,
                    "page_number": page_num,
                    "chunk_type": chunk_type,
                    "content_type": content_type,
                    "document_position": doc_pos,
                    "section_hierarchy": sec_hier,
                    "content": content_text,
                    "section_path": sec_path,
                    "parent_section": parent_sec,
                    "embedding": vector,
                    "filename": filename,
                    "document_type": doc_type,
                    "document_type_confidence": doc_conf,
                    "classification_method": doc_method,
                    "metadata": chunk_meta
                }

                chunks_to_insert.append(chunk_record)

            # Always register chunks in in-memory DB fallback for reliable retrieval
            _in_memory_db.document_chunks.extend(chunks_to_insert)

            if client and chunks_to_insert:
                try:
                    db_payload = [{k: v for k, v in c.items() if k not in ("filename", "document_type", "document_type_confidence", "classification_method")} for c in chunks_to_insert]
                    client.table("document_chunks").insert(db_payload).execute()
                except Exception as e:
                    logger.error(f"Error inserting chunks to Supabase: {e}")
                    if "metadata" in str(e) or "PGRST204" in str(e):
                        logger.warning("Retrying document_chunks insert with clean payload...")
                        try:
                            db_payload_clean = [{k: v for k, v in c.items() if k not in ("filename", "metadata", "document_type", "document_type_confidence", "classification_method")} for c in chunks_to_insert]
                            client.table("document_chunks").insert(db_payload_clean).execute()
                        except Exception as retry_err:
                            logger.error(f"Retry without metadata also failed: {retry_err}")
                    else:
                        logger.warning(f"Chunk insert exception swallowed: {e}")

            # 6. Mark document status ready with classification fields
            doc_record["status"] = "ready"
            if client:
                try:
                    client.table("documents").update({
                        "status": "ready",
                        "page_count": parse_result.page_count,
                        "document_type": doc_type,
                        "document_type_confidence": doc_conf,
                        "classification_method": doc_method
                    }).eq("id", doc_id).execute()
                except Exception as up_err:
                    if "PGRST204" in str(up_err) or "column" in str(up_err).lower():
                        logger.warning("Retrying status update without classification columns for schema compatibility...")
                        try:
                            client.table("documents").update({
                                "status": "ready",
                                "page_count": parse_result.page_count
                            }).eq("id", doc_id).execute()
                        except Exception as up_retry_err:
                            logger.error(f"Retry status update failed: {up_retry_err}")

            logger.info(f"Successfully processed {len(chunks_to_insert)} chunks for {filename} (Classified as '{doc_type}')")
            return {
                "document_id": doc_id,
                "filename": filename,
                "status": "ready",
                "page_count": parse_result.page_count,
                "chunk_count": len(chunks_to_insert),
                "document_category": doc_cat,
                "document_type": doc_type,
                "document_type_confidence": doc_conf,
                "classification_method": doc_method,
                "evidence": doc_evidence
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

    def reindex_existing_document(
        self,
        doc_id: str,
        workspace_id: str,
        filename: str,
        pdf_bytes: bytes,
        storage_path: str,
        access_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Parses PDF bytes, generates embeddings, and inserts chunks into database for an existing document record."""
        client = get_supabase_client(access_token)
        try:
            parse_result = self.parser.parse_pdf_bytes(pdf_bytes, filename)
            chunks_dicts = [c.model_dump() if hasattr(c, "model_dump") else dict(c) for c in parse_result.chunks]
            try:
                cls_result = self.document_agent.classify_document(chunks_dicts, filename)
            except Exception:
                cls_result = {"document_type": "General Document", "confidence": 0.5, "method": "default"}

            doc_type = cls_result.get("document_type", "General Document")
            doc_conf = float(cls_result.get("confidence", 0.5))
            doc_method = str(cls_result.get("method", "default"))

            chunk_contents = [
                getattr(c, "content", c.get("content") if isinstance(c, dict) else "")
                for c in parse_result.chunks
            ]
            embeddings = self.llm.get_embeddings_batch(chunk_contents) if chunk_contents else []

            chunks_to_insert = []
            for idx, chunk in enumerate(parse_result.chunks):
                chunk_id = str(uuid.uuid4())
                content_text = getattr(chunk, "content", chunk.get("content") if isinstance(chunk, dict) else "")
                vector = embeddings[idx] if idx < len(embeddings) else self.llm._mock_embedding(content_text)
                page_num = getattr(chunk, "page_number", chunk.get("page_number", 1) if isinstance(chunk, dict) else 1)
                chunk_type = getattr(chunk, "chunk_type", chunk.get("chunk_type", "text") if isinstance(chunk, dict) else "text")
                content_type = getattr(chunk, "content_type", chunk.get("content_type", "text") if isinstance(chunk, dict) else "text")
                doc_pos = getattr(chunk, "document_position", chunk.get("document_position", "general") if isinstance(chunk, dict) else "general")
                sec_hier = getattr(chunk, "section_hierarchy", chunk.get("section_hierarchy", []) if isinstance(chunk, dict) else [])
                sec_path = getattr(chunk, "section_path", chunk.get("section_path", "") if isinstance(chunk, dict) else "")
                parent_sec = getattr(chunk, "parent_section", chunk.get("parent_section", "") if isinstance(chunk, dict) else "")
                chunk_meta = getattr(chunk, "metadata", chunk.get("metadata", {}) if isinstance(chunk, dict) else {}) or {}

                chunk_record = {
                    "id": chunk_id,
                    "document_id": doc_id,
                    "workspace_id": workspace_id,
                    "page_number": page_num,
                    "chunk_type": chunk_type,
                    "content_type": content_type,
                    "document_position": doc_pos,
                    "section_hierarchy": sec_hier,
                    "content": content_text,
                    "section_path": sec_path,
                    "parent_section": parent_sec,
                    "embedding": vector,
                    "filename": filename,
                    "document_type": doc_type,
                    "document_type_confidence": doc_conf,
                    "classification_method": doc_method,
                    "metadata": chunk_meta
                }
                chunks_to_insert.append(chunk_record)

            _in_memory_db.document_chunks.extend(chunks_to_insert)

            if client and chunks_to_insert:
                try:
                    db_payload = [{k: v for k, v in c.items() if k not in ("filename", "document_type", "document_type_confidence", "classification_method")} for c in chunks_to_insert]
                    client.table("document_chunks").insert(db_payload).execute()
                    logger.info(f"Reindexed and inserted {len(chunks_to_insert)} chunks for {filename} ({doc_id})")
                except Exception as e:
                    logger.error(f"Error inserting reindexed chunks to Supabase: {e}")

            return chunks_to_insert
        except Exception as e:
            logger.error(f"Reindexing failed for {filename}: {e}")
            return []
