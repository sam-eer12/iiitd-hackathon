"""Unit tests for condition difference and amendment diffs."""

from app.domain.condition_diff import diff_conditions


def test_condition_diff_classifications():
    old_conditions = [
        {"clause": "3.1", "requirement": "Annual turnover ₹35 Lakh", "threshold": 3500000},
        {"clause": "1.1", "requirement": "Deadline 01-11-2026", "deadline": "2026-11-01T15:00:00Z"},
        {"clause": "5.1", "requirement": "Old clause to be removed"},
    ]

    new_conditions = [
        {
            "clause": "3.1",
            "requirement": "Annual turnover ₹35 Lakh",
            "threshold": 3500000,
        },  # Unchanged
        {
            "clause": "1.1",
            "requirement": "Extended deadline 15-11-2026",
            "deadline": "2026-11-15T15:00:00Z",
        },  # Modified
        {"clause": "6.1", "requirement": "Newly added clause", "threshold": 100000},  # Added
    ]

    diffs = diff_conditions(old_conditions, new_conditions)
    diff_map = {d["clause_identity"]: d for d in diffs}

    assert diff_map["3.1"]["change_type"] == "unchanged"
    assert not diff_map["3.1"]["material_change"]

    assert diff_map["1.1"]["change_type"] == "modified"
    assert diff_map["1.1"]["material_change"]

    assert diff_map["6.1"]["change_type"] == "added"
    assert diff_map["6.1"]["material_change"]

    assert diff_map["5.1"]["change_type"] == "removed"
    assert diff_map["5.1"]["material_change"]
