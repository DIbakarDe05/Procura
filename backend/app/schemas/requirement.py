"""
Procura — Requirement Schemas
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ParameterSchema(BaseModel):
    parameter: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    unit: Optional[str] = None


class RequirementResponse(BaseModel):
    id: str
    requirement: str
    normalized_requirement: Optional[str] = None
    requirement_type: str
    parameters: Optional[dict] = None
    source: str = "pdf"  # "pdf" or "query"
    page_number: Optional[int] = None
    section: Optional[str] = None

    model_config = {"from_attributes": True}


class NormalizedRequirementSchema(BaseModel):
    """Internal representation of a normalized requirement — shared by PDF and Query."""
    requirement_text: str
    normalized_requirement: str
    product_category: Optional[str] = None
    requirement_type: str = "general"
    parameters: Optional[dict] = None
    source: str  # "pdf" or "query"
    source_page: Optional[int] = None
    source_section: Optional[str] = None
