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

def _parse_float_vector(vec: Any) -> List[float]:
    if not vec:
        return []
    if isinstance(vec, str):
        try:
            import json
            vec = json.loads(vec)
        except Exception:
            return []
    if isinstance(vec, (list, tuple)):
        parsed = []
        for x in vec:
            try:
                parsed.append(float(x))
            except (ValueError, TypeError):
                continue
        return parsed
    return []

def cosine_similarity(vec1: Any, vec2: Any) -> float:
    v1 = _parse_float_vector(vec1)
    v2 = _parse_float_vector(vec2)
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
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
        access_token: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves candidate evidence chunks using hybrid search, structural boost, and section filtering from Supabase."""
        question = structured_query.original_query
        client = get_supabase_client(access_token)
        raw_candidates = []

        if document_id and not document_ids:
            document_ids = [document_id]

        allowed_doc_ids = set(str(d) for d in document_ids) if document_ids else None

        # Map full document metadata for citation rendering and QA context injection
        doc_meta_map: Dict[str, Dict[str, Any]] = {
            d_id: {
                "filename": d_rec.get("filename", "Document"),
                "document_category": d_rec.get("document_category", "General"),
                "document_type": d_rec.get("document_type", "General Document"),
                "document_type_confidence": d_rec.get("document_type_confidence", 0.5),
                "classification_method": d_rec.get("classification_method", "default"),
                "evidence": d_rec.get("evidence", [])
            }
            for d_id, d_rec in _in_memory_db.documents.items()
        }

        if client:
            try:
                doc_res = client.table("documents").select("id, filename, document_category, document_type, document_type_confidence, classification_method").eq("workspace_id", workspace_id).execute()
                if doc_res.data:
                    for d in doc_res.data:
                        doc_meta_map[d["id"]] = {
                            "filename": d.get("filename", "Document"),
                            "document_category": d.get("document_category", "General"),
                            "document_type": d.get("document_type", "General Document"),
                            "document_type_confidence": d.get("document_type_confidence", 0.5),
                            "classification_method": d.get("classification_method", "default"),
                            "evidence": d.get("evidence", [])
                        }
            except Exception as d_err:
                logger.warning(f"Failed to fetch full document metadata for workspace {workspace_id}: {d_err}")
                try:
                    doc_res = client.table("documents").select("id, filename, document_type, document_type_confidence, classification_method").eq("workspace_id", workspace_id).execute()
                    if doc_res.data:
                        for d in doc_res.data:
                            doc_meta_map[d["id"]] = {
                                "filename": d.get("filename", "Document"),
                                "document_category": "General",
                                "document_type": d.get("document_type", "General Document"),
                                "document_type_confidence": d.get("document_type_confidence", 0.5),
                                "classification_method": d.get("classification_method", "default"),
                                "evidence": []
                            }
                except Exception as d_retry_err:
                    logger.warning(f"Fallback fetch document names failed: {d_retry_err}")
                    try:
                        doc_res = client.table("documents").select("id, filename").eq("workspace_id", workspace_id).execute()
                        if doc_res.data:
                            for d in doc_res.data:
                                doc_meta_map[d["id"]] = {
                                    "filename": d.get("filename", "Document"),
                                    "document_category": "General",
                                    "document_type": "General Document",
                                    "document_type_confidence": 0.5,
                                    "classification_method": "default",
                                    "evidence": []
                                }
                    except Exception as d_basic_err:
                        logger.warning(f"Basic document fetch failed: {d_basic_err}")

        def _enrich_chunk_with_doc_meta(chunk_dict: Dict[str, Any]) -> Dict[str, Any]:
            doc_id = chunk_dict.get("document_id")
            meta = doc_meta_map.get(doc_id, _in_memory_db.documents.get(doc_id, {}))
            c_copy = dict(chunk_dict)
            c_copy["filename"] = meta.get("filename", "Document")
            c_copy["document_category"] = meta.get("document_category", "General")
            c_copy["document_type"] = meta.get("document_type", "General Document")
            c_copy["document_type_confidence"] = meta.get("document_type_confidence", 0.5)
            c_copy["classification_method"] = meta.get("classification_method", "default")
            c_copy["evidence"] = meta.get("evidence", [])
            return c_copy

        if client:
            try:
                rpc_count = top_k * 10 if allowed_doc_ids else top_k
                response = client.rpc(
                    "match_document_chunks",
                    {
                        "query_embedding": query_vector,
                        "match_threshold": settings.SIMILARITY_THRESHOLD,
                        "match_count": rpc_count,
                        "filter_workspace_id": workspace_id
                    }
                ).execute()

                if response.data:
                    raw = [_enrich_chunk_with_doc_meta(chunk) for chunk in response.data]
                    if allowed_doc_ids:
                        raw = [c for c in raw if str(c.get("document_id")) in allowed_doc_ids]
                    raw_candidates = raw[:top_k]
            except Exception as e:
                logger.warning(f"Supabase RPC search failed: {e}. Falling back to table search.")

        if not raw_candidates:
            workspace_chunks = []
            if client:
                try:
                    query = client.table("document_chunks").select("*").eq("workspace_id", workspace_id)
                    if document_ids:
                        if len(document_ids) == 1:
                            query = query.eq("document_id", document_ids[0])
                        else:
                            query = query.in_("document_id", document_ids)
                    res_db = query.execute()
                    if res_db.data:
                        workspace_chunks = res_db.data
                except Exception as ex:
                    logger.warning(f"Supabase table search failed: {ex}")

            if not workspace_chunks:
                workspace_chunks = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]
                if allowed_doc_ids:
                    workspace_chunks = [c for c in workspace_chunks if str(c.get("document_id")) in allowed_doc_ids]

            if not workspace_chunks and client:
                try:
                    doc_query = client.table("documents").select("id, filename, storage_path").eq("workspace_id", workspace_id)
                    if document_ids:
                        if len(document_ids) == 1:
                            doc_query = doc_query.eq("id", document_ids[0])
                        else:
                            doc_query = doc_query.in_("id", document_ids)
                    doc_records = doc_query.execute().data or []
                    for d_rec in doc_records:
                        d_id = d_rec["id"]
                        s_path = d_rec.get("storage_path")
                        f_name = d_rec.get("filename", "document.pdf")
                        if s_path:
                            try:
                                pdf_data = client.storage.from_("documents").download(s_path)
                                if pdf_data:
                                    from app.services.ingestion_service import (
                                        IngestionService,)
                                    reindexed = IngestionService().reindex_existing_document(
                                        doc_id=d_id,
                                        workspace_id=workspace_id,
                                        filename=f_name,
                                        pdf_bytes=pdf_data,
                                        storage_path=s_path,
                                        access_token=access_token
                                    )
                                    if reindexed:
                                        workspace_chunks.extend(reindexed)
                            except Exception as s_err:
                                logger.warning(f"Could not auto-download PDF {s_path} for reindexing: {s_err}")
                except Exception as auto_err:
                    logger.warning(f"Auto-healing chunk reindexing failed: {auto_err}")

            if not workspace_chunks:
                return []

            workspace_chunks = [_enrich_chunk_with_doc_meta(c) for c in workspace_chunks]

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
                    query = client.table("document_chunks").select("*").eq("workspace_id", workspace_id)
                    if document_ids:
                        if len(document_ids) == 1:
                            query = query.eq("document_id", document_ids[0])
                        else:
                            query = query.in_("document_id", document_ids)
                    res_all = query.execute()
                    if res_all.data:
                        workspace_all = res_all.data
                except Exception as ex:
                    logger.warning(f"Document overview fetch failed: {ex}")
            if not workspace_all:
                workspace_all = [c for c in _in_memory_db.document_chunks if c.get("workspace_id") == workspace_id]
                if allowed_doc_ids:
                    workspace_all = [c for c in workspace_all if str(c.get("document_id")) in allowed_doc_ids]

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

                # Step 1: Prioritize Page 1-3, TOC, Abstract, Intro, Overview chunks
                for c in non_noise:
                    pos = (c.get("document_position") or "").lower()
                    sec = (c.get("parent_section") or c.get("section_path") or "").lower()
                    c_type = (c.get("content_type") or c.get("chunk_type") or "").lower()
                    page = c.get("page_number", 1)
                    if page <= 3 or "contents" in sec or "toc" in pos or "abstract" in sec or "intro" in pos or "intro" in sec or "overview" in sec or c_type == "header":
                        if c.get("id") not in seen_ids:
                            selected.append(_enrich_chunk_with_doc_meta(c))
                            seen_ids.add(c.get("id"))
                    if len(selected) >= 6:
                        break

                # Step 2: Sample representative chunks evenly across the document
                total_chunks = len(non_noise)
                if total_chunks > 4 and len(selected) < top_k:
                    step = max(1, total_chunks // 6)
                    for i in range(0, total_chunks, step):
                        c = non_noise[i]
                        if c.get("id") not in seen_ids:
                            selected.append(_enrich_chunk_with_doc_meta(c))
                            seen_ids.add(c.get("id"))
                        if len(selected) >= top_k:
                            break

                # Step 3: Fill with raw vector search candidates
                for c in raw_candidates:
                    if c.get("id") not in seen_ids:
                        selected.append(_enrich_chunk_with_doc_meta(c))
                        seen_ids.add(c.get("id"))
                    if len(selected) >= top_k:
                        break

                if selected:
                    return selected[:top_k]

        # 2. Section & Intent-Aware Candidate Reranking
        reranked = []
        target_sections = [s.lower() for s in structured_query.preferred_sections]
        var_text = " ".join(structured_query.dynamic_query_variations) if structured_query.dynamic_query_variations else question
        q_terms = [w for w in TOKEN_RE.findall(var_text.lower()) if w not in STOP_WORDS]

        for chunk in raw_candidates:
            sim = chunk.get("similarity", 0.5)
            content_lower = (chunk.get("content") or "").lower()
            words = set(TOKEN_RE.findall(content_lower))

            pos = (chunk.get("document_position") or chunk.get("metadata", {}).get("document_position") or "").lower()
            p_sec = (chunk.get("parent_section") or chunk.get("metadata", {}).get("parent_section") or "").lower()
            s_path = (chunk.get("section_path") or chunk.get("metadata", {}).get("section_path") or "").lower()

            # Lexical BM25 term overlap calculation
            matches = sum(1 for term in q_terms if term_matches_words(term, words, content_lower)) if q_terms else 0
            term_score = min(0.35, matches * 0.08)

            # Exact phrase match bonus
            exact_phrase_bonus = 0.15 if question.lower() in content_lower and len(question.strip()) > 5 else 0.0

            hybrid_score = (sim * 0.55) + (term_score * 0.30) + exact_phrase_bonus

            # Secondary metadata signal: boost for section alignment
            if target_sections and any(ts in pos or ts in p_sec or ts in s_path for ts in target_sections):
                hybrid_score += 0.15

            # Secondary metadata signal: visual tables/figures for visual intent
            if structured_query.intent == "VISUAL_ANALYSIS" and (chunk.get("content_type") in ("table", "figure_caption") or chunk.get("chunk_type") in ("table", "figure_caption")):
                hybrid_score += 0.15

            # Secondary metadata signal: reduce reference noise unless specifically asked for
            c_type = (chunk.get("content_type") or chunk.get("chunk_type") or "").lower()
            if "reference" in pos or "reference" in p_sec or "bibliography" in p_sec or c_type == "reference":
                if target_sections and not any("ref" in ts for ts in target_sections):
                    hybrid_score -= 0.30

            chunk_copy = dict(chunk)
            chunk_copy["hybrid_score"] = round(hybrid_score, 4)
            reranked.append(chunk_copy)

        reranked.sort(key=lambda x: x["hybrid_score"], reverse=True)
        return reranked[:top_k]

