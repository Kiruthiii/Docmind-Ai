import os


def create_sample_pdf(filepath: str = "backend/tests/fixtures/sample_paper.pdf"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    # Minimal valid PDF file
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 120 >> stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"100 700 Td\n"
        b"(ResNet-101 model achieved 96.1% accuracy on ImageNet dataset.) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000060 00000 n \n"
        b"00000000117 00000 n \n"
        b"00000000250 00000 n \n"
        b"00000000420 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        b"490\n"
        b"%%EOF\n"
    )
    with open(filepath, "wb") as f:
        f.write(pdf_content)
    print(f"Sample PDF created at {filepath}")

if __name__ == "__main__":
    create_sample_pdf()
