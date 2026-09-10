from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    filename: str
    storage_path: Optional[str] = Field(default="")
    status: Optional[str] = Field(default="ready")  # pending, processing, ready, failed
    page_count: Optional[int] = Field(default=0)
    created_at: Optional[str] = Field(default="2026-08-24T20:00:00Z")

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
