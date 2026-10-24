"""Small, explicit demo purchase rules, independent of readiness scoring."""

from datetime import datetime

from app.core.errors import ConflictError, UnprocessableFactError
from app.schemas.purchases import PurchaseTender

DEMO_AMOUNT_PAISE = 49900


def require_open_tender(tender: PurchaseTender, now: datetime) -> None:
    if tender.deadline is None:
        raise ConflictError(
            "DEADLINE_UNKNOWN",
            "The closing date is unconfirmed. Review the official notice before checkout.",
        )
    if tender.deadline <= now:
        raise ConflictError(
            "TENDER_CLOSED", "This tender has closed. You can still review its documents."
        )


def purchase_supplier(facts: dict) -> dict[str, str]:
    fields = {key: str(facts.get(key) or "").strip() for key in ("company", "contact", "email")}
    if not all(fields.values()) or "@" not in fields["email"] or not facts.get("categories"):
        raise UnprocessableFactError(
            "Save your business name, contact, email and supply categories in Supplier profile first."
        )
    return fields


def payment_status(current: str, outcome: str) -> str:
    # A delayed failure or repeated click can never undo a completed purchase.
    if current == "purchased":
        return "purchased"
    return "purchased" if outcome == "success" else "failed"
