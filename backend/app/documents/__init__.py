"""Documents ingestion, extraction, and hashing package."""

from app.documents.downloader import download_document, validate_url_and_host
from app.documents.extract_clauses import extract_clauses_from_pages, verify_quote_on_page
from app.documents.extract_pages import extract_pages_from_pdf
from app.documents.hashing import compute_sha256
from app.documents.normalizers import (
    normalize_financial_years,
    normalize_inr_amount,
    normalize_iso_timestamp,
)

__all__ = [
    "compute_sha256",
    "download_document",
    "extract_clauses_from_pages",
    "extract_pages_from_pdf",
    "normalize_financial_years",
    "normalize_inr_amount",
    "normalize_iso_timestamp",
    "validate_url_and_host",
    "verify_quote_on_page",
]
