import unittest
from unittest.mock import MagicMock, patch

from app.db.supabase_client import _in_memory_db
from app.schemas.chat import QueryIntent
from app.services.agents.query_agent import StructuredQuery
from app.services.agents.retrieval_agent import RetrievalIntelligenceAgent
from app.services.agents.validation_agent import EvidenceValidationAgent
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService


class TestJavascriptRAGPipeline(unittest.TestCase):
    def setUp(self):
        _in_memory_db.documents.clear()
        _in_memory_db.document_chunks.clear()

        self.doc_id = "javascript-pdf-doc-123"
        self.workspace_id = "ws-test-js-456"
        self.filename = "javascript.pdf"

        # Populate sample chunks for javascript.pdf
        self.sample_chunks = [
            {
                "id": "c1",
                "document_id": self.doc_id,
                "workspace_id": self.workspace_id,
                "page_number": 1,
                "chunk_type": "text",
                "content_type": "text",
                "document_position": "introduction",
                "section_path": "Chapter 1: Introduction",
                "parent_section": "Introduction to JavaScript",
                "content": "JavaScript is a lightweight, cross-platform, interpreted programming language used for scripting web pages.",
                "embedding": [0.1] * 768,
                "filename": self.filename,
                "document_type": "Programming Book",
                "document_type_confidence": 0.95,
                "classification_method": "llm"
            },
            {
                "id": "c2",
                "document_id": self.doc_id,
                "workspace_id": self.workspace_id,
                "page_number": 2,
                "chunk_type": "text",
                "content_type": "text",
                "document_position": "data_types",
                "section_path": "Chapter 2: Variables and Data Types",
                "parent_section": "Data Types in JavaScript",
                "content": "JavaScript has primitive data types: Number, String, Boolean, Undefined, Null, Symbol, and BigInt, alongside Objects.",
                "embedding": [0.2] * 768,
                "filename": self.filename,
                "document_type": "Programming Book",
                "document_type_confidence": 0.95,
                "classification_method": "llm"
            }
        ]
        _in_memory_db.document_chunks.extend(self.sample_chunks)
        _in_memory_db.documents[self.doc_id] = {
            "id": self.doc_id,
            "workspace_id": self.workspace_id,
            "filename": self.filename,
            "document_type": "Programming Book",
            "document_type_confidence": 0.95,
            "classification_method": "llm"
        }

    def test_gemini_429_rate_limit_retry_handling(self):
        """Verify that Gemini API 429 rate limit triggers exponential backoff retry and falls back without throwing NameError."""
        llm = LLMService()
        mock_client = MagicMock()
        
        # Simulate 429 rate limit exception on first attempt, success on second
        mock_response = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.05] * 768
        mock_response.embeddings = [mock_embedding]

        mock_client.models.embed_content.side_effect = [
            Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded"),
            mock_response
        ]
        llm.client = mock_client
        llm.api_key = "test_key"

        with patch("time.sleep") as mock_sleep:
            res = llm.get_embeddings_batch(["Test input string"])
            self.assertEqual(len(res), 1)
            self.assertEqual(len(res[0]), 768)
            self.assertTrue(mock_sleep.called)
            self.assertEqual(mock_client.models.embed_content.call_count, 2)

    def test_obsolete_evidence_column_not_queried(self):
        """Verify retrieval agent queries document metadata without obsolete 'documents.evidence' column."""
        retrieval_agent = RetrievalIntelligenceAgent()
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.execute.return_value.data = [{
            "id": self.doc_id,
            "filename": self.filename,
            "document_category": "General",
            "document_type": "Programming Book",
            "document_type_confidence": 0.95,
            "classification_method": "llm"
        }]

        s_query = StructuredQuery(
            original_query="What is JavaScript?",
            intent="FACT_LOOKUP",
            answer_type="FACT",
            information_needed=["JavaScript"]
        )

        with patch("app.services.agents.retrieval_agent.get_supabase_client", return_value=mock_client):
            chunks = retrieval_agent.retrieve_candidates(
                workspace_id=self.workspace_id,
                structured_query=s_query,
                query_vector=[0.1] * 768,
                top_k=5
            )

        all_select_args = [c[0][0] for c in mock_table.select.call_args_list]
        for arg in all_select_args:
            self.assertNotIn("evidence", arg)

    def test_retrieval_returns_candidate_chunks_for_javascript(self):
        """Verify that retrieval returns valid candidate chunks with expected document ID and filename."""
        retrieval_agent = RetrievalIntelligenceAgent()
        s_query = StructuredQuery(
            original_query="What is JavaScript?",
            intent="FACT_LOOKUP",
            answer_type="FACT",
            information_needed=["JavaScript"]
        )

        with patch("app.services.agents.retrieval_agent.get_supabase_client", return_value=None):
            chunks = retrieval_agent.retrieve_candidates(
                workspace_id=self.workspace_id,
                structured_query=s_query,
                query_vector=[0.1] * 768,
                top_k=5
            )

        self.assertGreater(len(chunks), 0)
        self.assertEqual(chunks[0]["document_id"], self.doc_id)
        self.assertEqual(chunks[0]["filename"], self.filename)

    def test_evidence_validation_and_no_false_refusal(self):
        """Verify that evidence validation succeeds and RAG pipeline does NOT refuse when evidence exists."""
        validator = EvidenceValidationAgent()
        s_query = StructuredQuery(
            original_query="What are the different data types in JavaScript?",
            intent="FACT_LOOKUP",
            answer_type="FACT",
            information_needed=["data types", "JavaScript"]
        )

        validation_res = validator.validate_evidence(
            structured_query=s_query,
            assembled_chunks=self.sample_chunks,
            attempt=1
        )

        self.assertTrue(validation_res.sufficient)
        self.assertFalse(validation_res.is_abstention)
        self.assertGreater(len(validation_res.minimal_evidence), 0)


if __name__ == "__main__":
    unittest.main()
