from pypdf import PdfReader
import pdfplumber
from PIL import Image
import io
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("docmind")

class ExtractedChunk(BaseModel):
    page_number: int
    chunk_type: str  # 'text', 'table', 'image_description'
    content: str
    metadata: Dict[str, Any] = {}

class PDFParseResult(BaseModel):
    page_count: int
    chunks: List[ExtractedChunk]
    has_scanned_content: bool = False

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
                    metadata={"filename": filename, "page_number": page_num}
                ))

            # 2. Text Extraction & Recursive Chunking
            if text:
                text_chunks = self._chunk_text(text)
                for chunk_str in text_chunks:
                    extracted_chunks.append(ExtractedChunk(
                        page_number=page_num,
                        chunk_type="text",
                        content=chunk_str,
                        metadata={"filename": filename, "page_number": page_num}
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
        """Splits long text into semantically focused overlapping chunks using multi-level splitting."""
        if not text:
            return []

        # 1. Split by double line breaks first
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        # 2. Break down large paragraphs by single line breaks (common in resumes, slides, tables)
        blocks = []
        for p in paragraphs:
            if len(p) > self.chunk_size:
                lines = [l.strip() for l in p.split("\n") if l.strip()]
                blocks.extend(lines)
            else:
                blocks.append(p)

        # 3. Accumulate blocks into target chunk size
        chunks = []
        current_chunk = ""

        for block in blocks:
            if len(current_chunk) + len(block) + 2 <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + block
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                if len(block) > self.chunk_size:
                    # Slice oversized single block into overlapping windows
                    step = max(1, self.chunk_size - self.chunk_overlap)
                    sub_chunks = [block[i:i + self.chunk_size] for i in range(0, len(block), step)]
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = block

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
