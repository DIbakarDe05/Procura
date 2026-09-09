"""
Procura — Analysis Worker

Background pipeline orchestrator for both PDF and Query analysis.
Both paths converge into the same recommendation pipeline.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.tender import Tender, TenderPage, TenderSection
from app.models.requirement import TenderRequirement, QueryRequirement
from app.models.query import Query, QueryStatus
from app.models.bis_standard import BISStandard
from app.models.recommendation import Recommendation
from app.models.processing_job import ProcessingJob, JobStatus
from app.services.pdf_processor import pdf_processor
from app.services.document_structure import document_analyzer
from app.services.query_understanding import query_understanding
from app.services.requirement_extractor import requirement_extractor
from app.services.requirement_normalizer import requirement_normalizer
from app.services.embedding_service import embedding_service
from app.services.retrieval_service import get_retrieval_service
from app.services.relevance_scorer import relevance_scorer
from app.services.gemini_service import gemini_service
from app.services.compliance_scorer import compliance_scorer
from app.services.confidence_scorer import confidence_scorer

logger = logging.getLogger("procura.analysis_worker")


async def _update_job(db: AsyncSession, job_id: str, status: str, progress: int, error: str = None):
    """Update processing job status."""
    values = {"status": status, "progress": progress}
    if error:
        values["error_message"] = error
    if status == JobStatus.COMPLETED.value:
        values["completed_at"] = datetime.now(timezone.utc)
    await db.execute(update(ProcessingJob).where(ProcessingJob.id == job_id).values(**values))
    await db.commit()


# ═══════════════════════════════════════════════════════════════════
# SHARED RECOMMENDATION PIPELINE
# Both PDF and Query requirements enter this SAME pipeline
# ═══════════════════════════════════════════════════════════════════

async def run_recommendation_pipeline(
    requirements: list[dict],
    db: AsyncSession,
    is_generic_query: bool = False,
    job_id: Optional[str] = None,
) -> list[dict]:
    """
    The COMMON recommendation pipeline used by both PDF and Query modes.

    Args:
        requirements: List of dicts with keys: id, text, normalized, type, params, embedding, source
        db: Database session
        is_generic_query: True for generic queries (compliance = null)
        job_id: Optional job ID for progress tracking

    Returns:
        List of recommendation dicts ready for report building
    """
    all_recommendations = []
    retrieval_service = get_retrieval_service()

    # ── Step 1: Semantic Retrieval ─────────────────────────────
    if job_id:
        await _update_job(db, job_id, JobStatus.RETRIEVING_STANDARDS.value, 50)

    for req in requirements:
        embedding = req.get("embedding")
        if not embedding:
            continue

        # Retrieve candidates
        candidates = await retrieval_service.retrieve_candidates(embedding, db)

        if not candidates:
            logger.info(f"No candidates found for requirement: {req['text'][:80]}")
            continue

        # ── Step 2: Relevance Scoring ──────────────────────────
        if job_id:
            await _update_job(db, job_id, JobStatus.ANALYZING_TOP_K.value, 60)

        relevance_results = relevance_scorer.score_batch(
            candidates=candidates,
            requirement_text=req.get("normalized", req["text"]),
            requirement_params=req.get("params"),
            product_category=req.get("product_category"),
        )

        # ── Step 3: Gemini Analysis (Top-K only) ───────────────
        top_candidates = relevance_results[:4]  # Analyze top 4 to respect rate limits

        for rank, rel_result in enumerate(top_candidates):
            # Find the matching candidate
            candidate = next(
                (c for c in candidates if c.standard_id == rel_result.standard_id),
                None
            )
            if not candidate:
                continue

            std = candidate.standard

            # Gemini structured analysis
            analysis = await gemini_service.analyze_standard(
                requirement_text=req["text"],
                requirement_type=req.get("type", "general"),
                parameters=req.get("params"),
                standard_number=std.standard_number,
                standard_title=std.title,
                standard_scope=std.scope or "",
                standard_category=std.category,
                standard_edition=std.edition,
                standard_status=std.status,
                standard_id=std.id,
            )

            # ── Step 4: Compliance Scoring ─────────────────────
            if job_id:
                await _update_job(db, job_id, JobStatus.CALCULATING_SCORES.value, 75)

            comp_score = compliance_scorer.score(analysis, is_generic_query)

            # ── Step 5: Confidence Scoring ─────────────────────
            conf_score = confidence_scorer.score(
                relevance=rel_result,
                analysis=analysis,
                candidate_count=len(candidates),
                rank_position=rank,
            )

            # ── Step 6: Create Recommendation Record ───────────
            rec = Recommendation(
                tender_requirement_id=req["id"] if req["source"] == "pdf" else None,
                query_requirement_id=req["id"] if req["source"] == "query" else None,
                standard_id=std.id,
                relevance_score=rel_result.overall_score,
                confidence_score=conf_score,
                compliance_score=comp_score,
                applicable=analysis.applicable,
                reasoning=analysis.reasoning,
                coverage=analysis.coverage,
                gaps=analysis.gaps,
                evidence={"key_provisions": analysis.key_provisions},
            )
            db.add(rec)
            await db.flush()

            all_recommendations.append({
                "recommendation_id": rec.id,
                "standard_id": std.id,
                "standard_number": std.standard_number,
                "standard_title": std.title,
                "relevance_score": rel_result.overall_score,
                "confidence_score": conf_score,
                "compliance_score": comp_score,
                "applicable": analysis.applicable,
                "reasoning": analysis.reasoning,
                "coverage": analysis.coverage,
                "gaps": analysis.gaps,
                "total_requirements": len(requirements),
            })

    await db.commit()
    return all_recommendations


# ═══════════════════════════════════════════════════════════════════
# TENDER (PDF) ANALYSIS PIPELINE
# ═══════════════════════════════════════════════════════════════════

async def run_tender_analysis(tender_id: str, job_id: str):
    """Full tender PDF analysis pipeline."""
    async with async_session() as db:
        try:
            # ── Process PDF ────────────────────────────────────
            await _update_job(db, job_id, JobStatus.PROCESSING_PDF.value, 10)

            tender = await db.get(Tender, tender_id)
            if not tender or not tender.file_path:
                await _update_job(db, job_id, JobStatus.FAILED.value, 0, "Tender or file not found")
                return

            # Read PDF bytes
            with open(tender.file_path, "rb") as f:
                pdf_bytes = f.read()

            # Process PDF
            result = await pdf_processor.process_pdf(pdf_bytes)
            if result.error:
                await _update_job(db, job_id, JobStatus.FAILED.value, 0, result.error)
                return

            tender.page_count = result.total_pages
            tender.status = "processing"

            # Save pages
            for page in result.pages:
                db.add(TenderPage(
                    tender_id=tender_id,
                    page_number=page.page_number,
                    raw_text=page.text,
                    cleaned_text=page.text,
                    is_scanned=page.is_scanned,
                    ocr_used=page.ocr_used,
                    meta_data=page.metadata,
                ))
            await db.commit()

            # ── Detect Sections ────────────────────────────────
            pages_data = [{"page_number": p.page_number, "text": p.text} for p in result.pages]
            sections = document_analyzer.detect_sections(pages_data)

            for section in sections:
                db.add(TenderSection(
                    tender_id=tender_id,
                    page_start=section.page_start,
                    page_end=section.page_end,
                    section_title=section.title,
                    section_type=section.section_type,
                    content=section.content,
                    priority=section.priority,
                ))
            await db.commit()

            # ── Extract Requirements ───────────────────────────
            await _update_job(db, job_id, JobStatus.EXTRACTING_REQUIREMENTS.value, 25)

            # Prioritize high-priority sections
            high_priority = [s for s in sections if s.priority == "high"]
            sections_to_process = high_priority if high_priority else sections

            all_reqs = []
            for section in sections_to_process:
                extracted = await requirement_extractor.extract_from_text(
                    text=section.content,
                    source="pdf",
                    page_number=section.page_start,
                    section_title=section.title,
                )
                normalized = requirement_normalizer.normalize_batch(extracted)
                all_reqs.extend(normalized)

            # ── Generate Embeddings ────────────────────────────
            await _update_job(db, job_id, JobStatus.GENERATING_EMBEDDINGS.value, 40)

            requirement_dicts = []
            for req in all_reqs:
                emb = await embedding_service.generate_embedding(req.normalized_requirement)
                emb_json = embedding_service.embedding_to_json(emb) if emb else None

                tr = TenderRequirement(
                    tender_id=tender_id,
                    requirement=req.requirement_text,
                    normalized_requirement=req.normalized_requirement,
                    requirement_type=req.requirement_type,
                    parameters=req.parameters,
                    embedding=emb_json,
                    page_number=req.source_page,
                )
                db.add(tr)
                await db.flush()

                requirement_dicts.append({
                    "id": tr.id,
                    "text": req.requirement_text,
                    "normalized": req.normalized_requirement,
                    "type": req.requirement_type,
                    "params": req.parameters,
                    "product_category": req.product_category,
                    "embedding": emb,
                    "source": "pdf",
                })

            await db.commit()

            # ── Run SHARED Recommendation Pipeline ─────────────
            recommendations = await run_recommendation_pipeline(
                requirements=requirement_dicts,
                db=db,
                is_generic_query=False,
                job_id=job_id,
            )

            # ── Complete ───────────────────────────────────────
            await _update_job(db, job_id, JobStatus.BUILDING_REPORT.value, 90)
            tender.status = "completed"
            tender.processing_status = "completed"
            await db.commit()

            await _update_job(db, job_id, JobStatus.COMPLETED.value, 100)
            logger.info(f"Tender analysis completed: {tender_id}, {len(recommendations)} recommendations")

        except Exception as e:
            logger.error(f"Tender analysis failed: {e}", exc_info=True)
            await _update_job(db, job_id, JobStatus.FAILED.value, 0, str(e))
            tender_update = await db.get(Tender, tender_id)
            if tender_update:
                tender_update.status = "failed"
                await db.commit()


# ═══════════════════════════════════════════════════════════════════
# QUERY ANALYSIS PIPELINE
# ═══════════════════════════════════════════════════════════════════

async def run_query_analysis(query_id: str):
    """Full query analysis pipeline — converges into the same recommendation engine as PDF."""
    async with async_session() as db:
        try:
            query = await db.get(Query, query_id)
            if not query:
                logger.error(f"Query not found: {query_id}")
                return

            query.status = QueryStatus.PROCESSING.value
            await db.commit()

            # ── Parse Query ────────────────────────────────────
            parsed = await query_understanding.parse_query(query.query_text)
            is_generic = parsed.get("is_generic", False)

            query.normalized_query = json.dumps(parsed)
            await db.commit()

            # ── Extract Requirements ───────────────────────────
            extracted = await requirement_extractor.extract_from_parsed_query(
                parsed_query=parsed,
                original_query=query.query_text,
            )
            normalized = requirement_normalizer.normalize_batch(extracted)

            # ── Generate Embeddings ────────────────────────────
            requirement_dicts = []
            for req in normalized:
                emb = await embedding_service.generate_embedding(req.normalized_requirement)
                emb_json = embedding_service.embedding_to_json(emb) if emb else None

                qr = QueryRequirement(
                    query_id=query_id,
                    requirement=req.requirement_text,
                    normalized_requirement=req.normalized_requirement,
                    requirement_type=req.requirement_type,
                    parameters=req.parameters,
                    embedding=emb_json,
                )
                db.add(qr)
                await db.flush()

                requirement_dicts.append({
                    "id": qr.id,
                    "text": req.requirement_text,
                    "normalized": req.normalized_requirement,
                    "type": req.requirement_type,
                    "params": req.parameters,
                    "product_category": req.product_category,
                    "embedding": emb,
                    "source": "query",
                })

            await db.commit()

            # ── Run SHARED Recommendation Pipeline ─────────────
            query.status = QueryStatus.ANALYZING.value
            await db.commit()

            recommendations = await run_recommendation_pipeline(
                requirements=requirement_dicts,
                db=db,
                is_generic_query=is_generic,
            )

            # ── Complete ───────────────────────────────────────
            query.status = QueryStatus.COMPLETED.value
            await db.commit()

            logger.info(f"Query analysis completed: {query_id}, {len(recommendations)} recommendations")

        except Exception as e:
            logger.error(f"Query analysis failed: {e}", exc_info=True)
            query_update = await db.get(Query, query_id)
            if query_update:
                query_update.status = QueryStatus.FAILED.value
                await db.commit()
