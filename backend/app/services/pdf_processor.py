"""
Procura — PDF Processor

Handles digital, scanned, and mixed PDFs with intelligent OCR fallback.
Processes page-by-page for memory efficiency.
"""

import io
import logging
from typing import Optional
from dataclasses import dataclass, field

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # PyMuPDF fallback

from app.core.config import settings

logger = logging.getLogger("procura.pdf_processor")


@dataclass
class PageResult:
    """Result of processing a single PDF page."""
    page_number: int
    text: str
    is_scanned: bool
    ocr_used: bool
    metadata: dict = field(default_factory=dict)


@dataclass
class PDFProcessingResult:
    """Complete result of processing a PDF."""
    pages: list[PageResult]
    total_pages: int
    extraction_method: str  # "digital", "ocr", "mixed"
    full_text: str = ""
    error: Optional[str] = None


class PDFProcessor:
    """
    Intelligent PDF processor that:
    1. Detects whether each page is digital or scanned
    2. Uses native text extraction for digital pages
    3. Falls back to OCR only for scanned pages
    4. Preserves page numbers and structure
    """

    def __init__(self):
        self.min_text_length = settings.MIN_TEXT_LENGTH_FOR_DIGITAL
        self.max_pages = settings.MAX_PDF_PAGES
        self.ocr_service = None  # Lazy-loaded

    async def process_pdf(self, pdf_bytes: bytes) -> PDFProcessingResult:
        """Process a PDF file and extract text from all pages."""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            return PDFProcessingResult(
                pages=[], total_pages=0, extraction_method="error",
                error=f"Failed to open PDF: {str(e)}"
            )

        total_pages = len(doc)
        if total_pages > self.max_pages:
            logger.warning(f"PDF has {total_pages} pages, limiting to {self.max_pages}")
            total_pages = self.max_pages

        pages: list[PageResult] = []
        digital_count = 0
        ocr_count = 0

        for page_num in range(total_pages):
            try:
                page_result = await self._process_page(doc, page_num)
                pages.append(page_result)

                if page_result.ocr_used:
                    ocr_count += 1
                else:
                    digital_count += 1

            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {e}")
                pages.append(PageResult(
                    page_number=page_num + 1,
                    text=f"[Error extracting page {page_num + 1}]",
                    is_scanned=False,
                    ocr_used=False,
                    metadata={"error": str(e)}
                ))

        doc.close()

        # Determine overall extraction method
        if ocr_count == 0:
            method = "digital"
        elif digital_count == 0:
            method = "ocr"
        else:
            method = "mixed"

        # Build full text with page markers
        full_text_parts = []
        for page in pages:
            full_text_parts.append(f"\n--- PAGE {page.page_number} ---\n")
            full_text_parts.append(page.text)

        return PDFProcessingResult(
            pages=pages,
            total_pages=total_pages,
            extraction_method=method,
            full_text="\n".join(full_text_parts),
        )

    async def _process_page(self, doc: fitz.Document, page_idx: int) -> PageResult:
        """Process a single page: try digital extraction first, fall back to OCR."""
        page = doc[page_idx]
        page_number = page_idx + 1

        # Try native text extraction first
        text = page.get_text("text").strip()

        # Check if we got useful text
        clean_text = text.replace("[No selectable text found]", "").strip()
        has_useful_text = len(clean_text) >= self.min_text_length

        if has_useful_text:
            return PageResult(
                page_number=page_number,
                text=text,
                is_scanned=False,
                ocr_used=False,
                metadata={"char_count": len(text)}
            )

        # Fall back to OCR for scanned pages
        logger.info(f"Page {page_number}: insufficient text ({len(clean_text)} chars), attempting OCR")
        try:
            ocr_text = await self._ocr_page(page)
            return PageResult(
                page_number=page_number,
                text=ocr_text if ocr_text else "[No text could be extracted]",
                is_scanned=True,
                ocr_used=True,
                metadata={"char_count": len(ocr_text) if ocr_text else 0}
            )
        except Exception as e:
            logger.warning(f"OCR failed for page {page_number}: {e}")
            return PageResult(
                page_number=page_number,
                text=text if text else "[OCR failed — no text extracted]",
                is_scanned=True,
                ocr_used=False,
                metadata={"ocr_error": str(e)}
            )

    async def _ocr_page(self, page: fitz.Page) -> str:
        """Render page and perform OCR using Tesseract."""
        from app.services.ocr_service import OCRService

        if self.ocr_service is None:
            self.ocr_service = OCRService()

        return self.ocr_service.ocr_page(page)


# Singleton
pdf_processor = PDFProcessor()
