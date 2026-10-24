"""Unit tests for document processing, normalizers, and clause extraction."""

import pytest

from app.core.errors import AppError
from app.documents.downloader import validate_url_and_host
from app.documents.extract_clauses import extract_clauses_from_pages, verify_quote_on_page
from app.documents.hashing import compute_sha256
from app.documents.normalizers import (
    normalize_financial_years,
    normalize_inr_amount,
    normalize_iso_timestamp,
)


def test_sha256_hashing():
    data = b"TenderLens immutable test bytes"
    expected = "87d191d722d3baea5a09b66adc725a895cda466ad627111dd48e9dae691ad56a"
    assert compute_sha256(data) == expected


def test_downloader_security_rejections():
    # Reject HTTP
    with pytest.raises(AppError) as exc_http:
        validate_url_and_host("http://iiitd.ac.in/tenders/notice.pdf")
    assert "INVALID_URL_SCHEME" in exc_http.value.code

    # Reject unapproved host
    with pytest.raises(AppError) as exc_host:
        validate_url_and_host("https://malicious-domain.com/notice.pdf")
    assert "UNAPPROVED_HOST" in exc_host.value.code

    # Reject embedded credentials
    with pytest.raises(AppError) as exc_cred:
        validate_url_and_host("https://user:pass@iiitd.ac.in/notice.pdf")
    assert "EMBEDDED_CREDENTIALS" in exc_cred.value.code


def test_inr_normalizer():
    assert normalize_inr_amount("₹ 35 Lakh") == 3500000
    assert normalize_inr_amount("Rs. 1.5 Crore") == 15000000
    assert normalize_inr_amount("50,000") == 50000
    assert normalize_inr_amount("50k") == 50000
    assert normalize_inr_amount("no amount") is None


def test_financial_year_normalizer():
    years = normalize_financial_years("Turnover for 2023-24, 2024–25, and 2025/2026")
    assert "2023–24" in years
    assert "2024–25" in years
    assert "2025–26" in years


def test_iso_timestamp_normalizer():
    dt_iso = normalize_iso_timestamp("2026-11-06T15:00:00Z")
    assert dt_iso is not None
    assert "2026-11-06" in dt_iso

    dt_slash = normalize_iso_timestamp("06/11/2026 15:00")
    assert dt_slash is not None
    assert "2026-11-06" in dt_slash


def test_clause_extraction_and_quote_verification():
    pages = [
        {
            "page": 1,
            "text": "Tender Document. Submission deadline: 06-11-2026 15:00:00 IST.",
        },
        {
            "page": 2,
            "text": "The bidder must have an average annual turnover of at least ₹35 Lakh during 2023–24, 2024–25, and 2025–26.",
        },
    ]

    clauses = extract_clauses_from_pages(pages)
    assert len(clauses) >= 2

    turnover_clause = next(c for c in clauses if c["type"] == "turnover")
    assert turnover_clause["page"] == 2
    assert verify_quote_on_page(turnover_clause["quote"], pages[1]["text"])
    assert turnover_clause["threshold"] == 3500000.0
