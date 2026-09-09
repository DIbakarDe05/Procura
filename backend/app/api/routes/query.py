"""
Procura — Query API Routes

Natural-language technical query interface.
This is NOT a chatbot — it returns structured standard recommendations.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.query import Query, QueryStatus
from app.models.requirement import QueryRequirement
from app.models.recommendation import Recommendation
from app.models.bis_standard import BISStandard
from app.schemas.query import QueryRequest, QueryResponse, QueryDetailResponse
from app.schemas.requirement import RequirementResponse
from app.workers.analysis_worker import run_query_analysis
from app.services.report_builder import report_builder

logger = logging.getLogger("procura.routes.query")

router = APIRouter(prefix="/api/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def submit_query(
    request: QueryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a natural-language technical query.

    Example: "10 HP centrifugal water pump operating at 2900 RPM with stainless steel casing"

    Returns query_id and starts background analysis.
    """
    query = Query(
        query_text=request.query,
        status=QueryStatus.RECEIVED.value,
    )
    db.add(query)
    await db.commit()

    # Start background analysis immediately on event loop
    import asyncio
    asyncio.create_task(run_query_analysis(query.id))

    return QueryResponse(
        id=query.id,
        query_text=query.query_text,
        status=query.status,
        message="Query received. Analysis started in background.",
    )


@router.get("/{query_id}", response_model=QueryDetailResponse)
async def get_query(query_id: str, db: AsyncSession = Depends(get_db)):
    """Get query details and extracted requirements."""
    result = await db.execute(
        select(Query).where(Query.id == query_id).options(selectinload(Query.requirements))
    )
    query = result.scalar_one_or_none()

    if not query:
        raise HTTPException(404, "Query not found")

    return QueryDetailResponse(
        id=query.id,
        query_text=query.query_text,
        normalized_query=query.normalized_query,
        status=query.status,
        requirements=[
            RequirementResponse(
                id=r.id,
                requirement=r.requirement,
                normalized_requirement=r.normalized_requirement,
                requirement_type=r.requirement_type,
                parameters=r.parameters,
                source="query",
            )
            for r in query.requirements
        ],
        created_at=query.created_at,
    )


@router.get("/{query_id}/recommendations")
async def get_query_recommendations(query_id: str, db: AsyncSession = Depends(get_db)):
    """Get recommendations for a query."""
    result = await db.execute(
        select(Recommendation, BISStandard)
        .join(BISStandard, Recommendation.standard_id == BISStandard.id)
        .join(QueryRequirement, Recommendation.query_requirement_id == QueryRequirement.id)
        .where(QueryRequirement.query_id == query_id)
        .order_by(Recommendation.relevance_score.desc())
        .limit(4)
    )
    rows = result.all()

    return [
        {
            "id": rec.id,
            "standard_number": std.standard_number,
            "standard_title": std.title,
            "relevance_score": rec.relevance_score,
            "confidence_score": rec.confidence_score,
            "compliance_score": rec.compliance_score,
            "applicable": rec.applicable,
            "reasoning": rec.reasoning,
            "coverage": rec.coverage,
            "gaps": rec.gaps,
            "status": rec.status,
        }
        for rec, std in rows
    ]


@router.get("/{query_id}/report")
async def get_query_report(query_id: str, db: AsyncSession = Depends(get_db)):
    """Get the full structured recommendation report for a query."""
    query = await db.get(Query, query_id)
    if not query:
        raise HTTPException(404, "Query not found")

    if query.status != QueryStatus.COMPLETED.value:
        raise HTTPException(400, f"Analysis not complete. Current status: {query.status}")

    # Get all recommendations
    result = await db.execute(
        select(Recommendation, BISStandard)
        .join(BISStandard, Recommendation.standard_id == BISStandard.id)
        .join(QueryRequirement, Recommendation.query_requirement_id == QueryRequirement.id)
        .where(QueryRequirement.query_id == query_id)
    )
    rows = result.all()

    # Check if generic query
    import json
    is_generic = False
    if query.normalized_query:
        try:
            parsed = json.loads(query.normalized_query)
            is_generic = parsed.get("is_generic", False)
        except json.JSONDecodeError:
            pass

    recommendations_data = [
        {
            "recommendation_id": rec.id,
            "standard_id": std.id,
            "standard_number": std.standard_number,
            "standard_title": std.title,
            "relevance_score": rec.relevance_score,
            "confidence_score": rec.confidence_score,
            "compliance_score": rec.compliance_score,
            "applicable": rec.applicable,
            "reasoning": rec.reasoning,
            "coverage": rec.coverage or {},
            "gaps": rec.gaps or [],
            "status": rec.status,
            "total_requirements": len(rows),
        }
        for rec, std in rows
    ]

    return await report_builder.build_report(
        source_type="query",
        source_id=query_id,
        recommendations_data=recommendations_data,
        db=db,
        is_generic_query=is_generic,
    )
