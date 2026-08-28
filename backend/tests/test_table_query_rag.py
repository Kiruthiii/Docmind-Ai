import pytest
import uuid
from app.services.rag_service import RAGService
from app.db.supabase_client import _in_memory_db
from app.services.llm_service import extract_target_numbered_entity, chunk_contains_target_entity

def test_extract_target_numbered_entity_helper():
    assert extract_target_numbered_entity("What is the table 1 ") == ("table", "1")
    assert extract_target_numbered_entity("What does Table 12 show?") == ("table", "12")
    assert extract_target_numbered_entity("What is shown in Figure 3?") == ("figure", "3")
    assert extract_target_numbered_entity("According to Fig. 2, what happens?") == ("figure", "2")
    assert extract_target_numbered_entity("Summarize section 4.1") == ("section", "4.1")
    assert extract_target_numbered_entity("What is the summary?") is None

def test_chunk_contains_target_entity_helper():
    chunk_t1 = "Section: Experiments > Table 1\n### Table 1: Baseline traffic timings\nState: 01, Green time: 30 seconds."
    chunk_t12 = "Section: Experiments > Table 12\n### Table 12 yields the following observations\nHigh density state."
    chunk_t9 = "Section: Experiments > Table 9\n### Table 9: Density levels\nHigh density: green time = 120s."

    # Strict Table 1 check
    assert chunk_contains_target_entity(chunk_t1, "table", "1") is True
    assert chunk_contains_target_entity(chunk_t12, "table", "1") is False
    assert chunk_contains_target_entity(chunk_t9, "table", "1") is False

    # Strict Table 12 check
    assert chunk_contains_target_entity(chunk_t12, "table", "12") is True
    assert chunk_contains_target_entity(chunk_t1, "table", "12") is False

def test_table_1_query_when_table_1_exists():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    filename = "An_Edge-Deployed_Real-Time_Adaptive_Traffic_Light_Control_System_Using_YOLO-Based_Vehicle_Detection_and_PCE-Aware_Density_Estimation.pdf"

    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": filename}

    _in_memory_db.document_chunks.append({
        "id": "c_t1",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 5,
        "chunk_type": "table",
        "content": "Section: Results > Table 1\n### Table 1: PCE Values for Vehicles\nVehicle Type | PCE Value\nCar | 1.0\nBus | 2.5\nMotorcycle | 0.5",
        "embedding": rag.llm.get_embedding("Table 1 PCE Values for Vehicles Car Bus Motorcycle"),
        "filename": filename
    })

    _in_memory_db.document_chunks.append({
        "id": "c_t9",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 13,
        "chunk_type": "table",
        "content": "Section: (2) > Table 9\n### Table 9\nHigh density: state = 01, green time = 120 seconds.\nModerate density: state = 10, green time = 60 seconds.",
        "embedding": rag.llm.get_embedding("Table 9 High density green time 120 seconds"),
        "filename": filename
    })

    _in_memory_db.document_chunks.append({
        "id": "c_t12",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 17,
        "chunk_type": "text",
        "content": "Section: N > Table 12 yields the following observations\n### Table 12 yields the following observations\nCommon in low-light or night-vision traffic footage.",
        "embedding": rag.llm.get_embedding("Table 12 yields the following observations low-light night-vision"),
        "filename": filename
    })

    response = rag.query_workspace(ws_id, "What is the table 1 ")

    assert response.is_grounded is True
    assert "Table 1" in response.answer or "PCE" in response.answer or "Car" in response.answer
    assert "Table 12" not in response.answer
    assert "Table 9" not in response.answer
    assert "night-vision" not in response.answer

    page_numbers = [c.page_number for c in response.citations]
    assert 5 in page_numbers
    assert 17 not in page_numbers
    assert 13 not in page_numbers

def test_table_1_query_abstention_when_table_1_is_missing():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())
    filename = "Traffic_System_Report.pdf"

    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": filename}

    # Only contains Table 9 and Table 12
    _in_memory_db.document_chunks.append({
        "id": "c_missing_t9",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 13,
        "chunk_type": "table",
        "content": "Section: (2) > Table 9\n### Table 9\nHigh density: state = 01, green time = 120 seconds.\nModerate density: state = 10, green time = 60 seconds.",
        "embedding": rag.llm.get_embedding("Table 9 High density green time 120 seconds"),
        "filename": filename
    })

    _in_memory_db.document_chunks.append({
        "id": "c_missing_t12",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 17,
        "chunk_type": "text",
        "content": "Section: N > Table 12 yields the following observations\n### Table 12 yields the following observations\nCommon in low-light or night-vision traffic footage.",
        "embedding": rag.llm.get_embedding("Table 12 yields the following observations low-light night-vision"),
        "filename": filename
    })

    response = rag.query_workspace(ws_id, "What is the table 1 ")

    assert response.is_grounded is False
    assert "I couldn't find sufficient evidence" in response.answer
    assert len(response.citations) == 0
