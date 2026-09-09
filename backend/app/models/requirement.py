"""
Procura — Requirement Models

Common requirement model shared by PDF and Query input paths.
Embeddings stored as JSON text for SQLite prototype.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Float,
    DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class RequirementType(str, enum.Enum):
    PERFORMANCE = "performance"
    MATERIAL = "material"
    SAFETY = "safety"
    TESTING = "testing"
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    DIMENSIONAL = "dimensional"
    ENVIRONMENTAL = "environmental"
    CERTIFICATION = "certification"
    MARKING = "marking"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class TenderRequirement(Base):
    """Requirement extracted from a tender PDF."""
    __tablename__ = "tender_requirements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tender_id = Column(String, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(String, ForeignKey("tender_sections.id", ondelete="SET NULL"), nullable=True)
    page_number = Column(Integer, nullable=True)
    requirement = Column(Text, nullable=False)
    normalized_requirement = Column(Text, nullable=True)
    requirement_type = Column(String(50), default=RequirementType.GENERAL.value)
    parameters = Column(JSON, nullable=True)
    # Embedding stored as JSON array of floats for SQLite prototype
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tender = relationship("Tender", back_populates="requirements")
    section = relationship("TenderSection", back_populates="requirements")
    recommendations = relationship("Recommendation", back_populates="tender_requirement",
                                   foreign_keys="Recommendation.tender_requirement_id",
                                   cascade="all, delete-orphan")


class QueryRequirement(Base):
    """Requirement extracted from a natural-language query."""
    __tablename__ = "query_requirements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String, ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    requirement = Column(Text, nullable=False)
    normalized_requirement = Column(Text, nullable=True)
    requirement_type = Column(String(50), default=RequirementType.GENERAL.value)
    parameters = Column(JSON, nullable=True)
    # Embedding stored as JSON array of floats for SQLite prototype
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    query = relationship("Query", back_populates="requirements")
    recommendations = relationship("Recommendation", back_populates="query_requirement",
                                   foreign_keys="Recommendation.query_requirement_id",
                                   cascade="all, delete-orphan")
