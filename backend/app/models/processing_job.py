"""
Procura — Processing Job Model

Tracks background processing pipeline status for tender analysis.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Text, Integer, Float,
    DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING_PDF = "processing_pdf"
    EXTRACTING_REQUIREMENTS = "extracting_requirements"
    NORMALIZING = "normalizing"
    GENERATING_EMBEDDINGS = "generating_embeddings"
    RETRIEVING_STANDARDS = "retrieving_standards"
    ANALYZING_TOP_K = "analyzing_top_k"
    CALCULATING_SCORES = "calculating_scores"
    BUILDING_REPORT = "building_report"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tender_id = Column(String, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=True)
    query_id = Column(String, nullable=True)
    job_type = Column(String(50), nullable=False)  # "tender_analysis" or "query_analysis"
    status = Column(String(50), default=JobStatus.QUEUED.value)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    tender = relationship("Tender", back_populates="jobs")
