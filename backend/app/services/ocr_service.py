"""
Procura — OCR Service

Tesseract OCR wrapper for scanned PDF pages.
"""

import logging
from io import BytesIO

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # PyMuPDF fallback
from PIL import Image

from app.core.config import settings

logger = logging.getLogger("procura.ocr_service")


class OCRService:
    """OCR service using Tesseract via pytesseract."""

    def __init__(self):
        self.scale_factor = settings.OCR_SCALE_FACTOR

        # Configure tesseract path if specified
        try:
            import pytesseract
            if settings.TESSERACT_CMD != "tesseract":
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            self.pytesseract = pytesseract
            self.available = True
        except ImportError:
            logger.warning("pytesseract not installed — OCR will be unavailable")
            self.available = False

    def ocr_page(self, page: fitz.Page) -> str:
        """
        Render a PDF page at high resolution and extract text via OCR.

        Args:
            page: PyMuPDF page object

        Returns:
            Extracted text string
        """
        if not self.available:
            raise RuntimeError("Tesseract OCR is not available")

        # Render page at higher resolution for better OCR
        matrix = fitz.Matrix(self.scale_factor, self.scale_factor)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        # Convert pixmap to PIL Image
        img_data = pixmap.samples
        img = Image.frombytes(
            "RGB",
            (pixmap.width, pixmap.height),
            img_data,
        )

        # Run OCR
        text = self.pytesseract.image_to_string(img)

        logger.debug(f"OCR extracted {len(text)} chars from page")
        return text.strip()

    def is_available(self) -> bool:
        """Check if Tesseract is installed and accessible."""
        if not self.available:
            return False
        try:
            self.pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
