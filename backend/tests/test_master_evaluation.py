import uuid
import pytest
from app.services.rag_service import RAGService
from app.db.supabase_client import _in_memory_db
from app.schemas.chat import ChatMessageResponse

@pytest.fixture
def sample_workspace():
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    _in_memory_db.documents[doc_id] = {
        "id": doc_id,
        "filename": "Research_Paper_Evaluation.pdf"
    }

    rag = RAGService()

    # Ingest representative chunks
    chunks = [
        {
            "id": "c_intro",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "document_position": "introduction",
            "section_hierarchy": ["Introduction"],
            "parent_section": "INTRODUCTION",
            "section_path": "INTRODUCTION",
            "content": "Section: INTRODUCTION\nIntelligent Transportation Systems (ITS) leverage deep neural networks to optimize traffic control. In this research, we introduce RSEN, a novel spatial-temporal network.",
            "embedding": rag.llm.get_embedding("Intelligent Transportation Systems ITS RSEN spatial temporal traffic control research introduction"),
            "filename": "Research_Paper_Evaluation.pdf"
        },
        {
            "id": "c_dataset",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 3,
            "document_position": "methodology",
            "section_hierarchy": ["Methodology", "Datasets"],
            "parent_section": "METHODOLOGY",
            "section_path": "METHODOLOGY > Datasets",
            "content": "Section: METHODOLOGY > Datasets\nThe proposed model was trained and evaluated on the CIFAR-10 dataset and the Cityscapes traffic dataset.",
            "embedding": rag.llm.get_embedding("The proposed model was trained and evaluated on the CIFAR-10 dataset and Cityscapes traffic dataset."),
            "filename": "Research_Paper_Evaluation.pdf"
        },
        {
            "id": "c_results",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 6,
            "document_position": "results",
            "section_hierarchy": ["Results"],
            "parent_section": "RESULTS",
            "section_path": "RESULTS",
            "content": "Section: RESULTS\nExperimental results show that RSEN achieved a mean Average Precision (mAP) of 89.4% on traffic detection benchmarks, outperforming baseline models by 5.2%.",
            "embedding": rag.llm.get_embedding("Experimental results show that RSEN achieved a mean Average Precision mAP of 89.4% on traffic benchmarks."),
            "filename": "Research_Paper_Evaluation.pdf"
        }
    ]

    # Add Page 1 Header chunk with Title, Authors, Publication Date, and Dataset Location
    chunks.extend([
        {
            "id": "c_header",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "document_position": "introduction",
            "chunk_type": "header",
            "content_type": "header",
            "section_hierarchy": ["Header"],
            "parent_section": "HEADER",
            "section_path": "HEADER",
            "content": "An Edge-Deployed Real-Time Adaptive Traffic Light Control System Using YOLO-Based Vehicle Detection and PCE-Aware Density Estimation\nDate of publication August 26, 2025.\nAuthors: A. Smith, B. Jones, and K. Assaleh.\nPublished in IEEE Access.",
            "embedding": rag.llm.get_embedding("An Edge-Deployed Real-Time Adaptive Traffic Light Control System Authors A. Smith B. Jones K. Assaleh Date of publication August 26 2025 IEEE Access"),
            "filename": "Research_Paper_Evaluation.pdf"
        },
        {
            "id": "c_calc",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 4,
            "document_position": "methodology",
            "section_hierarchy": ["Methodology", "Traffic Density Calculation"],
            "parent_section": "METHODOLOGY",
            "section_path": "METHODOLOGY > Traffic Density Calculation",
            "content": "Section: METHODOLOGY > Traffic Density Calculation\nTraffic density is calculated as traffic_density = (vehicle_count * PCE_weight) / lane_area, where PCE_weight represents Passenger Car Equivalent and lane_area is measured in square meters.",
            "embedding": rag.llm.get_embedding("Traffic density is calculated as traffic_density = (vehicle_count * PCE_weight) / lane_area Passenger Car Equivalent calculation formula"),
            "filename": "Research_Paper_Evaluation.pdf"
        },
        {
            "id": "c_contrib",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 2,
            "document_position": "introduction",
            "section_hierarchy": ["Introduction", "Contributions"],
            "parent_section": "INTRODUCTION",
            "section_path": "INTRODUCTION > Key Contributions",
            "content": "Section: INTRODUCTION > Key Contributions\nThe key contributions of this work are as follows:\n1) A novel spatial-temporal network (RSEN) for traffic flow forecasting.\n2) A PCE-aware traffic density estimation algorithm.\n3) An edge-deployed adaptive traffic signal controller.",
            "embedding": rag.llm.get_embedding("The key contributions of this work are as follows RSEN PCE-aware traffic density estimation adaptive traffic signal controller"),
            "filename": "Research_Paper_Evaluation.pdf"
        },
        {
            "id": "c_problem",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 1,
            "document_position": "introduction",
            "section_hierarchy": ["Introduction", "Motivation"],
            "parent_section": "INTRODUCTION",
            "section_path": "INTRODUCTION > Motivation",
            "content": "Section: INTRODUCTION > Motivation\nThe main problem addressed by this paper is severe urban traffic congestion and excessive vehicle delay caused by traditional fixed-timer traffic signal controllers.",
            "embedding": rag.llm.get_embedding("The main problem addressed by this paper is severe urban traffic congestion and excessive vehicle delay caused by traditional fixed-timer traffic signal controllers"),
            "filename": "Research_Paper_Evaluation.pdf"
        },
        {
            "id": "c_yolo",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 3,
            "document_position": "methodology",
            "section_hierarchy": ["Methodology", "Vehicle Detection"],
            "parent_section": "METHODOLOGY",
            "section_path": "METHODOLOGY > Vehicle Detection",
            "content": "Section: METHODOLOGY > Vehicle Detection\nWe utilized YOLOv8 as the primary vehicle detection model for processing real-time traffic camera feeds.",
            "embedding": rag.llm.get_embedding("We utilized YOLOv8 as the primary vehicle detection model for processing real-time traffic camera feeds"),
            "filename": "Research_Paper_Evaluation.pdf"
        },
        {
            "id": "c_algo",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 5,
            "document_position": "methodology",
            "section_hierarchy": ["Methodology", "Control Algorithm"],
            "parent_section": "METHODOLOGY",
            "section_path": "METHODOLOGY > Control Algorithm",
            "content": "Section: METHODOLOGY > Control Algorithm\nThe adaptive traffic light control algorithm dynamically adjusts green signal duration based on real-time traffic density estimates from RSEN nodes.",
            "embedding": rag.llm.get_embedding("The adaptive traffic light control algorithm dynamically adjusts green signal duration based on real-time traffic density estimates"),
            "filename": "Research_Paper_Evaluation.pdf"
        },
        {
            "id": "c_location",
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": 4,
            "document_position": "methodology",
            "section_hierarchy": ["Methodology", "Data Collection"],
            "parent_section": "METHODOLOGY",
            "section_path": "METHODOLOGY > Data Collection",
            "content": "Section: METHODOLOGY > Data Collection\nTraffic video recordings were collected at Allama Shabbir Usmani Road, Karachi, Pakistan during peak hours.",
            "embedding": rag.llm.get_embedding("Traffic video recordings collected at Allama Shabbir Usmani Road Karachi Pakistan peak hours"),
            "filename": "Research_Paper_Evaluation.pdf"
        }
    ])

    _in_memory_db.document_chunks.extend(chunks)

    return ws_id, doc_id

