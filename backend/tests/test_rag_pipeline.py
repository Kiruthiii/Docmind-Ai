import pytest
from app.services.rag_service import RAGService
from app.db.supabase_client import _in_memory_db
import uuid

def test_rag_abstention_guardrail_when_no_evidence():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    
    # Query workspace with 0 uploaded documents
    response = rag.query_workspace(ws_id, "What dataset was used in Paper A?")
    
    assert response.is_grounded is False
    assert "I couldn't find sufficient evidence in the uploaded documents to answer this question." in response.answer
    assert len(response.citations) == 0

def test_rag_grounded_answer_with_evidence():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    # Add mock chunk to in-memory store
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "ResNet_Paper.pdf"}
    _in_memory_db.document_chunks.append({
        "id": str(uuid.uuid4()),
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 3,
        "chunk_type": "text",
        "content": "ResNet-50 achieved an accuracy of 94.2% on the ImageNet dataset using residual skip connections.",
        "embedding": rag.llm.get_embedding("ResNet-50 accuracy ImageNet dataset"),
        "filename": "ResNet_Paper.pdf"
    })

    # Query with answerable question
    response = rag.query_workspace(ws_id, "What accuracy did ResNet-50 achieve on ImageNet?")

    assert response.is_grounded is True
    assert "94.2%" in response.answer or "ResNet" in response.answer
    assert len(response.citations) > 0
    assert response.citations[0].document_name == "ResNet_Paper.pdf"
    assert response.citations[0].page_number == 3

def test_document_comparison():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "ViT_Paper.pdf"}
    _in_memory_db.document_chunks.append({
        "id": str(uuid.uuid4()),
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 1,
        "chunk_type": "text",
        "content": "Vision Transformer (ViT) achieved 96.5% top-1 accuracy on ImageNet.",
        "embedding": rag.llm.get_embedding("Vision Transformer ViT accuracy"),
        "filename": "ViT_Paper.pdf"
    })

    comp = rag.compare_documents(ws_id, categories=["Summary", "Accuracy"])
    assert comp.markdown_matrix is not None
    assert "| Comparison Category |" in comp.markdown_matrix or "| Category |" in comp.markdown_matrix

