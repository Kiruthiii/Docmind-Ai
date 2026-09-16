import io
import json
from unittest.mock import MagicMock, patch
import pytest

from app.api.documents import router
from app.db.supabase_client import _in_memory_db
from app.schemas.document_types import DocumentTypeEnum
from app.services.agents.document_agent import DocumentIntelligenceAgent
from app.services.heuristic_classifier import classify_by_heuristics
from app.services.ingestion_service import IngestionService
from app.services.llm_service import LLMService


# Helper to build dummy PDF bytes for testing
def create_test_pdf_bytes(text_content: str = "Test document content for classification testing.") -> bytes:
    """Creates simple PDF bytes containing text_content."""
    from pypdf import PdfWriter
    from pypdf.annotations import FreeText
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    annotation = FreeText(
        text=text_content,
        rect=(50, 505, 550, 750),
        font_size="12pt",
        bold=True,
        border_color="000000",
        background_color="ffffff",
    )
    writer.add_annotation(page_number=0, annotation=annotation)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


# 1. Test Document Types Enum & Student Examples
def test_document_type_enum_values():
    assert DocumentTypeEnum.COURSE_SYLLABUS.value == "Course Syllabus"
    assert DocumentTypeEnum.LECTURE_NOTES.value == "Lecture Notes"
    assert DocumentTypeEnum.HOMEWORK_ASSIGNMENT.value == "Homework Assignment"
    assert DocumentTypeEnum.LAB_REPORT.value == "Lab Report"
    assert DocumentTypeEnum.EXAM_PAPER.value == "Exam / Practice Test"
    assert DocumentTypeEnum.STUDY_GUIDE.value == "Study Guide"
    assert DocumentTypeEnum.ACADEMIC_PAPER.value == "Academic / Research Paper"
    assert DocumentTypeEnum.INVOICE.value == "Invoice / Financial Document"


# 2. Test Heuristic Classifier Directly (Student & General Documents)
def test_heuristic_classifier_syllabus():
    res = classify_by_heuristics(
        text_sample="CS101 Course Syllabus - Fall 2026\nInstructor: Prof. Alan Turing\nOffice Hours & Grading Policy",
        filename="CS101_Syllabus.pdf"
    )
    assert res.document_type == DocumentTypeEnum.COURSE_SYLLABUS.value
    assert res.method == "heuristic"


def test_heuristic_classifier_lecture_notes():
    res = classify_by_heuristics(
        text_sample="CS102 Lecture Notes: Binary Search Trees & Hash Tables\nKey Concepts & Definitions",
        filename="lecture_notes_ch3.pdf"
    )
    assert res.document_type == DocumentTypeEnum.LECTURE_NOTES.value
    assert res.method == "heuristic"


def test_heuristic_classifier_homework_assignment():
    res = classify_by_heuristics(
        text_sample="Homework Assignment 2\nDue Date: Oct 15\nProblem 1 (25 pts): Prove master theorem",
        filename="assignment_2.pdf"
    )
    assert res.document_type == DocumentTypeEnum.HOMEWORK_ASSIGNMENT.value
    assert res.method == "heuristic"


def test_heuristic_classifier_lab_report():
    res = classify_by_heuristics(
        text_sample="Physics 101 Laboratory Report: Pendulum Oscillation & Gravity Measurements\nObjective, Procedure & Results",
        filename="lab_report_3.pdf"
    )
    assert res.document_type == DocumentTypeEnum.LAB_REPORT.value
    assert res.method == "heuristic"


def test_heuristic_classifier_exam_paper():
    res = classify_by_heuristics(
        text_sample="Calculus II Midterm Exam - Duration: 90 Minutes\nInstructions: Show all work. Multiple Choice Section",
        filename="midterm_exam.pdf"
    )
    assert res.document_type == DocumentTypeEnum.EXAM_PAPER.value
    assert res.method == "heuristic"


def test_heuristic_classifier_invoice():
    res = classify_by_heuristics(
        text_sample="INVOICE # 1001\nBill To: Acme Inc.\nTotal Amount Due: $500.00\nSubtotal: $450.00 Tax: $50.00",
        filename="invoice_1001.pdf"
    )
    assert res.document_type == DocumentTypeEnum.INVOICE.value
    assert res.method == "heuristic"


