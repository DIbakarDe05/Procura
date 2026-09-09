"""
Procura — Requirement Extractor

Extracts individual requirements from PDF sections and parsed queries.
Produces the same internal format regardless of source.
"""

import re
import json
import logging
import asyncio
from typing import Optional

from app.core.config import settings
from app.schemas.requirement import NormalizedRequirementSchema

logger = logging.getLogger("procura.requirement_extractor")

EXTRACTION_PROMPT = """You are an expert technical requirements analyst. Extract individual technical requirements from the following text.
Note: The source text may be in English or an Indian language (Hindi, etc.). Translate and standardize requirement statements into clear English technical terminology.

For each requirement, identify:
1. requirement_text - The clear technical requirement statement in English
2. requirement_type - One of: performance, material, safety, testing, electrical, mechanical, dimensional, environmental, certification, marking, documentation, general
3. parameters - Any technical parameters with name, value, unit, operator

Text:
\"\"\"
{text}
\"\"\"

Return ONLY valid JSON array (no markdown, no explanation):
[
    {{
        "requirement_text": "string",
        "requirement_type": "string",
        "parameters": {{
            "parameter_name": {{
                "value": "string or number",
                "unit": "string or null",
                "operator": "= or >= or <= or > or < or null"
            }}
        }}
    }}
]

Extract at most 20 requirements. Focus on technical specifications, not administrative clauses.
"""


class RequirementExtractor:
    """
    Extracts requirements from both PDF sections and parsed queries.
    Both paths produce identical NormalizedRequirementSchema objects.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def extract_from_text(
        self,
        text: str,
        source: str = "pdf",
        page_number: Optional[int] = None,
        section_title: Optional[str] = None,
    ) -> list[NormalizedRequirementSchema]:
        """
        Extract requirements from arbitrary text (PDF section content).

        Args:
            text: Raw text to extract requirements from
            source: "pdf" or "query"
            page_number: Source page number (for traceability)
            section_title: Source section title

        Returns:
            List of normalized requirement schemas
        """
        if not text or len(text.strip()) < 10:
            return []

        # Truncate very long text
        truncated = text[:settings.MAX_TENDER_CHARACTERS]

        try:
            client = self._get_client()
            prompt = EXTRACTION_PROMPT.format(text=truncated)

            def _call_gemini():
                return client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                )

            response = await asyncio.wait_for(asyncio.to_thread(_call_gemini), timeout=30.0)
            requirements_data = self._parse_response(response.text)

            return [
                NormalizedRequirementSchema(
                    requirement_text=req.get("requirement_text", ""),
                    normalized_requirement=req.get("requirement_text", "").lower().strip(),
                    product_category=None,
                    requirement_type=req.get("requirement_type", "general"),
                    parameters=req.get("parameters"),
                    source=source,
                    source_page=page_number,
                    source_section=section_title,
                )
                for req in requirements_data
                if req.get("requirement_text")
            ]

        except Exception as e:
            logger.warning(f"Gemini requirement extraction failed/timed out: {e}, using heuristic fallback")
            return self._fallback_extract(text, source, page_number, section_title)

    async def extract_from_parsed_query(
        self,
        parsed_query: dict,
        original_query: str,
    ) -> list[NormalizedRequirementSchema]:
        """
        Convert a parsed query structure into normalized requirements.
        These enter the SAME pipeline as PDF requirements.

        Args:
            parsed_query: Output from QueryUnderstandingService
            original_query: The original query text

        Returns:
            List of normalized requirement schemas
        """
        requirements = []

        product = parsed_query.get("product")
        application = parsed_query.get("application")
        parameters = parsed_query.get("parameters", {})

        # Requirement for the product itself
        if product:
            requirements.append(NormalizedRequirementSchema(
                requirement_text=f"Product type: {product}",
                normalized_requirement=f"product type = {product.lower()}",
                product_category=product,
                requirement_type="general",
                parameters=None,
                source="query",
                source_page=None,
                source_section=None,
            ))

        # Requirement for each parameter
        for param_name, param_data in parameters.items():
            if isinstance(param_data, dict):
                value = param_data.get("value", "")
                unit = param_data.get("unit", "")
                operator = param_data.get("operator", "=")
                req_text = f"{param_name}: {value} {unit}".strip()
                norm_text = f"{param_name} {operator} {value} {unit}".strip().lower()
            else:
                req_text = f"{param_name}: {param_data}"
                norm_text = f"{param_name} = {param_data}".lower()

            requirements.append(NormalizedRequirementSchema(
                requirement_text=req_text,
                normalized_requirement=norm_text,
                product_category=product,
                requirement_type=self._infer_type(param_name),
                parameters={param_name: param_data} if isinstance(param_data, dict) else {param_name: {"value": param_data}},
                source="query",
                source_page=None,
                source_section=None,
            ))

        # Requirement for application
        if application:
            requirements.append(NormalizedRequirementSchema(
                requirement_text=f"Application: {application}",
                normalized_requirement=f"application = {application.lower()}",
                product_category=product,
                requirement_type="general",
                parameters=None,
                source="query",
                source_page=None,
                source_section=None,
            ))

        # If no specific requirements were extracted, use the whole query
        if not requirements:
            requirements.append(NormalizedRequirementSchema(
                requirement_text=original_query,
                normalized_requirement=original_query.lower().strip(),
                product_category=product,
                requirement_type="general",
                parameters=None,
                source="query",
                source_page=None,
                source_section=None,
            ))

        return requirements

    def _parse_response(self, text: str) -> list[dict]:
        """Parse Gemini JSON response."""
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
        text = text.strip()

        try:
            result = json.loads(text)
            return result if isinstance(result, list) else [result]
        except json.JSONDecodeError:
            logger.warning("Failed to parse requirement extraction response")
            return []

    def _fallback_extract(
        self, text: str, source: str,
        page_number: Optional[int], section_title: Optional[str],
    ) -> list[NormalizedRequirementSchema]:
        """Heuristic fallback: split text into sentence-level requirements."""
        sentences = re.split(r'[.;]\s+', text)
        requirements = []

        for sentence in sentences[:20]:
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue

            # Check if it looks like a technical requirement
            tech_indicators = [
                "shall", "must", "should", "require", "specification",
                "standard", "minimum", "maximum", "rating", "capacity",
                "material", "test", "comply", "accordance",
            ]
            if any(ind in sentence.lower() for ind in tech_indicators):
                requirements.append(NormalizedRequirementSchema(
                    requirement_text=sentence,
                    normalized_requirement=sentence.lower(),
                    requirement_type="general",
                    parameters=None,
                    source=source,
                    source_page=page_number,
                    source_section=section_title,
                ))

        return requirements

    def _infer_type(self, param_name: str) -> str:
        """Infer requirement type from parameter name."""
        param_lower = param_name.lower()
        type_map = {
            "power": "electrical", "voltage": "electrical", "current": "electrical",
            "speed": "performance", "efficiency": "performance", "capacity": "performance",
            "flow": "performance", "pressure": "performance", "temperature": "performance",
            "material": "material", "steel": "material", "alloy": "material",
            "weight": "dimensional", "dimension": "dimensional", "size": "dimensional",
            "length": "dimensional", "width": "dimensional", "height": "dimensional",
        }
        for key, req_type in type_map.items():
            if key in param_lower:
                return req_type
        return "general"


# Singleton
requirement_extractor = RequirementExtractor()
