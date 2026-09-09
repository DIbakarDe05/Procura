"""
Procura — Recommendation API Routes

Allows procurement officers to review, accept, or reject recommendations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.recommendation import Recommendation, RecommendationStatus
from app.models.bis_standard import BISStandard
from app.schemas.recommendation import (
    RecommendationActionRequest,
    RecommendationActionResponse,
)

logger = logging.getLogger("procura.routes.recommendations")

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


@router.get("/{recommendation_id}")
async def get_recommendation(recommendation_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single recommendation with full details."""
    result = await db.execute(
        select(Recommendation, BISStandard)
        .join(BISStandard, Recommendation.standard_id == BISStandard.id)
        .where(Recommendation.id == recommendation_id)
    )
    row = result.one_or_none()

    if not row:
        raise HTTPException(404, "Recommendation not found")

    rec, std = row

    return {
        "id": rec.id,
        "standard_number": std.standard_number,
        "standard_title": std.title,
        "standard_scope": std.scope,
        "standard_edition": std.edition,
        "standard_status": std.status,
        "relevance_score": rec.relevance_score,
        "confidence_score": rec.confidence_score,
        "compliance_score": rec.compliance_score,
        "applicable": rec.applicable,
        "recommendation_type": rec.recommendation_type,
        "reasoning": rec.reasoning,
        "coverage": rec.coverage,
        "gaps": rec.gaps,
        "evidence": rec.evidence,
        "status": rec.status,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
    }


@router.post("/{recommendation_id}/accept", response_model=RecommendationActionResponse)
async def accept_recommendation(
    recommendation_id: str,
    request: RecommendationActionRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Officer accepts this recommendation."""
    rec = await db.get(Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(404, "Recommendation not found")

    rec.status = RecommendationStatus.ACCEPTED.value
    return RecommendationActionResponse(
        id=rec.id, status="accepted",
        message="Recommendation accepted by procurement officer.",
    )


@router.post("/{recommendation_id}/reject", response_model=RecommendationActionResponse)
async def reject_recommendation(
    recommendation_id: str,
    request: RecommendationActionRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Officer rejects this recommendation."""
    rec = await db.get(Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(404, "Recommendation not found")

    rec.status = RecommendationStatus.REJECTED.value
    return RecommendationActionResponse(
        id=rec.id, status="rejected",
        message="Recommendation rejected by procurement officer.",
    )


@router.post("/{recommendation_id}/review", response_model=RecommendationActionResponse)
async def mark_for_review(
    recommendation_id: str,
    request: RecommendationActionRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Officer marks this recommendation for further review."""
    rec = await db.get(Recommendation, recommendation_id)
    if not rec:
        raise HTTPException(404, "Recommendation not found")

    rec.status = RecommendationStatus.UNDER_REVIEW.value
    return RecommendationActionResponse(
        id=rec.id, status="under_review",
        message="Recommendation marked for further review.",
    )
