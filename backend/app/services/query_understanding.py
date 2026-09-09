"""
Procura — Query Understanding Service

Parses natural-language technical queries into structured requirements
using Gemini. This is NOT a chatbot — it extracts structured data.
"""

import json
import logging
import asyncio
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("procura.query_understanding")

QUERY_PARSE_PROMPT = """You are an expert technical procurement analyst for the Bureau of Indian Standards (BIS).
Parse the following natural-language technical query into a structured representation.

Note: The user query may be in English, Hindi (हिन्दी), Bengali (বাংলা), Marathi (मराठी), Tamil (தமிழ்), Gujarati (ગુજરાતી), or any other Indian language/script.
Regardless of the input language, always translate and output the extracted product, application, and parameters into standard English technical terminology so they can be matched against the BIS standards repository.

Extract:
1. product - The main product, material, or equipment being described (in English)
2. application - The intended application or use case (in English)
3. parameters - Technical parameters with their values and units
4. requirement_categories - Types of requirements mentioned (performance, material, safety, testing, etc.)

Query: "{query}"

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
    "product": "string - main product name in English",
    "application": "string or null - intended application in English",
    "parameters": {{
        "parameter_name": {{
            "value": "string or number",
            "unit": "string or null",
            "operator": "string: =, >=, <=, >, <, range, or null"
        }}
    }},
    "requirement_categories": ["list of requirement types"],
    "is_generic": false
}}

If the query is generic (e.g., "What standards apply to pumps?") with no specific technical parameters, set "is_generic": true.
If a field cannot be determined, use null.
"""


class QueryUnderstandingService:
    """Converts natural-language queries into structured requirement representations."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        """Lazy-load Gemini client."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    async def parse_query(self, query_text: str) -> dict:
        """
        Parse a natural-language technical query into structured form.

        Args:
            query_text: Raw query text from the user

        Returns:
            Structured dict with product, parameters, categories
        """
        try:
            client = self._get_client()
            prompt = QUERY_PARSE_PROMPT.format(query=query_text)

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )

            result_text = response.text.strip()
            parsed = self._clean_and_parse_json(result_text)

            if parsed:
                logger.info(f"Parsed query into structured form: product={parsed.get('product')}")
                return parsed

        except Exception as e:
            logger.error(f"Gemini query parsing failed: {e}")

        # Fallback: basic heuristic parsing
        return self._fallback_parse(query_text)

    def _clean_and_parse_json(self, text: str) -> Optional[dict]:
        """Clean Gemini response and parse JSON."""
        # Remove markdown code fences
        import re
        text = re.sub(r"```(?:json)?\s*", "", text)
        text = re.sub(r"```\s*$", "", text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Gemini JSON response")
            return None

    def _fallback_parse(self, query_text: str) -> dict:
        """Basic heuristic parsing when Gemini is unavailable."""
        import re

        query_lower = query_text.lower()

        # Try to detect product robustly:
        # Match common phrases: "need [a] <product> for/with", "looking for <product>", "procure <product>"
        product = None
        match = re.search(
            r"(?:need|looking for|require|procuring|procure|supply of|purchase of)\s+(?:an?|the)?\s*([a-zA-Z0-9\s\-]+?)(?:\s+\b(?:for|with|having|to|suitable)\b|[.,;:\n]|$)",
            query_text,
            re.IGNORECASE,
        )
        if match:
            product = match.group(1).strip()
        else:
            # Fallback: take text before first punctuation or standalone \bfor\b
            first_clause = re.split(r"[.:;\n]|\bfor\b", query_text, flags=re.IGNORECASE)[0]
            product = re.sub(
                r"^(?:i\s+need\s+(?:an?|the)?|we\s+need\s+(?:an?|the)?|please\s+recommend\s+standards\s+for\s+)\s*",
                "",
                first_clause,
                flags=re.IGNORECASE,
            ).strip()

        if not product:
            product = query_text[:100]

        # Try to detect parameters
        parameters = {}

        # Pattern: number + unit
        param_patterns = [
            (r"(\d+(?:\.\d+)?)\s*(hp|kw|kva|volt|v|amp|a|rpm|mm|cm|m|kg|mpa|bar|psi|°c|celsius|%)",
             lambda m: (m.group(2).lower(), {"value": float(m.group(1)), "unit": m.group(2), "operator": "="})),
        ]

        for pattern, extractor in param_patterns:
            for match in re.finditer(pattern, query_text, re.IGNORECASE):
                key, val = extractor(match)
                parameters[key] = val

        return {
            "product": product[:200],
            "application": None,
            "parameters": parameters,
            "requirement_categories": ["general"],
            "is_generic": len(parameters) == 0,
        }


# Singleton
query_understanding = QueryUnderstandingService()
