"""
Procura — Retrieval Service

Semantic retrieval of BIS standards using vector similarity.
Prototype uses NumPy cosine similarity; swappable to pgvector.
"""

import json
import logging
from typing import Optional
from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.bis_standard import BISStandard
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger("procura.retrieval_service")


@dataclass
class RetrievalCandidate:
    """A BIS standard candidate from semantic retrieval."""
    standard_id: str
    standard_number: str
    title: str
    scope: str
    category: Optional[str]
    similarity_score: float
    standard: BISStandard


class RetrievalService:
    """
    Retrieves relevant BIS standards using semantic similarity.
    Prototype: in-memory NumPy cosine similarity.
    Production: pgvector HNSW index.
    """

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.top_k = settings.TOP_K
        self.similarity_threshold = settings.SIMILARITY_THRESHOLD

    async def retrieve_candidates(
        self,
        query_embedding: list[float],
        db: AsyncSession,
        top_k: Optional[int] = None,
        category_filter: Optional[str] = None,
    ) -> list[RetrievalCandidate]:
        """
        Retrieve Top-K BIS standards by semantic similarity.

        Args:
            query_embedding: Embedding vector of the requirement
            db: Database session
            top_k: Number of candidates to return (overrides config)
            category_filter: Optional category to filter by

        Returns:
            List of candidates ranked by similarity
        """
        k = top_k or self.top_k

        # Load all BIS standards with embeddings
        query = select(BISStandard)
        if category_filter:
            query = query.where(BISStandard.category == category_filter)

        result = await db.execute(query)
        standards = result.scalars().all()

        if not standards:
            logger.warning("No BIS standards found in database")
            return []

        # Compute similarity for each standard
        query_vec = np.array(query_embedding, dtype=np.float32)
        candidates = []

        for std in standards:
            if not std.embedding:
                continue

            try:
                std_vec = np.array(json.loads(std.embedding), dtype=np.float32)
                similarity = self.embedding_service.cosine_similarity(query_vec, std_vec)

                if similarity >= self.similarity_threshold:
                    candidates.append(RetrievalCandidate(
                        standard_id=std.id,
                        standard_number=std.standard_number,
                        title=std.title,
                        scope=std.scope or "",
                        category=std.category,
                        similarity_score=similarity,
                        standard=std,
                    ))
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Invalid embedding for standard {std.standard_number}: {e}")
                continue

        # Sort by similarity (descending) and take top-k
        candidates.sort(key=lambda c: c.similarity_score, reverse=True)
        top_candidates = candidates[:k]

        logger.info(
            f"Retrieved {len(top_candidates)} candidates from {len(standards)} standards "
            f"(threshold={self.similarity_threshold})"
        )

        return top_candidates

    async def retrieve_for_requirements(
        self,
        requirements: list[dict],
        db: AsyncSession,
    ) -> dict[str, list[RetrievalCandidate]]:
        """
        Retrieve candidates for multiple requirements.

        Args:
            requirements: List of dicts with 'id' and 'embedding' keys
            db: Database session

        Returns:
            Dict mapping requirement_id -> list of candidates
        """
        results = {}

        for req in requirements:
            req_id = req.get("id", "unknown")
            embedding = req.get("embedding")

            if embedding:
                candidates = await self.retrieve_candidates(embedding, db)
                results[req_id] = candidates
            else:
                results[req_id] = []

        return results


# Factory function
def get_retrieval_service() -> RetrievalService:
    from app.services.embedding_service import embedding_service
    return RetrievalService(embedding_service)
