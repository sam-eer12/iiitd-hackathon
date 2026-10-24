"""Clause extraction and physical page quote verification."""

import re
from typing import Any

from app.documents.normalizers import (
    normalize_financial_years,
    normalize_inr_amount,
    normalize_iso_timestamp,
)


def verify_quote_on_page(quote: str, page_text: str) -> bool:
    """Validate that the exact quoted span actually occurs on the cited document page."""
    if not quote or not page_text:
        return False
    # Normalize whitespaces for comparison
    clean_quote = " ".join(quote.split())
    clean_page = " ".join(page_text.split())
    return clean_quote.lower() in clean_page.lower()


def extract_clauses_from_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scan extracted page texts and produce validated condition candidates.
    Every published condition is guaranteed to have its quote physically present on its page.
    """
    conditions: list[dict[str, Any]] = []

    for page_item in pages:
        page_num = page_item["page"]
        text = page_item["text"]
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # 1. Turnover candidate
            if "turnover" in line_lower and any(
                kw in line_lower for kw in ["average", "annual", "minimum", "lakh", "crore", "rs"]
            ):
                years = normalize_financial_years(line)
                threshold = normalize_inr_amount(line)
                # Formulate quote (1-2 lines)
                quote = line
                if i + 1 < len(lines) and len(quote) < 80:
                    quote += " " + lines[i + 1]

                if verify_quote_on_page(quote, text):
                    conditions.append(
                        {
                            "type": "turnover",
                            "label": "Annual Turnover",
                            "requirement": line,
                            "clause": f"Clause P{page_num}.{i + 1}",
                            "page": page_num,
                            "quote": quote,
                            "threshold": float(threshold) if threshold else None,
                            "years": years if years else None,
                            "mandatory": True,
                        }
                    )

            # 2. Experience candidate
            elif any(
                kw in line_lower
                for kw in ["experience", "completed work", "similar work", "past performance"]
            ):
                # Look for numbers of orders
                order_match = re.search(
                    r"(\d+)\s*(?:completed\s*)?(?:orders?|contracts?|works?)", line_lower
                )
                threshold_val = float(order_match.group(1)) if order_match else None
                quote = line
                if verify_quote_on_page(quote, text):
                    conditions.append(
                        {
                            "type": "experience",
                            "label": "Work Experience",
                            "requirement": line,
                            "clause": f"Clause P{page_num}.{i + 1}",
                            "page": page_num,
                            "quote": quote,
                            "threshold": threshold_val,
                            "mandatory": True,
                        }
                    )

            # 3. Certificate candidate
            elif any(kw in line_lower for kw in ["gst", "iso", "oem", "manufacturer"]):
                cert_type = None
                if "gst" in line_lower:
                    cert_type = "gst"
                elif "iso" in line_lower:
                    cert_type = "iso"
                elif "oem" in line_lower or "manufacturer" in line_lower:
                    cert_type = "manufacturer"

                quote = line
                if verify_quote_on_page(quote, text):
                    conditions.append(
                        {
                            "type": "certificate",
                            "label": f"Certificate ({cert_type.upper() if cert_type else 'General'})",
                            "requirement": line,
                            "clause": f"Clause P{page_num}.{i + 1}",
                            "page": page_num,
                            "quote": quote,
                            "certificate": cert_type,
                            "mandatory": True,
                        }
                    )

            # 4. Deposit / EMD candidate
            elif any(kw in line_lower for kw in ["emd", "earnest money", "bid security"]):
                threshold = normalize_inr_amount(line)
                quote = line
                if verify_quote_on_page(quote, text):
                    conditions.append(
                        {
                            "type": "deposit",
                            "label": "Earnest Money Deposit (EMD)",
                            "requirement": line,
                            "clause": f"Clause P{page_num}.{i + 1}",
                            "page": page_num,
                            "quote": quote,
                            "threshold": float(threshold) if threshold else None,
                            "mandatory": True,
                        }
                    )

            # 5. Deadline candidate
            elif any(
                kw in line_lower
                for kw in [
                    "submission deadline",
                    "due date",
                    "closing date",
                    "last date of submission",
                ]
            ):
                quote = line
                iso_dt = normalize_iso_timestamp(line)
                if verify_quote_on_page(quote, text):
                    conditions.append(
                        {
                            "type": "deadline",
                            "label": "Submission Deadline",
                            "requirement": line,
                            "clause": f"Clause P{page_num}.{i + 1}",
                            "page": page_num,
                            "quote": quote,
                            "deadline": iso_dt,
                            "mandatory": True,
                        }
                    )

    return conditions