def test_heuristic_classifier_resume():
    res = classify_by_heuristics(
        text_sample="Work Experience: Senior Developer at Tech Corp. Education: Bachelor of Science in CS.",
        filename="john_doe_resume.pdf"
    )
    assert res.document_type == DocumentTypeEnum.RESUME.value
    assert res.method == "heuristic"


def test_heuristic_classifier_academic_paper():
    res = classify_by_heuristics(
        text_sample="Abstract: In this paper we propose... Introduction... Methodology... Experimental Results... References: [1] Vaswani et al. doi:10.1109/5.771073",
        filename="attention_paper.pdf"
    )
    assert res.document_type == DocumentTypeEnum.ACADEMIC_PAPER.value
    assert res.method == "heuristic"


def test_heuristic_classifier_unknown_defaults():
    res = classify_by_heuristics(
        text_sample="Hello world, random unclassified text content.",
        filename="file.pdf"
    )
    assert res.document_type == DocumentTypeEnum.GENERAL_DOC.value
    assert res.method == "default"


# 3. Test LLM Service Dynamic Classification with Mocks
def test_llm_service_classify_dynamic_student_document():
    llm = LLMService()
    llm.api_key = "mock_key"
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "document_type": "Course Syllabus",
        "confidence": 0.96,
        "primary_topics": ["computer science", "course schedule"],
        "reason": "Contains course description, grading policy, and office hours"
    })
    llm.client = MagicMock()
    llm.client.models.generate_content.return_value = mock_response

    res = llm.classify_document_type("CS101 Course Syllabus Fall 2026...", "syllabus.pdf")
    assert res is not None
    assert res["document_type"] == "Course Syllabus"
    assert res["confidence"] == 0.96
    assert res["method"] == "llm"


def test_llm_service_classify_document_type_quota_error_falls_back():
    llm = LLMService()
    llm.api_key = "mock_key"
    llm.client = MagicMock()
    llm.client.models.generate_content.side_effect = Exception("429 Resource Exhausted Quota Exceeded")

    res = llm.classify_document_type("Some text", "doc.pdf")
    assert res is None  # Gracefully returns None without crashing


# 4. Test DocumentIntelligenceAgent 3-Tiered Classification
def test_document_agent_classification_llm_first():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.classify_document_type.return_value = {
        "document_type": "Lab Report",
        "confidence": 0.94,
        "method": "llm"
    }
    agent = DocumentIntelligenceAgent(llm_service=mock_llm)
    chunks = [{"content": "Physics 101 Lab Report: Pendulum Experiment", "page_number": 1}]

    res = agent.classify_document(chunks, "lab_report.pdf")
    assert res["document_type"] == "Lab Report"
    assert res["method"] == "llm"


def test_document_agent_classification_heuristic_fallback_when_llm_fails():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.classify_document_type.return_value = None  # LLM fails/returns None
    agent = DocumentIntelligenceAgent(llm_service=mock_llm)
    chunks = [{"content": "CS101 Course Syllabus - Fall 2026\nGrading Policy & Office Hours", "page_number": 1}]

    res = agent.classify_document(chunks, "CS101_Syllabus.pdf")
    assert res["document_type"] == DocumentTypeEnum.COURSE_SYLLABUS.value
    assert res["method"] == "heuristic"


def test_document_agent_classification_safe_default_when_all_fail():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.classify_document_type.side_effect = Exception("API Timeout")
    agent = DocumentIntelligenceAgent(llm_service=mock_llm)
    chunks = [{"content": "Random unclassified text content", "page_number": 1}]

    with patch("app.services.agents.document_agent.classify_by_heuristics") as mock_heur:
        mock_heur.side_effect = Exception("Heuristic error")
        res = agent.classify_document(chunks, "file.pdf")

    assert res["document_type"] == "General Document"
    assert res["method"] == "default"