# ==================== 11 CORE BEHAVIORAL QUESTIONS TEST MATRIX ====================

def test_1_overview_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "What is this paper about?")
    assert response.is_grounded is True
    assert "RSEN" in response.answer or "traffic" in response.answer or "Transportation" in response.answer

def test_2_problem_statement_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "What is the main problem addressed by the paper?")
    assert response.is_grounded is True
    assert "congestion" in response.answer.lower() or "fixed-timer" in response.answer.lower() or "delay" in response.answer.lower()

def test_3_contributions_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "What are the main contributions of this work?")
    assert response.is_grounded is True
    assert "contributions" in response.answer.lower() or "RSEN" in response.answer or "PCE-aware" in response.answer

def test_4_calculation_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "How is traffic density calculated?")
    assert response.is_grounded is True
    assert "traffic_density =" in response.answer or "vehicle_count" in response.answer or "PCE_weight" in response.answer or "calculated" in response.answer.lower()

def test_5_dataset_location_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "Where was the traffic dataset collected?")
    assert response.is_grounded is True
    assert "Karachi" in response.answer or "Allama Shabbir Usmani" in response.answer

def test_6_title_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "What is the title of the paper?")
    assert response.is_grounded is True
    assert "Adaptive Traffic Light Control System" in response.answer or "Edge-Deployed" in response.answer

def test_7_authors_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "Who are the authors of the paper?")
    assert response.is_grounded is True
    assert "Smith" in response.answer or "Jones" in response.answer or "Assaleh" in response.answer

def test_8_publication_date_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "When was the paper published?")
    assert response.is_grounded is True
    assert "2025" in response.answer or "August 26" in response.answer

def test_9_vehicle_detection_model_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "What model was used for vehicle detection?")
    assert response.is_grounded is True
    assert "YOLOv8" in response.answer or "YOLO" in response.answer

def test_10_algorithm_workflow_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "How does the adaptive traffic light control algorithm work?")
    assert response.is_grounded is True
    assert "green signal" in response.answer.lower() or "density" in response.answer.lower()

def test_11_no_evidence_abstention_query(sample_workspace):
    ws_id, _ = sample_workspace
    rag = RAGService()

    response = rag.query_workspace(ws_id, "What is the cost of deploying this system?")
    assert response.is_grounded is False
    assert "couldn't find sufficient evidence" in response.answer
