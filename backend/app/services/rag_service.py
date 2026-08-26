import logging
import math
import uuid
import re
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
        """Retrieves evidence and generates a grounded response using a 3-stage evidence pipeline."""
        if not session_id:
            session_id = str(uuid.uuid4())

        # 1. Embed query
        query_vector = self.llm.get_embedding(question)

        # 2. Stage 1: Candidate Retrieval
        candidate_chunks = self._retrieve_chunks(workspace_id, query_vector, question=question, top_k=settings.MAX_RETRIEVAL_CHUNKS)

        # 3. Stage 2: Post-Retrieval Semantic Relevance Filtering
        relevant_chunks = self._filter_relevant_evidence(question, candidate_chunks)

        # 4. Stage 3: Grounded Answer Generation & Answer-Supporting Evidence Extraction
        answer_text, is_grounded, supporting_chunks = self.llm.generate_grounded_answer(question, relevant_chunks)

        # 5. Format Citations STRICTLY from Answer-Supporting Evidence
        citations = []
        if show_sources and is_grounded:
            citations = self._build_citations(supporting_chunks)

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
        """Retrieves top-K chunks with Parent Section Expansion for complete evidence context."""
        client = get_supabase_client()
        raw_candidates = []

        if client:
            try:
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
                    for chunk in response.data:
                        doc_id = chunk.get("document_id")
                        doc_rec = _in_memory_db.documents.get(doc_id)
                        if doc_rec:
                            chunk["filename"] = doc_rec.get("filename", "Document")
                    raw_candidates = response.data
            except Exception as e:
                logger.warning(f"Supabase RPC search failed: {e}. Falling back to in-memory search.")

        if not raw_candidates:
            workspace_chunks = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]
            if not workspace_chunks:
                return []

            STOP_WORDS = {"tell", "about", "the", "what", "is", "are", "a", "an", "of", "in", "for", "and", "or", "to", "with", "on", "at", "from", "by", "my", "your", "show", "me", "can", "you", "please", "give", "list", "info", "details", "does", "do", "did", "how", "why", "which"}
            q_terms = [re.sub(r'[^a-zA-Z0-9]', '', w.lower()) for w in question.split() if re.sub(r'[^a-zA-Z0-9]', '', w.lower()) not in STOP_WORDS and len(re.sub(r'[^a-zA-Z0-9]', '', w.lower())) >= 2 and not re.sub(r'[^a-zA-Z0-9]', '', w.lower()).isdigit()] if question else []

            scored_chunks = []
            for chunk in workspace_chunks:
                chunk_vec = chunk.get("embedding", [])
                score = cosine_similarity(query_vector, chunk_vec) if chunk_vec else 0.0
                
                content_lower = chunk.get("content", "").lower()
                words = set(re.findall(r'\b[a-zA-Z0-9]+\b', content_lower))
                
                has_match = False
                for term in q_terms:
                    if term in words or any(w.startswith(term[:4]) for w in words if len(term) >= 4 and len(w) >= 4):
                        has_match = True
                        break

                if has_match:
                    score = max(score + 0.5, 0.5)

                if score >= settings.SIMILARITY_THRESHOLD:
                    scored_chunk = dict(chunk)
                    scored_chunk["similarity"] = score
                    scored_chunks.append(scored_chunk)

            scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            raw_candidates = scored_chunks[:top_k]

        if not raw_candidates:
            return []

        # UNIVERSAL PARENT SECTION & NEIGHBORING CONTEXT EXPANSION
        retrieved_ids = {c.get("id") for c in raw_candidates}
        expanded_chunks = list(raw_candidates)

        top_parent_sections = set()
        for c in raw_candidates[:5]:
            p_sec = c.get("parent_section") or c.get("metadata", {}).get("parent_section")
            if not p_sec:
                content = c.get("content", "")
                if "Section:" in content:
                    first_line = content.split("\n")[0].replace("Section:", "").strip()
                    p_sec = first_line.split(">")[0].strip()
            if p_sec and p_sec.lower() != "general":
                top_parent_sections.add(p_sec.lower())

        if top_parent_sections:
            if client:
                try:
                    res_db = client.from_("document_chunks") \
                        .select("*") \
                        .eq("workspace_id", workspace_id) \
                        .execute()
                    if res_db.data:
                        for sister in res_db.data:
                            s_id = sister.get("id")
                            if s_id not in retrieved_ids:
                                s_content = sister.get("content", "")
                                s_p_sec = sister.get("parent_section") or sister.get("metadata", {}).get("parent_section")
                                if not s_p_sec and "Section:" in s_content:
                                    first_line = s_content.split("\n")[0].replace("Section:", "").strip()
                                    s_p_sec = first_line.split(">")[0].strip()

                                if s_p_sec and s_p_sec.lower() in top_parent_sections:
                                    sister_copy = dict(sister)
                                    doc_id = sister_copy.get("document_id")
                                    doc_rec = _in_memory_db.documents.get(doc_id)
                                    if doc_rec:
                                        sister_copy["filename"] = doc_rec.get("filename", "Document")
                                    sister_copy["similarity"] = 0.6
                                    expanded_chunks.append(sister_copy)
                                    retrieved_ids.add(s_id)
                except Exception as e:
                    logger.warning(f"Supabase parent section expansion query failed: {e}")

            workspace_all_chunks = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]
            if workspace_all_chunks:
                for c in workspace_all_chunks:
                    c_id = c.get("id")
                    if c_id not in retrieved_ids:
                        content = c.get("content", "")
                        c_p_sec = c.get("parent_section") or c.get("metadata", {}).get("parent_section")
                        if not c_p_sec and "Section:" in content:
                            first_line = content.split("\n")[0].replace("Section:", "").strip()
                            c_p_sec = first_line.split(">")[0].strip()

                        if c_p_sec and c_p_sec.lower() in top_parent_sections:
                            c_copy = dict(c)
                            c_copy["similarity"] = 0.6
                            expanded_chunks.append(c_copy)
                            retrieved_ids.add(c_id)

        return expanded_chunks[:top_k]

    def _filter_relevant_evidence(self, question: str, candidate_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 2: Semantic Relevance Filter with Parent Section Context Preservation."""
        if not candidate_chunks:
            return []

        STOP_WORDS = {"tell", "about", "the", "what", "is", "are", "a", "an", "of", "in", "for", "and", "or", "to", "with", "on", "at", "from", "by", "my", "your", "show", "me", "can", "you", "please", "give", "list", "info", "details", "does", "do", "did", "how", "why", "which"}
        q_terms = [re.sub(r'[^a-zA-Z0-9]', '', w.lower()) for w in question.split() if re.sub(r'[^a-zA-Z0-9]', '', w.lower()) not in STOP_WORDS and len(re.sub(r'[^a-zA-Z0-9]', '', w.lower())) >= 2 and not re.sub(r'[^a-zA-Z0-9]', '', w.lower()).isdigit()]

        if not q_terms:
            return candidate_chunks

        filtered = []
        for chunk in candidate_chunks:
            content_lower = chunk.get("content", "").lower()
            words = set(re.findall(r'\b[a-zA-Z0-9]+\b', content_lower))
            
            term_matches = 0
            for term in q_terms:
                if term in words or any(w.startswith(term[:4]) for w in words if len(term) >= 4 and len(w) >= 4):
                    term_matches += 1

            similarity = chunk.get("similarity", 0.0)

            # Keep chunk if terms match, similarity is sufficient, or if chunk is part of parent section expansion
            if term_matches > 0 or similarity >= 0.5:
                filtered.append(chunk)

        return filtered if filtered else candidate_chunks[:3]

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
