import difflib
import logging
import math
import uuid
import re
from typing import List, Dict, Any, Tuple
from app.services.llm_service import (
    LLMService,
    STOP_WORDS,
    NOISE_SECTION_MARKERS,
    SECTION_KEYWORD_EXPANSIONS,
    CLEAN_WORD_RE,
    TOKEN_RE,
    term_matches_words,
    extract_target_numbered_entity,
    chunk_contains_target_entity,
    get_clean_q_terms
)
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

        # Diagnostic Trajectory Logger
        query_scope = self.llm._classify_query_scope(question)
        final_evidence = self.llm._select_minimal_evidence(question, query_scope, relevant_chunks)

        print("\n================ RAG PIPELINE DIAGNOSTICS ================")
        print(f"QUESTION: {question} (Scope: {query_scope})")
        print(f"RAW RETRIEVAL: {len(candidate_chunks)} candidate chunks retrieved")
        print(f"FILTERED EVIDENCE: {len(relevant_chunks)} relevant chunks after Stage 2 filter")
        print(f"FINAL EVIDENCE: {len(final_evidence)} selected minimal chunks for scope {query_scope}")
        context_preview = "\n---\n".join([c.get("content", "")[:120] for c in final_evidence])
        print(f"CONTEXT SENT TO LLM:\n{context_preview}")
        print(f"RAW LLM OUTPUT:\n{answer_text}")
        print(f"ANSWER VALIDATION: evidence_grounded={is_grounded}, answer_relevant={is_grounded}, citation_supported={bool(citations)}")
        print(f"FINAL ANSWER:\n{answer_text}")
        print(f"CITATIONS: {[c.document_name + ' Page ' + str(c.page_number) for c in citations]}")
        print("==========================================================\n")

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

            q_terms = get_clean_q_terms(question)

            scored_chunks = []
            for chunk in workspace_chunks:
                chunk_vec = chunk.get("embedding", [])
                score = cosine_similarity(query_vector, chunk_vec) if chunk_vec else 0.0
                
                content_lower = chunk.get("content", "").lower()
                words = set(TOKEN_RE.findall(content_lower))
                
                has_match = False
                for term in q_terms:
                    if term_matches_words(term, words):
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

        query_scope = self.llm._classify_query_scope(question)

        if not raw_candidates and query_scope not in ("DOCUMENT_OVERVIEW", "DOCUMENT_META"):
            return []
        if query_scope == "FACT_LOOKUP":
            return raw_candidates[:top_k]

        if query_scope in ("DOCUMENT_OVERVIEW", "DOCUMENT_META"):
            # Fetch representative chunks across the workspace (e.g. Page 1 header/intro, middle, and conclusion)
            workspace_all_chunks = []
            if client:
                try:
                    res_db = client.from_("document_chunks") \
                        .select("*") \
                        .eq("workspace_id", workspace_id) \
                        .execute()
                    if res_db.data:
                        for chunk in res_db.data:
                            doc_id = chunk.get("document_id")
                            doc_rec = _in_memory_db.documents.get(doc_id)
                            if doc_rec:
                                chunk["filename"] = doc_rec.get("filename", "Document")
                        workspace_all_chunks = res_db.data
                except Exception as e:
                    logger.warning(f"Supabase all chunks fetch failed: {e}")

            if not workspace_all_chunks:
                workspace_all_chunks = [dict(c) for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]

            if workspace_all_chunks:
                workspace_all_chunks.sort(key=lambda x: (x.get("page_number", 1), x.get("id", "")))
                non_noise_chunks = [
                    c for c in workspace_all_chunks
                    if not any(r in (c.get("parent_section") or "").lower() or r in (c.get("section_path") or "").lower() for r in NOISE_SECTION_MARKERS)
                ]
                if not non_noise_chunks:
                    non_noise_chunks = workspace_all_chunks

                selected = []
                seen_ids = set()

                # Always prioritize Page 1 chunk(s) containing document title / preamble
                page1_chunks = [c for c in non_noise_chunks if c.get("page_number", 1) == 1]
                for c in page1_chunks[:2]:
                    selected.append(c)
                    seen_ids.add(c.get("id"))

                for c in raw_candidates:
                    c_id = c.get("id")
                    if c_id not in seen_ids:
                        selected.append(c)
                        seen_ids.add(c_id)

                if len(selected) < top_k and len(non_noise_chunks) > len(selected):
                    mid_idx = len(non_noise_chunks) // 2
                    for c in [non_noise_chunks[mid_idx], non_noise_chunks[-1]]:
                        if c.get("id") not in seen_ids:
                            selected.append(c)
                            seen_ids.add(c.get("id"))

                return selected[:top_k]

            return raw_candidates[:top_k]

        # UNIVERSAL PARENT SECTION & NEIGHBORING CONTEXT EXPANSION (for section / category queries)
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
                            first_line = c.get("content", "").split("\n")[0].replace("Section:", "").strip()
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

        query_scope = self.llm._classify_query_scope(question)

        if query_scope in ("DOCUMENT_OVERVIEW", "DOCUMENT_META", "SECTION_QUERY"):
            non_noise = [
                c for c in candidate_chunks
                if not any(r in (c.get("parent_section") or "").lower() or r in (c.get("section_path") or "").lower() or r in c.get("content", "").lower()[:100] for r in NOISE_SECTION_MARKERS)
            ]
            if non_noise:
                candidate_chunks = non_noise

        if query_scope in ("DOCUMENT_OVERVIEW", "DOCUMENT_META"):
            return candidate_chunks[:6]

        target_ent = extract_target_numbered_entity(question)
        if target_ent:
            ent_type, ent_num = target_ent
            exact_chunks = [
                c for c in candidate_chunks
                if chunk_contains_target_entity(c.get("content", ""), ent_type, ent_num)
            ]
            if exact_chunks:
                return exact_chunks[:5]

        q_terms = get_clean_q_terms(question)

        if not q_terms:
            return candidate_chunks[:5]

        expanded_q_terms = list(q_terms)
        for t in q_terms:
            if t.lower() in SECTION_KEYWORD_EXPANSIONS:
                expanded_q_terms.extend(SECTION_KEYWORD_EXPANSIONS[t.lower()])

        # Check if candidate chunks contain direct section header matches for the expanded query terms
        header_matched_chunks = []
        for chunk in candidate_chunks:
            p_sec = (chunk.get("parent_section") or chunk.get("metadata", {}).get("parent_section") or "").lower()
            s_path = (chunk.get("section_path") or chunk.get("metadata", {}).get("section_path") or "").lower()
            if not p_sec and "Section:" in chunk.get("content", ""):
                header = chunk.get("content", "").split("\n")[0].replace("Section:", "").strip()
                p_sec = header.split(">")[0].strip().lower()
                s_path = header.lower()

            words_header = set(re.findall(r'\b[a-zA-Z0-9]+\b', f"{p_sec} {s_path}"))
            if any(term_matches_words(term, words_header) for term in expanded_q_terms):
                header_matched_chunks.append(chunk)

        if header_matched_chunks:
            header_parents = {(c.get("parent_section") or "").lower() for c in header_matched_chunks if c.get("parent_section")}
            filtered = [
                c for c in candidate_chunks
                if (c.get("parent_section") or "").lower() in header_parents
                or any(term_matches_words(t, set(re.findall(r'\b[a-zA-Z0-9]+\b', (c.get("section_path") or "").lower()))) for t in expanded_q_terms)
            ]
            return filtered if filtered else header_matched_chunks

        scored_candidates = []
        for chunk in candidate_chunks:
            content_lower = chunk.get("content", "").lower()
            words = set(re.findall(r'\b[a-zA-Z0-9]+\b', content_lower))

            term_matches = sum(1 for term in expanded_q_terms if term_matches_words(term, words))
            sim = chunk.get("similarity", 0.5)

            if term_matches > 0 or sim >= 0.45:
                scored_candidates.append((term_matches, sim, chunk))

        if scored_candidates:
            scored_candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
            return [item[2] for item in scored_candidates[:5]]

        return candidate_chunks[:3]

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
