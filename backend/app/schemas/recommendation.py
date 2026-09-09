"""
Procura — Recommendation Schemas
"""

from typing import Optional, Any
from pydantic import BaseModel


class CoverageDetail(BaseModel):
    category: str
    status: str  # "covered", "partial", "missing", "not_applicable"
    detail: Optional[str] = None


class RelatedStandardSchema(BaseModel):
    standard_number: str
    title: str
    reference_type: str
    description: Optional[str] = None


class RecommendationResponse(BaseModel):
    id: str
    standard_number: str
    standard_title: str
    relevance_score: Optional[float] = None
    confidence_score: Optional[float] = None
    compliance_score: Optional[float] = None  # null for generic queries
    applicable: bool = True
    applicability_level: str = "HIGH"  # HIGH, MEDIUM, LOW
    reasoning: Optional[str] = None
    coverage: list[CoverageDetail] = []
    gaps: list[str] = []
    related_standards: list[RelatedStandardSchema] = []
    version_info: Optional[dict] = None
    certification_info: Optional[dict] = None
    status: str = "pending"

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    """Full structured recommendation report for PDF or Query."""
    source_type: str  # "tender" or "query"
    source_id: str
    total_requirements: int = 0
    total_standards_evaluated: int = 0
    recommendations: list[RecommendationResponse] = []
    summary: Optional[str] = None
    compliance_note: Optional[str] = None  # e.g., "Compliance cannot be assessed..."
    generated_at: Optional[str] = None


class RecommendationActionRequest(BaseModel):
    note: Optional[str] = None


class RecommendationActionResponse(BaseModel):
    id: str
    status: str
    message: str
