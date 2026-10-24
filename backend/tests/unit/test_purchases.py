"""Checkout rules and API contracts with isolated persistence; no external services."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import quote
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.api.dependencies import get_authenticated_context
from app.api.routes import purchases
from app.core.auth import Principal
from app.core.authorization import AuthenticatedContext
from app.core.errors import ConflictError, UnprocessableFactError
from app.database import get_db
from app.domain.purchases import purchase_supplier, require_open_tender
from app.main import app
from app.models.purchases import DemoPurchase
from app.schemas.purchases import PurchaseStartRequest, PurchaseTender


def notice():
    return {
        "id": f"iiitd-{quote('TEST/2026/BUY', safe='')}",
        "reference": "TEST/2026/BUY",
        "title": "Test notice - synthetic fixture",
        "issuer": "IIIT-Delhi",
        "sourceUrl": "https://iiitd.ac.in/tenders",
        "pdfUrls": ["https://iiitd.ac.in/test.pdf"],
        "amendmentUrls": [],
        "deadline": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        "deadlineText": "Synthetic future deadline",
        "retrievedAt": datetime.now(UTC).isoformat(),
    }


def test_deadline_boundaries_and_profile_gate():
    tender = PurchaseTender.model_validate(notice())
    require_open_tender(tender, tender.deadline - timedelta(microseconds=1))
    with pytest.raises(ConflictError, match="closed"):
        require_open_tender(tender, tender.deadline)
    with pytest.raises(ConflictError, match="unconfirmed"):
        require_open_tender(tender.model_copy(update={"deadline": None}), datetime.now(UTC))
    with pytest.raises(UnprocessableFactError):
        purchase_supplier({"company": "  "})


@pytest.mark.parametrize(
    "change",
    [
        {"amountPaise": 1},
        {"status": "purchased"},
        {"reviewed": False},
        {"demoAcknowledged": False},
        {"demoAcknowledged": None},
    ],
)
def test_checkout_request_cannot_claim_amount_status_or_skip_acknowledgement(change):
    with pytest.raises(ValidationError):
        PurchaseStartRequest.model_validate(
            {"tender": notice(), "reviewed": True, "demoAcknowledged": True, **change}
        )


@pytest.mark.parametrize(
    "change",
    [
        {"sourceUrl": "https://iiitd.ac.in.evil.test/tenders"},
        {"pdfUrls": ["http://127.0.0.1/private.pdf"]},
        {"id": "sample-1"},
        {"deadline": "2026-10-25"},
    ],
)
def test_checkout_snapshot_rejects_wrong_source_identity_and_ambiguous_time(change):
    with pytest.raises(ValidationError):
        PurchaseTender.model_validate({**notice(), **change})


@pytest.fixture
def checkout_api(monkeypatch):
    now = datetime.now(UTC)
    first = AuthenticatedContext(Principal("buyer-a"), uuid4(), uuid4())
    second = AuthenticatedContext(Principal("buyer-b"), uuid4(), uuid4())
    context = {"value": first}
    supplier = {"company": "Test Supplier", "contact": "Test Contact", "email": "test@example.test"}
    order = DemoPurchase(
        id=uuid4(),
        workspace_id=first.workspace_id,
        user_id=first.user_id,
        tender_key=notice()["id"],
        tender=notice(),
        supplier=supplier,
        amount_paise=49900,
        currency="INR",
        status="pending",
        identity_status="unverified",
        created_at=now,
        updated_at=now,
        purchased_at=None,
    )
    db = AsyncMock()

    async def lookup(query):
        params = query.compile().params
        # Exercise the actual ownership predicate and lock on the SQLAlchemy query.
        assert "workspace_id_1" in params
        if params["workspace_id_1"] != order.workspace_id:
            return None
        if "id_1" in params and params["id_1"] != order.id:
            return None
        return order

    async def listing(query):
        return SimpleNamespace(
            all=lambda: (
                [order] if query.compile().params["workspace_id_1"] == order.workspace_id else []
            )
        )

    db.scalar.side_effect = lookup
    db.scalars.side_effect = listing
    monkeypatch.setattr(purchases, "saved_supplier", AsyncMock(return_value=supplier))
    monkeypatch.setattr(purchases, "identity_status", AsyncMock(return_value="unverified"))
    app.dependency_overrides[get_authenticated_context] = lambda: context["value"]
    app.dependency_overrides[get_db] = lambda: db
    try:
        yield order, db, context, second
    finally:
        app.dependency_overrides.pop(get_authenticated_context, None)
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_failure_retry_receipt_replay_and_persistence_contract(checkout_api):
    order, db, _, _ = checkout_api
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start = await client.post(
            "/api/v1/demo-purchases",
            json={"tender": order.tender, "reviewed": True, "demoAcknowledged": True},
        )
        assert start.status_code == 200
        assert start.json()["status"] == "pending"
        assert start.json()["demo"] is True
        assert start.json()["amountPaise"] == 49900
        assert start.json()["identityStatus"] == "unverified"
        failed = await client.post(
            f"/api/v1/demo-purchases/{order.id}/pay", json={"outcome": "failure"}
        )
        assert failed.json()["status"] == "failed"
        assert failed.json()["receiptNumber"] is None
        paid = await client.post(
            f"/api/v1/demo-purchases/{order.id}/pay", json={"outcome": "success"}
        )
        assert paid.json()["status"] == "purchased"
        assert paid.json()["receiptNumber"].startswith("DEMO-")
        for outcome in ("success", "failure"):
            replay = await client.post(
                f"/api/v1/demo-purchases/{order.id}/pay", json={"outcome": outcome}
            )
            assert replay.json() == paid.json()
        history = await client.get("/api/v1/demo-purchases")
        assert history.json()["purchases"] == [paid.json()]
        assert (await client.get(f"/api/v1/demo-purchases/{order.id}")).json() == paid.json()
    assert db.commit.await_count == 3
    assert db.scalar.call_args_list[1].args[0]._for_update_arg is not None


@pytest.mark.asyncio
async def test_another_workspace_cannot_list_inspect_or_pay_order(checkout_api):
    order, db, context, other = checkout_api
    context["value"] = other
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/v1/demo-purchases")).json() == {"purchases": []}
        assert (await client.get(f"/api/v1/demo-purchases/{order.id}")).status_code == 404
        assert (
            await client.post(f"/api/v1/demo-purchases/{order.id}/pay", json={"outcome": "success"})
        ).status_code == 404
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_deadline_is_rechecked_before_payment(checkout_api):
    order, db, _, _ = checkout_api
    order.tender = {
        **order.tender,
        "deadline": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/demo-purchases/{order.id}/pay", json={"outcome": "success"}
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "TENDER_CLOSED"
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_saved_profile_never_creates_order(checkout_api, monkeypatch):
    order, db, _, _ = checkout_api
    monkeypatch.setattr(
        purchases,
        "saved_supplier",
        AsyncMock(side_effect=UnprocessableFactError("Save your profile first.")),
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/demo-purchases",
            json={"tender": order.tender, "reviewed": True, "demoAcknowledged": True},
        )
        assert response.status_code == 422
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_checkout_requires_authentication():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/v1/demo-purchases")).status_code == 401
        assert (await client.post("/api/v1/demo-purchases", json={})).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("holder", "status", "environment", "expected"),
    [
        ("Test Contact", "verified", "live", "verified"),
        ("Test Contact", "test_passed", "test", "test_passed"),
        ("Someone Else", "verified", "live", "unverified"),
        ("Test Contact", "verified", "test", "unverified"),
        ("Test Contact", "test_passed", "live", "unverified"),
    ],
)
async def test_checkout_identity_preserves_holder_and_environment(
    holder, status, environment, expected
):
    db = AsyncMock()
    db.scalars.return_value = SimpleNamespace(
        all=lambda: [
            SimpleNamespace(
                subject_name=holder,
                status=status,
                environment=environment,
            )
        ]
    )
    assert (
        await purchases.identity_status(db, uuid4(), "Test Contact", datetime.now(UTC)) == expected
    )
