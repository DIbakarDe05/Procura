"""
Procura — Document Structure Analyzer

Detects sections in PDFs and classifies them by type and priority.
Technical specification sections get HIGH priority.
Administrative sections get LOW priority.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("procura.document_structure")


# Section patterns and their classifications
SECTION_PATTERNS = {
    "technical_specification": {
        "patterns": [
            r"technical\s+specification",
            r"technical\s+requirements?",
            r"technical\s+details?",
            r"product\s+specification",
            r"detailed\s+specification",
            r"specification\s+of\s+(?:the\s+)?(?:product|equipment|material)",
        ],
        "priority": "high",
    },
    "scope_of_supply": {
        "patterns": [
            r"scope\s+of\s+(?:supply|work)",
            r"bill\s+of\s+(?:quantity|quantities|materials?)",
            r"schedule\s+of\s+(?:requirement|supply)",
        ],
        "priority": "high",
    },
    "performance_requirements": {
        "patterns": [
            r"performance\s+requirements?",
            r"performance\s+specification",
            r"functional\s+requirements?",
            r"operational\s+requirements?",
        ],
        "priority": "high",
    },
    "material_requirements": {
        "patterns": [
            r"material\s+requirements?",
            r"material\s+specification",
            r"raw\s+materials?",
            r"material\s+of\s+construction",
        ],
        "priority": "high",
    },
    "testing_requirements": {
        "patterns": [
            r"test(?:ing)?\s+requirements?",
            r"inspection\s+(?:and\s+)?test",
            r"quality\s+(?:assurance|control)\s+test",
            r"type\s+test",
            r"acceptance\s+test",
            r"routine\s+test",
        ],
        "priority": "high",
    },
    "safety_requirements": {
        "patterns": [
            r"safety\s+requirements?",
            r"safety\s+provisions?",
            r"safety\s+standards?",
            r"health\s+(?:and\s+)?safety",
        ],
        "priority": "high",
    },
    "quality_requirements": {
        "patterns": [
            r"quality\s+requirements?",
            r"quality\s+(?:assurance|control)",
            r"quality\s+standards?",
        ],
        "priority": "high",
    },
    "inspection_requirements": {
        "patterns": [
            r"inspection\s+requirements?",
            r"inspection\s+(?:and\s+)?acceptance",
            r"stage\s+inspection",
        ],
        "priority": "high",
    },
    "standards_codes": {
        "patterns": [
            r"applicable\s+standards?",
            r"relevant\s+standards?",
            r"standards?\s+(?:and\s+)?codes?",
            r"indian\s+standards?",
            r"bis\s+standards?",
            r"reference\s+standards?",
        ],
        "priority": "high",
    },
    "administrative": {
        "patterns": [
            r"tender\s+conditions?",
            r"general\s+conditions?",
            r"terms?\s+(?:and|&)\s+conditions?",
            r"instructions?\s+to\s+(?:bidders?|tenderers?)",
            r"eligibility\s+criteria",
            r"pre-?qualification",
        ],
        "priority": "low",
    },
    "commercial": {
        "patterns": [
            r"commercial\s+(?:terms?|conditions?)",
            r"payment\s+(?:terms?|conditions?|schedule)",
            r"price\s+schedule",
            r"bid\s+(?:security|bond)",
            r"earnest\s+money",
            r"liquidated\s+damages?",
            r"warranty\s+(?:terms?|conditions?|period)",
            r"delivery\s+(?:schedule|period|terms?)",
        ],
        "priority": "low",
    },
    "legal": {
        "patterns": [
            r"legal\s+(?:provisions?|requirements?)",
            r"dispute\s+resolution",
            r"arbitration",
            r"force\s+majeure",
            r"indemnity",
            r"jurisdiction",
            r"declaration",
        ],
        "priority": "low",
    },
}


@dataclass
class DetectedSection:
    """A detected section in the document."""
    title: str
    section_type: str
    priority: str
    page_start: int
    page_end: int
    content: str


class DocumentStructureAnalyzer:
    """Analyzes document structure and classifies sections by priority."""

    def __init__(self):
        # Compile patterns for efficiency
        self.compiled_patterns = {}
        for section_type, config in SECTION_PATTERNS.items():
            self.compiled_patterns[section_type] = {
                "patterns": [re.compile(p, re.IGNORECASE) for p in config["patterns"]],
                "priority": config["priority"],
            }

    def detect_sections(
        self, pages: list[dict],
    ) -> list[DetectedSection]:
        """
        Detect and classify sections from page-level text.

        Args:
            pages: List of dicts with 'page_number' and 'text' keys

        Returns:
            List of detected sections with classifications
        """
        if not pages:
            return []

        # Strategy: look for heading-like lines and classify them
        sections: list[DetectedSection] = []
        current_section: Optional[dict] = None
        current_content_lines: list[str] = []

        for page in pages:
            page_num = page.get("page_number", 0)
            text = page.get("text", "")
            lines = text.split("\n")

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue

                # Check if this line looks like a section heading
                section_type, priority = self._classify_line(stripped)

                if section_type and self._looks_like_heading(stripped):
                    # Check if this is just a repeated running header on a new page
                    if current_section:
                        is_same_title = current_section["title"].strip().lower() == stripped.lower()
                        is_same_type_continuation = (
                            current_section["type"] == section_type and 
                            len(current_content_lines) < 30
                        )
                        if is_same_title or is_same_type_continuation:
                            # Skip repeated header, continue accumulating in current section
                            continue

                        # Save previous section if it has meaningful content
                        content_str = "\n".join(current_content_lines).strip()
                        if content_str or len(sections) == 0:
                            sections.append(DetectedSection(
                                title=current_section["title"],
                                section_type=current_section["type"],
                                priority=current_section["priority"],
                                page_start=current_section["page_start"],
                                page_end=page_num,
                                content=content_str,
                            ))

                    # Start new section
                    current_section = {
                        "title": stripped,
                        "type": section_type,
                        "priority": priority,
                        "page_start": page_num,
                    }
                    current_content_lines = []
                else:
                    current_content_lines.append(stripped)

        # Don't forget the last section
        if current_section:
            last_page = pages[-1].get("page_number", 0) if pages else 0
            content_str = "\n".join(current_content_lines).strip()
            sections.append(DetectedSection(
                title=current_section["title"],
                section_type=current_section["type"],
                priority=current_section["priority"],
                page_start=current_section["page_start"],
                page_end=last_page,
                content=content_str,
            ))

        # If no sections detected, treat entire document as one section
        if not sections:
            all_text = "\n".join(p.get("text", "") for p in pages)
            sections.append(DetectedSection(
                title="Full Document",
                section_type="general",
                priority="medium",
                page_start=1,
                page_end=len(pages),
                content=all_text,
            ))

        # Cap sections to reasonable limit (max 30)
        if len(sections) > 30:
            # Keep highest priority sections first, then order by page
            high_prio = [s for s in sections if s.priority == "high"]
            other_prio = [s for s in sections if s.priority != "high"]
            sections = (high_prio + other_prio)[:30]
            sections.sort(key=lambda s: s.page_start)

        return sections

    def _classify_line(self, line: str) -> tuple[Optional[str], str]:
        """Classify a line against known section patterns."""
        for section_type, config in self.compiled_patterns.items():
            for pattern in config["patterns"]:
                if pattern.search(line):
                    return section_type, config["priority"]
        return None, "medium"

    def _looks_like_heading(self, line: str) -> bool:
        """Heuristic: does this line look like a section heading?"""
        # Short lines are more likely headings
        if len(line) > 200:
            return False
        # Lines that are mostly uppercase
        if line.isupper() and len(line) > 3:
            return True
        # Lines starting with numbers (e.g., "1. Technical Specifications")
        if re.match(r"^\d+[\.\)]\s+", line):
            return True
        # Lines with heading-like formatting
        if re.match(r"^(?:section|part|chapter|schedule|annexure|appendix)\s+", line, re.IGNORECASE):
            return True
        # Short lines that match a pattern are likely headings
        if len(line) < 80:
            return True
        return False

    def get_high_priority_content(self, sections: list[DetectedSection]) -> str:
        """Get concatenated content from high-priority technical sections."""
        high_priority = [s for s in sections if s.priority == "high"]
        if not high_priority:
            # Fall back to all content
            return "\n\n".join(s.content for s in sections)
        return "\n\n".join(
            f"[Section: {s.title}]\n{s.content}" for s in high_priority
        )


# Singleton
document_analyzer = DocumentStructureAnalyzer()
