from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., json_schema_extra={"example": "Machine Learning Research"})
    user_id: Optional[str] = Field(default="demo-student-user")

class WorkspaceResponse(BaseModel):
    id: str
    user_id: str
    name: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)
