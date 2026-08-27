import io
import re
import logging
from typing import List, Dict, Any, Optional
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

logger = logging.getLogger("docmind")

class ExtractedChunk(BaseModel):
    page_number: int
    chunk_type: str  # 'text', 'table', 'image_description'
    content: str
    section_path: str = ""
    parent_section: str = ""
    metadata: Dict[str, Any] = {}

class PDFParseResult(BaseModel):
    page_count: int
    chunks: List[ExtractedChunk]
    has_scanned_content: bool = False

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
        """Parses PDF bytes to extract text, tables, and detect visual/scanned pages."""
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
            text = (pypdf_page.extract_text() or "").strip()

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
                extracted_chunks.append(ExtractedChunk(
                    page_number=page_num,
                    chunk_type="table",
                    content=f"[Table on Page {page_num}]\n{md_table}",
                    section_path="Tables",
                    parent_section="Tables",
                    metadata={"filename": filename, "page_number": page_num, "parent_section": "Tables"}
                ))

            # 2. Text Extraction & Parent-Child Section Chunking
            if text:
                text_chunks = self._chunk_text_structured(text)
                for chunk_info in text_chunks:
                    extracted_chunks.append(ExtractedChunk(
                        page_number=page_num,
                        chunk_type="text",
                        content=chunk_info["content"],
                        section_path=chunk_info["section_path"],
                        parent_section=chunk_info["parent_section"],
                        metadata={
                            "filename": filename,
                            "page_number": page_num,
                            "section_path": chunk_info["section_path"],
                            "parent_section": chunk_info["parent_section"]
                        }
                    ))

        if plumber_pdf:
            plumber_pdf.close()

        # Fallback if no text was found anywhere (scanned document)
        if not extracted_chunks and page_count > 0:
            has_scanned = True

        return PDFParseResult(
            page_count=page_count,
            chunks=extracted_chunks,
            has_scanned_content=has_scanned
        )

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

    def _chunk_text_structured(self, text: str) -> List[Dict[str, Any]]:
        """Line-by-line section boundary parser for document-agnostic parent-child structure."""
        if not text:
            return []

        raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not raw_lines:
            return []

        structured_chunks = []
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
            
            # Preserve sub-item title in body content if not already present
            title_prefix = f"### {current_sub}\n" if (current_sub and current_sub.lower() not in body.lower()) else ""
            full_body = f"{title_prefix}{body}".strip()
            
            # Sub-chunk long text blocks (>600 chars) to ensure tight snippet retrieval rather than full-page dumps
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
                            "parent_section": current_parent
                        })
            else:
                structured_chunks.append({
                    "content": f"Section: {sec_path}\n{full_body}",
                    "section_path": sec_path,
                    "parent_section": current_parent
                })
            current_lines = []

        for line in raw_lines:
            raw_l = line.strip()
            clean_l = re.sub(r'^[\-\=\*\_\s\:\.\#]+', '', raw_l)
            clean_l = re.sub(r'[\-\=\*\_\s\:\.\#]+$', '', clean_l).strip()
            clean_l_nobullet = re.sub(r'^[•\-\*\\s]+', '', clean_l).strip()
            has_bullet = bool(re.match(r'^(?:[•\*\]|[\-\*]\s)', raw_l))

            if _is_structural_heading(line):
                is_decorated = bool(re.match(r'^[\-\=\*\_\#]{3,}', raw_l)) or bool(re.search(r'[\-\=\*\_\#]{3,}$', raw_l))
                is_all_caps = clean_l_nobullet.isupper() and len(clean_l_nobullet) >= 3 and not re.match(r'^[0-9\s\W]+$', clean_l_nobullet)
                is_numbered_section = bool(re.match(r'^(?:[0-9]+(?:\.[0-9]+)*|[A-Z]\.|[IVXLCDM]+\.)\s+[A-Z]', clean_l_nobullet))

                # Dynamic, document-agnostic section detection (NO hardcoded section names/keywords):
                # A line is a major parent section if it has ASCII borders, ALL-CAPS text, or numbered heading syntax AND is not a bullet item
                is_major = (is_decorated or is_all_caps or is_numbered_section) and not has_bullet and not (":" in clean_l_nobullet and len(clean_l_nobullet) > 25)

                had_lines = bool(current_lines)

                # 1. Flush body lines collected under previous section
                flush_current()

                # 2. Update section state for new section
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
