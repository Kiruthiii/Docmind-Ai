import logging
import re
from typing import Any, Dict, List, Tuple, Optional

from pydantic import BaseModel, Field

from app.services.agents.query_agent import StructuredQuery
from app.services.llm_service import (STOP_WORDS, TOKEN_RE,
                                      chunk_contains_target_entity,
                                      extract_target_numbered_entity)

logger = logging.getLogger("docmind")

class ValidationResult(BaseModel):
    sufficient: bool
    relevance_score: float
    minimal_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    requires_retry: bool = False
    is_abstention: bool = False
    refusal_reason: str = ""
    topic_relevant: bool = True
    answer_supported: bool = True
    missing_information: List[str] = Field(default_factory=list)
    status: str = "SUPPORTED"  # SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | CONTRADICTED
    confidence: float = 1.0

class EvidenceValidationAgent:
    """Agent 5: Evidence Validation Agent.
    Responsible ONLY for evaluating evidence relevance, completeness, sufficiency, and deciding
    whether enough evidence exists to answer OR if a retry or abstention ("no evidence") is required.
    Evaluates Question-Answerability and Semantic Evidence Support over rigid keyword presence.
    Does NOT invent missing information.
    """

    def validate_evidence(
        self,
        structured_query: StructuredQuery,
        assembled_chunks: List[Dict[str, Any]],
        attempt: int = 1,
        max_attempts: int = 2
    ) -> ValidationResult:
        """Evaluates assembled evidence against StructuredQuery semantically."""
        refusal_phrase = "I couldn't find sufficient evidence in the uploaded documents to answer this question."

        if not assembled_chunks:
            if attempt < max_attempts:
                return ValidationResult(
                    sufficient=False,
                    relevance_score=0.0,
                    minimal_evidence=[],
                    requires_retry=True,
                    is_abstention=False,
                    refusal_reason="No candidate chunks retrieved.",
                    topic_relevant=False,
                    answer_supported=False,
                    missing_information=["candidate evidence chunks"],
                    status="UNSUPPORTED",
                    confidence=0.0
                )
            else:
                return ValidationResult(
                    sufficient=False,
                    relevance_score=0.0,
                    minimal_evidence=[],
                    requires_retry=False,
                    is_abstention=True,
                    refusal_reason=refusal_phrase,
                    topic_relevant=False,
                    answer_supported=False,
                    missing_information=["candidate evidence chunks"],
                    status="UNSUPPORTED",
                    confidence=0.0
                )

        question = structured_query.original_query
        q_low = question.lower()

        # 1. Target Entity Validation (Table 1, Figure 2, Section 3)
        target_ent = extract_target_numbered_entity(question)
        if target_ent:
            ent_type, ent_num = target_ent
            matching_chunks = [
                c for c in assembled_chunks
                if chunk_contains_target_entity(c.get("content", ""), ent_type, ent_num)
            ]
            if matching_chunks:
                return ValidationResult(
                    sufficient=True,
                    relevance_score=0.98,
                    minimal_evidence=matching_chunks[:4],
                    requires_retry=False,
                    is_abstention=False,
                    topic_relevant=True,
                    answer_supported=True,
                    status="SUPPORTED",
                    confidence=0.98
                )
            else:
                if attempt < max_attempts:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.2,
                        minimal_evidence=[],
                        requires_retry=True,
                        is_abstention=False,
                        refusal_reason=f"Target entity {ent_type} {ent_num} not found in retrieved chunks.",
                        topic_relevant=False,
                        answer_supported=False,
                        missing_information=[f"target entity {ent_type} {ent_num}"],
                        status="UNSUPPORTED",
                        confidence=0.2
                    )
                else:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.0,
                        minimal_evidence=[],
                        requires_retry=False,
                        is_abstention=True,
                        refusal_reason=refusal_phrase,
                        topic_relevant=False,
                        answer_supported=False,
                        missing_information=[f"target entity {ent_type} {ent_num}"],
                        status="UNSUPPORTED",
                        confidence=0.0
                    )

        # 2. Section Filtering: Prioritize requested section chunks while retaining other candidate evidence
        target_sections = [s.lower() for s in structured_query.preferred_sections]
        if target_sections and not any(k in q_low for k in ["title", "author", "authors", "published", "publication date"]):
            matched_sec_chunks = []
            other_chunks = []
            for c in assembled_chunks:
                pos = (c.get("document_position") or "").lower()
                sec = (c.get("parent_section") or c.get("section_path") or "").lower()
                c_type = (c.get("content_type") or c.get("chunk_type") or "").lower()
                if c_type == "reference" or pos == "references" or "reference" in sec:
                    if not any("ref" in ts for ts in target_sections):
                        continue
                if any(ts in pos or ts in sec or ts in c.get("content", "").lower() for ts in target_sections):
                    matched_sec_chunks.append(c)
                else:
                    other_chunks.append(c)
            if matched_sec_chunks:
                assembled_chunks = matched_sec_chunks + [c for c in other_chunks if c not in matched_sec_chunks]

        # 3. Special Title / Metadata / Header queries
        if any(k in q_low for k in ["title", "author", "authors", "published", "publication date", "who wrote", "who authored"]):
            header_chunks = [c for c in assembled_chunks if c.get("chunk_type") == "header" or c.get("content_type") == "header" or c.get("page_number", 1) == 1]
            if not header_chunks:
                header_chunks = [c for c in assembled_chunks if c.get("page_number", 1) <= 2]
            if header_chunks:
                return ValidationResult(
                    sufficient=True,
                    relevance_score=0.98,
                    minimal_evidence=header_chunks[:8],
                    requires_retry=False,
                    is_abstention=False,
                    topic_relevant=True,
                    answer_supported=True,
                    status="SUPPORTED",
                    confidence=0.98
                )

        # 4. Semantic Evidence Assessment:
        # Select top semantically relevant chunks as minimal evidence
        top_chunks = sorted(assembled_chunks, key=lambda x: x.get("similarity", x.get("hybrid_score", 0.5)), reverse=True)[:6]

        similarities = [c.get("similarity", c.get("hybrid_score", 0.6)) for c in top_chunks]
        max_sim = max(similarities) if similarities else 0.85

        status_val = "SUPPORTED" if max_sim >= 0.3 else "PARTIALLY_SUPPORTED"

        return ValidationResult(
            sufficient=True,
            relevance_score=max_sim if max_sim > 0 else 0.85,
            minimal_evidence=top_chunks,
            requires_retry=False,
            is_abstention=False,
            topic_relevant=True,
            answer_supported=True,
            status=status_val,
            confidence=max_sim if max_sim > 0 else 0.85
        )

