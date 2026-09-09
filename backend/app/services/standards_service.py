"""
Procura — Standards Service

Handles allied/normative standard lookups, version/amendment checks.
All data comes from the verified BIS database — never from Gemini.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bis_standard import BISStandard, StandardReference

logger = logging.getLogger("procura.standards_service")


@dataclass
class RelatedStandard:
    standard_number: str
    title: str
    reference_type: str
    description: Optional[str] = None


@dataclass
class VersionInfo:
    standard_number: str
    edition: Optional[str] = None
    status: Optional[str] = None
    amendments: Optional[list] = None
    is_current: bool = True
    note: Optional[str] = None


class StandardsService:
    """
    Lookup service for related standards, versions, and amendments.
    All data comes from the verified BIS database.
    """

    async def get_related_standards(
        self,
        standard_id: str,
        db: AsyncSession,
    ) -> list[RelatedStandard]:
        """
        Get all related standards (normative, test method, safety, etc.).

        Args:
            standard_id: ID of the primary standard
            db: Database session

        Returns:
            List of related standards with relationship types
        """
        result = await db.execute(
            select(StandardReference, BISStandard)
            .join(BISStandard, StandardReference.referenced_standard_id == BISStandard.id)
            .where(StandardReference.standard_id == standard_id)
        )
        rows = result.all()

        related = []
        for ref, std in rows:
            related.append(RelatedStandard(
                standard_number=std.standard_number,
                title=std.title,
                reference_type=ref.reference_type,
                description=ref.description,
            ))

        return related

    async def check_version(
        self,
        standard_id: str,
        db: AsyncSession,
    ) -> VersionInfo:
        """
        Check version/amendment info from verified database.

        Never allows Gemini to invent version information.
        """
        result = await db.execute(
            select(BISStandard).where(BISStandard.id == standard_id)
        )
        standard = result.scalar_one_or_none()

        if not standard:
            return VersionInfo(
                standard_number="Unknown",
                note="Standard not found in verified database",
                is_current=False,
            )

        amendments = standard.amendments if standard.amendments else []

        return VersionInfo(
            standard_number=standard.standard_number,
            edition=standard.edition,
            status=standard.status,
            amendments=amendments,
            is_current=standard.status == "current",
            note=None if standard.status == "current" else f"Standard status: {standard.status}",
        )

    async def validate_standard_exists(
        self,
        standard_number: str,
        db: AsyncSession,
    ) -> Optional[BISStandard]:
        """
        Verify that a standard number exists in the verified database.
        Used to reject Gemini-hallucinated standard numbers.
        """
        result = await db.execute(
            select(BISStandard).where(BISStandard.standard_number == standard_number)
        )
        return result.scalar_one_or_none()


# Singleton
standards_service = StandardsService()
