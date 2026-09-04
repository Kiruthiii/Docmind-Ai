from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    workspace_id: str
    filename: str
    storage_path: str
    status: str  # pending, processing, ready, failed
    page_count: int
    created_at: str

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str
