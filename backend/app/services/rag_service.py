import difflib
import logging
import math
import re
import uuid
from typing import Any, Dict, List, Tuple

from app.core.config import settings
from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.schemas.chat import ChatMessageResponse, Citation, ComparisonResponse
from app.services.agents.answer_agent import AnswerIntelligenceAgent
from app.services.agents.assembly_agent import EvidenceAssemblyAgent
from app.services.agents.document_agent import DocumentIntelligenceAgent
from app.services.agents.query_agent import (QueryIntelligenceAgent,
                                             StructuredQuery)
from app.services.agents.retrieval_agent import RetrievalIntelligenceAgent
from app.services.agents.validation_agent import EvidenceValidationAgent
from app.services.llm_service import (CLEAN_WORD_RE, NOISE_SECTION_MARKERS,
                                      SECTION_KEYWORD_EXPANSIONS, STOP_WORDS,
                                      TOKEN_RE, LLMService,
                                      chunk_contains_target_entity,
                                      extract_target_numbered_entity,
                                      get_clean_q_terms, term_matches_words)

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
        self.query_agent = QueryIntelligenceAgent()
        self.document_agent = DocumentIntelligenceAgent()
        self.retrieval_agent = RetrievalIntelligenceAgent()
        self.assembly_agent = EvidenceAssemblyAgent()
        self.validation_agent = EvidenceValidationAgent()
        self.answer_agent = AnswerIntelligenceAgent(self.llm)

    def query_workspace(
        self,
        workspace_id: str,
        question: str,
        session_id: str = None,
        show_sources: bool = True
    ) -> ChatMessageResponse:
        """Retrieves evidence and generates a grounded response using Multi-Agent Evidence-Sufficiency Pipeline."""
        if not session_id:
            session_id = str(uuid.uuid4())

        # 1. Agent 1: Query Intelligence
        structured_query = self.query_agent.analyze_query(question)

        # 2. Agent 3: Retrieval Intelligence (Candidate Pool)
        query_vector = self.llm.get_embedding(question)
        candidate_chunks = self.retrieval_agent.retrieve_candidates(
            workspace_id=workspace_id,
            structured_query=structured_query,
            query_vector=query_vector,
            top_k=settings.MAX_RETRIEVAL_CHUNKS
        )

        # 3. Agent 4: Evidence Assembly
        assembly_result = self.assembly_agent.assemble_evidence_context(candidate_chunks)

        # 4. Agent 5: Evidence Validation
        validation_result = self.validation_agent.validate_evidence(
            structured_query=structured_query,
            assembled_chunks=assembly_result["assembled_chunks"],
            attempt=1,
            max_attempts=2
        )

        # 5. Informed Retry / Reformulation Loop if initial evidence check fails
        retry_triggered = False
        if not validation_result.sufficient and validation_result.requires_retry:
            retry_triggered = True
            missing_info = getattr(validation_result, "missing_information", [])
            logger.info(f"Initial evidence validation incomplete (Missing: {missing_info}). Triggering Query Reformulation & Retry step.")
            reformulated_query = self.query_agent.reformulate_query(structured_query, attempt=2, missing_info=missing_info)
            retry_candidates = self.retrieval_agent.retrieve_candidates(
                workspace_id=workspace_id,
                structured_query=reformulated_query,
                query_vector=query_vector,
                top_k=settings.MAX_RETRIEVAL_CHUNKS
            )
            assembly_result = self.assembly_agent.assemble_evidence_context(retry_candidates)
            validation_result = self.validation_agent.validate_evidence(
                structured_query=reformulated_query,
                assembled_chunks=assembly_result["assembled_chunks"],
                attempt=2,
                max_attempts=2
            )

        # 6. Agent 6: Answer Intelligence & Verification
        if not validation_result.sufficient or validation_result.is_abstention or not validation_result.minimal_evidence:
            answer_text = "I couldn't find sufficient evidence in the uploaded documents to answer this question."
            is_grounded = False
            citations = []
        else:
            answer_text, is_grounded, supporting_chunks = self.answer_agent.generate_verified_answer(
                structured_query=structured_query,
                validation_result=validation_result,
                assembled_context_str=assembly_result["context_str"]
            )
            citations = self._build_citations(supporting_chunks) if show_sources and is_grounded else []

        # Comprehensive Behavioral Diagnostic Matrix Logging
        diag_matrix = {
            "original_query": question,
            "structured_query": {
                "intent": structured_query.intent,
                "answer_type": structured_query.answer_type,
                "information_needed": structured_query.information_needed,
                "retrieval_scope": structured_query.retrieval_scope,
                "preferred_sections": structured_query.preferred_sections
            },
            "retrieval_strategy": structured_query.retrieval_strategy,
            "candidate_chunks_count": len(candidate_chunks),
            "selected_evidence_count": len(validation_result.minimal_evidence),
            "validation": {
                "topic_relevant": getattr(validation_result, "topic_relevant", True),
                "answer_supported": getattr(validation_result, "answer_supported", True),
                "sufficient": validation_result.sufficient,
                "missing_information": getattr(validation_result, "missing_information", [])
            },
            "retry_triggered": retry_triggered,
            "final_answer": answer_text,
            "is_grounded": is_grounded,
            "citations": [c.document_name + " Page " + str(c.page_number) for c in citations]
        }

        print("\n================ RAG PIPELINE DIAGNOSTIC MATRIX ================")
        import json
        print(json.dumps(diag_matrix, indent=2))
        print("=================================================================\n")

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

    def _retrieve_chunks(
        self,
        workspace_id: str,
        query_vector: List[float],
        question: str = "",
        query_intent: Any = None,
        top_k: int = 15
    ) -> List[Dict[str, Any]]:
        """Retrieves top-K chunks with Hybrid Search and Parent Section Expansion."""
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

    def _filter_relevant_evidence(
        self,
        question: str,
        candidate_chunks: List[Dict[str, Any]],
        query_intent: Any = None
    ) -> List[Dict[str, Any]]:
        """Stage 2: Structural & Semantic Relevance Filter with Query Intent Awareness."""
        if not candidate_chunks:
            return []

        target_section = getattr(query_intent, "target_section", "any") if query_intent else "any"
        query_type = getattr(query_intent, "query_type", "specific_fact") if query_intent else "specific_fact"

        # 1. Target Section Filtering (Fixes Bug #1: Discards page 27 / reference section for "introduction" queries)
        if target_section and target_section != "any":
            target_sec_lower = target_section.lower()
            section_matching_chunks = []
            for c in candidate_chunks:
                pos = (c.get("document_position") or c.get("metadata", {}).get("document_position") or "").lower()
                p_sec = (c.get("parent_section") or c.get("metadata", {}).get("parent_section") or "").lower()
                s_path = (c.get("section_path") or c.get("metadata", {}).get("section_path") or "").lower()
                content = c.get("content", "").lower()
                page_num = c.get("page_number", 1)

                is_target_pos = pos == target_sec_lower
                is_header_match = target_sec_lower in p_sec or target_sec_lower in s_path
                is_early_intro = (target_sec_lower == "introduction" and page_num <= 3 and "reference" not in pos and "reference" not in p_sec)

                if is_target_pos or is_header_match or is_early_intro:
                    section_matching_chunks.append(c)

            if section_matching_chunks:
                candidate_chunks = section_matching_chunks

        # 2. Visual Analysis / Table / Chart Filtering (Fixes Bug #6)
        if query_type == "visual_analysis" or any(k in question.lower() for k in ["table", "figure", "fig", "chart", "diagram"]):
            visual_chunks = [
                c for c in candidate_chunks
                if c.get("content_type") in ("table", "figure_caption")
                or c.get("chunk_type") in ("table", "figure_caption")
                or "table" in c.get("content", "").lower()[:100]
                or "figure" in c.get("content", "").lower()[:100]
            ]
            if visual_chunks:
                candidate_chunks = visual_chunks

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
