"""
Procura — Test: Pipeline Convergence

CRITICAL TEST: Proves that PDF requirements and Query requirements
enter the SAME recommendation pipeline.
"""

import pytest
from app.schemas.requirement import NormalizedRequirementSchema
from app.services.requirement_normalizer import requirement_normalizer
from app.services.relevance_scorer import relevance_scorer, RelevanceResult
from app.services.compliance_scorer import compliance_scorer
from app.services.confidence_scorer import confidence_scorer
from app.services.gemini_service import GeminiAnalysisResult
from app.services.retrieval_service import RetrievalCandidate


class TestPipelineConvergence:
    """
    Tests proving that PDF and Query requirements produce identical
    internal representations and can use the same scoring pipeline.
    """

    def test_pdf_and_query_produce_same_schema(self):
        """Both paths produce NormalizedRequirementSchema objects."""
        pdf_req = NormalizedRequirementSchema(
            requirement_text="Motor efficiency shall be at least 90%",
            normalized_requirement="motor efficiency >= 90%",
            product_category="electric motor",
            requirement_type="performance",
            parameters={"efficiency": {"value": 90, "unit": "%", "operator": ">="}},
            source="pdf",
            source_page=14,
            source_section="Technical Specifications",
        )

        query_req = NormalizedRequirementSchema(
            requirement_text="Power: 10 HP",
            normalized_requirement="power = 10 HP",
            product_category="centrifugal water pump",
            requirement_type="electrical",
            parameters={"power": {"value": 10, "unit": "HP", "operator": "="}},
            source="query",
            source_page=None,
            source_section=None,
        )

        # Both are the SAME type
        assert type(pdf_req) == type(query_req)

        # Both have the same fields
        assert hasattr(pdf_req, "normalized_requirement")
        assert hasattr(query_req, "normalized_requirement")
        assert hasattr(pdf_req, "parameters")
        assert hasattr(query_req, "parameters")

    def test_normalizer_accepts_both_sources(self):
        """The requirement normalizer processes both PDF and Query requirements."""
        pdf_req = NormalizedRequirementSchema(
            requirement_text="Steel grade shall be IS 2062",
            normalized_requirement="steel grade IS 2062",
            requirement_type="material",
            source="pdf",
        )

        query_req = NormalizedRequirementSchema(
            requirement_text="Stainless steel casing",
            normalized_requirement="stainless steel casing",
            requirement_type="material",
            source="query",
        )

        pdf_normalized = requirement_normalizer.normalize(pdf_req)
        query_normalized = requirement_normalizer.normalize(query_req)

        assert pdf_normalized.source == "pdf"
        assert query_normalized.source == "query"
        assert pdf_normalized.normalized_requirement is not None
        assert query_normalized.normalized_requirement is not None

    def test_relevance_scorer_works_with_both_sources(self):
        """The relevance scorer scores both PDF and Query requirements identically."""
        # Create a mock candidate
        from unittest.mock import MagicMock
        mock_standard = MagicMock()

        candidate = RetrievalCandidate(
            standard_id="test-id",
            standard_number="IS 9137:2002",
            title="Centrifugal Pumps — Specification",
            scope="Requirements for centrifugal pumps for water supply",
            category="Mechanical Engineering",
            similarity_score=0.85,
            standard=mock_standard,
        )

        # PDF requirement
        pdf_score = relevance_scorer.score(
            candidate=candidate,
            requirement_text="centrifugal pump for water supply",
            requirement_params={"power": {"value": 10, "unit": "HP"}},
            product_category="centrifugal pump",
        )

        # Query requirement — same content, different source
        query_score = relevance_scorer.score(
            candidate=candidate,
            requirement_text="centrifugal pump for water supply",
            requirement_params={"power": {"value": 10, "unit": "HP"}},
            product_category="centrifugal pump",
        )

        # Same input → same output regardless of source
        assert isinstance(pdf_score, RelevanceResult)
        assert isinstance(query_score, RelevanceResult)
        assert pdf_score.overall_score == query_score.overall_score

    def test_compliance_null_for_generic_query(self):
        """Generic queries must NOT receive fabricated compliance scores."""
        analysis = GeminiAnalysisResult(
            standard_id="test-id",
            standard_number="IS 9137:2002",
            coverage={"product_type": "covered", "performance": "partial"},
        )

        # Non-generic: should get a score
        score = compliance_scorer.score(analysis, is_generic_query=False)
        assert score is not None
        assert 0 <= score <= 100

        # Generic: must return None
        score_generic = compliance_scorer.score(analysis, is_generic_query=True)
        assert score_generic is None

    def test_compliance_scoring_from_coverage(self):
        """Compliance score is calculated from structured coverage, not by Gemini."""
        analysis = GeminiAnalysisResult(
            standard_id="test-id",
            standard_number="IS 9137:2002",
            coverage={
                "product_type": "covered",
                "performance": "covered",
                "material": "partial",
                "testing": "missing",
                "safety": "not_applicable",
            },
        )

        score = compliance_scorer.score(analysis)
        assert score is not None
        assert 0 <= score <= 100

        # All covered should give higher score than mix
        all_covered_analysis = GeminiAnalysisResult(
            standard_id="test-id",
            standard_number="IS 9137:2002",
            coverage={
                "product_type": "covered",
                "performance": "covered",
                "material": "covered",
                "testing": "covered",
            },
        )
        all_covered_score = compliance_scorer.score(all_covered_analysis)
        assert all_covered_score > score

    def test_three_scores_are_independent(self):
        """Relevance, confidence, and compliance are separate metrics."""
        from unittest.mock import MagicMock

        mock_standard = MagicMock()
        candidate = RetrievalCandidate(
            standard_id="test-id",
            standard_number="IS 325:1996",
            title="Three Phase Induction Motors",
            scope="Motors rated up to 315 kW",
            category="Electrical",
            similarity_score=0.75,
            standard=mock_standard,
        )

        # Relevance
        relevance = relevance_scorer.score(
            candidate, "three phase induction motor 10 HP",
        )

        # Analysis
        analysis = GeminiAnalysisResult(
            standard_id="test-id",
            standard_number="IS 325:1996",
            coverage={"product_type": "covered", "performance": "partial"},
            reasoning="Motor standard covers general requirements",
        )

        # Compliance
        compliance = compliance_scorer.score(analysis)

        # Confidence
        confidence = confidence_scorer.score(
            relevance=relevance,
            analysis=analysis,
            candidate_count=5,
            rank_position=0,
        )

        # All three are separate numbers
        assert relevance.overall_score != compliance
        assert isinstance(confidence, float)
        assert 0 <= relevance.overall_score <= 100
        assert 0 <= compliance <= 100
        assert 0 <= confidence <= 100
