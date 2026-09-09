"""
Procura — Quick OCR Smoke Test

Run:  python scripts/test_ocr.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

from app.services.ocr_service import OCRService


def main():
    print("=" * 60)
    print("  PROCURA — Tesseract OCR Smoke Test")
    print("=" * 60)

    ocr = OCRService()

    # 1) Check pytesseract import
    status = "YES" if ocr.available else "NO"
    print(f"\n[1] pytesseract imported:     {status}")

    # 2) Check tesseract binary
    available = ocr.is_available()
    status = "YES" if available else "NO"
    print(f"[2] Tesseract binary found:   {status}")

    if available:
        ver = ocr.pytesseract.get_tesseract_version()
        cmd = ocr.pytesseract.pytesseract.tesseract_cmd
        print(f"[3] Tesseract version:        {ver}")
        print(f"[4] Tesseract binary path:    {cmd}")

        # 3) Quick OCR on a synthetic image
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (400, 100), color="white")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except OSError:
            font = ImageFont.load_default()
        draw.text((20, 30), "IS 456:2000 Concrete", fill="black", font=font)

        text = ocr.pytesseract.image_to_string(img).strip()
        print(f"[5] OCR test image result:    \"{text}\"")
        passed = "PASS" if text else "FAIL"
        print(f"[6] OCR working:              {passed}")
    else:
        print("\n[FAIL] Tesseract is NOT installed or not on PATH.")
        print("   Install from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Or on Windows: winget install UB-Mannheim.TesseractOCR")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
