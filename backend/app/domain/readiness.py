"""Authoritative readiness evaluation engine and condition rules."""

import re
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

try:
    from zoneinfo import ZoneInfo

    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30))


def format_inr(amount: Decimal | float) -> str:
    """Format money as INR currency string."""
    val = int(amount) if float(amount).is_integer() else round(float(amount), 2)
    s = str(val)
    if "." in s:
        integer_part, dec_part = s.split(".")
    else:
        integer_part, dec_part = s, ""

    if len(integer_part) > 3:
        last3 = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        formatted_int = ",".join(groups) + "," + last3
    else:
        formatted_int = integer_part

    if dec_part:
        return f"₹{formatted_int}.{dec_part}"
    return f"₹{formatted_int}"


def evaluate_condition(
    condition: dict[str, Any],
    profile: dict[str, Any],
    now: datetime,
    verified_certificates: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Evaluate a single condition against a supplier profile at a given clock time.
    Returns a finding dict: {condition, status, reason, supplier_value}.
    """
    quote = condition.get("quote") or condition.get("exact_quote", "")
    page = condition.get("page") or condition.get("page_number", 0)

    # Missing evidence check
    if not quote or not isinstance(page, int) or page < 1:
        return {
            "condition": condition,
            "status": "review",
            "reason": "The requirement needs a source clause and a valid page reference.",
            "supplier_value": "Not provided",
        }

    cond_type = condition.get("type")

    # 1. Turnover rule
    if cond_type == "turnover":
        years = condition.get("years")
        threshold = condition.get("threshold") or condition.get("threshold_amount")

        if not years or threshold is None:
            return {
                "condition": condition,
                "status": "review",
                "reason": "The exact turnover period or required amount is unresolved.",
                "supplier_value": "Not provided",
            }

        profile_turnover = profile.get("turnover", [])
        turnover_map = {entry.get("year"): entry.get("amount") for entry in profile_turnover}

        amounts: list[float] = []
        for year in years:
            amt = turnover_map.get(year)
            if amt is None:
                return {
                    "condition": condition,
                    "status": "review",
                    "reason": "Add turnover for every requested financial year before comparing the average.",
                    "supplier_value": "Not provided",
                }
            try:
                amt_float = float(amt)
                if amt_float < 0:
                    return {
                        "condition": condition,
                        "status": "review",
                        "reason": "Add turnover for every requested financial year before comparing the average.",
                        "supplier_value": "Not provided",
                    }
                amounts.append(amt_float)
            except (ValueError, TypeError):
                return {
                    "condition": condition,
                    "status": "review",
                    "reason": "Add turnover for every requested financial year before comparing the average.",
                    "supplier_value": "Not provided",
                }

        avg = sum(amounts) / len(amounts)
        threshold_float = float(threshold)
        passed = avg >= threshold_float

        return {
            "condition": condition,
            "status": "meets" if passed else "blocked",
            "supplier_value": f"{format_inr(avg)} average",
            "reason": f"{', '.join(years)}: your average {'meets' if passed else 'is below'} the required {format_inr(threshold_float)}.",
        }

    # 2. Experience or Deposit rule
    if cond_type in ("experience", "deposit"):
        threshold = condition.get("threshold") or condition.get("threshold_amount")
        value = (
            profile.get("completedOrders")
            if cond_type == "experience"
            else profile.get("depositCapacity")
        )

        if value is None or threshold is None:
            return {
                "condition": condition,
                "status": "review",
                "reason": "Add a known supplier value and confirm the exact requirement.",
                "supplier_value": "Not provided",
            }

        try:
            val_float = float(value)
            threshold_float = float(threshold)
            if val_float < 0:
                return {
                    "condition": condition,
                    "status": "review",
                    "reason": "Add a known supplier value and confirm the exact requirement.",
                    "supplier_value": "Not provided",
                }
        except (ValueError, TypeError):
            return {
                "condition": condition,
                "status": "review",
                "reason": "Add a known supplier value and confirm the exact requirement.",
                "supplier_value": "Not provided",
            }

        passed = val_float >= threshold_float
        supplier_val = (
            format_inr(val_float)
            if cond_type == "deposit"
            else f"{int(val_float)} completed orders"
        )
        reason = (
            "Compares your stated available funds with the required EMD; this does not confirm payment."
            if cond_type == "deposit"
            else "Compares the declared count of completed supply orders in this sample category."
        )

        return {
            "condition": condition,
            "status": "meets" if passed else "blocked",
            "supplier_value": supplier_val,
            "reason": reason,
        }

    # 3. Certificate rule
    if cond_type == "certificate":
        cert_name = condition.get("certificate") or condition.get("certificate_type")
        if not cert_name:
            return {
                "condition": condition,
                "status": "review",
                "reason": "The certificate type is unresolved.",
                "supplier_value": "Not provided",
            }

        certs = profile.get("certificates", {})
        val = certs.get(cert_name)

        if val is None:
            return {
                "condition": condition,
                "status": "review",
                "reason": "Confirm whether you have this certificate. Unknown does not count as a pass.",
                "supplier_value": "Not provided",
            }

        is_present = bool(val)
        if is_present and cert_name not in verified_certificates:
            return {
                "condition": condition,
                "status": "review",
                "supplier_value": "Present · self-declared",
                "reason": "The certificate is self-declared. An issuer verification is required before this check can pass.",
            }
        return {
            "condition": condition,
            "status": "meets" if is_present else "blocked",
            "supplier_value": "Issuer verified" if is_present else "Confirmed absent",
            "reason": (
                "The certificate has a current issuer verification matching this supplier."
                if is_present
                else "Your profile confirms that the required certificate is absent."
            ),
        }

    # 4. Deadline rule
    if cond_type == "deadline":
        deadline_raw = condition.get("deadline") or condition.get("deadline_timestamp")
        if not deadline_raw:
            return {
                "condition": condition,
                "status": "review",
                "reason": "The deadline needs an exact time and timezone.",
                "supplier_value": "Not provided",
            }

        deadline_str = str(deadline_raw)
        # Strict check matching frontend / (?:Z|[+-]\d{2}:\d{2})$ /
        if not re.search(r"(?:Z|[+-]\d{2}:\d{2})$", deadline_str):
            return {
                "condition": condition,
                "status": "review",
                "reason": "The deadline needs an exact time and timezone.",
                "supplier_value": "Not provided",
            }

        try:
            deadline_dt = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
            if deadline_dt.tzinfo is None:
                deadline_dt = deadline_dt.replace(tzinfo=UTC)
        except ValueError:
            return {
                "condition": condition,
                "status": "review",
                "reason": "A valid evaluation time and deadline are required.",
                "supplier_value": "Not provided",
            }

        now_utc = now if now.tzinfo else now.replace(tzinfo=UTC)
        # Normalize timezones for comparison
        if now_utc.tzinfo != deadline_dt.tzinfo:
            now_utc = now_utc.astimezone(deadline_dt.tzinfo)

        # Strict inequality: if now >= deadline -> blocked!
        passed = now_utc < deadline_dt
        now_ist_str = now_utc.astimezone(IST).strftime("%d/%m/%Y, %H:%M:%S")

        return {
            "condition": condition,
            "status": "meets" if passed else "blocked",
            "supplier_value": "Open at evaluation time" if passed else "Deadline passed",
            "reason": f"Checked against {now_ist_str} IST.",
        }

    return {
        "condition": condition,
        "status": "review",
        "reason": f"Unsupported condition type '{cond_type}'.",
        "supplier_value": "Not provided",
    }


def evaluate_tender(
    conditions: list[dict[str, Any]],
    profile: dict[str, Any],
    now: datetime,
    verified_certificates: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Aggregate evaluation over all conditions for a tender."""
    findings = [evaluate_condition(c, profile, now, verified_certificates) for c in conditions]
    unique_types = {c.get("type") for c in conditions}
    coverage_complete = len(unique_types) == 5

    has_blocked = any(f["status"] == "blocked" for f in findings)
    has_review = any(f["status"] == "review" for f in findings)

    if has_blocked:
        status = "blocked"
    elif not coverage_complete or has_review:
        status = "review"
    else:
        status = "meets"

    return {
        "status": status,
        "findings": findings,
        "coverage_complete": coverage_complete,
    }
