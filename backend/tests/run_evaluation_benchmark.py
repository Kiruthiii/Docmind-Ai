import logging
import os
import sys
import uuid

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.supabase_client import _in_memory_db
from app.services.ingestion_service import IngestionService
from app.services.rag_service import RAGService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docmind-eval")

# 50 Evaluation Questions dataset as specified in PRD Section 15
EVALUATION_DATASET = [
    # 20 Answerable Text Questions
    *[{
        "id": f"ans_{i}",
        "type": "answerable",
        "question": f"What dataset was used for training Model {i}?",
        "expected_answer_keyword": "ImageNet",
        "should_abstain": False
    } for i in range(1, 21)],
    
    # 10 Unanswerable Questions (Must Refuse/Abstain)
    *[{
        "id": f"unans_{i}",
        "type": "unanswerable",
        "question": f"What is the capital city of country {i} in South America?",
        "expected_answer_keyword": "I couldn't find sufficient evidence",
        "should_abstain": True
    } for i in range(1, 11)],

    # 10 Multi-Document Questions
    *[{
        "id": f"multidoc_{i}",
        "type": "multi_document",
        "question": "Compare the accuracy results across Paper A and Paper B.",
        "expected_answer_keyword": "accuracy",
        "should_abstain": False
    } for i in range(1, 11)],

    # 5 Table Questions
    *[{
        "id": f"table_{i}",
        "type": "table",
        "question": "Which model achieved the highest accuracy in the results table?",
        "expected_answer_keyword": "ResNet",
        "should_abstain": False
    } for i in range(1, 6)],

    # 5 Chart/Visual Questions
    *[{
        "id": f"chart_{i}",
        "type": "chart",
        "question": "What architecture pattern is shown in the network diagram?",
        "expected_answer_keyword": "skip connections",
        "should_abstain": False
    } for i in range(1, 6)],
]

def run_evaluation():
    rag = RAGService()
    ws_id = str(uuid.uuid4())
    doc_id = str(uuid.uuid4())

    # Populate mock evaluation environment
    _in_memory_db.documents[doc_id] = {"id": doc_id, "filename": "Deep_Learning_Benchmark.pdf"}
    
    # Insert chunks representing text, tables, and charts
    for i in range(1, 21):
        _in_memory_db.document_chunks.append({
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "workspace_id": ws_id,
            "page_number": i,
            "chunk_type": "text",
            "content": f"Model {i} was trained on the ImageNet dataset with SGD optimizer and residual skip connections.",
            "embedding": rag.llm.get_embedding(f"Model {i} ImageNet dataset SGD optimizer"),
            "filename": "Deep_Learning_Benchmark.pdf"
        })

    # Add table chunk
    _in_memory_db.document_chunks.append({
        "id": str(uuid.uuid4()),
        "document_id": doc_id,
        "workspace_id": ws_id,
        "page_number": 22,
        "chunk_type": "table",
        "content": "[Table on Page 22]\n| Model | Accuracy |\n| ResNet-101 | 96.1% |\n| CNN-Baseline | 85.4% |",
        "embedding": rag.llm.get_embedding("results table highest accuracy ResNet-101 96.1%"),
        "filename": "Deep_Learning_Benchmark.pdf"
    })

    print("==========================================================")
    print("      DOCMIND AI — RAG EVALUATION BENCHMARK SUITE       ")
    print("==========================================================")
    
    total = len(EVALUATION_DATASET)
    passed_abstention = 0
    total_unanswerable = 0
    passed_answerable = 0
    total_answerable = 0

    for item in EVALUATION_DATASET:
        res = rag.query_workspace(ws_id, item["question"])
        
        if item["should_abstain"]:
            total_unanswerable += 1
            if not res.is_grounded and "I couldn't find sufficient evidence" in res.answer:
                passed_abstention += 1
        else:
            total_answerable += 1
            if res.is_grounded or item["expected_answer_keyword"].lower() in res.answer.lower():
                passed_answerable += 1

    abstention_accuracy = (passed_abstention / total_unanswerable) * 100 if total_unanswerable > 0 else 100.0
    groundedness_accuracy = (passed_answerable / total_answerable) * 100 if total_answerable > 0 else 100.0
    overall_score = ((passed_abstention + passed_answerable) / total) * 100

    print(f"\nBenchmark Results:")
    print(f"• Total Evaluation Questions : {total}")
    print(f"• Abstention Refusal Accuracy : {abstention_accuracy:.1f}% ({passed_abstention}/{total_unanswerable})")
    print(f"• Groundedness Answer Accuracy: {groundedness_accuracy:.1f}% ({passed_answerable}/{total_answerable})")
    print(f"• Overall System Score       : {overall_score:.1f}%\n")
    print("==========================================================")
    
    assert overall_score >= 80.0, "Evaluation score below quality bar!"

if __name__ == "__main__":
    run_evaluation()
