"""
Procura — Tender Models

Represents uploaded tender PDFs, their pages, sections, and extracted requirements.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    DateTime, Enum, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class TenderStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    COMPLETED = "completed"
    FAILED = "failed"


class SectionType(str, enum.Enum):
    TECHNICAL_SPECIFICATION = "technical_specification"
    SCOPE_OF_SUPPLY = "scope_of_supply"
    PERFORMANCE_REQUIREMENTS = "performance_requirements"
    MATERIAL_REQUIREMENTS = "material_requirements"
    TESTING_REQUIREMENTS = "testing_requirements"
    SAFETY_REQUIREMENTS = "safety_requirements"
    QUALITY_REQUIREMENTS = "quality_requirements"
    INSPECTION_REQUIREMENTS = "inspection_requirements"
    STANDARDS_CODES = "standards_codes"
    ADMINISTRATIVE = "administrative"
    COMMERCIAL = "commercial"
    LEGAL = "legal"
    GENERAL = "general"
    UNKNOWN = "unknown"


class SectionPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=True)
    status = Column(String(50), default=TenderStatus.UPLOADED.value)
    processing_status = Column(String(100), nullable=True)
    page_count = Column(Integer, nullable=True)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    pages = relationship("TenderPage", back_populates="tender", cascade="all, delete-orphan")
    sections = relationship("TenderSection", back_populates="tender", cascade="all, delete-orphan")
    requirements = relationship("TenderRequirement", back_populates="tender", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="tender", cascade="all, delete-orphan")


class TenderPage(Base):
    __tablename__ = "tender_pages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tender_id = Column(String, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=True)
    is_scanned = Column(Boolean, default=False)
    ocr_used = Column(Boolean, default=False)
    meta_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tender = relationship("Tender", back_populates="pages")


class TenderSection(Base):
    __tablename__ = "tender_sections"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tender_id = Column(String, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    page_start = Column(Integer, nullable=True)
    page_end = Column(Integer, nullable=True)
    section_title = Column(String(500), nullable=True)
    section_type = Column(String(50), default=SectionType.UNKNOWN.value)
    content = Column(Text, nullable=True)
    priority = Column(String(20), default=SectionPriority.MEDIUM.value)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tender = relationship("Tender", back_populates="sections")
    requirements = relationship("TenderRequirement", back_populates="section", cascade="all, delete-orphan")
