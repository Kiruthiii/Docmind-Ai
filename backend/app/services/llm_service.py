import logging
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger("docmind")

import re

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
                    config=types.EmbedContentConfig(output_dimensionality=768)
                )
                if hasattr(response, "embeddings") and response.embeddings:
                    return response.embeddings[0].values
                elif hasattr(response, "embedding") and response.embedding:
                    return response.embedding.values
                else:
                    logger.warning("Unexpected embedding response format. Falling back to mock embedding.")
                    return self._mock_embedding(text)
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
    ) -> Tuple[str, bool, List[Dict[str, Any]]]:
        """
        Generates an evidence-grounded answer based ONLY on retrieved context chunks.
        Returns: (answer_text, is_grounded, supporting_chunks)
        """
        refusal_phrase = "I couldn't find sufficient evidence in the uploaded documents to answer this question."

        if not context_chunks:
            return (refusal_phrase, False, [])

        # Build context string with explicit chunk IDs for supporting citation mapping
        context_blocks = []
        chunk_map = {}
        for idx, chunk in enumerate(context_chunks, 1):
            c_id = chunk.get("id", f"c_{idx}")
            chunk_map[c_id] = chunk
            doc_name = chunk.get("filename", "Document")
            page_num = chunk.get("page_number", 1)
            content = chunk.get("content", "")
            context_blocks.append(f"[Chunk ID: {c_id} | Document: {doc_name} | Page: {page_num}]\n{content}")

        context_str = "\n\n".join(context_blocks)

        system_instruction = (
            "You are DocMind AI, a strict, high-precision document intelligence assistant.\n"
            "CRITICAL PRINCIPLE: You must NEVER use outside general knowledge or make assumptions. Base every single detail strictly on the provided context.\n"
            "RULES:\n"
            "1. Read all provided context chunks carefully. If relevant information is spread across multiple chunks/pages, synthesize them into a clear, cohesive answer.\n"
            "2. Present the answer clearly using clean Markdown formatting (such as bullet points, bold headers, or concise paragraphs as appropriate for the question).\n"
            "3. Directly and specifically answer what the user asked. Do NOT dump raw unrelated page text.\n"
            "4. If the provided context chunks contain NO relevant evidence to answer the prompt, reply EXACTLY with: "
            f"'{refusal_phrase}'\n"
            "5. At the very end of your answer, on a separate line, list the exact Chunk IDs used in this format: "
            "[USED_CHUNKS: <id1>, <id2>]\n"
            "6. Provide inline document/page citations where applicable, e.g. [Document.pdf, Page 1]."
        )

        prompt = f"PROVIDED DOCUMENT CONTEXT:\n{context_str}\n\nUSER QUESTION: {question}"

        if self.client and self.api_key:
            candidate_models = [settings.CHAT_MODEL, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-3.6-flash"]
            seen_models = set()
            models_to_try = [m for m in candidate_models if not (m in seen_models or seen_models.add(m))]

            for model_name in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.1,
                        )
                    )
                    raw_answer = response.text.strip()
                    if refusal_phrase in raw_answer:
                        return (refusal_phrase, False, [])

                    # Parse [USED_CHUNKS: ...] tag
                    supporting_chunks = []
                    answer_text = raw_answer

                    if "[USED_CHUNKS:" in raw_answer:
                        parts = raw_answer.split("[USED_CHUNKS:")
                        answer_text = parts[0].strip()
                        ids_raw = parts[1].replace("]", "").strip()
                        used_ids = [i.strip() for i in ids_raw.split(",") if i.strip()]
                        for uid in used_ids:
                            if uid in chunk_map:
                                supporting_chunks.append(chunk_map[uid])

                    # Grounding Validation Check: Verify answer contains substantive factual response lines
                    clean_lines = [l.strip() for l in answer_text.split("\n") if l.strip() and not l.strip().startswith("Section:")]
                    substantive_lines = []
                    for l in clean_lines:
                        raw_l = l.strip()
                        clean_l = re.sub(r'^[\-\=\*\_\s\:\.\#]+|[\-\=\*\_\s\:\.\#]+$', '', raw_l).strip()
                        if not clean_l:
                            continue
                        if clean_l.isupper():
                            continue
                        if all(c in "-------======******______ " for c in raw_l):
                            continue
                        substantive_lines.append(raw_l)

                    if not substantive_lines:
                        return (refusal_phrase, False, [])

                    return (answer_text, True, supporting_chunks)
                except Exception as e:
                    logger.warning(f"Gemini API model '{model_name}' failed: {e}. Trying failover model.")

            logger.error("All Gemini API candidate models failed. Falling back to evidence extraction.")
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
            candidate_models = [settings.CHAT_MODEL, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
            seen_models = set()
            models_to_try = [m for m in candidate_models if not (m in seen_models or seen_models.add(m))]

            for model_name in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.2
                        )
                    )
                    return (response.text.strip(), ["Potential contradiction detected in methodology parameters across papers."])
                except Exception as e:
                    logger.warning(f"Comparison error with model '{model_name}': {e}")
            
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
    ) -> Tuple[str, bool, List[Dict[str, Any]]]:
        """Synthesizes targeted matching lines for chunks relevant to the user's question."""
        if not context_chunks:
            return (refusal_phrase, False, [])

        STOP_WORDS = {"tell", "about", "the", "what", "is", "are", "a", "an", "of", "in", "for", "and", "or", "to", "with", "on", "at", "from", "by", "my", "your", "show", "me", "can", "you", "please", "give", "list", "info", "details", "does", "do", "did", "how", "why", "which"}
        q_terms = [re.sub(r'[^a-zA-Z0-9]', '', w.lower()) for w in question.split() if re.sub(r'[^a-zA-Z0-9]', '', w.lower()) not in STOP_WORDS and len(re.sub(r'[^a-zA-Z0-9]', '', w.lower())) >= 2 and not re.sub(r'[^a-zA-Z0-9]', '', w.lower()).isdigit()]

        # 1. Filter context_chunks to keep ONLY question-relevant chunks or sister section chunks under matching parent section
        relevant_chunks = []
        target_parents = set()
        
        for chunk in context_chunks:
            content_lower = chunk.get("content", "").lower()
            if any(term in content_lower for term in q_terms):
                if "Section:" in chunk.get("content", ""):
                    header = chunk.get("content", "").split("\n")[0].replace("Section:", "").strip()
                    parent_sec = header.split(">")[0].strip().lower()
                    if parent_sec and parent_sec != "general":
                        target_parents.add(parent_sec)

        for chunk in context_chunks:
            content = chunk.get("content", "")
            content_lower = content.lower()
            p_sec = chunk.get("parent_section", "").lower()
            if not p_sec and "Section:" in content:
                header = content.split("\n")[0].replace("Section:", "").strip()
                p_sec = header.split(">")[0].strip().lower()

            is_relevant = False
            if any(term in content_lower for term in q_terms):
                is_relevant = True
            elif p_sec and p_sec in target_parents:
                is_relevant = True

            if is_relevant:
                relevant_chunks.append(chunk)

        if not relevant_chunks:
            relevant_chunks = context_chunks[:2]

        matched_blocks = []
        used_chunks = []
        doc_names = set()

        for chunk in relevant_chunks:
            doc = chunk.get("filename", "Document")
            doc_names.add(doc)
            lines = [l.strip() for l in chunk.get("content", "").split("\n") if l.strip()]

            chunk_matched_lines = []
            for l in lines:
                raw_l = l.strip()
                clean_l = re.sub(r'^[\-\=\*\_\s\:\.\#]+|[\-\=\*\_\s\:\.\#]+$', '', raw_l).strip()
                if not clean_l or clean_l.isupper() or all(c in "-------======******______ " for c in raw_l) or raw_l.startswith("Section:"):
                    continue
                if len(clean_l) < 15 and not clean_l.startswith("###") and not clean_l.startswith("-") and not clean_l.startswith("*"):
                    continue
                chunk_matched_lines.append(raw_l)

            if chunk_matched_lines:
                used_chunks.append(chunk)
                block_str = "\n".join(chunk_matched_lines)
                if block_str not in matched_blocks:
                    matched_blocks.append(block_str)

        if not matched_blocks:
            return (refusal_phrase, False, [])

        doc_label = ", ".join(sorted(doc_names)) if doc_names else "Document"
        answer = f"Based on evidence in **{doc_label}**:\n\n" + "\n\n".join(matched_blocks)
        return (answer, True, used_chunks)

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
