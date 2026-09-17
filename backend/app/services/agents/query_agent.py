import logging
import re
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("docmind")

STOP_WORDS = frozenset({
    "tell", "about", "the", "what", "is", "are", "a", "an", "of", "in", "for", "and", "or",
    "to", "with", "on", "at", "from", "by", "my", "your", "show", "me", "can", "you", "please",
    "give", "list", "info", "details", "does", "do", "did", "how", "why", "which", "this", "that", "these", "those", "it", "its"
})

TOKEN_RE = re.compile(r'\b[a-zA-Z0-9]+\b')

class StructuredQuery(BaseModel):
    original_query: str
    intent: Literal["FACT_LOOKUP", "DOCUMENT_OVERVIEW", "TECHNICAL_EXPLANATION", "METHODOLOGY", "RESULTS", "COMPARISON", "VISUAL_ANALYSIS", "SECTION_QUERY", "NO_EVIDENCE_EXPECTED"]
    answer_type: Literal["OVERVIEW", "PROBLEM_STATEMENT", "CONTRIBUTIONS", "CALCULATION", "METHODOLOGY", "RESULT", "FACT", "DATE", "LIST", "COMPARISON"] = "FACT"
    information_needed: List[str] = Field(default_factory=list)
    dynamic_query_variations: List[str] = Field(default_factory=list)
    retrieval_scope: Literal["LOCAL", "MULTI_CHUNK", "DOCUMENT_LEVEL", "ITERATIVE"] = "LOCAL"
    preferred_sections: List[str] = Field(default_factory=list)
    evidence_requirement: Literal["SINGLE_OR_FEW_CHUNKS", "MULTI_SECTION", "DOCUMENT_OVERVIEW", "VISUAL_TABLE"] = "SINGLE_OR_FEW_CHUNKS"
    retrieval_strategy: Literal["TARGETED", "HYBRID_SECTION", "OVERVIEW", "ITERATIVE_STEP"] = "TARGETED"

