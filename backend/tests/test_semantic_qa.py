import uuid
import pytest
from app.db.supabase_client import _in_memory_db
from app.services.rag_service import RAGService


@pytest.fixture
def setup_semantic_workspace():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Annual_Financial_Report_2025.pdf"}

    # Chunk 1: Revenue and financial performance
    c1 = {
        "id": "c1_rev",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "In fiscal year 2025, Acme Corp generated $150 million in total gross sales revenue, representing a 25% year-over-year growth driven by expanding enterprise software subscriptions.",
        "embedding": rag.llm.get_embedding("Acme Corp gross sales revenue $150 million 25% growth enterprise subscriptions"),
        "filename": "Annual_Financial_Report_2025.pdf"
    }

    # Chunk 2: Operational challenges and driver details
    c2 = {
        "id": "c2_ops",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 5,
        "chunk_type": "text",
        "content": "Operating expenses increased due to hiring 50 new AI research engineers and building a new datacenter infrastructure.",
        "embedding": rag.llm.get_embedding("Operating expenses increased hiring 50 AI research engineers datacenter infrastructure"),
        "filename": "Annual_Financial_Report_2025.pdf"
    }

    # Chunk 3: Tabular metrics
    c3 = {
        "id": "c3_table",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 8,
        "chunk_type": "table",
        "content": "Table 4: Key Performance Indicators\nMetric | FY2024 | FY2025\nActive Users | 1.2M | 2.4M\nCustomer Churn | 4.5% | 1.8%\nNet Promoter Score | 65 | 82",
        "embedding": rag.llm.get_embedding("Table 4 Key Performance Indicators Active Users Customer Churn Net Promoter Score"),
        "filename": "Annual_Financial_Report_2025.pdf"
    }

    # Chunk 4: Similar-but-wrong distractor (different company/year)
    c4 = {
        "id": "c4_distractor",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 12,
        "chunk_type": "text",
        "content": "Historical records show that Beta Corp achieved $10 million in revenue back in 2010.",
        "embedding": rag.llm.get_embedding("Beta Corp revenue 2010 $10 million"),
        "filename": "Annual_Financial_Report_2025.pdf"
    }

    _in_memory_db.document_chunks.extend([c1, c2, c3, c4])
    return rag, ws_id


def test_exact_vs_paraphrased_queries(setup_semantic_workspace):
    rag, ws_id = setup_semantic_workspace

    # Exact query
    q_exact = "What is the revenue reported in the document?"
    resp_exact = rag.query_workspace(ws_id, q_exact)

    # Paraphrased query using completely different vocabulary
    q_paraphrase = "How much money did the company generate according to the report?"
    resp_para = rag.query_workspace(ws_id, q_paraphrase)

    assert resp_exact.is_grounded is True
    assert resp_para.is_grounded is True
    assert "150" in resp_exact.answer
    assert "150" in resp_para.answer


def test_synonym_and_conceptual_queries(setup_semantic_workspace):
    rag, ws_id = setup_semantic_workspace

    # Domain synonyms and conceptual question without exact matching words
    q_synonym = "What were the organization's total gross sales income metrics?"
    resp = rag.query_workspace(ws_id, q_synonym)

    assert resp.is_grounded is True
    assert "150" in resp.answer or "revenue" in resp.answer.lower() or "sales" in resp.answer.lower()


def test_multi_part_and_multi_chunk_queries(setup_semantic_workspace):
    rag, ws_id = setup_semantic_workspace

    q_multipart = "What was the total revenue, what caused the growth, and why did operating expenses increase?"
    resp = rag.query_workspace(ws_id, q_multipart)

    assert resp.is_grounded is True
    answer_low = resp.answer.lower()
    # Check multi-chunk synthesis (revenue from c1, expenses from c2)
    assert "150" in answer_low or "revenue" in answer_low
    assert "subscription" in answer_low or "growth" in answer_low
    assert "engineer" in answer_low or "datacenter" in answer_low or "expense" in answer_low


def test_tabular_data_query(setup_semantic_workspace):
    rag, ws_id = setup_semantic_workspace

    # Table query without stating "Table 4"
    q_table = "How many active users did the company have in FY2025 and what was the churn rate?"
    resp = rag.query_workspace(ws_id, q_table)

    assert resp.is_grounded is True
    assert "2.4" in resp.answer or "1.8" in resp.answer


def test_unsupported_question_abstention(setup_semantic_workspace):
    rag, ws_id = setup_semantic_workspace

    # Question asking for facts not present in the document
    q_unsupported = "What was the company's stock price in 2020?"
    resp = rag.query_workspace(ws_id, q_unsupported)

    assert resp.is_grounded is False
    assert "I couldn't find sufficient evidence" in resp.answer


def test_negative_semantic_retrieval_support_validation():
    """Validates that semantic similarity alone is NOT treated as factual support.
    Chunk A is semantically related ('The company experienced strong revenue growth')
    Chunk B contains exact factual figures ('Revenue increased from $10M to $15M').
    Question: 'What was the exact revenue increase?'
    Expected: Chunk B provides the factual answer ($5M / $10M to $15M).
    """
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Financial_Statement.pdf"}

    chunk_a = {
        "id": "chunk_a_vague",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "The company experienced strong revenue growth across all primary business divisions during the quarter.",
        "embedding": rag.llm.get_embedding("The company experienced strong revenue growth across all primary business divisions"),
        "filename": "Financial_Statement.pdf"
    }

    chunk_b = {
        "id": "chunk_b_exact",
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 2,
        "chunk_type": "text",
        "content": "Revenue increased from $10M to $15M in Q3.",
        "embedding": rag.llm.get_embedding("Revenue increased from $10M to $15M in Q3"),
        "filename": "Financial_Statement.pdf"
    }

    _in_memory_db.document_chunks.extend([chunk_a, chunk_b])

    response = rag.query_workspace(ws_id, "What was the exact revenue increase?")

    assert response.is_grounded is True
    # The factual answer must include the exact numbers from Chunk B ($10M to $15M or $5M)
    assert ("10" in response.answer and "15" in response.answer) or "5" in response.answer or "$5M" in response.answer
    assert any(c.page_number == 2 for c in response.citations)

