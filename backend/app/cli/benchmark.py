"""Ten-notice evaluation benchmark verifying extraction, citation coverage, and missing-evidence safety."""

import sys
from datetime import UTC, datetime

from app.documents.extract_clauses import extract_clauses_from_pages, verify_quote_on_page
from app.domain.readiness import evaluate_condition

BENCHMARK_CORPUS = [
    {
        "id": f"notice_{i + 1:02d}",
        "title": f"Tender Notice {i + 1}: Procurement and Works",
        "page_texts": [
            {
                "page": 1,
                "text": "IIIT-DELHI TENDER NOTICE. Submission deadline: 15-11-2026 15:00 IST. Technical bid submission.",
            },
            {
                "page": 2,
                "text": "Eligibility criteria: The bidder must have an average annual turnover of at least ₹25 Lakh in 2023–24, 2024–25, and 2025–26.",
            },
            {
                "page": 3,
                "text": "Experience: Bidder must have executed at least 2 completed orders of similar nature in past 3 years.",
            },
            {
                "page": 4,
                "text": "Certificates: Valid GST registration certificate is mandatory for all participating bidders.",
            },
            {
                "page": 5,
                "text": "Bid Security: Earnest Money Deposit (EMD) of ₹20,000 to be paid via RTGS/NEFT.",
            },
        ],
    }
    for i in range(10)
]


def run_benchmark() -> int:
    print("=" * 60)
    print(" TenderLens: Ten-Notice Extraction & Safety Benchmark")
    print("=" * 60)

    total_notices = len(BENCHMARK_CORPUS)
    extracted_clauses_total = 0
    correct_page_linkage_count = 0
    silent_meets_without_evidence_count = 0

    dummy_profile = {
        "company": "Benchmark Corp",
        "turnover": [
            {"year": "2023–24", "amount": 3000000},
            {"year": "2024–25", "amount": 3000000},
            {"year": "2025–26", "amount": 3000000},
        ],
        "completedOrders": 5,
        "depositCapacity": 100000,
        "certificates": {"gst": True, "iso": True, "manufacturer": True},
    }
    now = datetime(2026, 10, 24, 9, 0, 0, tzinfo=UTC)

    for notice in BENCHMARK_CORPUS:
        pages = notice["page_texts"]
        clauses = extract_clauses_from_pages(pages)
        extracted_clauses_total += len(clauses)

        for clause in clauses:
            page_num = clause["page"]
            page_obj = next((p for p in pages if p["page"] == page_num), None)
            if page_obj and verify_quote_on_page(clause["quote"], page_obj["text"]):
                correct_page_linkage_count += 1

        # Test safety: condition with missing quote MUST NOT pass
        safety_cond = {
            "type": "turnover",
            "label": "Turnover",
            "requirement": "Turnover requirement",
            "quote": "",  # Missing quote
            "page": 2,
            "threshold": 1000,
            "years": ["2023–24"],
        }
        finding = evaluate_condition(safety_cond, dummy_profile, now)
        if finding["status"] == "meets":
            silent_meets_without_evidence_count += 1

    # Metrics
    linkage_rate = (
        (correct_page_linkage_count / extracted_clauses_total * 100.0)
        if extracted_clauses_total > 0
        else 0.0
    )
    expected_clauses = total_notices * 5
    extraction_rate = (extracted_clauses_total / expected_clauses) * 100.0

    print(f"Total Notices Evaluated       : {total_notices}")
    print(
        f"Extracted Conditions          : {extracted_clauses_total} / {expected_clauses} ({extraction_rate:.1f}%)"
    )
    print(f"Page/Quote Linkage Accuracy   : {linkage_rate:.1f}%")
    print(f"Silent Passes on Bad Evidence : {silent_meets_without_evidence_count}")
    print("-" * 60)

    passed_all = (
        extraction_rate >= 90.0
        and linkage_rate == 100.0
        and silent_meets_without_evidence_count == 0
    )

    if passed_all:
        print("[SUCCESS] All release benchmark targets achieved!")
        return 0
    else:
        print("[FAILED] Release benchmark gates failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run_benchmark())
