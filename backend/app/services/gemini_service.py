"""
Procura — Gemini Analysis Service

Gemini is the reasoning layer — it analyzes applicability and coverage
of verified BIS standards against requirements.

CRITICAL: Gemini is NEVER the source of truth for BIS data.
It only evaluates standards that already exist in the verified database.
"""

import json
import re
import logging
import asyncio
from typing import Optional
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger("procura.gemini_service")


ANALYSIS_PROMPT = """You are a technical standards analyst for Indian procurement. Analyze whether the given BIS standard is applicable to the given technical requirement.

CRITICAL RULES:
1. Use ONLY the BIS standard information provided below. Do NOT invent standards.
2. NEVER fabricate BIS standard numbers, titles, versions, or clauses.
3. NEVER claim certification status unless explicitly provided.
4. Evaluate coverage honestly — if something is not covered, say "missing".
5. Distinguish: covered, partial, missing, not_applicable.
6. Provide reasoning based on the standard's scope and the requirement's specifics.

REQUIREMENT:
\"\"\"{requirement_text}\"\"\"

Requirement Type: {requirement_type}
Parameters: {parameters}

BIS STANDARD:
Standard Number: {standard_number}
Title: {standard_title}
Scope: {standard_scope}
Category: {standard_category}
Edition: {standard_edition}
Status: {standard_status}

Return ONLY valid JSON (no markdown, no code fences):
{{
    "applicable": true or false,
    "applicability_level": "HIGH" or "MEDIUM" or "LOW",
    "coverage": {{
        "product_type": "covered" or "partial" or "missing" or "not_applicable",
        "performance": "covered" or "partial" or "missing" or "not_applicable",
        "material": "covered" or "partial" or "missing" or "not_applicable",
        "testing": "covered" or "partial" or "missing" or "not_applicable",
        "safety": "covered" or "partial" or "missing" or "not_applicable",
        "electrical": "covered" or "partial" or "missing" or "not_applicable",
        "mechanical": "covered" or "partial" or "missing" or "not_applicable",
        "marking": "covered" or "partial" or "missing" or "not_applicable",
        "documentation": "covered" or "partial" or "missing" or "not_applicable"
    }},
    "gaps": ["list of specific gaps or missing coverage areas"],
    "reasoning": "Brief technical explanation of why this standard is or is not applicable",
    "key_provisions": ["list of key provisions from the standard that are relevant"]
}}
"""


@dataclass
class GeminiAnalysisResult:
    """Structured result from Gemini analysis."""
    standard_id: str
    standard_number: str
    applicable: bool = True
    applicability_level: str = "MEDIUM"
    coverage: dict = field(default_factory=dict)
    gaps: list[str] = field(default_factory=list)
    reasoning: str = ""
    key_provisions: list[str] = field(default_factory=list)
    error: Optional[str] = None


class GeminiService:
    """
    Gemini-powered analysis of BIS standard applicability.

    Gemini receives verified BIS data and requirement context,
    then returns structured coverage findings.

    Gemini does NOT:
    - Invent BIS standard numbers
    - Calculate final scores
    - Act as the BIS source of truth
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def analyze_standard(
        self,
        requirement_text: str,
        requirement_type: str,
        parameters: Optional[dict],
        standard_number: str,
        standard_title: str,
        standard_scope: str,
        standard_category: Optional[str],
        standard_edition: Optional[str],
        standard_status: Optional[str],
        standard_id: str,
    ) -> GeminiAnalysisResult:
        """
        Analyze a single BIS standard against a requirement.

        Returns structured coverage findings for the compliance scorer.
        """
        try:
            client = self._get_client()
            prompt = ANALYSIS_PROMPT.format(
                requirement_text=requirement_text,
                requirement_type=requirement_type,
                parameters=json.dumps(parameters) if parameters else "None specified",
                standard_number=standard_number,
                standard_title=standard_title,
                standard_scope=standard_scope or "Not available",
                standard_category=standard_category or "Not specified",
                standard_edition=standard_edition or "Not specified",
                standard_status=standard_status or "Not specified",
            )

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )

            parsed = self._parse_response(response.text)

            if parsed:
                return GeminiAnalysisResult(
                    standard_id=standard_id,
                    standard_number=standard_number,
                    applicable=parsed.get("applicable", True),
                    applicability_level=parsed.get("applicability_level", "MEDIUM"),
                    coverage=parsed.get("coverage", {}),
                    gaps=self._safe_list(parsed.get("gaps", [])),
                    reasoning=parsed.get("reasoning", ""),
                    key_provisions=self._safe_list(parsed.get("key_provisions", [])),
                )

        except Exception as e:
            logger.error(f"Gemini analysis failed for {standard_number}: {e}")
            return GeminiAnalysisResult(
                standard_id=standard_id,
                standard_number=standard_number,
                applicable=True,
                applicability_level="MEDIUM",
                coverage={},
                gaps=[],
                reasoning=f"Analysis could not be completed: {str(e)}",
                error=str(e),
            )

        # Fallback
        return GeminiAnalysisResult(
            standard_id=standard_id,
            standard_number=standard_number,
            error="Failed to parse Gemini response",
        )

    async def analyze_batch(
        self,
        requirement_text: str,
        requirement_type: str,
        parameters: Optional[dict],
        candidates: list[dict],
    ) -> list[GeminiAnalysisResult]:
        """Analyze multiple candidate standards for a single requirement."""
        results = []
        for candidate in candidates:
            result = await self.analyze_standard(
                requirement_text=requirement_text,
                requirement_type=requirement_type,
                parameters=parameters,
                standard_number=candidate["standard_number"],
                standard_title=candidate["title"],
                standard_scope=candidate.get("scope", ""),
                standard_category=candidate.get("category"),
                standard_edition=candidate.get("edition"),
                standard_status=candidate.get("status"),
                standard_id=candidate["id"],
            )
            results.append(result)
        return results

    def _parse_response(self, text: str) -> Optional[dict]:
        """Clean and parse Gemini JSON response."""
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Gemini response: {text[:200]}")
            return None

    @staticmethod
    def _safe_list(value) -> list:
        """Ensure value is a list."""
        if isinstance(value, list):
            return value
        if value is None:
            return []
        return [str(value)]


# Singleton
gemini_service = GeminiService()
