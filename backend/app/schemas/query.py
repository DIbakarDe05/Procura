"""
Procura — Query Schemas
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.requirement import RequirementResponse
from app.schemas.recommendation import ReportResponse


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=5, description="Natural-language technical query")
    language: str = Field(default="en", description="Response language code")


class QueryResponse(BaseModel):
    id: str
    query_text: str
    normalized_query: Optional[str] = None
    status: str
    requirements: list[RequirementResponse] = []
    message: str = "Query received and processing started"

    model_config = {"from_attributes": True}


class QueryDetailResponse(BaseModel):
    id: str
    query_text: str
    normalized_query: Optional[str] = None
    status: str
    requirements: list[RequirementResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}
