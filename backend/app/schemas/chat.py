from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Citation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    content_snippet: str
    chunk_type: str

class Claim(BaseModel):
    text: str
    evidence_ids: List[str] = []

class GroundedAnswerSchema(BaseModel):
    answer: str
    answer_type: str
    sufficient_evidence: bool = True
    claims: List[Claim] = []

class ChatMessageRequest(BaseModel):
    workspace_id: str
    session_id: Optional[str] = None
    question: str = Field(..., json_schema_extra={"example": "What methodology was used in Paper A?"})
    show_sources: bool = Field(default=True)

class ChatMessageResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    is_grounded: bool
    citations: List[Citation] = []

class ComparisonRequest(BaseModel):
    workspace_id: str
    document_ids: Optional[List[str]] = None  # None means compare all in workspace
    categories: List[str] = Field(default=["Summary", "Methodology", "Results", "Advantages", "Limitations"])

class ComparisonResponse(BaseModel):
    workspace_id: str
    markdown_matrix: str
    potential_contradictions: List[str] = []
    citations: List[Citation] = []
