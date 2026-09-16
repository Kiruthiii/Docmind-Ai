from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    filename: str
    storage_path: Optional[str] = Field(default="")
    status: Optional[str] = Field(default="ready")  # pending, processing, ready, failed
    page_count: Optional[int] = Field(default=0)
    created_at: Optional[str] = Field(default="2026-08-24T20:00:00Z")
    document_category: Optional[str] = Field(default="General")
    document_type: Optional[str] = Field(default="General Document")
    document_type_confidence: Optional[float] = Field(default=1.0)
    classification_method: Optional[str] = Field(default="default")
    evidence: Optional[List[str]] = Field(default_factory=list)


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
    document_category: Optional[str] = Field(default="General")
    document_type: Optional[str] = Field(default="General Document")
    document_type_confidence: Optional[float] = Field(default=1.0)
    classification_method: Optional[str] = Field(default="default")
    evidence: Optional[List[str]] = Field(default_factory=list)


class DocumentAnalysisResponse(BaseModel):
    document_id: str
    filename: str
    document_category: str = Field(default="General")
    document_type: str = Field(default="General Document")
    document_type_confidence: float = Field(default=1.0)
    classification_method: str = Field(default="default")
    evidence: List[str] = Field(default_factory=list)
    page_count: int = Field(default=0)
    total_chunks: int = Field(default=0)
    detected_sections: List[str] = Field(default_factory=list)
    detected_positions: List[str] = Field(default_factory=list)
    content_types: List[str] = Field(default_factory=list)
