"""Normalizers for monetary amounts, financial periods, and date strings."""

import re
from datetime import UTC, datetime, timezone
from decimal import Decimal

# Matches e.g. "35 lakh", "1.5 crore", "₹ 50,000", "50000"
AMOUNT_PATTERN = re.compile(
    r"(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?)\s*(lakhs?|lacs?|crores?|cr|k)?",
    re.IGNORECASE,
)

# Matches financial years like 2023-24, 2023–24, 2024-2025
FY_PATTERN = re.compile(r"\b(20\d{2})[-–/](20\d{2}|\d{2})\b")


def normalize_inr_amount(text: str) -> Decimal | None:
    """Normalize Indian currency text to Decimal amount."""
    if not text:
        return None

    cleaned = text.replace(",", "").strip()
    match = AMOUNT_PATTERN.search(cleaned)
    if not match:
        return None

    num_str, multiplier = match.groups()
    try:
        val = Decimal(num_str)
    except Exception:
        return None

    if multiplier:
        m = multiplier.lower()
        if "lakh" in m or "lac" in m:
            val *= Decimal(100000)
        elif "crore" in m or "cr" in m:
            val *= Decimal(10000000)
        elif m == "k":
            val *= Decimal(1000)

    return val


def normalize_financial_years(text: str) -> list[str]:
    """Extract and standardize financial years to 'YYYY–YY' format."""
    matches = FY_PATTERN.findall(text)
    years: list[str] = []
    for start_year, end_year in matches:
        if len(end_year) == 4:
            end_short = end_year[2:]
        else:
            end_short = end_year
        years.append(f"{start_year}–{end_short}")
    return years


def normalize_iso_timestamp(text: str) -> str | None:
    """Attempt to parse date text into ISO-8601 string with timezone."""
    if not text:
        return None

    text = text.strip()
    # Check if already ISO
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.isoformat()
    except Exception:
        pass

    # Common Indian date formats: DD/MM/YYYY HH:MM or DD-MM-YYYY
    date_formats = [
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y",
        "%d-%m-%Y",
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(text, fmt)
            # Default to IST (+05:30) if timezone is unspecified
            dt = dt.replace(
                tzinfo=timezone(datetime.now().astimezone().utcoffset() or UTC.utcoffset(None))
            )
            return dt.isoformat()
        except ValueError:
            continue

    return None
