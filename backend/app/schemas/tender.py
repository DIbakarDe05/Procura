"""
Procura — Tender Schemas (Pydantic v2 request/response models)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TenderUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    page_count: Optional[int] = None
    message: str = "Tender uploaded successfully"


class TenderStatusResponse(BaseModel):
    id: str
    status: str
    processing_status: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None


class TenderPageSchema(BaseModel):
    page_number: int
    is_scanned: bool
    ocr_used: bool
    text_preview: Optional[str] = None

    model_config = {"from_attributes": True}


class TenderSectionSchema(BaseModel):
    id: str
    section_title: Optional[str] = None
    section_type: str
    priority: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None

    model_config = {"from_attributes": True}


class TenderDetailResponse(BaseModel):
    id: str
    title: Optional[str] = None
    filename: str
    status: str
    processing_status: Optional[str] = None
    page_count: Optional[int] = None
    language: Optional[str] = None
    created_at: datetime
    sections: list[TenderSectionSchema] = []

    model_config = {"from_attributes": True}
