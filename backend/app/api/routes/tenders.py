"""
Procura — Tender API Routes

Handles PDF upload, processing, and report retrieval.
Business logic lives in services — routes are thin.
"""

import os
import uuid
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.tender import Tender, TenderSection
from app.models.requirement import TenderRequirement
from app.models.recommendation import Recommendation
from app.models.bis_standard import BISStandard
from app.models.processing_job import ProcessingJob, JobStatus
from app.schemas.tender import (
    TenderUploadResponse, TenderStatusResponse,
    TenderDetailResponse, TenderSectionSchema,
)
from app.schemas.requirement import RequirementResponse
from app.schemas.recommendation import ReportResponse
from app.workers.analysis_worker import run_tender_analysis
from app.services.report_builder import report_builder

logger = logging.getLogger("procura.routes.tenders")

router = APIRouter(prefix="/api/tenders", tags=["Tenders"])


@router.post("/upload", response_model=TenderUploadResponse)
async def upload_tender(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a tender PDF for analysis."""
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are accepted")

    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(400, f"Invalid content type: {file.content_type}")

    # Save file
    file_id = str(uuid.uuid4())
    upload_dir = settings.upload_path
    file_path = upload_dir / f"{file_id}.pdf"

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    with open(file_path, "wb") as f:
        f.write(content)

    # Create tender record
    tender = Tender(
        title=file.filename.rsplit(".", 1)[0],
        filename=file.filename,
        file_path=str(file_path),
        status="uploaded",
    )
    db.add(tender)
    await db.flush()

    return TenderUploadResponse(
        id=tender.id,
        filename=file.filename,
        status="uploaded",
        message="Tender uploaded successfully. Use POST /api/tenders/{id}/analyze to start analysis.",
    )


@router.get("/{tender_id}", response_model=TenderDetailResponse)
async def get_tender(tender_id: str, db: AsyncSession = Depends(get_db)):
    """Get tender details."""
    result = await db.execute(
        select(Tender).where(Tender.id == tender_id).options(selectinload(Tender.sections))
    )
    tender = result.scalar_one_or_none()

    if not tender:
        raise HTTPException(404, "Tender not found")

    return TenderDetailResponse(
        id=tender.id,
        title=tender.title,
        filename=tender.filename,
        status=tender.status,
        processing_status=tender.processing_status,
        page_count=tender.page_count,
        language=tender.language,
        created_at=tender.created_at,
        sections=[TenderSectionSchema.model_validate(s) for s in tender.sections],
    )


@router.get("/{tender_id}/status", response_model=TenderStatusResponse)
async def get_tender_status(tender_id: str, db: AsyncSession = Depends(get_db)):
    """Get tender processing status."""
    tender = await db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    # Get latest job
    result = await db.execute(
        select(ProcessingJob)
        .where(ProcessingJob.tender_id == tender_id)
        .order_by(ProcessingJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()

    return TenderStatusResponse(
        id=tender.id,
        status=tender.status,
        processing_status=job.status if job else None,
        progress=job.progress if job else None,
        message=job.error_message if job and job.error_message else None,
    )


@router.post("/{tender_id}/analyze")
async def analyze_tender(
    tender_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Start background analysis of a tender."""
    tender = await db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    if tender.status == "processing":
        raise HTTPException(409, "Analysis already in progress")

    # Create processing job
    job = ProcessingJob(
        tender_id=tender_id,
        job_type="tender_analysis",
        status=JobStatus.QUEUED.value,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)

    tender.status = "processing"
    tender.processing_status = "queued"
    await db.commit()

    # Launch background task immediately on event loop
    import asyncio
    asyncio.create_task(run_tender_analysis(tender_id, job.id))

    return {
        "tender_id": tender.id,
        "job_id": job.id,
        "status": "queued",
        "message": "Analysis started. Poll GET /api/tenders/{id}/status for progress.",
    }


@router.get("/{tender_id}/requirements")
async def get_tender_requirements(tender_id: str, db: AsyncSession = Depends(get_db)):
    """Get extracted requirements for a tender."""
    tender = await db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    result = await db.execute(
        select(TenderRequirement).where(TenderRequirement.tender_id == tender_id)
    )
    reqs = result.scalars().all()

    return [
        RequirementResponse(
            id=r.id,
            requirement=r.requirement,
            normalized_requirement=r.normalized_requirement,
            requirement_type=r.requirement_type,
            parameters=r.parameters,
            source="pdf",
            page_number=r.page_number,
        )
        for r in reqs
    ]


@router.get("/{tender_id}/recommendations")
async def get_tender_recommendations(tender_id: str, db: AsyncSession = Depends(get_db)):
    """Get recommendations for a tender."""
    result = await db.execute(
        select(Recommendation, BISStandard)
        .join(BISStandard, Recommendation.standard_id == BISStandard.id)
        .join(TenderRequirement, Recommendation.tender_requirement_id == TenderRequirement.id)
        .where(TenderRequirement.tender_id == tender_id)
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


@router.get("/{tender_id}/report")
async def get_tender_report(tender_id: str, db: AsyncSession = Depends(get_db)):
    """Get the full structured recommendation report for a tender."""
    tender = await db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "Tender not found")

    if tender.status != "completed":
        raise HTTPException(400, f"Analysis not complete. Current status: {tender.status}")

    # Get all recommendations
    result = await db.execute(
        select(Recommendation, BISStandard)
        .join(BISStandard, Recommendation.standard_id == BISStandard.id)
        .join(TenderRequirement, Recommendation.tender_requirement_id == TenderRequirement.id)
        .where(TenderRequirement.tender_id == tender_id)
    )
    rows = result.all()

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
        source_type="tender",
        source_id=tender_id,
        recommendations_data=recommendations_data,
        db=db,
    )
