"""
Procura — Recommendation Model

Stores individual standard recommendations with separate scores for
relevance, confidence, and compliance.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Float, Boolean,
    DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Polymorphic FK: one of these will be set
    tender_requirement_id = Column(
        String, ForeignKey("tender_requirements.id", ondelete="CASCADE"), nullable=True
    )
    query_requirement_id = Column(
        String, ForeignKey("query_requirements.id", ondelete="CASCADE"), nullable=True
    )

    standard_id = Column(
        String, ForeignKey("bis_standards.id", ondelete="CASCADE"), nullable=False
    )

    # Three separate scores
    relevance_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    compliance_score = Column(Float, nullable=True)  # Can be NULL for generic queries

    applicable = Column(Boolean, default=True)
    recommendation_type = Column(String(50), default="primary")
    status = Column(String(50), default=RecommendationStatus.PENDING.value)
    reasoning = Column(Text, nullable=True)
    coverage = Column(JSON, nullable=True)
    gaps = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tender_requirement = relationship(
        "TenderRequirement", back_populates="recommendations",
        foreign_keys=[tender_requirement_id]
    )
    query_requirement = relationship(
        "QueryRequirement", back_populates="recommendations",
        foreign_keys=[query_requirement_id]
    )
    standard = relationship("BISStandard", back_populates="recommendations")
