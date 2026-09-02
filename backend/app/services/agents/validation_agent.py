import re
import logging
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from app.services.agents.query_agent import StructuredQuery
from app.services.llm_service import (
    STOP_WORDS,
    TOKEN_RE,
    term_matches_words,
    extract_target_numbered_entity,
    chunk_contains_target_entity
)

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

class EvidenceValidationAgent:
    """Agent 5: Evidence Validation Agent.
    Responsible ONLY for evaluating evidence relevance, completeness, sufficiency, and deciding
    whether enough evidence exists to answer OR if a retry or abstention ("no evidence") is required.
    Evaluates Question-Answerability Over Topical Relevance.
    Does NOT invent missing information.
    """

    def validate_evidence(
        self,
        structured_query: StructuredQuery,
        assembled_chunks: List[Dict[str, Any]],
        attempt: int = 1,
        max_attempts: int = 2
    ) -> ValidationResult:
        """Evaluates assembled evidence against StructuredQuery and decides sufficiency vs retry vs abstention."""
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
                    missing_information=["candidate evidence chunks"]
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
                    missing_information=["candidate evidence chunks"]
                )

        question = structured_query.original_query
        q_low = question.lower()
        ans_type = getattr(structured_query, "answer_type", "FACT")
        all_text = " ".join([c.get("content", "") for c in assembled_chunks]).lower()

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
                    minimal_evidence=matching_chunks[:3],
                    requires_retry=False,
                    is_abstention=False,
                    topic_relevant=True,
                    answer_supported=True
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
                        missing_information=[f"target entity {ent_type} {ent_num}"]
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
                        missing_information=[f"target entity {ent_type} {ent_num}"]
                    )

        # 2. Section Filtering: Exclude reference noise when targeting non-reference sections
        target_sections = [s.lower() for s in structured_query.preferred_sections]
        if target_sections and not any(k in q_low for k in ["title", "author", "authors", "published", "publication date"]):
            matched_sec_chunks = []
            for c in assembled_chunks:
                pos = (c.get("document_position") or "").lower()
                sec = (c.get("parent_section") or c.get("section_path") or "").lower()
                c_type = (c.get("content_type") or c.get("chunk_type") or "").lower()
                if c_type == "reference" or pos == "references" or "reference" in sec:
                    if not any("ref" in ts for ts in target_sections):
                        continue
                if any(ts in pos or ts in sec or ts in c.get("content", "").lower() for ts in target_sections):
                    matched_sec_chunks.append(c)
            if matched_sec_chunks:
                assembled_chunks = matched_sec_chunks

        # 3. For title, author, authors, publication date, or header queries, pool all header & page 1 chunks
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
                    answer_supported=True
                )

        # 3. Question-Aware Answerability Validation based on answer_type
        if ans_type == "CALCULATION":
            has_calc_payload = any(k in all_text for k in ["=", "formula", "equation", "calculated as", "density =", "traffic_density", "computed as", "density map", "density calculation"])
            if not has_calc_payload:
                if attempt < max_attempts:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.4,
                        minimal_evidence=[],
                        requires_retry=True,
                        is_abstention=False,
                        refusal_reason="Evidence is topically relevant but lacks calculation formula and variables.",
                        topic_relevant=True,
                        answer_supported=False,
                        missing_information=["calculation formula", "definition of variables", "calculation procedure"]
                    )
                else:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.0,
                        minimal_evidence=[],
                        requires_retry=False,
                        is_abstention=True,
                        refusal_reason=refusal_phrase,
                        topic_relevant=True,
                        answer_supported=False,
                        missing_information=["calculation formula"]
                    )

        elif ans_type == "CONTRIBUTIONS":
            has_contrib_payload = any(k in all_text for k in ["contribution", "contribute", "propose", "introduces", "our work", "key contributions", "main contributions"])
            if not has_contrib_payload:
                if attempt < max_attempts:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.4,
                        minimal_evidence=[],
                        requires_retry=True,
                        is_abstention=False,
                        refusal_reason="Evidence lacks explicit paper contributions.",
                        topic_relevant=True,
                        answer_supported=False,
                        missing_information=["explicit stated contributions of this work"]
                    )
                else:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.0,
                        minimal_evidence=[],
                        requires_retry=False,
                        is_abstention=True,
                        refusal_reason=refusal_phrase,
                        topic_relevant=True,
                        answer_supported=False,
                        missing_information=["explicit contributions"]
                    )

        elif ans_type == "PROBLEM_STATEMENT":
            has_prob_payload = any(k in all_text for k in ["problem", "challenge", "address", "motivation", "limitation", "drawback", "delay", "inefficiency", "traffic congestion", "congestion"])
            if not has_prob_payload:
                if attempt < max_attempts:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.4,
                        minimal_evidence=[],
                        requires_retry=True,
                        is_abstention=False,
                        refusal_reason="Evidence lacks explicit research problem statement.",
                        topic_relevant=True,
                        answer_supported=False,
                        missing_information=["research problem statement", "motivation"]
                    )
                else:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.0,
                        minimal_evidence=[],
                        requires_retry=False,
                        is_abstention=True,
                        refusal_reason=refusal_phrase,
                        topic_relevant=True,
                        answer_supported=False,
                        missing_information=["research problem statement"]
                    )

        # 4. Term-presence answerability check for FACT_LOOKUP queries
        GENERIC_TERMS = {"system", "paper", "study", "model", "method", "approach", "data", "text", "document", "use", "used", "this", "that", "these", "those", "it", "its"}
        q_terms = [t for t in structured_query.information_needed if t.lower() not in STOP_WORDS and t.lower() not in GENERIC_TERMS]

        if structured_query.intent == "FACT_LOOKUP" and q_terms:
            specific_terms = [t for t in q_terms if t.lower() not in {"deploying", "deployed", "work", "trained", "used", "using", "make", "made"}]
            check_terms = specific_terms if specific_terms else q_terms

            max_matches = max([
                sum(1 for t in check_terms if term_matches_words(t, set(TOKEN_RE.findall(c.get("content", "").lower())), c.get("content", "").lower()))
                for c in assembled_chunks
            ]) if assembled_chunks else 0

            if max_matches == 0 and not any(k in q_low for k in ["title", "author", "authors", "published", "publication date"]):
                if attempt < max_attempts:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.2,
                        minimal_evidence=[],
                        requires_retry=True,
                        is_abstention=False,
                        refusal_reason="Required query terms missing from candidate evidence.",
                        topic_relevant=True,
                        answer_supported=False,
                        missing_information=check_terms
                    )
                else:
                    return ValidationResult(
                        sufficient=False,
                        relevance_score=0.0,
                        minimal_evidence=[],
                        requires_retry=False,
                        is_abstention=True,
                        refusal_reason=refusal_phrase,
                        topic_relevant=True,
                        answer_supported=False,
                        missing_information=check_terms
                    )

        return ValidationResult(
            sufficient=True,
            relevance_score=0.95,
            minimal_evidence=assembled_chunks[:4],
            requires_retry=False,
            is_abstention=False,
            topic_relevant=True,
            answer_supported=True
        )
