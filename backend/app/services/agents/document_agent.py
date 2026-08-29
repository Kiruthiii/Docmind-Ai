import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("docmind")

class DocumentIntelligenceAgent:
    """Agent 2: Document Intelligence Agent.
    Responsible ONLY for understanding PDF structure, section hierarchy, page metadata,
    and content types (text, table, figure_caption, reference, header).
    Answers: 'Where can useful information exist in this document?'
    """

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
            if sec and sec.lower() != "general":
                sections.add(sec)

            pos = chunk.get("document_position") or chunk.get("metadata", {}).get("document_position", "")
            if pos:
                positions.add(pos)

            c_type = chunk.get("content_type") or chunk.get("chunk_type") or "text"
            content_types.add(c_type)

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