# 5. Test Ingestion Service Classification Persistence
@patch("app.services.ingestion_service.get_supabase_client", return_value=None)
def test_ingestion_service_persists_classification(mock_get_client):
    service = IngestionService()

    mock_parse_result = MagicMock()
    mock_parse_result.page_count = 2
    mock_chunk = {
        "content": "CS101 Course Syllabus\nInstructor: Prof. Turing\nGrading Policy",
        "page_number": 1,
        "chunk_type": "text",
        "content_type": "text",
        "document_position": "general",
        "section_hierarchy": [],
        "section_path": "",
        "parent_section": "",
        "metadata": {}
    }
    mock_parse_result.chunks = [mock_chunk]

    service.parser.parse_pdf_bytes = MagicMock(return_value=mock_parse_result)
    service.llm.get_embeddings_batch = MagicMock(return_value=[[0.1] * 768])
    service.llm.classify_document_type = MagicMock(return_value={
        "document_type": "Course Syllabus",
        "confidence": 0.98,
        "method": "llm"
    })

    res = service.process_pdf(
        workspace_id="00000000-0000-0000-0000-000000000001",
        filename="syllabus_cs101.pdf",
        pdf_bytes=b"dummy_pdf"
    )

    assert res["status"] == "ready"
    assert res["document_type"] == "Course Syllabus"
    assert res["document_type_confidence"] == 0.98
    assert res["classification_method"] == "llm"

    # Verify saved record in memory DB
    doc_id = res["document_id"]
    saved_doc = _in_memory_db.documents.get(doc_id)
    assert saved_doc is not None
    assert saved_doc["document_type"] == "Course Syllabus"


# 6. Test Context Metadata Injection into Grounded Answer
def test_generate_grounded_answer_injects_metadata():
    llm = LLMService()
    llm.api_key = "mock_key"
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "answer": "This is a Course Syllabus covering Python programming and data structures.",
        "answer_type": "OVERVIEW",
        "sufficient_evidence": True,
        "claims": [{"text": "Course Syllabus", "evidence_ids": ["c_1"]}]
    })
    mock_client.models.generate_content.return_value = mock_response
    llm.client = mock_client

    context_chunks = [{
        "id": "c_1",
        "filename": "CS101_Syllabus.pdf",
        "page_number": 1,
        "content": "CS101 Course Syllabus...",
        "document_type": "Course Syllabus",
        "document_type_confidence": 0.98,
        "classification_method": "llm"
    }]

    ans, grounded, supporting = llm.generate_grounded_answer("What am I looking at?", context_chunks)
    assert grounded is True
    assert "syllabus" in ans.lower()

    # Verify that DOCUMENT METADATA was passed into prompt call to Gemini
    called_prompt = mock_client.models.generate_content.call_args[1]["contents"]
    assert "DOCUMENT METADATA:" in called_prompt
    assert "Classified Document Type: Course Syllabus" in called_prompt


# 7. Test Short Technical & Partially Extracted Document Snippet (YOLO / Edge Node)
def test_short_technical_snippet_2level_classification():
    llm = LLMService()
    llm.api_key = "mock_key"
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "document_category": "Academic / Research",
        "document_type": "Computer Vision Research Paper",
        "confidence": 0.85,
        "primary_topics": ["YOLO vehicle detection", "edge computing", "traffic monitoring"],
        "reason": "Technical model methodology, edge deployment context, and research writing style",
        "evidence": [
            "research-oriented writing style",
            "model architecture methodology (YOLO)",
            "edge deployment evaluation (Jetson Xavier NX)"
        ]
    })
    llm.client = MagicMock()
    llm.client.models.generate_content.return_value = mock_response

    text_snippet = (
        "A lightweight vehicle detection model, based on (You Only Look Once) YOLO and "
        "deployed on a Jetson Xavier NX-powered roadside edge node (RSEN), enables real-time traffic monitoring..."
    )
    res = llm.classify_document_type(text_snippet, "paper_draft_v1.pdf")
    assert res is not None
    assert res["document_category"] == "Academic / Research"
    assert res["document_type"] == "Computer Vision Research Paper"
    assert res["confidence"] == 0.85
    assert len(res["evidence"]) == 3
    assert "research-oriented writing style" in res["evidence"]


# 8. Negative Test: Technical SDK / API Spec is Classified as Technical (Not Academic)
def test_negative_technical_spec_not_academic():
    llm = LLMService()
    llm.api_key = "mock_key"
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "document_category": "Technical",
        "document_type": "SDK & Deployment Specification",
        "confidence": 0.92,
        "primary_topics": ["Jetson SDK", "system configuration"],
        "reason": "Contains CLI parameters, configuration flags, and hardware deployment setup instructions",
        "evidence": [
            "command-line syntax",
            "system setup parameters",
            "hardware configuration specifications"
        ]
    })
    llm.client = MagicMock()
    llm.client.models.generate_content.return_value = mock_response

    text_snippet = (
        "NVIDIA Jetson Xavier NX SDK Configuration Specification. "
        "Usage: ./deploy --model-path /models/yolo.onnx --batch-size 8 --device 0"
    )
    res = llm.classify_document_type(text_snippet, "jetson_config.pdf")
    assert res is not None
    assert res["document_category"] == "Technical"
    assert res["document_type"] == "Sdk & Deployment Specification"
    assert res["document_category"] != "Academic / Research"


