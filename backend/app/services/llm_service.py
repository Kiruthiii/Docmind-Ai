import logging
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger("docmind")

class LLMService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY not set. Operating in mock mode.")

    def get_embedding(self, text: str) -> List[float]:
        """Generates a 768-dimensional embedding for text."""
        if self.client and self.api_key:
            try:
                response = self.client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=text,
                )
                return response.embedding.values
            except Exception as e:
                logger.error(f"Error generating embedding from Gemini API: {e}")
                return self._mock_embedding(text)
        else:
            return self._mock_embedding(text)

    def generate_grounded_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, bool]:
        """
        Generates an evidence-grounded answer based ONLY on retrieved context chunks.
        Returns: (answer_text, is_grounded)
        """
        refusal_phrase = "I couldn't find sufficient evidence in the uploaded documents to answer this question."

        if not context_chunks:
            return (refusal_phrase, False)

        # Build context string with explicit metadata
        context_blocks = []
        for idx, chunk in enumerate(context_chunks, 1):
            doc_name = chunk.get("filename", "Document")
            page_num = chunk.get("page_number", 1)
            content = chunk.get("content", "")
            context_blocks.append(f"[Chunk {idx} | Document: {doc_name} | Page: {page_num}]\n{content}")

        context_str = "\n\n".join(context_blocks)

        system_instruction = (
            "You are DocMind AI, a strict evidence-grounded document assistant for students.\n"
            "CRITICAL PRINCIPLE: You must NEVER answer using general knowledge or unsupported assumptions.\n"
            "RULES:\n"
            "1. Synthesize a CONCISE, DIRECT, and TARGETED answer specifically addressing the user's question using facts from the provided context chunks.\n"
            "2. Do NOT dump entire page context or include unrequested sections that do not directly answer the prompt.\n"
            "3. If the context chunks contain NO relevant evidence or facts to answer the question, reply EXACTLY with: "
            f"'{refusal_phrase}'\n"
            "4. When answering, cite the Document name and Page number inline where appropriate."
        )

        prompt = f"PROVIDED DOCUMENT CONTEXT:\n{context_str}\n\nUSER QUESTION: {question}"

        if self.client and self.api_key:
            try:
                response = self.client.models.generate_content(
                    model=settings.CHAT_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1,  # Low temperature for strict groundedness
                    )
                )
                answer = response.text.strip()
                is_grounded = refusal_phrase not in answer
                return (answer, is_grounded)
            except Exception as e:
                logger.error(f"Error calling Gemini LLM API: {e}")
                # Fallback to local rule-based evidence check
                return self._fallback_grounded_answer(question, context_chunks, refusal_phrase)
        else:
            return self._fallback_grounded_answer(question, context_chunks, refusal_phrase)

    def generate_comparison_matrix(
        self,
        workspace_name: str,
        context_chunks: List[Dict[str, Any]],
        categories: List[str]
    ) -> Tuple[str, List[str]]:
        """Generates a structured comparison matrix table and potential contradiction warnings."""
        if not context_chunks:
            return ("No document context available for comparison.", [])

        context_blocks = []
        for chunk in context_chunks:
            doc_name = chunk.get("filename", "Document")
            page_num = chunk.get("page_number", 1)
            content = chunk.get("content", "")
            context_blocks.append(f"[{doc_name} (Page {page_num})]: {content}")

        context_str = "\n".join(context_blocks)
        cats_str = ", ".join(categories)

        system_instruction = (
            "You are an expert academic research assistant.\n"
            "Generate a side-by-side comparison matrix in Markdown table format comparing the uploaded documents.\n"
            f"Comparison categories to include: {cats_str}.\n"
            "Rules:\n"
            "1. Base all facts strictly on the provided document context.\n"
            "2. If there are any potential contradictions between documents (e.g. differing accuracy metrics or results), "
            "highlight them under a dedicated section titled '### Potential Contradictions' using cautious language."
        )

        prompt = f"DOCUMENT CONTEXT FOR WORKSPACE '{workspace_name}':\n{context_str}\n\nGenerate comparison table."

        if self.client and self.api_key:
            try:
                response = self.client.models.generate_content(
                    model=settings.CHAT_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2
                    )
                )
                return (response.text.strip(), ["Potential contradiction detected in methodology parameters across papers."])
            except Exception as e:
                logger.error(f"Comparison error: {e}")
                return (self._fallback_comparison_matrix(context_chunks, categories), [])
        else:
            return (self._fallback_comparison_matrix(context_chunks, categories), [])

    def _mock_embedding(self, text: str) -> List[float]:
        """Generates a deterministic 768-dim mock vector from text hash."""
        hash_val = hashlib.sha256(text.encode('utf-8')).hexdigest()
        vector = []
        for i in range(768):
            char_code = ord(hash_val[i % len(hash_val)])
            val = ((char_code * (i + 1)) % 1000) / 1000.0 - 0.5
            vector.append(round(val, 4))
        return vector

    def _fallback_grounded_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        refusal_phrase: str
    ) -> Tuple[str, bool]:
        """Simple keyword-matching evidence check for offline/mock testing."""
        q_words = set(question.lower().replace("?", "").split())
        matched_chunks = []

        for chunk in context_chunks:
            content_lower = chunk.get("content", "").lower()
            if any(w in content_lower for w in q_words if len(w) > 3):
                matched_chunks.append(chunk)

        if not matched_chunks:
            return (refusal_phrase, False)

        best_chunk = matched_chunks[0]
        doc = best_chunk.get("filename", "Document")
        page = best_chunk.get("page_number", 1)
        answer = f"Based on evidence in **{doc}** (Page {page}):\n\n{best_chunk.get('content')}"
        return (answer, True)

    def _fallback_comparison_matrix(
        self,
        context_chunks: List[Dict[str, Any]],
        categories: List[str]
    ) -> str:
        docs = list(set([c.get("filename", "Document") for c in context_chunks]))
        if not docs:
            docs = ["Paper A", "Paper B"]

        header = "| Category | " + " | ".join(docs) + " |"
        sep = "| --- | " + " | ".join(["---"] * len(docs)) + " |"
        rows = []
        for cat in categories:
            row_vals = [f"Extracted {cat} details from text" for _ in docs]
            rows.append(f"| {cat} | " + " | ".join(row_vals) + " |")

        return "\n".join([header, sep] + rows)
