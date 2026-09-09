"""
Procura — Relevance Scorer

Dedicated relevance scoring engine. Relevance answers:
"How relevant is this BIS standard to the user's requirement?"

This is SEPARATE from compliance and confidence.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.services.retrieval_service import RetrievalCandidate

logger = logging.getLogger("procura.relevance_scorer")


@dataclass
class RelevanceResult:
    """Detailed relevance scoring result."""
    standard_id: str
    standard_number: str
    overall_score: float  # 0–100
    semantic_score: float  # 0–100
    product_match_score: float  # 0–100
    scope_match_score: float  # 0–100
    parameter_score: float  # 0–100


class RelevanceScorer:
    """
    Calculates relevance score using multiple signals.
    Gemini does NOT determine the final relevance score.

    Signals:
    - Semantic similarity (from embedding retrieval)
    - Product/category match
    - Scope match
    - Technical parameter compatibility
    """

    def __init__(self):
        self.weight_semantic = settings.RELEVANCE_WEIGHT_SEMANTIC
        self.weight_product = settings.RELEVANCE_WEIGHT_PRODUCT
        self.weight_scope = settings.RELEVANCE_WEIGHT_SCOPE
        self.weight_parameter = settings.RELEVANCE_WEIGHT_PARAMETER

    def score(
        self,
        candidate: RetrievalCandidate,
        requirement_text: str,
        requirement_params: Optional[dict] = None,
        product_category: Optional[str] = None,
    ) -> RelevanceResult:
        """
        Calculate the relevance score for a candidate standard against a requirement.

        Args:
            candidate: Retrieved BIS standard candidate
            requirement_text: Normalized requirement text
            requirement_params: Extracted technical parameters
            product_category: Product category from requirement

        Returns:
            RelevanceResult with overall and component scores
        """
        # 1. Semantic similarity score (already computed during retrieval)
        semantic = candidate.similarity_score * 100

        # 2. Product/category match
        product_score = self._product_match(
            candidate, requirement_text, product_category
        )

        # 3. Scope match
        scope_score = self._scope_match(candidate, requirement_text)

        # 4. Parameter compatibility
        param_score = self._parameter_match(candidate, requirement_params)

        # Weighted combination
        overall = (
            self.weight_semantic * semantic
            + self.weight_product * product_score
            + self.weight_scope * scope_score
            + self.weight_parameter * param_score
        )

        # Clamp to 0–100
        overall = max(0.0, min(100.0, overall))

        return RelevanceResult(
            standard_id=candidate.standard_id,
            standard_number=candidate.standard_number,
            overall_score=round(overall, 1),
            semantic_score=round(semantic, 1),
            product_match_score=round(product_score, 1),
            scope_match_score=round(scope_score, 1),
            parameter_score=round(param_score, 1),
        )

    def score_batch(
        self,
        candidates: list[RetrievalCandidate],
        requirement_text: str,
        requirement_params: Optional[dict] = None,
        product_category: Optional[str] = None,
    ) -> list[RelevanceResult]:
        """Score and rank a batch of candidates."""
        results = [
            self.score(c, requirement_text, requirement_params, product_category)
            for c in candidates
        ]
        results.sort(key=lambda r: r.overall_score, reverse=True)
        return results

    def _product_match(
        self,
        candidate: RetrievalCandidate,
        requirement_text: str,
        product_category: Optional[str] = None,
    ) -> float:
        """Score product/category alignment."""
        score = 0.0
        req_lower = requirement_text.lower()
        title_lower = candidate.title.lower()
        scope_lower = (candidate.scope or "").lower()

        # Check if product category appears in standard title or scope
        if product_category:
            product_lower = product_category.lower()
            product_tokens = product_lower.split()

            # Exact product mention in title
            if product_lower in title_lower:
                score = 90.0
            # Tokens overlap with title
            elif any(t in title_lower for t in product_tokens if len(t) > 2):
                score = 70.0
            # Product in scope
            elif product_lower in scope_lower:
                score = 60.0
            elif any(t in scope_lower for t in product_tokens if len(t) > 2):
                score = 40.0

        # Also check requirement text tokens against standard
        if score < 50:
            req_tokens = set(re.findall(r'\b\w{3,}\b', req_lower))
            title_tokens = set(re.findall(r'\b\w{3,}\b', title_lower))
            overlap = req_tokens & title_tokens
            if overlap:
                score = max(score, min(len(overlap) * 15, 80))

        return min(score, 100.0)

    def _scope_match(
        self,
        candidate: RetrievalCandidate,
        requirement_text: str,
    ) -> float:
        """Score scope alignment using token overlap."""
        if not candidate.scope:
            return 30.0  # Neutral if no scope data

        req_tokens = set(re.findall(r'\b\w{3,}\b', requirement_text.lower()))
        scope_tokens = set(re.findall(r'\b\w{3,}\b', candidate.scope.lower()))

        if not req_tokens or not scope_tokens:
            return 30.0

        overlap = req_tokens & scope_tokens
        overlap_ratio = len(overlap) / min(len(req_tokens), len(scope_tokens))

        return min(overlap_ratio * 100, 100.0)

    def _parameter_match(
        self,
        candidate: RetrievalCandidate,
        params: Optional[dict] = None,
    ) -> float:
        """Score technical parameter compatibility."""
        if not params:
            return 50.0  # Neutral if no params

        scope_lower = (candidate.scope or "").lower()
        title_lower = candidate.title.lower()
        combined = f"{title_lower} {scope_lower}"

        matched = 0
        total = len(params)

        for param_name, param_data in params.items():
            param_lower = param_name.lower().replace("_", " ")
            if param_lower in combined:
                matched += 1
            # Also check unit
            if isinstance(param_data, dict) and param_data.get("unit"):
                unit = str(param_data["unit"]).lower()
                if unit in combined:
                    matched += 0.5

        if total == 0:
            return 50.0

        return min((matched / total) * 100, 100.0)


# Singleton
relevance_scorer = RelevanceScorer()