# 9. Test Strategic Multi-Chunk Sampling Aggregation
def test_strategic_multi_chunk_sampling():
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.classify_document_type.return_value = {
        "document_category": "Academic / Research",
        "document_type": "Deep Learning Research Paper",
        "confidence": 0.95,
        "evidence": ["Title section", "Methodology section", "References list"],
        "method": "llm"
    }
    agent = DocumentIntelligenceAgent(llm_service=mock_llm)

    chunks = [
        {
            "content": "Deep Learning Framework for Edge Computing in Smart Cities",
            "page_number": 1,
            "section_path": "Title",
            "chunk_type": "header"
        },
        {
            "content": "Section 1: Introduction. We present a novel architecture for real-time edge processing...",
            "page_number": 1,
            "section_path": "Introduction",
            "chunk_type": "text"
        },
        {
            "content": "Section 3: Methodology and Model Architecture. The proposed neural network uses feature pyramids...",
            "page_number": 5,
            "section_path": "Methodology",
            "chunk_type": "text"
        },
        {
            "content": "References: [1] J. Doe et al., 'Real-time Object Detection', IEEE Trans. Pattern Anal., 2024.",
            "page_number": 10,
            "section_path": "References",
            "chunk_type": "text"
        }
    ]

    res = agent.classify_document(chunks, "edge_computing_paper.pdf")
    assert res["document_category"] == "Academic / Research"
    assert res["document_type"] == "Deep Learning Research Paper"

    # Verify strategic sampling passed aggregated sample text to LLM
    called_sample = mock_llm.classify_document_type.call_args[0][0]
    assert "Filename: edge_computing_paper.pdf" in called_sample
    assert "[Document Headings]: Title, Introduction, Methodology, References" in called_sample
    assert "[Body Sample - Page 5]" in called_sample


# 10. Test Heuristic Classifier Generic Evidence Generation
def test_heuristic_classifier_evidence_generation():
    res = classify_by_heuristics(
        text_sample="Abstract: We present a new algorithm. Methodology: Section 2 describes our model. Results and References follow.",
        filename="unnamed.pdf"
    )
    assert res.document_category == "Academic / Research"
    assert res.document_type == "Academic / Research Paper"
    assert isinstance(res.evidence, list)
    assert len(res.evidence) > 0
    assert any("Structural signal" in ev for ev in res.evidence)


# 11. Test 'What am I looking at?' Natural Language Question Intent & Metadata Retrieval
def test_what_am_i_looking_at_query_intent_and_metadata_retrieval():
    from app.services.agents.query_agent import QueryIntelligenceAgent
    from app.services.agents.retrieval_agent import RetrievalIntelligenceAgent

    q_agent = QueryIntelligenceAgent()
    sq = q_agent.analyze_query("What am I looking at?")
    assert sq.intent == "DOCUMENT_OVERVIEW"
    assert sq.retrieval_scope == "DOCUMENT_LEVEL"

    ret_agent = RetrievalIntelligenceAgent()
    _in_memory_db.documents["doc_123"] = {
        "id": "doc_123",
        "filename": "yolo_paper.pdf",
        "document_category": "Academic / Research",
        "document_type": "Computer Vision Research Paper",
        "document_type_confidence": 0.95,
        "classification_method": "llm",
        "evidence": ["Methodology", "Abstract"]
    }
    _in_memory_db.document_chunks = [{
        "id": "chunk_1",
        "document_id": "doc_123",
        "workspace_id": "ws_test",
        "content": "An Edge-Deployed Real-Time Adaptive Traffic Light Control System Using YOLO",
        "page_number": 1,
        "embedding": [0.1] * 768
    }]

    candidates = ret_agent.retrieve_candidates(
        workspace_id="ws_test",
        structured_query=sq,
        query_vector=[0.1] * 768
    )
    assert len(candidates) > 0
    assert candidates[0]["document_category"] == "Academic / Research"
    assert candidates[0]["document_type"] == "Computer Vision Research Paper"

    llm = LLMService()
    scope = llm._classify_query_scope("What am I looking at?")
    assert scope == "DOCUMENT_META"


