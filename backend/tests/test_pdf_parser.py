import pytest
from app.services.pdf_parser import PDFParser

def test_convert_table_to_markdown():
    parser = PDFParser()
    raw_table = [
        ["Model", "Accuracy", "Dataset"],
        ["ResNet-50", "94.2%", "ImageNet"],
        ["ViT-Base", "96.1%", "ImageNet"]
    ]
    md = parser._convert_table_to_markdown(raw_table)
    assert "| Model | Accuracy | Dataset |" in md
    assert "| ResNet-50 | 94.2% | ImageNet |" in md
    assert "| ViT-Base | 96.1% | ImageNet |" in md

def test_chunk_text():
    parser = PDFParser(chunk_size=100, chunk_overlap=20)
    long_text = "Paragraph 1 with some text.\n\nParagraph 2 with more text details.\n\nParagraph 3 continuing the discussion."
    chunks = parser._chunk_text(long_text)
    assert len(chunks) > 0
    assert any("Paragraph 1" in c for c in chunks)

def test_chunk_text_single_line_breaks():
    parser = PDFParser(chunk_size=80, chunk_overlap=20)
    # Resume/Slide style text with single line breaks
    resume_text = "John Doe\nSoftware Engineer\n\nExperience:\nSenior Dev at TechCorp (2021-2024)\nBuilt microservices\n\nEducation:\nBS Computer Science\nGraduated with Honors"
    chunks = parser._chunk_text(resume_text)
    assert len(chunks) >= 2
    assert any("EXPERIENCE" in c.upper() for c in chunks)

