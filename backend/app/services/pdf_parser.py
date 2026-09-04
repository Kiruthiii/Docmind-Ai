import io
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = Any  # type: ignore

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore

try:
    from PIL import Image
except ImportError:
    Image = Any  # type: ignore

from pydantic import BaseModel, Field

logger = logging.getLogger("docmind")

class ExtractedChunk(BaseModel):
    page_number: int
    chunk_type: str = "text"  # 'text', 'table', 'figure_caption', 'reference', 'header'
    content_type: str = "text"  # 'text' | 'table' | 'figure_caption' | 'reference' | 'header'
    document_position: str = "general"  # 'introduction' | 'methodology' | 'results' | 'conclusion' | 'references' | 'general'
    content: str
    section_path: str = ""
    parent_section: str = ""
    section_hierarchy: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PDFParseResult(BaseModel):
    page_count: int
    chunks: List[ExtractedChunk]
    has_scanned_content: bool = False
    doc_metadata: Dict[str, Any] = Field(default_factory=dict)

def detect_document_position(page_number: int, section_title: str = "", text_snippet: str = "") -> str:
    """Auto-detects document position based on page number, section title, and text content."""
    title_lower = (section_title or "").lower()
    text_lower = (text_snippet or "").lower()[:250]

    if any(k in title_lower for k in ["reference", "bibliography", "citations", "references"]):
        return "references"
    if any(k in title_lower for k in ["conclusion", "future work", "summary and conclusion"]):
        return "conclusion"
    if any(k in title_lower for k in ["results", "experiments", "evaluation", "experimental results", "performance"]):
        return "results"
    if any(k in title_lower for k in ["methodology", "methods", "proposed approach", "system model", "implementation", "architecture"]):
        return "methodology"
    if any(k in title_lower for k in ["introduction", "overview", "background", "motivation", "preamble"]):
        return "introduction"

    if page_number <= 3:
        if any(k in text_lower for k in ["reference", "bibliography"]):
            return "references"
        return "introduction"

    return "general"

def detect_content_type(content: str, is_table: bool = False, is_fig: bool = False, section_name: str = "") -> str:
    """Tags content with content_type: text | table | figure_caption | reference | header."""
    if is_table:
        return "table"
    if is_fig or re.search(r'\b(?:figure|fig|chart|diagram|illustration|image)\s*\.?:?\s*\d+', content, re.IGNORECASE):
        return "figure_caption"
    if any(k in section_name.lower() for k in ["reference", "bibliography", "citations"]):
        return "reference"
    lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
    if len(lines) == 1 and len(lines[0]) < 80 and not lines[0].endswith("."):
        return "header"
    return "text"

def _is_structural_heading(line: str) -> bool:
    """Document-agnostic structural heading detector (works for papers, manuals, textbooks, reports, resumes, and ASCII-decorated headings)."""
    raw_line = line.strip()
    if not raw_line:
        return False

    # Strip decorative ASCII borders: dashes (-), equals (=), asterisks (*), underscores (_)
    clean_line = re.sub(r'^[\-\=\*\_\s\:\.\#]+', '', raw_line)
    clean_line = re.sub(r'[\-\=\*\_\s\:\.\#]+$', '', clean_line).strip()
    if not clean_line or len(clean_line) > 60:
        return False

    if raw_line.endswith(":") or clean_line.endswith(":"):
        return True
    if re.match(r'^(?:[0-9]+(?:\.[0-9]+)*|[A-Z]\.|[IVXLCDM]+\.)\s+[A-Z]', clean_line):
        return True
    if clean_line.isupper() and len(clean_line) >= 3 and not re.match(r'^[0-9\s\W]+$', clean_line):
        return True
    words = clean_line.split()
    if 1 <= len(words) <= 4 and all(w[0].isupper() for w in words if w[0].isalpha()):
        return True
    return False

