"""
Procura — Compliance Scorer

Dedicated compliance scoring engine. Compliance answers:
"How much does this standard cover the user's requirements?"

Calculated AFTER Gemini analysis from structured coverage findings.
Gemini does NOT output the final numerical compliance score.
"""

import logging
from typing import Optional

from app.core.config import settings
from app.services.gemini_service import GeminiAnalysisResult

logger = logging.getLogger("procura.compliance_scorer")


# Coverage status weights
COVERAGE_WEIGHTS = {
    "covered": 1.0,
    "partial": 0.5,
    "missing": 0.0,
    "not_applicable": None,  # Excluded from calculation
}

# Category importance weights (configurable)
CATEGORY_WEIGHTS = {
    "product_type": 1.5,
    "performance": 1.3,
    "safety": 1.4,
    "material": 1.1,
    "testing": 1.2,
    "electrical": 1.0,
    "mechanical": 1.0,
    "marking": 0.8,
    "documentation": 0.7,
}


class ComplianceScorer:
    """
    Converts Gemini's structured coverage findings into a numerical compliance score.

    Architecture:
        Gemini Analysis → Structured Coverage → ComplianceScorer → Score (0–100)

    Rules:
    - Gemini outputs coverage categories (covered/partial/missing/not_applicable)
    - This engine converts those into a weighted numerical score
    - Returns None for generic queries with insufficient specs
    """

    def __init__(self):
        self.weight_covered = settings.COMPLIANCE_WEIGHT_COVERED
        self.weight_partial = settings.COMPLIANCE_WEIGHT_PARTIAL
        self.weight_missing = settings.COMPLIANCE_WEIGHT_MISSING

    def score(
        self,
        analysis: GeminiAnalysisResult,
        is_generic_query: bool = False,
    ) -> Optional[float]:
        """
        Calculate compliance score from Gemini's structured coverage.

        Args:
            analysis: Gemini analysis result with coverage dict
            is_generic_query: If True, return None (can't assess compliance without specs)

        Returns:
            Compliance score 0–100, or None if insufficient info
        """
        # Rule: generic queries must NOT receive fabricated compliance scores
        if is_generic_query:
            logger.info("Generic query detected — compliance score set to None")
            return None

        coverage = analysis.coverage
        if not coverage:
            return None

        total_weight = 0.0
        weighted_sum = 0.0

        for category, status in coverage.items():
            status_lower = str(status).lower().strip()

            # Skip not_applicable categories
            if status_lower == "not_applicable":
                continue

            # Get coverage value
            coverage_value = COVERAGE_WEIGHTS.get(status_lower, 0.0)
            if coverage_value is None:
                continue

            # Get category weight
            cat_weight = CATEGORY_WEIGHTS.get(category, 1.0)

            weighted_sum += coverage_value * cat_weight
            total_weight += cat_weight

        if total_weight == 0:
            return None

        score = (weighted_sum / total_weight) * 100
        return round(max(0.0, min(100.0, score)), 1)


# Singleton
compliance_scorer = ComplianceScorer()
