import logging
from typing import Any, Dict, List, Optional
from app.schemas.document_types import DocumentClassificationResult, DocumentTypeEnum
from app.services.heuristic_classifier import classify_by_heuristics
from app.services.llm_service import LLMService

logger = logging.getLogger("docmind")


class DocumentIntelligenceAgent:
    """Agent 2: Document Intelligence Agent.
    Responsible for understanding PDF structure, section hierarchy, page metadata,
    content types, and performing automated document type classification.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    def classify_document(self, chunks: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """
        Orchestrates 3-tiered hierarchical document classification with Strategic Multi-Chunk Sampling:
        1. Primary: Hierarchical LLM classification via Gemini AI
        2. Fallback: Generic weighted heuristic classifier
        3. Safe Default: 'General' / 'General Document'
        Never raises exceptions to break ingestion.
        """
        logger.info(f"Document classification started for file '{filename}' ({len(chunks)} chunks)")

        # Strategic Multi-Chunk Sampling (Filename + Title + First Page + Headings + Middle Chunk + Last Page)
        sample_parts = [f"Filename: {filename}"]

        if chunks:
            # First chunk (Page 1 / Title / Preamble)
            first_content = str(chunks[0].get("content", "")).strip()
            if first_content:
                sample_parts.append(f"[First Page / Header]\n{first_content[:1000]}")

            # Section headings collected across document
            collected_sections = []
            for c in chunks:
                sec = c.get("parent_section") or c.get("section_path")
                if sec and str(sec) not in collected_sections:
                    collected_sections.append(str(sec))
            if collected_sections:
                sample_parts.append(f"[Document Headings]: {', '.join(collected_sections[:10])}")

            # Middle chunk (Body content / Methodology / Purpose)
            if len(chunks) > 3:
                mid_idx = len(chunks) // 2
                mid_content = str(chunks[mid_idx].get("content", "")).strip()
                if mid_content:
                    sample_parts.append(f"[Body Sample - Page {chunks[mid_idx].get('page_number', 1)}]\n{mid_content[:800]}")

            # Last chunk (Conclusions / References / Billing Terms)
            if len(chunks) > 4:
                last_content = str(chunks[-1].get("content", "")).strip()
                if last_content:
                    sample_parts.append(f"[End Sample - Page {chunks[-1].get('page_number', 1)}]\n{last_content[:600]}")

        text_sample = "\n\n".join(sample_parts)[:3500]

        # 1. Primary Method: LLM Classification
        try:
            llm_result = self.llm.classify_document_type(text_sample, filename)
            if llm_result and llm_result.get("document_type"):
                logger.info(f"LLM classification succeeded for '{filename}': {llm_result['document_type']} (conf: {llm_result.get('confidence')})")
                return llm_result
        except Exception as e:
            logger.warning(f"LLM classification error for '{filename}': {e}")

        # 2. Fallback Method: Deterministic Weighted Heuristic Classifier
        logger.info(f"LLM classification unavailable/failed for '{filename}'; using heuristic fallback.")
        try:
            heuristic_res = classify_by_heuristics(text_sample, filename, chunks)
            logger.info(f"Heuristic classification completed for '{filename}': {heuristic_res.document_type} (conf: {heuristic_res.confidence})")
            return heuristic_res.model_dump()
        except Exception as e:
            logger.error(f"Heuristic classification error for '{filename}': {e}")

        # 3. Safe Default Fallback
        logger.info(f"Document classification completed with safe default for '{filename}'")
        return {
            "document_category": "General",
            "document_type": DocumentTypeEnum.GENERAL_DOC.value,
            "confidence": 0.5,
            "primary_topics": ["General"],
            "reason": "Default fallback classification",
            "evidence": ["Default fallback classification"],
            "method": "default"
        }

    def analyze_document_structure(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes document structural map from ingested chunks."""
        sections = set()
        positions = set()
        content_types = set()
        page_count = 0

        for chunk in chunks:
            p_num = chunk.get("page_number", 1)
            if p_num > page_count:
                page_count = p_num

            sec = chunk.get("parent_section") or chunk.get("metadata", {}).get("parent_section", "")
            if sec and str(sec).lower() != "general":
                sections.add(str(sec))

            pos = chunk.get("document_position") or chunk.get("metadata", {}).get("document_position", "")
            if pos:
                positions.add(str(pos))

            c_type = chunk.get("content_type") or chunk.get("chunk_type") or "text"
            content_types.add(str(c_type))

        return {
            "total_chunks": len(chunks),
            "page_count": page_count,
            "detected_sections": sorted(list(sections)),
            "detected_positions": sorted(list(positions)),
            "content_types": sorted(list(content_types))
        }

    def filter_chunks_by_document_location(
        self,
        chunks: List[Dict[str, Any]],
        target_sections: List[str] = None,
        target_positions: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Filters or prioritizes chunks based on structural location in document."""
        if not chunks:
            return []

        if not target_sections and not target_positions:
            return chunks

        matching = []
        for c in chunks:
            sec = (c.get("parent_section") or c.get("section_path") or "").lower()
            pos = (c.get("document_position") or c.get("metadata", {}).get("document_position") or "").lower()

            match_sec = any(ts.lower() in sec for ts in target_sections) if target_sections else False
            match_pos = any(tp.lower() == pos for tp in target_positions) if target_positions else False

            if match_sec or match_pos:
                matching.append(c)

        return matching if matching else chunks
