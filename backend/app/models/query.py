"""
Procura — Query Model

Represents natural-language technical queries submitted by procurement officers.
"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class QueryStatus(str, enum.Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class Query(Base):
    __tablename__ = "queries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_text = Column(Text, nullable=False)
    normalized_query = Column(Text, nullable=True)
    status = Column(String(50), default=QueryStatus.RECEIVED.value)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    requirements = relationship("QueryRequirement", back_populates="query", cascade="all, delete-orphan")