class QueryIntelligenceAgent:
    """Agent 1: Query Intelligence Agent.
    Responsible ONLY for query understanding, intent detection, information need extraction, answer_type determination,
    and scope determination.
    """

    def analyze_query(self, question: str) -> StructuredQuery:
        """Transforms natural language question into internal structured representation."""
        if not question or not question.strip():
            return StructuredQuery(
                original_query=question,
                intent="FACT_LOOKUP",
                answer_type="FACT",
                information_needed=[],
                retrieval_scope="LOCAL",
                preferred_sections=[],
                evidence_requirement="SINGLE_OR_FEW_CHUNKS",
                retrieval_strategy="TARGETED"
            )

        q_lower = question.lower().strip()

        # Default query parameters
        intent = "FACT_LOOKUP"
        answer_type = "FACT"
        preferred_sections = []
        scope = "LOCAL"
        requirement = "SINGLE_OR_FEW_CHUNKS"
        strategy = "TARGETED"

        # 1. Answer Type & Intent Detection
        # A. Technical Code & Software Queries
        if re.search(r'\b(?:code|function|class|method|variable|async|await|event\s+loop|api|route|type|object|array|string|scope|closure|promise|module|import|export|syntax)\b', q_lower):
            intent = "TECHNICAL_EXPLANATION"
            answer_type = "METHODOLOGY" if any(k in q_lower for k in ["how", "explain", "work", "implement"]) else "FACT"
            scope = "MULTI_CHUNK"
            requirement = "MULTI_SECTION"
            strategy = "HYBRID_SECTION"
            preferred_sections = ["Code", "Functions", "Implementation", "Syntax", "Overview", "Methodology"]

        # B. Calculation & Formula queries
        elif re.search(r'\b(?:how\s+is|calculate|calculated|computation|formula|equation|metric)\b', q_lower) and any(k in q_lower for k in ["calculated", "computed", "determine", "determined", "formula", "equation", "metric", "rate"]):
            intent = "TECHNICAL_EXPLANATION"
            answer_type = "CALCULATION"
            scope = "LOCAL"
            requirement = "SINGLE_OR_FEW_CHUNKS"
            strategy = "TARGETED"
            preferred_sections = ["Methodology", "Proposed Approach", "Traffic Density", "Calculation", "Evaluation"]

        # C. Contribution queries
        elif re.search(r'\b(?:main|key|our|primary)?\s*contributions?\b|\bwhat\s+does\s+(?:this\s+)?(?:paper|work|study)\s+contribute\b', q_lower):
            intent = "TECHNICAL_EXPLANATION"
            answer_type = "CONTRIBUTIONS"
            scope = "MULTI_CHUNK"
            requirement = "MULTI_SECTION"
            strategy = "HYBRID_SECTION"
            preferred_sections = ["Introduction", "Abstract", "Contributions", "Results", "Conclusion", "Proposed Approach"]

        # D. Problem Statement queries
        elif re.search(r'\b(?:main\s+problem|problem\s+addressed|research\s+problem|motivation|challenges\s+in|what\s+problem\s+does)\b', q_lower):
            intent = "TECHNICAL_EXPLANATION"
            answer_type = "PROBLEM_STATEMENT"
            scope = "MULTI_CHUNK"
            requirement = "MULTI_SECTION"
            strategy = "HYBRID_SECTION"
            preferred_sections = ["Introduction", "Abstract", "Background", "Motivation"]

        # E. Location / Dataset Origin Queries
        elif re.search(r'\b(?:where\s+was|where\s+is|location|collected|city|country|region|site)\b', q_lower) and any(k in q_lower for k in ["dataset", "collected", "data", "where", "location"]):
            intent = "FACT_LOOKUP"
            answer_type = "FACT"
            scope = "LOCAL"
            requirement = "SINGLE_OR_FEW_CHUNKS"
            strategy = "TARGETED"
            preferred_sections = ["Methodology", "Datasets", "Experimental Setup", "Introduction", "Data Collection"]

        # F. Network Diagram & Architecture Pattern Queries
        elif re.search(r'\b(?:architecture|pattern|network\s+diagram|skip\s+connections?|diagram)\b', q_lower):
            intent = "TECHNICAL_EXPLANATION"
            answer_type = "FACT"
            scope = "LOCAL"
            requirement = "SINGLE_OR_FEW_CHUNKS"
            strategy = "TARGETED"
            preferred_sections = ["Architecture", "Methodology", "Proposed Approach", "Network", "Diagram"]

        # G. Document Overview & Document Type / Identity queries
        elif (
            re.search(
                r'\b(?:summarize|summary|overview|abstract|executive\s+summary)\b'
                r'|\b(?:whats|what\s+is|what\'s)\s+in\s+this\b'
                r'|\b(?:tell|explain|show)\s+(?:me\s+)?(?:whats|what\s+is|what\'s)\s+in\s+this\b'
                r'|\bwhat\s+is\s+(?:this\s+)?(?:paper|document|file|pdf)\s+about\b'
                r'|\bwhat\s+does\s+this\s+(?:document|paper|file|pdf)\s+(?:say|contain|cover|discuss)\b'
                r'|\b(?:describe|explain|tell\s+me\s+about)\s+(?:this\s+)?(?:document|file|paper|pdf)\b'
                r'|\b(?:what|which)\s+(?:am\s+i\s+(?:looking\s+at|reading|viewing)|is\s+this|document\s+is\s+this|file\s+is\s+this)\b'
                r'|\b(?:what|which)\s+(?:type|kind|class|category|nature|format)\s+of\s+(?:document|file|paper|text)\b'
                r'|\bis\s+this\s+a\s+(?:academic|research|paper|contract|syllabus|invoice|resume|report|manual|doc)\b',
                q_lower
            )
            or q_lower in ("summarize", "summary", "overview", "whats in this", "what is in this", "what is this document", "what am i looking at", "what is this file", "what am i reading", "what file is this")
            or re.search(r'\bsummarize\b', q_lower)
        ):
            intent = "DOCUMENT_OVERVIEW"
            answer_type = "OVERVIEW"
            scope = "DOCUMENT_LEVEL"
            requirement = "DOCUMENT_OVERVIEW"
            strategy = "OVERVIEW"
            preferred_sections = ["Title", "Abstract", "Introduction", "Conclusion"]
            if "introduction" in q_lower or "intro" in q_lower:
                preferred_sections = ["Introduction"]
            elif "methodology" in q_lower or "method" in q_lower:
                preferred_sections = ["Methodology"]
            elif "results" in q_lower or "result" in q_lower:
                preferred_sections = ["Results"]
            elif "conclusion" in q_lower:
                preferred_sections = ["Conclusion"]

        # H. Resume & Document Section queries (Work Experience, Education, Skills)
        elif any(k in q_lower for k in ["work experience", "experience", "education", "projects", "project", "certificates", "qualifications", "skills"]):
            intent = "SECTION_QUERY"
            answer_type = "LIST"
            scope = "MULTI_CHUNK"
            requirement = "MULTI_SECTION"
            strategy = "HYBRID_SECTION"
            if "experience" in q_lower or "work" in q_lower:
                preferred_sections = ["Work Experience"]
            elif "education" in q_lower:
                preferred_sections = ["Education"]
            elif "skills" in q_lower:
                preferred_sections = ["Skills"]
            elif "project" in q_lower:
                preferred_sections = ["Projects"]

        # I. Author & Contributor Queries
        elif re.search(r'\b(?:who\s+(?:are|is)\s+(?:the\s+)?authors?|who\s+(?:wrote|authored|created)|authors?\s+of|written\s+by|contributors?|list\s+(?:the\s+)?authors)\b', q_lower):
            intent = "DOCUMENT_OVERVIEW"
            answer_type = "LIST"
            scope = "DOCUMENT_LEVEL"
            requirement = "MULTI_SECTION"
            strategy = "OVERVIEW"
            preferred_sections = ["Header", "Title", "Introduction", "Abstract"]

        # J. Document Title, Date, & Metadata Queries
        elif re.search(r'\b(?:what\s+is\s+the\s+title|paper\s+called|title\s+of\s+the\s+paper|paper\s+title|published|publication\s+date|doi)\b', q_lower):
            intent = "DOCUMENT_OVERVIEW"
            answer_type = "DATE" if "published" in q_lower or "date" in q_lower else "FACT"
            scope = "DOCUMENT_LEVEL"
            requirement = "SINGLE_OR_FEW_CHUNKS"
            strategy = "OVERVIEW"
            preferred_sections = ["Header", "Title", "Introduction"]

        # K. Methodology queries
        elif any(k in q_lower for k in ["methodology", "methods", "proposed approach", "how does the", "algorithm work", "pipeline"]):
            intent = "METHODOLOGY"
            answer_type = "METHODOLOGY"
            scope = "MULTI_CHUNK"
            requirement = "MULTI_SECTION"
            strategy = "HYBRID_SECTION"
            preferred_sections = ["Methodology", "Proposed Approach", "System Model"]

        # L. Results queries
        elif any(k in q_lower for k in ["results", "evaluation", "performance", "findings", "accuracy"]):
            intent = "RESULTS"
            answer_type = "RESULT"
            scope = "MULTI_CHUNK"
            requirement = "MULTI_SECTION"
            strategy = "HYBRID_SECTION"
            preferred_sections = ["Results", "Experiments", "Evaluation"]

        # 2. Extract information needed & key terms
        words = TOKEN_RE.findall(question)
        info_needed = [w for w in words if w.lower() not in STOP_WORDS and len(w) >= 2]

        # Preserve question context terms like 'where', 'how' if info_needed is sparse
        if len(info_needed) <= 2:
            for w in words:
                if w.lower() in ("where", "how", "why", "who", "when") and w.lower() not in info_needed:
                    info_needed.append(w.lower())

        # Extract multi-word phrases (proper nouns, camelCase, snake_case)
        phrases = re.findall(r'\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+\b|\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', question)
        for ph in phrases:
            if ph not in info_needed:
                info_needed.append(ph)

        # 3. Dynamic Query Variations Generation
        variations = [question]
        base_keywords = " ".join(info_needed)
        if answer_type == "CALCULATION":
            variations.append(f"{base_keywords} formula equation variables calculation procedure")
        elif answer_type == "CONTRIBUTIONS":
            variations.append(f"{base_keywords} key contributions main contributions results proposed approach latency accuracy")
        elif answer_type == "PROBLEM_STATEMENT":
            variations.append(f"{base_keywords} problem addressed research motivation challenges")
        elif answer_type == "OVERVIEW":
            variations.append(f"{base_keywords} research topic abstract introduction overall purpose document type")
        elif intent == "TECHNICAL_EXPLANATION":
            variations.append(f"{base_keywords} code implementation definition specification function example skip connections architecture")
        elif "where" in q_lower or "location" in q_lower or "collected" in q_lower:
            variations.append(f"{base_keywords} location city region country site collected gathered dataset")
            variations.append(f"{base_keywords} code implementation definition specification function example")

        return StructuredQuery(
            original_query=question,
            intent=intent,
            answer_type=answer_type,
            information_needed=info_needed,
            dynamic_query_variations=variations,
            retrieval_scope=scope,
            preferred_sections=list(set(preferred_sections)),
            evidence_requirement=requirement,
            retrieval_strategy=strategy
        )

    def reformulate_query(self, structured_q: StructuredQuery, attempt: int, missing_info: List[str] = None) -> StructuredQuery:
        """Reformulates structured query for retry retrieval step if initial evidence was insufficient."""
        new_info = list(structured_q.information_needed)
        if missing_info:
            for item in missing_info:
                words = TOKEN_RE.findall(item)
                for w in words:
                    if w.lower() not in STOP_WORDS and w.lower() not in new_info:
                        new_info.append(w.lower())

        new_scope = "MULTI_CHUNK" if structured_q.retrieval_scope == "LOCAL" else structured_q.retrieval_scope
        new_strategy = "HYBRID_SECTION" if structured_q.retrieval_strategy == "TARGETED" else "OVERVIEW"

        variations = list(structured_q.dynamic_query_variations)
        if missing_info:
            variations.append(f"{structured_q.original_query} {' '.join(missing_info)}")

        logger.info(f"QueryIntelligenceAgent reformulating query (Attempt {attempt}): missing {missing_info}")

        return StructuredQuery(
            original_query=structured_q.original_query,
            intent=structured_q.intent,
            answer_type=structured_q.answer_type,
            information_needed=new_info,
            dynamic_query_variations=variations,
            retrieval_scope=new_scope,
            preferred_sections=structured_q.preferred_sections,
            evidence_requirement=structured_q.evidence_requirement,
            retrieval_strategy=new_strategy
        )
