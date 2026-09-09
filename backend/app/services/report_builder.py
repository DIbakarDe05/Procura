"""
Procura — Report Builder

Assembles the final structured recommendation report.
Works identically for both PDF and Query inputs.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.recommendation import (
    RecommendationResponse,
    CoverageDetail,
    RelatedStandardSchema,
    ReportResponse,
)
from app.services.standards_service import StandardsService
from app.services.certification_service import CertificationService

logger = logging.getLogger("procura.report_builder")


class ReportBuilder:
    """
    Assembles the final structured recommendation report from:
    - Relevance scores
    - Confidence scores
    - Compliance scores
    - Gemini analysis results
    - Related standards
    - Version info
    - Certification info

    Produces identical output format for PDF and Query inputs.
    """

    def __init__(self):
        self.standards_service = StandardsService()
        self.certification_service = CertificationService()

    async def build_report(
        self,
        source_type: str,  # "tender" or "query"
        source_id: str,
        recommendations_data: list[dict],
        db: AsyncSession,
        is_generic_query: bool = False,
    ) -> ReportResponse:
        """
        Build the complete structured recommendation report.

        Args:
            source_type: "tender" or "query"
            source_id: ID of the tender or query
            recommendations_data: List of dicts with scoring/analysis data
            db: Database session
            is_generic_query: Whether this is a generic (low-detail) query

        Returns:
            Complete ReportResponse
        """
        # Sort incoming recommendations by relevance score descending and deduplicate
        sorted_raw = sorted(
            recommendations_data,
            key=lambda r: r.get("relevance_score") or 0,
            reverse=True,
        )

        seen_standards = set()
        top_candidates = []
        for r in sorted_raw:
            sid = r.get("standard_id") or r.get("standard_number")
            if sid and sid in seen_standards:
                continue
            if sid:
                seen_standards.add(sid)
            top_candidates.append(r)
            if len(top_candidates) == 4:
                break

        recommendations = []

        for rec_data in top_candidates:
            standard_id = rec_data["standard_id"]

            # Get related standards
            related = await self.standards_service.get_related_standards(standard_id, db)
            related_schemas = [
                RelatedStandardSchema(
                    standard_number=r.standard_number,
                    title=r.title,
                    reference_type=r.reference_type,
                    description=r.description,
                )
                for r in related
            ]

            # Get version info
            version = await self.standards_service.check_version(standard_id, db)
            version_dict = {
                "edition": version.edition,
                "status": version.status,
                "amendments": version.amendments,
                "is_current": version.is_current,
                "note": version.note,
            }

            # Get certification info
            cert = await self.certification_service.check_certification(standard_id, db)
            cert_dict = {
                "certification_required": cert.certification_required,
                "certification_details": cert.certification_details,
                "verified": cert.verified,
                "note": cert.note,
            }

            # Build coverage details
            coverage_details = []
            coverage_data = rec_data.get("coverage", {})
            for category, status in coverage_data.items():
                coverage_details.append(CoverageDetail(
                    category=category,
                    status=status,
                ))

            # Determine applicability level
            relevance = rec_data.get("relevance_score", 0)
            if relevance >= 85:
                applicability = "HIGH"
            elif relevance >= 60:
                applicability = "MEDIUM"
            else:
                applicability = "LOW"

            recommendations.append(RecommendationResponse(
                id=rec_data.get("recommendation_id", ""),
                standard_number=rec_data["standard_number"],
                standard_title=rec_data["standard_title"],
                relevance_score=rec_data.get("relevance_score"),
                confidence_score=rec_data.get("confidence_score"),
                compliance_score=rec_data.get("compliance_score"),
                applicable=rec_data.get("applicable", True),
                applicability_level=applicability,
                reasoning=rec_data.get("reasoning", ""),
                coverage=coverage_details,
                gaps=rec_data.get("gaps", []),
                related_standards=related_schemas,
                version_info=version_dict,
                certification_info=cert_dict,
                status=rec_data.get("status", "pending"),
            ))

        # Build compliance note for generic queries
        compliance_note = None
        if is_generic_query:
            compliance_note = (
                "Compliance cannot be assessed from the provided information because "
                "insufficient technical specifications were supplied. "
                "Provide specific technical parameters for compliance scoring."
            )

        return ReportResponse(
            source_type=source_type,
            source_id=source_id,
            total_requirements=recommendations_data[0].get("total_requirements", 0) if recommendations_data else 0,
            total_standards_evaluated=len(recommendations_data),
            recommendations=recommendations,
            compliance_note=compliance_note,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )


# Singleton
report_builder = ReportBuilder()
