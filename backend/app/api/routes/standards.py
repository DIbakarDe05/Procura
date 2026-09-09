"""
Procura — BIS Standards Catalog API Routes

Allows clients to query the verified BIS database and knowledge base statistics.
"""

import logging
from fastapi import APIRouter, Depends, Query as QueryParam
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.bis_standard import BISStandard, StandardReference

logger = logging.getLogger("procura.routes.standards")

router = APIRouter(prefix="/api/standards", tags=["BIS Standards"])


@router.get("/stats")
async def get_standards_stats(db: AsyncSession = Depends(get_db)):
    """Get high-level knowledge base metrics."""
    total_stds = await db.scalar(select(func.count(BISStandard.id)))
    embedded_stds = await db.scalar(
        select(func.count(BISStandard.id)).where(BISStandard.embedding.isnot(None))
    )
    total_refs = await db.scalar(select(func.count(StandardReference.id)))

    # Category breakdown
    cat_query = await db.execute(
        select(BISStandard.category, func.count(BISStandard.id))
        .group_by(BISStandard.category)
    )
    categories = {cat or "general": count for cat, count in cat_query.all()}

    return {
        "total_standards": total_stds or 0,
        "embedded_standards": embedded_stds or 0,
        "total_references": total_refs or 0,
        "embedding_dimension": 3072,
        "embedding_model": "gemini-embedding-2",
        "categories": categories,
    }


@router.get("")
async def list_standards(
    skip: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    category: str = QueryParam(None),
    db: AsyncSession = Depends(get_db),
):
    """List indexed BIS standards from verified database."""
    query = select(BISStandard).options(selectinload(BISStandard.outgoing_references))
    if category:
        query = query.where(BISStandard.category == category)

    total = await db.scalar(select(func.count(BISStandard.id)))
    query = query.offset(skip).limit(limit).order_by(BISStandard.standard_number)

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": [
            {
                "id": std.id,
                "standard_number": std.standard_number,
                "title": std.title,
                "scope": std.scope,
                "category": std.category,
                "edition": std.edition,
                "status": std.status,
                "certification_required": std.certification_required,
                "references_count": len(std.outgoing_references) if std.outgoing_references else 0,
                "has_embedding": std.embedding is not None,
            }
            for std in items
        ],
    }
