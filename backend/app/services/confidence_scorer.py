"""
Procura — Confidence Scorer

Confidence answers: "How confident is the system in this recommendation?"
Separate from both relevance and compliance.
"""

import logging
from typing import Optional

from app.core.config import settings
from app.services.gemini_service import GeminiAnalysisResult
from app.services.relevance_scorer import RelevanceResult

logger = logging.getLogger("procura.confidence_scorer")


class ConfidenceScorer:
    """
    Calculates confidence based on multiple signals:
    - Retrieval agreement (similarity strength)
    - Scope match quality
    - Gemini assessment consistency
    - Evidence availability
    """

    def __init__(self):
        self.weight_retrieval = settings.CONFIDENCE_WEIGHT_RETRIEVAL
        self.weight_similarity = settings.CONFIDENCE_WEIGHT_SIMILARITY
        self.weight_scope = settings.CONFIDENCE_WEIGHT_SCOPE
        self.weight_evidence = settings.CONFIDENCE_WEIGHT_EVIDENCE

    def score(
        self,
        relevance: RelevanceResult,
        analysis: Optional[GeminiAnalysisResult] = None,
        candidate_count: int = 0,
        rank_position: int = 0,
    ) -> float:
        """
        Calculate confidence score.

        Args:
            relevance: Relevance scoring result
            analysis: Gemini analysis result (if available)
            candidate_count: Total candidates retrieved
            rank_position: This standard's rank (0-indexed)

        Returns:
            Confidence score 0–100
        """
        # 1. Retrieval signal: how strongly did this standard emerge from retrieval?
        retrieval_score = self._retrieval_confidence(
            relevance.semantic_score, candidate_count, rank_position
        )

        # 2. Similarity strength: how close was the embedding match?
        similarity_score = min(relevance.semantic_score * 1.1, 100.0)

        # 3. Scope match: how well does the scope align?
        scope_score = relevance.scope_match_score

        # 4. Evidence availability: does Gemini analysis provide clear reasoning?
        evidence_score = self._evidence_confidence(analysis)

        # Weighted combination
        confidence = (
            self.weight_retrieval * retrieval_score
            + self.weight_similarity * similarity_score
            + self.weight_scope * scope_score
            + self.weight_evidence * evidence_score
        )

        return round(max(0.0, min(100.0, confidence)), 1)

    def _retrieval_confidence(
        self, semantic_score: float, candidate_count: int, rank_position: int,
    ) -> float:
        """Higher confidence when standard ranks well among many candidates."""
        if candidate_count == 0:
            return 50.0

        # Top-ranked standards get higher confidence
        rank_ratio = 1.0 - (rank_position / max(candidate_count, 1))
        rank_signal = rank_ratio * 100

        # Boost if semantic score is very high
        if semantic_score > 80:
            rank_signal = min(rank_signal * 1.2, 100.0)

        return rank_signal

    def _evidence_confidence(self, analysis: Optional[GeminiAnalysisResult]) -> float:
        """Higher confidence when Gemini provides strong evidence."""
        if not analysis:
            return 40.0

        score = 50.0  # Base

        # Has reasoning?
        if analysis.reasoning and len(analysis.reasoning) > 20:
            score += 15

        # Has key provisions?
        if analysis.key_provisions:
            score += 10

        # Clear applicability determination?
        if analysis.applicability_level == "HIGH":
            score += 15
        elif analysis.applicability_level == "MEDIUM":
            score += 5

        # Has coverage data?
        if analysis.coverage:
            covered_count = sum(
                1 for v in analysis.coverage.values()
                if str(v).lower() == "covered"
            )
            score += min(covered_count * 3, 15)

        # No errors?
        if not analysis.error:
            score += 5

        return min(score, 100.0)


# Singleton
confidence_scorer = ConfidenceScorer()
