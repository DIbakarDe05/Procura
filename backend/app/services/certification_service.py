"""
Procura — Certification Service

Checks verified BIS certification requirements.
Never guesses — if data isn't available, says so explicitly.
"""

import logging
from typing import Optional
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bis_standard import BISStandard

logger = logging.getLogger("procura.certification_service")


@dataclass
class CertificationInfo:
    standard_number: str
    certification_required: Optional[bool] = None
    certification_details: Optional[str] = None
    verified: bool = False
    note: str = ""


class CertificationService:
    """
    Looks up verified BIS certification requirements.
    If data is not available, explicitly states so — never fabricates.
    """

    async def check_certification(
        self,
        standard_id: str,
        db: AsyncSession,
    ) -> CertificationInfo:
        """
        Check certification requirements from verified BIS data.

        Returns explicit "not verified" message if data is unavailable.
        """
        result = await db.execute(
            select(BISStandard).where(BISStandard.id == standard_id)
        )
        standard = result.scalar_one_or_none()

        if not standard:
            return CertificationInfo(
                standard_number="Unknown",
                note="Standard not found in verified database.",
            )

        if standard.certification_required is not None:
            return CertificationInfo(
                standard_number=standard.standard_number,
                certification_required=standard.certification_required,
                certification_details=standard.certification_details,
                verified=True,
                note="Certification information verified from BIS database.",
            )

        return CertificationInfo(
            standard_number=standard.standard_number,
            certification_required=None,
            certification_details=None,
            verified=False,
            note="Certification requirement could not be verified from the available BIS dataset.",
        )


# Singleton
certification_service = CertificationService()
