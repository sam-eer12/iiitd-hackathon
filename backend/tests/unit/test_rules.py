"""Unit tests for deterministic readiness rules matching golden cases."""

from datetime import UTC, datetime

from app.domain.readiness import evaluate_condition, evaluate_tender

PROFILE = {
    "company": "Test Supplier",
    "contact": "Test",
    "email": "test@example.com",
    "categories": ["Electronics"],
    "turnover": [
        {"year": "2023–24", "amount": 3000000},
        {"year": "2024–25", "amount": 3500000},
        {"year": "2025–26", "amount": 4000000},
    ],
    "completedOrders": 3,
    "depositCapacity": 50000,
    "certificates": {"gst": True, "iso": False, "manufacturer": None},
}

EVAL_CLOCK = datetime(2026, 10, 24, 9, 0, 0, tzinfo=UTC)
EVIDENCE = {
    "quote": "An explicitly evidenced sample requirement.",
    "page": 4,
    "clause": "3.2",
}

TURNOVER_COND = {
    **EVIDENCE,
    "type": "turnover",
    "label": "Turnover",
    "requirement": "Average at least 35 lakh",
    "years": ["2023–24", "2024–25", "2025–26"],
    "threshold": 3500000,
}


def test_turnover_at_threshold():
    finding = evaluate_condition(TURNOVER_COND, PROFILE, EVAL_CLOCK)
    assert finding["status"] == "meets"


def test_turnover_missing_year():
    profile_missing_year = {
        **PROFILE,
        "turnover": PROFILE["turnover"][1:],  # Drop 2023-24
    }
    finding = evaluate_condition(TURNOVER_COND, profile_missing_year, EVAL_CLOCK)
    assert finding["status"] == "review"
    assert "Add turnover for every requested financial year" in finding["reason"]


def test_zero_deposit_blocks_positive_threshold():
    cond = {
        **EVIDENCE,
        "type": "deposit",
        "label": "EMD",
        "requirement": "₹1",
        "threshold": 1,
    }
    profile_zero_deposit = {**PROFILE, "depositCapacity": 0}
    finding = evaluate_condition(cond, profile_zero_deposit, EVAL_CLOCK)
    assert finding["status"] == "blocked"


def test_unknown_and_absent_certificates():
    cond_unknown = {
        **EVIDENCE,
        "type": "certificate",
        "label": "OEM",
        "requirement": "OEM",
        "certificate": "manufacturer",
    }
    finding_unknown = evaluate_condition(cond_unknown, PROFILE, EVAL_CLOCK)
    assert finding_unknown["status"] == "review"
    assert "Unknown does not count as a pass" in finding_unknown["reason"]

    cond_absent = {
        **EVIDENCE,
        "type": "certificate",
        "label": "ISO",
        "requirement": "ISO",
        "certificate": "iso",
    }
    finding_absent = evaluate_condition(cond_absent, PROFILE, EVAL_CLOCK)
    assert finding_absent["status"] == "blocked"
    assert "confirmed absent" in finding_absent["supplier_value"].lower()


def test_missing_evidence_prevents_pass():
    cond_no_quote = {**TURNOVER_COND, "quote": ""}
    finding = evaluate_condition(cond_no_quote, PROFILE, EVAL_CLOCK)
    assert finding["status"] == "review"
    assert "needs a source clause" in finding["reason"]

    cond_invalid_page = {**TURNOVER_COND, "page": 0}
    finding_page = evaluate_condition(cond_invalid_page, PROFILE, EVAL_CLOCK)
    assert finding_page["status"] == "review"


def test_passed_deadline_blocks_including_equality():
    cond_equality = {
        **EVIDENCE,
        "type": "deadline",
        "label": "Deadline",
        "requirement": "Now",
        "deadline": EVAL_CLOCK.isoformat(),
    }
    finding = evaluate_condition(cond_equality, PROFILE, EVAL_CLOCK)
    assert finding["status"] == "blocked"


def test_date_only_deadline_stays_unresolved():
    cond_date_only = {
        **EVIDENCE,
        "type": "deadline",
        "label": "Deadline",
        "requirement": "Date only",
        "deadline": "2026-11-01",  # No time or timezone
    }
    finding = evaluate_condition(cond_date_only, PROFILE, EVAL_CLOCK)
    assert finding["status"] == "review"
    assert "needs an exact time and timezone" in finding["reason"]


def test_incomplete_clause_coverage_cannot_pass():
    result_empty = evaluate_tender([], PROFILE, EVAL_CLOCK)
    assert result_empty["status"] == "review"
    assert not result_empty["coverage_complete"]

    result_one = evaluate_tender([TURNOVER_COND], PROFILE, EVAL_CLOCK)
    assert result_one["status"] == "review"
    assert not result_one["coverage_complete"]


def test_confirmed_blocker_precedence_preserves_unresolved():
    cond_blocker = {**TURNOVER_COND, "threshold": 5000000}  # Required 50L > average 35L
    cond_unknown_cert = {
        **EVIDENCE,
        "type": "certificate",
        "label": "OEM",
        "requirement": "OEM",
        "certificate": "manufacturer",
    }
    result = evaluate_tender([cond_blocker, cond_unknown_cert], PROFILE, EVAL_CLOCK)
    assert result["status"] == "blocked"
    # First is blocker, second stays unresolved 'review'
    assert result["findings"][0]["status"] == "blocked"
    assert result["findings"][1]["status"] == "review"


def test_all_five_evidenced_checks_pass_for_aggregate_meets():
    conditions = [
        TURNOVER_COND,
        {
            **EVIDENCE,
            "type": "experience",
            "label": "Experience",
            "requirement": "3 orders",
            "threshold": 3,
        },
        {
            **EVIDENCE,
            "type": "certificate",
            "label": "GST",
            "requirement": "GST",
            "certificate": "gst",
        },
        {
            **EVIDENCE,
            "type": "deposit",
            "label": "EMD",
            "requirement": "₹50,000",
            "threshold": 50000,
        },
        {
            **EVIDENCE,
            "type": "deadline",
            "label": "Deadline",
            "requirement": "Later",
            "deadline": "2026-11-06T15:00:00+05:30",
        },
    ]
    result = evaluate_tender(
        conditions, PROFILE, EVAL_CLOCK, verified_certificates=frozenset({"gst"})
    )
    assert result["status"] == "meets"
    assert result["coverage_complete"] is True
