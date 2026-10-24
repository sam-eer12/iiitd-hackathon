"""Condition and clause difference analysis for amendments."""

from typing import Any


def diff_conditions(
    old_conditions: list[dict[str, Any]],
    new_conditions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare two sets of conditions and compute before/after diffs."""
    old_map = {
        c.get("clause") or c.get("clause_reference") or c.get("type"): c for c in old_conditions
    }
    new_map = {
        c.get("clause") or c.get("clause_reference") or c.get("type"): c for c in new_conditions
    }

    changes: list[dict[str, Any]] = []

    # Check additions and modifications
    for clause_id, new_cond in new_map.items():
        if clause_id not in old_map:
            changes.append(
                {
                    "clause_identity": str(clause_id),
                    "change_type": "added",
                    "before_text": None,
                    "after_text": new_cond.get("requirement", ""),
                    "material_change": True,
                }
            )
        else:
            old_cond = old_map[clause_id]
            is_same = (
                old_cond.get("requirement") == new_cond.get("requirement")
                and old_cond.get("threshold") == new_cond.get("threshold")
                and old_cond.get("deadline") == new_cond.get("deadline")
                and old_cond.get("certificate") == new_cond.get("certificate")
            )
            if is_same:
                changes.append(
                    {
                        "clause_identity": str(clause_id),
                        "change_type": "unchanged",
                        "before_text": old_cond.get("requirement", ""),
                        "after_text": new_cond.get("requirement", ""),
                        "material_change": False,
                    }
                )
            else:
                changes.append(
                    {
                        "clause_identity": str(clause_id),
                        "change_type": "modified",
                        "before_text": old_cond.get("requirement", ""),
                        "after_text": new_cond.get("requirement", ""),
                        "material_change": True,
                    }
                )

    # Check removals
    for clause_id, old_cond in old_map.items():
        if clause_id not in new_map:
            changes.append(
                {
                    "clause_identity": str(clause_id),
                    "change_type": "removed",
                    "before_text": old_cond.get("requirement", ""),
                    "after_text": None,
                    "material_change": True,
                }
            )

    return changes
