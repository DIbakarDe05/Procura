"""
Procura — Requirement Normalizer

Normalizes requirements into a common internal representation.
Both PDF and Query requirements pass through this normalizer.
"""

import re
import logging
from typing import Optional

from app.schemas.requirement import NormalizedRequirementSchema

logger = logging.getLogger("procura.requirement_normalizer")


class RequirementNormalizer:
    """
    Normalizes requirement text and parameters into a consistent format.
    This is the bridge between extraction and the recommendation engine.
    """

    # Common unit normalizations
    UNIT_ALIASES = {
        "horsepower": "HP", "hp": "HP", "h.p.": "HP",
        "kilowatt": "kW", "kw": "kW",
        "kilovolt-ampere": "kVA", "kva": "kVA",
        "volt": "V", "volts": "V", "v": "V",
        "ampere": "A", "amp": "A", "amps": "A",
        "rpm": "RPM", "r.p.m.": "RPM",
        "millimeter": "mm", "millimetre": "mm",
        "centimeter": "cm", "centimetre": "cm",
        "meter": "m", "metre": "m",
        "kilogram": "kg", "kgs": "kg",
        "megapascal": "MPa", "mpa": "MPa",
        "degree celsius": "°C", "deg c": "°C", "celsius": "°C",
        "percent": "%", "percentage": "%",
        "liter": "L", "litre": "L",
        "liter per minute": "LPM", "lpm": "LPM",
        "cubic meter per hour": "m³/h",
    }

    def normalize(self, requirement: NormalizedRequirementSchema) -> NormalizedRequirementSchema:
        """
        Normalize a requirement's text, parameters, and units.

        Args:
            requirement: Raw requirement schema

        Returns:
            Normalized requirement schema
        """
        # Normalize the requirement text
        normalized_text = self._normalize_text(requirement.requirement_text)

        # Normalize parameters
        normalized_params = None
        if requirement.parameters:
            normalized_params = self._normalize_parameters(requirement.parameters)

        return NormalizedRequirementSchema(
            requirement_text=requirement.requirement_text,
            normalized_requirement=normalized_text,
            product_category=requirement.product_category,
            requirement_type=requirement.requirement_type,
            parameters=normalized_params,
            source=requirement.source,
            source_page=requirement.source_page,
            source_section=requirement.source_section,
        )

    def normalize_batch(
        self, requirements: list[NormalizedRequirementSchema],
    ) -> list[NormalizedRequirementSchema]:
        """Normalize a batch of requirements."""
        return [self.normalize(req) for req in requirements]

    def _normalize_text(self, text: str) -> str:
        """Normalize requirement text to canonical form."""
        if not text:
            return ""

        normalized = text.lower().strip()

        # Remove excessive whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Normalize common abbreviations
        normalized = re.sub(r"\bis\b", "IS", normalized)  # Indian Standard
        normalized = re.sub(r"\bbis\b", "BIS", normalized)

        # Normalize operators in text
        normalized = normalized.replace("shall be at least", ">=")
        normalized = normalized.replace("shall not exceed", "<=")
        normalized = normalized.replace("minimum", ">=")
        normalized = normalized.replace("maximum", "<=")
        normalized = normalized.replace("not less than", ">=")
        normalized = normalized.replace("not more than", "<=")
        normalized = normalized.replace("at least", ">=")
        normalized = normalized.replace("up to", "<=")

        return normalized

    def _normalize_parameters(self, params: dict) -> dict:
        """Normalize parameter names, values, and units."""
        normalized = {}
        for key, value in params.items():
            norm_key = key.lower().strip().replace(" ", "_")

            if isinstance(value, dict):
                norm_value = dict(value)
                # Normalize unit
                if "unit" in norm_value and norm_value["unit"]:
                    unit = str(norm_value["unit"]).lower().strip()
                    norm_value["unit"] = self.UNIT_ALIASES.get(unit, norm_value["unit"])
                # Ensure value is numeric where possible
                if "value" in norm_value:
                    try:
                        norm_value["value"] = float(norm_value["value"])
                    except (ValueError, TypeError):
                        pass
                normalized[norm_key] = norm_value
            else:
                normalized[norm_key] = {"value": value}

        return normalized


# Singleton
requirement_normalizer = RequirementNormalizer()
