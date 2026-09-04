import logging
import re
from typing import Any, Dict, List, Tuple

from app.services.agents.query_agent import StructuredQuery
from app.services.agents.validation_agent import ValidationResult
from app.services.llm_service import LLMService

logger = logging.getLogger("docmind")

class AnswerIntelligenceAgent:
    """Agent 6: Answer Intelligence & Verification Agent.
    Responsible ONLY for generating adaptive-length answers (concise for simple facts, structured for explanations)
    strictly grounded in validated evidence, followed by Answer Verification.
    Does NOT use pretrained world knowledge or invent facts.
    """

    def __init__(self, llm_service: LLMService = None):
        self.llm = llm_service or LLMService()

    def generate_verified_answer(
        self,
        structured_query: StructuredQuery,
        validation_result: ValidationResult,
        assembled_context_str: str
    ) -> Tuple[str, bool, List[Dict[str, Any]]]:
        """Generates grounded answer and performs Answer Verification."""
        refusal_phrase = "I couldn't find sufficient evidence in the uploaded documents to answer this question."

        if not validation_result.sufficient or validation_result.is_abstention or not validation_result.minimal_evidence:
            return (refusal_phrase, False, [])

        question = structured_query.original_query

        # Delegate answer generation and claim validation to LLM service using validated minimal evidence
        answer_text, is_grounded, supporting_chunks = self.llm.generate_grounded_answer(
            question=question,
            context_chunks=validation_result.minimal_evidence
        )

        if not is_grounded or answer_text == refusal_phrase:
            return (refusal_phrase, False, [])

        # Answer Verification Step: Clean up conversational filler or raw markdown quotes
        verified_answer = self._verify_and_clean_answer(question, answer_text, structured_query)

        return (verified_answer, True, supporting_chunks)

    def _verify_and_clean_answer(self, question: str, answer_text: str, structured_query: StructuredQuery) -> str:
        """Runs Answer Verification to ensure adaptive length and clean formatting."""
        cleaned = answer_text.strip()

        # Remove conversational filler prefix
        FILLER_PREFIXES = [
            "based on the provided context,",
            "based on the provided document,",
            "based on the context,",
            "based on the document,",
            "according to the provided context,",
            "according to the provided document,"
        ]
        for prefix in FILLER_PREFIXES:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                if cleaned:
                    cleaned = cleaned[0].upper() + cleaned[1:]
                break

        # Remove raw chunk quotes like ('### 3,4...') in document_meta responses
        cleaned = re.sub(r"\s*\(\'###[^\']+\'\)", "", cleaned)
        cleaned = re.sub(r"\s*\(\'Section:[^\']+\'\)", "", cleaned)

        q_lower = question.lower()

        # Exact Answer Selection for Title queries
        if any(k in q_lower for k in ["title", "paper called", "name of this paper"]):
            lines = [l.strip() for l in cleaned.split("\n") if l.strip()]
            for l in lines:
                l_low = l.lower()
                if not any(k in l_low for k in ["structured as follows", "infineon", "grant", "approved", "volume", "journal"]):
                    if len(l) > 15:
                        cleaned = l
                        break

        # Exact Answer Selection for Publication Date queries
        elif any(k in q_lower for k in ["published", "publication date", "when was"]):
            date_m = re.search(r'\b(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}|\d{4})\b', cleaned, re.IGNORECASE)
            if date_m and not any(k in cleaned.lower() for k in ["supported by", "grant", "university"]):
                cleaned = f"The paper was published on {date_m.group(1)}."

        return cleaned
