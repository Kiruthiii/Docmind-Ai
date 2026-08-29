import pytest
import uuid
from app.services.llm_service import LLMService
from app.services.pdf_parser import PDFParser, detect_document_position, detect_content_type
from app.services.rag_service import RAGService
from app.schemas.chat import QueryIntent
from app.db.supabase_client import _in_memory_db

def test_query_intent_analysis():
    llm = LLMService()

    # Intro query
    intent1 = llm.analyze_query_intent("summarize the introduction section of the paper")
    assert intent1.query_type in ("overview", "specific_fact")
    assert intent1.target_section == "introduction"

    # Fact query in results
    intent2 = llm.analyze_query_intent("what is the mAP value in the results section?")
    assert intent2.target_section == "results"

    # Visual analysis query
    intent3 = llm.analyze_query_intent("what data is shown in Table 1?")
    assert intent3.query_type == "visual_analysis"

    # Comparison query
    intent4 = llm.analyze_query_intent("compare the methodology between model A and model B")
    assert intent4.query_type == "comparison"
    assert intent4.target_section == "methodology"

def test_document_position_detection():
    # Intro on page 1
    pos1 = detect_document_position(1, "1. INTRODUCTION", "This paper presents a novel approach...")
    assert pos1 == "introduction"

    # Results on page 15
    pos2 = detect_document_position(15, "4. EXPERIMENTAL RESULTS", "We evaluated our approach on MS COCO...")
    assert pos2 == "results"

    # References on page 27
    pos3 = detect_document_position(27, "REFERENCES", "[1] Vaswani et al. Attention is all you need.")
    assert pos3 == "references"

def test_introduction_query_filters_page_27():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Research_Paper.pdf"}

    # Page 1: Introduction chunk
    _in_memory_db.document_chunks.append({
        "id": "c_page1_intro",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content_type": "text",
        "document_position": "introduction",
        "section_hierarchy": ["1. INTRODUCTION"],
        "content": "Section: 1. INTRODUCTION\nIn this paper, we introduce DocMind AI, a precision document intelligence system.",
        "embedding": rag.llm.get_embedding("Introduction DocMind AI precision document intelligence system"),
        "filename": "Research_Paper.pdf"
    })

    # Page 27: Reference chunk containing the keyword "introduction"
    _in_memory_db.document_chunks.append({
        "id": "c_page27_ref",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 27,
        "chunk_type": "text",
        "content_type": "reference",
        "document_position": "references",
        "section_hierarchy": ["REFERENCES"],
        "content": "Section: REFERENCES\n[42] Smith et al. 'An Introduction to Deep Learning for Document Parsing', 2021.",
        "embedding": rag.llm.get_embedding("Smith An Introduction to Deep Learning for Document Parsing 2021"),
        "filename": "Research_Paper.pdf"
    })

    response = rag.query_workspace(ws_id, "Summarize the introduction of the paper")

    assert response.is_grounded is True
    assert "DocMind AI" in response.answer or "precision document intelligence" in response.answer
    page_numbers = [c.page_number for c in response.citations]
    assert 1 in page_numbers
    assert 27 not in page_numbers

def test_table_and_figure_chunk_retrieval():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Evaluation_Report.pdf"}

    # Table chunk
    _in_memory_db.document_chunks.append({
        "id": "c_table_1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 5,
        "chunk_type": "table",
        "content_type": "table",
        "document_position": "results",
        "section_hierarchy": ["Results", "Tables"],
        "content": "[Table 1 on Page 5]\n| Model | mAP | Accuracy |\n| --- | --- | --- |\n| DocMind AI | 89.4% | 94.2% |",
        "embedding": rag.llm.get_embedding("Table 1 Model mAP Accuracy DocMind AI 89.4%"),
        "filename": "Evaluation_Report.pdf"
    })

    response = rag.query_workspace(ws_id, "What is the mAP value in Table 1?")
    assert response.is_grounded is True
    assert "89.4" in response.answer
    assert 5 in [c.page_number for c in response.citations]
