import logging
import math
import uuid
from typing import List, Dict, Any, Tuple
from app.services.llm_service import LLMService
from app.db.supabase_client import get_supabase_client, _in_memory_db
from app.schemas.chat import Citation, ChatMessageResponse, ComparisonResponse
from app.core.config import settings

logger = logging.getLogger("docmind")

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculates cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class RAGService:
    def __init__(self):
        self.llm = LLMService()

    def query_workspace(
        self,
        workspace_id: str,
        question: str,
        session_id: str = None,
        show_sources: bool = True
    ) -> ChatMessageResponse:
        """Retrieves evidence and generates a grounded response."""
        if not session_id:
            session_id = str(uuid.uuid4())

        # 1. Embed query
        query_vector = self.llm.get_embedding(question)

        # 2. Retrieve top-K relevant chunks
        relevant_chunks = self._retrieve_chunks(workspace_id, query_vector, question=question, top_k=settings.MAX_RETRIEVAL_CHUNKS)

        # 3. Generate grounded answer via Gemini
        answer_text, is_grounded = self.llm.generate_grounded_answer(question, relevant_chunks)

        # 4. Format citations if sources enabled and answer is grounded
        citations = []
        if show_sources and is_grounded:
            citations = self._build_citations(relevant_chunks)

        # Save to chat history
        self._save_message(session_id, "user", question)
        self._save_message(session_id, "assistant", answer_text, citations)

        return ChatMessageResponse(
            session_id=session_id,
            question=question,
            answer=answer_text,
            is_grounded=is_grounded,
            citations=citations
        )

    def compare_documents(
        self,
        workspace_id: str,
        document_ids: List[str] = None,
        categories: List[str] = None
    ) -> ComparisonResponse:
        """Performs multi-document analysis and comparison matrix generation."""
        if not categories:
            categories = ["Summary", "Methodology", "Results", "Advantages", "Limitations"]

        # Fetch chunks for workspace
        chunks = self._get_all_workspace_chunks(workspace_id, document_ids)
        workspace_name = "Selected Workspace Documents"

        matrix_md, contradictions = self.llm.generate_comparison_matrix(workspace_name, chunks, categories)
        citations = self._build_citations(chunks[:10])

        return ComparisonResponse(
            workspace_id=workspace_id,
            markdown_matrix=matrix_md,
            potential_contradictions=contradictions,
            citations=citations
        )

    def _retrieve_chunks(self, workspace_id: str, query_vector: List[float], question: str = "", top_k: int = 15) -> List[Dict[str, Any]]:
        """Retrieves top-K chunks from Supabase RPC or in-memory vector store."""
        client = get_supabase_client()
        if client:
            try:
                # Call Supabase pgvector match RPC function
                response = client.rpc(
                    "match_document_chunks",
                    {
                        "query_embedding": query_vector,
                        "match_threshold": settings.SIMILARITY_THRESHOLD,
                        "match_count": top_k,
                        "filter_workspace_id": workspace_id
                    }
                ).execute()

                if response.data:
                    # Enrich with filename metadata
                    for chunk in response.data:
                        doc_id = chunk.get("document_id")
                        doc_rec = _in_memory_db.documents.get(doc_id)
                        if doc_rec:
                            chunk["filename"] = doc_rec.get("filename", "Document")
                    return response.data
            except Exception as e:
                logger.warning(f"Supabase RPC search failed: {e}. Falling back to in-memory search.")

        # Fallback to In-Memory Vector & Keyword Search
        workspace_chunks = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]
        if not workspace_chunks:
            return []

        scored_chunks = []
        for chunk in workspace_chunks:
            chunk_vec = chunk.get("embedding", [])
            score = cosine_similarity(query_vector, chunk_vec) if chunk_vec else 0.0
            
            # Additional fallback for mock mode: boost score if keywords match
            content_lower = chunk.get("content", "").lower()
            q_terms = [w.lower() for w in question.split() if len(w) >= 2] if question else []
            if any(term in content_lower for term in q_terms):
                score += 0.5

            if score >= settings.SIMILARITY_THRESHOLD or len(workspace_chunks) <= 3:
                scored_chunk = dict(chunk)
                scored_chunk["similarity"] = score
                scored_chunks.append(scored_chunk)

        scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_chunks[:top_k]

    def _get_all_workspace_chunks(self, workspace_id: str, document_ids: List[str] = None) -> List[Dict[str, Any]]:
        chunks = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]
        if document_ids:
            chunks = [c for c in chunks if c.get("document_id") in document_ids]
        return chunks

    def _build_citations(self, chunks: List[Dict[str, Any]]) -> List[Citation]:
        citations = []
        seen = set()
        for chunk in chunks:
            doc_id = chunk.get("document_id", "doc-1")
            page_num = chunk.get("page_number", 1)
            key = f"{doc_id}_{page_num}"
            if key not in seen:
                seen.add(key)
                doc_name = chunk.get("filename") or _in_memory_db.documents.get(doc_id, {}).get("filename", "PDF Document")
                content = chunk.get("content", "")
                snippet = content[:150] + ("..." if len(content) > 150 else "")
                citations.append(Citation(
                    document_id=doc_id,
                    document_name=doc_name,
                    page_number=page_num,
                    content_snippet=snippet,
                    chunk_type=chunk.get("chunk_type", "text")
                ))
        return citations

    def _save_message(self, session_id: str, role: str, content: str, citations: List[Citation] = None):
        msg_record = {
            "id": str(uuid.uuid4()),
            "session_id": session_id,
            "role": role,
            "content": content,
            "citations": [c.model_dump() for c in (citations or [])],
            "created_at": "2026-08-24T20:00:00Z"
        }
        _in_memory_db.messages.append(msg_record)
