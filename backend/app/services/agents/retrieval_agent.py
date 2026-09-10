import logging
import math
import re
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.db.supabase_client import _in_memory_db, get_supabase_client
from app.services.agents.query_agent import StructuredQuery
from app.services.llm_service import (NOISE_SECTION_MARKERS,
                                      SECTION_KEYWORD_EXPANSIONS, STOP_WORDS,
                                      TOKEN_RE, chunk_contains_target_entity,
                                      extract_target_numbered_entity,
                                      term_matches_words)

logger = logging.getLogger("docmind")

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

class RetrievalIntelligenceAgent:
    """Agent 3: Retrieval Intelligence Agent.
    Responsible ONLY for candidate retrieval, hybrid search, reranking, section-aware filtering,
    and retrieving evidence candidates based on StructuredQuery.
    Answers: 'What evidence should I retrieve for this particular question?'
    """

    def retrieve_candidates(
        self,
        workspace_id: str,
        structured_query: StructuredQuery,
        query_vector: List[float],
        top_k: int = 15,
        access_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves candidate evidence chunks using hybrid search, structural boost, and section filtering from Supabase."""
        question = structured_query.original_query
        client = get_supabase_client(access_token)
        raw_candidates = []

        # Map document filenames for citation rendering
        doc_filename_map: Dict[str, str] = {
            d_id: d_rec.get("filename", "Document")
            for d_id, d_rec in _in_memory_db.documents.items()
        }

        if client:
            try:
                doc_res = client.table("documents").select("id, filename").eq("workspace_id", workspace_id).execute()
                if doc_res.data:
                    for d in doc_res.data:
                        doc_filename_map[d["id"]] = d["filename"]
            except Exception as d_err:
                logger.warning(f"Failed to fetch document names for workspace {workspace_id}: {d_err}")


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
                        chunk["filename"] = doc_filename_map.get(doc_id, _in_memory_db.documents.get(doc_id, {}).get("filename", "Document"))
                    raw_candidates = response.data
            except Exception as e:
                logger.warning(f"Supabase RPC search failed: {e}. Falling back to table search.")

        if not raw_candidates:
            workspace_chunks = []
            if client:
                try:
                    res_db = client.table("document_chunks").select("*").eq("workspace_id", workspace_id).execute()
                    if res_db.data:
                        workspace_chunks = res_db.data
                except Exception as ex:
                    logger.warning(f"Supabase table search failed: {ex}")

            if not workspace_chunks:
                workspace_chunks = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]

            if not workspace_chunks:
                return []

            for chunk in workspace_chunks:
                doc_id = chunk.get("document_id")
                chunk["filename"] = chunk.get("filename") or doc_filename_map.get(doc_id) or _in_memory_db.documents.get(doc_id, {}).get("filename", "Document")

            # Build query term tokens from information_needed and dynamic_query_variations
            var_text = " ".join(structured_query.dynamic_query_variations) if structured_query.dynamic_query_variations else question
            q_terms = [w for w in TOKEN_RE.findall(var_text.lower()) if w not in STOP_WORDS]

            scored_chunks = []
            for chunk in workspace_chunks:
                chunk_vec = chunk.get("embedding", [])
                score = cosine_similarity(query_vector, chunk_vec) if chunk_vec else 0.0

                if not chunk_vec or score < 0.15:
                    content_lower = chunk.get("content", "").lower()
                    words = set(TOKEN_RE.findall(content_lower))
                    matches = sum(1 for term in q_terms if term_matches_words(term, words, content_lower))
                    rescue_score = min(0.6, matches * 0.15)
                    score = max(score, rescue_score)

                scored_chunk = dict(chunk)
                scored_chunk["similarity"] = score
                scored_chunks.append(scored_chunk)

            scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
            raw_candidates = scored_chunks[:top_k]

        # 1. Document Overview Scope Candidate Assembly
        if structured_query.retrieval_scope == "DOCUMENT_LEVEL" or structured_query.intent == "DOCUMENT_OVERVIEW" or structured_query.answer_type == "OVERVIEW":
            workspace_all = []
            if client:
                try:
                    res_all = client.table("document_chunks").select("*").eq("workspace_id", workspace_id).execute()
                    if res_all.data:
                        workspace_all = res_all.data
                except Exception as ex:
                    logger.warning(f"Document overview fetch failed: {ex}")
            if not workspace_all:
                workspace_all = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]

            if workspace_all:
                workspace_all.sort(key=lambda x: (x.get("page_number", 1), x.get("id", "")))
                non_noise = [
                    c for c in workspace_all
                    if not any(r in (c.get("parent_section") or "").lower() or r in (c.get("section_path") or "").lower() for r in NOISE_SECTION_MARKERS)
                ]
                if not non_noise:
                    non_noise = workspace_all

                selected = []
                seen_ids = set()

                # Prioritize Page 1 header and Abstract / Introduction chunks
                for c in non_noise:
                    pos = (c.get("document_position") or "").lower()
                    sec = (c.get("parent_section") or c.get("section_path") or "").lower()
                    page = c.get("page_number", 1)
                    if page <= 2 or "abstract" in sec or "intro" in pos or "intro" in sec or "overview" in sec:
                        c_copy = dict(c)
                        c_copy["filename"] = doc_filename_map.get(c.get("document_id"), "Document")
                        selected.append(c_copy)
                        seen_ids.add(c.get("id"))
                    if len(selected) >= 4:
                        break

                for c in raw_candidates:
                    if c.get("id") not in seen_ids:
                        selected.append(c)
                        seen_ids.add(c.get("id"))

                return selected[:top_k]

        # 2. Section & Intent-Aware Candidate Reranking
        reranked = []
        target_sections = [s.lower() for s in structured_query.preferred_sections]

        for chunk in raw_candidates:
            sim = chunk.get("similarity", 0.5)
            pos = (chunk.get("document_position") or chunk.get("metadata", {}).get("document_position") or "").lower()
            p_sec = (chunk.get("parent_section") or chunk.get("metadata", {}).get("parent_section") or "").lower()
            s_path = (chunk.get("section_path") or chunk.get("metadata", {}).get("section_path") or "").lower()

            hybrid_score = sim

            # Secondary metadata signal: slight boost for section alignment
            if target_sections and any(ts in pos or ts in p_sec or ts in s_path for ts in target_sections):
                hybrid_score += 0.10

            # Secondary metadata signal: visual tables/figures for visual intent
            if structured_query.intent == "VISUAL_ANALYSIS" and (chunk.get("content_type") in ("table", "figure_caption") or chunk.get("chunk_type") in ("table", "figure_caption")):
                hybrid_score += 0.10

            # Secondary metadata signal: reduce reference noise unless specifically asked for
            c_type = (chunk.get("content_type") or chunk.get("chunk_type") or "").lower()
            if "reference" in pos or "reference" in p_sec or "bibliography" in p_sec or c_type == "reference":
                if target_sections and not any("ref" in ts for ts in target_sections):
                    hybrid_score -= 0.30

            chunk_copy = dict(chunk)
            chunk_copy["hybrid_score"] = hybrid_score
            reranked.append(chunk_copy)

        reranked.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return reranked[:top_k]

