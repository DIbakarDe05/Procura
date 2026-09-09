"""
Procura — BIS Standard Models

Verified BIS database — the single source of truth for Indian Standards.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class StandardStatus(str, enum.Enum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    UNDER_REVISION = "under_revision"


class ReferenceType(str, enum.Enum):
    NORMATIVE_REFERENCE = "normative_reference"
    TEST_METHOD = "test_method"
    SAFETY = "safety"
    INSTALLATION = "installation"
    TERMINOLOGY = "terminology"
    RELATED_PRODUCT = "related_product"
    ALLIED = "allied"


class BISStandard(Base):
    """Verified BIS standard — the source of truth."""
    __tablename__ = "bis_standards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    standard_number = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(1000), nullable=False)
    scope = Column(Text, nullable=True)
    category = Column(String(200), nullable=True)
    edition = Column(String(50), nullable=True)
    status = Column(String(50), default=StandardStatus.CURRENT.value)
    amendments = Column(JSON, nullable=True)
    certification_required = Column(Boolean, nullable=True)
    certification_details = Column(Text, nullable=True)
    source = Column(String(200), nullable=True)
    meta_data = Column("metadata", JSON, nullable=True)
    # Embedding stored as JSON array of floats for SQLite prototype
    embedding = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    outgoing_references = relationship(
        "StandardReference",
        back_populates="standard",
        foreign_keys="StandardReference.standard_id",
        cascade="all, delete-orphan",
    )
    incoming_references = relationship(
        "StandardReference",
        back_populates="referenced_standard",
        foreign_keys="StandardReference.referenced_standard_id",
    )
    recommendations = relationship("Recommendation", back_populates="standard")


class StandardReference(Base):
    """Relational link between standards (replaces graph DB)."""
    __tablename__ = "standard_references"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    standard_id = Column(String, ForeignKey("bis_standards.id", ondelete="CASCADE"), nullable=False)
    referenced_standard_id = Column(String, ForeignKey("bis_standards.id", ondelete="CASCADE"), nullable=False)
    reference_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    standard = relationship("BISStandard", back_populates="outgoing_references",
                            foreign_keys=[standard_id])
    referenced_standard = relationship("BISStandard", back_populates="incoming_references",
                                       foreign_keys=[referenced_standard_id])
