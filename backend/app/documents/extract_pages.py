"""Page text extraction from PDF using PyMuPDF."""

from typing import Any

import pymupdf as fitz

from app.core.config import get_settings
from app.core.errors import AppError, PayloadTooLargeError


def extract_pages_from_pdf(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extract 1-indexed page text from PDF bytes.
    Returns list of dicts: {"page": int, "text": str}.
    """
    settings = get_settings()

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise AppError("PDF_PARSE_FAILED", f"Could not parse PDF content: {exc}")

    try:
        page_count = doc.page_count
        if page_count > settings.MAX_PDF_PAGES:
            raise PayloadTooLargeError(
                f"PDF exceeds page limit ({page_count} pages > max {settings.MAX_PDF_PAGES})."
            )

        pages: list[dict[str, Any]] = []
        for idx in range(page_count):
            page_obj = doc.load_page(idx)
            text = page_obj.get_text("text")
            pages.append(
                {
                    "page": idx + 1,  # 1-indexed physical page
                    "text": text,
                }
            )

        return pages
    finally:
        doc.close()
