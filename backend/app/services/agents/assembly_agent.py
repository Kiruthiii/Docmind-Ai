import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger("docmind")

class EvidenceAssemblyAgent:
    """Agent 4: Evidence Assembly Agent.
    Responsible ONLY for organizing, deduplicating, ordering, and maintaining provenance metadata
    of retrieved candidate evidence chunks before validation and synthesis.
    """

    def assemble_evidence_context(self, candidate_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assembles structured evidence payload, removing duplicates and publishing noise."""
        if not candidate_chunks:
            return {"assembled_chunks": [], "context_str": "", "provenance": []}

        assembled = []
        seen_contents = set()
        provenance = []
        context_blocks = []

        for idx, chunk in enumerate(candidate_chunks, 1):
            c_id = chunk.get("id", f"chunk_{idx}")
            raw_content = chunk.get("content", "").strip()

            if not raw_content or raw_content in seen_contents:
                continue

            # Strip publication, grant, and editor noise lines
            lines = [l.strip() for l in raw_content.split("\n") if l.strip()]
            clean_lines = []
            for l in lines:
                l_lower = l.lower()
                if any(k in l_lower for k in ["creative commons", "licensed under", "all rights reserved", "this work is licensed", "creativecommons.org", "associate editor coordinating", "approving it for publication was", "this work was supported by"]):
                    continue
                clean_lines.append(l)

            if not clean_lines:
                continue

            clean_content = "\n".join(clean_lines)
            seen_contents.add(raw_content)

            chunk_copy = dict(chunk)
            chunk_copy["content"] = clean_content
            assembled.append(chunk_copy)

            doc_name = chunk.get("filename") or chunk.get("metadata", {}).get("filename", "Document")
            page_num = chunk.get("page_number", 1)

            context_blocks.append(f"[Chunk ID: {c_id} | Document: {doc_name} | Page: {page_num}]\n{clean_content}")

            provenance.append({
                "chunk_id": c_id,
                "document_name": doc_name,
                "page_number": page_num,
                "section_path": chunk.get("section_path", ""),
                "content_snippet": clean_content[:150] + ("..." if len(clean_content) > 150 else "")
            })

        context_str = "\n\n".join(context_blocks)

        return {
            "assembled_chunks": assembled,
            "context_str": context_str,
            "provenance": provenance
        }