class PDFParser:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_pdf_bytes(self, pdf_bytes: bytes, filename: str) -> PDFParseResult:
        """Parses PDF bytes to extract text, tables, visual captions, and structure."""
        extracted_chunks: List[ExtractedChunk] = []
        page_count = 0
        has_scanned = False

        # Open with pypdf for fast text extraction
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        page_count = len(reader.pages)

        # Open with pdfplumber for high quality table extraction
        try:
            plumber_pdf = pdfplumber.open(io.BytesIO(pdf_bytes))
        except Exception as e:
            logger.warning(f"pdfplumber failed to open PDF {filename}: {e}")
            plumber_pdf = None

        for page_idx in range(page_count):
            page_num = page_idx + 1
            pypdf_page = reader.pages[page_idx]
            raw_text = (pypdf_page.extract_text() or "").strip()
            # Clean up split words (e.g., "V ehicle" -> "Vehicle", "Im pact" -> "Impact")
            text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', raw_text)
            text = re.sub(r'\b([A-Za-z])\s+([a-z]{2,})\b', r'\1\2', text)
            text = re.sub(r'\b([A-Z]{3,})\s+([A-Z])\b', r'\1\2', text)

            # Check if page has images / low text
            images_on_page = getattr(pypdf_page, 'images', [])
            if len(text) < 50 and len(images_on_page) > 0:
                has_scanned = True

            # 1. Table Extraction via pdfplumber
            table_markdowns = []
            if plumber_pdf and page_idx < len(plumber_pdf.pages):
                try:
                    plumber_page = plumber_pdf.pages[page_idx]
                    tables = plumber_page.extract_tables()
                    for table in tables:
                        if table:
                            md_table = self._convert_table_to_markdown(table)
                            if md_table:
                                table_markdowns.append(md_table)
                except Exception as e:
                    logger.debug(f"Table extraction error on page {page_num}: {e}")

            for md_table in table_markdowns:
                doc_pos = detect_document_position(page_num, "Tables", md_table)
                extracted_chunks.append(ExtractedChunk(
                    page_number=page_num,
                    chunk_type="table",
                    content_type="table",
                    document_position=doc_pos,
                    section_hierarchy=["Tables"],
                    content=f"[Table on Page {page_num}]\n{md_table}",
                    section_path="Tables",
                    parent_section="Tables",
                    metadata={
                        "filename": filename,
                        "page_number": page_num,
                        "parent_section": "Tables",
                        "content_type": "table",
                        "document_position": doc_pos,
                        "section_hierarchy": ["Tables"]
                    }
                ))

            # 2. Extract Figure/Image Captions
            fig_matches = re.findall(r'((?:Figure|Fig|Chart|Diagram)\s*\d+[\:\.\-][^\n]+)', text, re.IGNORECASE)
            for fig_caption in fig_matches:
                doc_pos = detect_document_position(page_num, "Figures", fig_caption)
                extracted_chunks.append(ExtractedChunk(
                    page_number=page_num,
                    chunk_type="figure_caption",
                    content_type="figure_caption",
                    document_position=doc_pos,
                    section_hierarchy=["Figures & Visuals"],
                    content=f"[Figure Caption on Page {page_num}] {fig_caption.strip()}",
                    section_path="Figures & Visuals",
                    parent_section="Figures & Visuals",
                    metadata={
                        "filename": filename,
                        "page_number": page_num,
                        "parent_section": "Figures & Visuals",
                        "content_type": "figure_caption",
                        "document_position": doc_pos,
                        "section_hierarchy": ["Figures & Visuals"]
                    }
                ))

            # 3. Text Extraction & Parent-Child Section Chunking
            if text:
                text_chunks = self._chunk_text_structured(text, page_number=page_num)
                for chunk_info in text_chunks:
                    extracted_chunks.append(ExtractedChunk(
                        page_number=page_num,
                        chunk_type=chunk_info.get("chunk_type", "text"),
                        content_type=chunk_info.get("content_type", "text"),
                        document_position=chunk_info.get("document_position", "general"),
                        section_hierarchy=chunk_info.get("section_hierarchy", []),
                        content=chunk_info["content"],
                        section_path=chunk_info["section_path"],
                        parent_section=chunk_info["parent_section"],
                        metadata={
                            "filename": filename,
                            "page_number": page_num,
                            "section_path": chunk_info["section_path"],
                            "parent_section": chunk_info["parent_section"],
                            "content_type": chunk_info.get("content_type", "text"),
                            "document_position": chunk_info.get("document_position", "general"),
                            "section_hierarchy": chunk_info.get("section_hierarchy", [])
                        }
                    ))

        if plumber_pdf:
            plumber_pdf.close()

        # Fallback if no text was found anywhere (scanned document)
        if not extracted_chunks and page_count > 0:
            has_scanned = True

        page1_text = (reader.pages[0].extract_text() or "").strip() if page_count > 0 else ""
        doc_meta = self.extract_header_metadata(page1_text)

        return PDFParseResult(
            page_count=page_count,
            chunks=extracted_chunks,
            has_scanned_content=has_scanned,
            doc_metadata=doc_meta
        )

    def extract_header_metadata(self, page1_text: str) -> Dict[str, Any]:
        """Extracts structured document metadata (title, authors, publication date, doi) from Page 1 text."""
        meta = {
            "title": "",
            "authors": "",
            "publication_date": "",
            "doi": ""
        }
        if not page1_text:
            return meta

        lines = [l.strip() for l in page1_text.split("\n") if l.strip()]

        # 1. DOI
        doi_match = re.search(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b', page1_text)
        if doi_match:
            meta["doi"] = doi_match.group(1)

        # 2. Publication Date
        date_match = re.search(r'\b(?:date of publication|published|publication date)?\s*:?\s*(\d{1,2}\s+(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}|\d{4})\b', page1_text, re.IGNORECASE)
        if date_match:
            meta["publication_date"] = date_match.group(1)

        # 3. Authors
        author_match = re.search(r'\b(?:by|authors?)\s*:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s*(?:,|and)\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)*)', page1_text, re.IGNORECASE)
        if author_match:
            meta["authors"] = author_match.group(1)
        else:
            cand_authors = []
            for line in lines[1:7]:
                l_clean = re.sub(r'[\d\*\†\‡\§\$\#]', '', line).strip()
                if re.match(r'^(?:[A-Z][a-zA-Z\.\-]+\s+)+[A-Z][a-zA-Z\.\-]+(?:\s*,\s*(?:[A-Z][a-zA-Z\.\-]+\s+)+[A-Z][a-zA-Z\.\-]+)*(?:\s*and\s+(?:[A-Z][a-zA-Z\.\-]+\s+)+[A-Z][a-zA-Z\.\-]+)?$', l_clean):
                    cand_authors.append(l_clean)
            if cand_authors:
                meta["authors"] = ", ".join(cand_authors)

        # 4. Title
        for line in lines[:8]:
            l_lower = line.lower()
            if not any(k in l_lower for k in ["ieee", "volume", "license", "creative commons", "issn", "doi", "http", "http:", "https:"]):
                if len(line) > 10 and not line.startswith("Section:"):
                    meta["title"] = line
                    break

        return meta

    def _convert_table_to_markdown(self, table: List[List[Optional[str]]]) -> str:
        """Converts a 2D matrix table into GitHub Flavored Markdown."""
        clean_table = []
        for row in table:
            clean_row = [str(cell).replace('\n', ' ').strip() if cell is not None else "" for cell in row]
            if any(clean_row):
                clean_table.append(clean_row)

        if not clean_table:
            return ""

        headers = clean_table[0]
        rows = clean_table[1:]

        header_str = "| " + " | ".join(headers) + " |"
        sep_str = "| " + " | ".join(["---"] * len(headers)) + " |"
        row_strs = ["| " + " | ".join(r) + " |" for r in rows]

        return "\n".join([header_str, sep_str] + row_strs)

    def _chunk_text(self, text: str) -> List[str]:
        res = self._chunk_text_structured(text)
        return [r["content"] for r in res]

    def _chunk_text_structured(self, text: str, page_number: int = 1) -> List[Dict[str, Any]]:
        """Line-by-line section boundary parser for document-agnostic parent-child structure."""
        if not text:
            return []

        raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not raw_lines:
            return []

        structured_chunks = []

        # Unified Page 1 Document Header & Author Metadata chunk
        if page_number == 1:
            header_preamble = "\n".join(raw_lines[:20]).strip()
            if header_preamble:
                structured_chunks.append({
                    "content": f"Section: Document Header & Author Metadata\n{header_preamble}",
                    "section_path": "Document Header & Author Metadata",
                    "parent_section": "Document Header",
                    "section_hierarchy": ["Document Header"],
                    "document_position": "introduction",
                    "content_type": "header",
                    "chunk_type": "header"
                })
        current_parent = "General"
        current_sub = ""
        current_lines = []

        def flush_current():
            nonlocal current_lines, current_parent, current_sub, structured_chunks
            if not current_lines:
                return
            body = "\n".join(current_lines).strip()
            if not body:
                return
            sec_path = f"{current_parent} > {current_sub}" if current_sub else current_parent
            sec_hierarchy = [h for h in [current_parent, current_sub] if h and h.lower() != "general"]

            title_prefix = f"### {current_sub}\n" if (current_sub and current_sub.lower() not in body.lower()) else ""
            full_body = f"{title_prefix}{body}".strip()

            doc_pos = detect_document_position(page_number, sec_path, full_body)
            c_type = detect_content_type(full_body, section_name=sec_path)

            if len(full_body) > 600 and len(current_lines) >= 4:
                sub_blocks = []
                curr_block = []
                curr_len = 0
                for l_item in current_lines:
                    curr_block.append(l_item)
                    curr_len += len(l_item)
                    if curr_len >= 400:
                        sub_blocks.append("\n".join(curr_block).strip())
                        curr_block = []
                        curr_len = 0
                if curr_block:
                    sub_blocks.append("\n".join(curr_block).strip())

                for s_blk in sub_blocks:
                    if s_blk:
                        s_body = f"{title_prefix}{s_blk}".strip()
                        structured_chunks.append({
                            "content": f"Section: {sec_path}\n{s_body}",
                            "section_path": sec_path,
                            "parent_section": current_parent,
                            "section_hierarchy": sec_hierarchy,
                            "document_position": doc_pos,
                            "content_type": c_type,
                            "chunk_type": c_type
                        })
            else:
                structured_chunks.append({
                    "content": f"Section: {sec_path}\n{full_body}",
                    "section_path": sec_path,
                    "parent_section": current_parent,
                    "section_hierarchy": sec_hierarchy,
                    "document_position": doc_pos,
                    "content_type": c_type,
                    "chunk_type": c_type
                })
            current_lines = []

        for line in raw_lines:
            raw_l = line.strip()

            # Filter out publishing noise/copyright boilerplate lines
            l_lower = raw_l.lower()
            if any(k in l_lower for k in ["creative commons", "licensed under", "all rights reserved", "this work is licensed", "creativecommons.org", "associate editor coordinating"]):
                continue

            clean_l = re.sub(r'^[\-\=\*\_\s\:\.\#]+', '', raw_l)
            clean_l = re.sub(r'[\-\=\*\_\s\:\.\#]+$', '', clean_l).strip()
            clean_l_nobullet = re.sub(r'^[•\-\*\\s]+', '', clean_l).strip()
            has_bullet = bool(re.match(r'^(?:[•\*\]|[\-\*]\s)', raw_l))

            if _is_structural_heading(line):
                is_decorated = bool(re.match(r'^[\-\=\*\_\#]{3,}', raw_l)) or bool(re.search(r'[\-\=\*\_\#]{3,}$', raw_l))
                is_all_caps = clean_l_nobullet.isupper() and len(clean_l_nobullet) >= 3 and not re.match(r'^[0-9\s\W]+$', clean_l_nobullet)
                is_numbered_section = bool(re.match(r'^(?:[0-9]+(?:\.[0-9]+)*|[A-Z]\.|[IVXLCDM]+\.)\s+[A-Z]', clean_l_nobullet))

                is_major = (is_decorated or is_all_caps or is_numbered_section) and not has_bullet and not (":" in clean_l_nobullet and len(clean_l_nobullet) > 25)
                had_lines = bool(current_lines)

                flush_current()

                if is_major:
                    current_parent = clean_l_nobullet.upper()
                    current_sub = ""
                elif current_sub and not had_lines:
                    current_parent = current_sub.upper()
                    current_sub = clean_l_nobullet
                else:
                    current_sub = clean_l_nobullet
            else:
                current_lines.append(line)

        flush_current()
        return structured_chunks
