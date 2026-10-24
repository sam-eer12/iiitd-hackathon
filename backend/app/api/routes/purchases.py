"""Workspace-isolated hackathon checkout. No payment provider is contacted."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_authenticated_context
from app.core.authorization import AuthenticatedContext
from app.core.errors import NotFoundError
from app.database import get_db
from app.domain.certificates import normalized_name
from app.domain.purchases import (
    DEMO_AMOUNT_PAISE,
    payment_status,
    purchase_supplier,
    require_open_tender,
)
from app.models.certificates import CertificateVerification
from app.models.purchases import DemoPurchase
from app.repositories.profiles import get_profile_by_workspace
from app.schemas.purchases import (
    DemoPaymentRequest,
    PurchaseResponse,
    PurchaseStartRequest,
    PurchaseTender,
)

router = APIRouter(prefix="/demo-purchases", tags=["Demo checkout"])


def public_purchase(order: DemoPurchase) -> PurchaseResponse:
    return PurchaseResponse(
        id=order.id,
        tender=PurchaseTender.model_validate(order.tender),
        supplier=order.supplier,
        amount_paise=order.amount_paise,
        currency=order.currency,
        status=order.status,
        identity_status=order.identity_status,
        created_at=order.created_at,
        updated_at=order.updated_at,
        purchased_at=order.purchased_at,
        receipt_number=f"DEMO-{str(order.id).upper()}" if order.status == "purchased" else None,
    )


async def saved_supplier(db: AsyncSession, workspace_id: UUID) -> dict[str, str]:
    pair = await get_profile_by_workspace(db, workspace_id)
    return purchase_supplier(pair[1].facts if pair else {})


async def identity_status(db: AsyncSession, workspace_id: UUID, contact: str, now: datetime) -> str:
    records = (
        await db.scalars(
            sa.select(CertificateVerification).where(
                CertificateVerification.workspace_id == workspace_id,
                CertificateVerification.kind == "pan",
                CertificateVerification.provider == "digilocker",
                CertificateVerification.status.in_(["verified", "test_passed"]),
                CertificateVerification.verified_at <= now,
                CertificateVerification.valid_until > now,
                CertificateVerification.document_sha256.is_not(None),
            )
        )
    ).all()
    matches = [
        record
        for record in records
        if normalized_name(record.subject_name) == normalized_name(contact)
    ]
    if any(record.status == "verified" and record.environment == "live" for record in matches):
        return "verified"
    if any(record.status == "test_passed" and record.environment == "test" for record in matches):
        return "test_passed"
    return "unverified"


async def owned_order(
    db: AsyncSession, workspace_id: UUID, purchase_id: UUID, *, lock: bool = False
) -> DemoPurchase:
    query = sa.select(DemoPurchase).where(
        DemoPurchase.id == purchase_id, DemoPurchase.workspace_id == workspace_id
    )
    if lock:
        query = query.with_for_update()
    order = await db.scalar(query)
    if order is None:
        raise NotFoundError("Demo purchase not found.")
    return order


@router.get("")
async def list_purchases(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> dict:
    orders = (
        await db.scalars(
            sa.select(DemoPurchase)
            .where(DemoPurchase.workspace_id == ctx.workspace_id)
            .order_by(DemoPurchase.created_at.desc())
        )
    ).all()
    return {
        "purchases": [
            public_purchase(order).model_dump(mode="json", by_alias=True) for order in orders
        ]
    }


@router.get("/{purchase_id}", response_model=PurchaseResponse)
async def get_purchase(
    purchase_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> PurchaseResponse:
    return public_purchase(await owned_order(db, ctx.workspace_id, purchase_id))


@router.post("", response_model=PurchaseResponse)
async def start_purchase(
    payload: PurchaseStartRequest,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> PurchaseResponse:
    now = datetime.now(UTC)
    supplier = await saved_supplier(db, ctx.workspace_id)
    require_open_tender(payload.tender, now)
    # One record per supplier and tender, including simultaneous requests/retries.
    await db.execute(
        insert(DemoPurchase)
        .values(
            id=uuid4(),
            workspace_id=ctx.workspace_id,
            user_id=ctx.user_id,
            tender_key=payload.tender.id,
            tender=payload.tender.model_dump(mode="json", by_alias=True),
            supplier=supplier,
            amount_paise=DEMO_AMOUNT_PAISE,
            currency="INR",
            status="pending",
            identity_status="unverified",
            created_at=now,
            updated_at=now,
        )
        .on_conflict_do_nothing(constraint="uq_demo_purchase_tender")
    )
    order = await db.scalar(
        sa.select(DemoPurchase)
        .where(
            DemoPurchase.workspace_id == ctx.workspace_id,
            DemoPurchase.tender_key == payload.tender.id,
        )
        .with_for_update()
    )
    if order.status != "purchased":
        order.tender = payload.tender.model_dump(mode="json", by_alias=True)
        order.supplier = supplier
        order.identity_status = await identity_status(
            db, ctx.workspace_id, supplier["contact"], now
        )
        order.updated_at = now
    await db.commit()
    return public_purchase(order)


@router.post("/{purchase_id}/pay", response_model=PurchaseResponse)
async def pay(
    purchase_id: UUID,
    payload: DemoPaymentRequest,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
) -> PurchaseResponse:
    order = await owned_order(db, ctx.workspace_id, purchase_id, lock=True)
    if order.status == "purchased":
        return public_purchase(order)
    now = datetime.now(UTC)
    require_open_tender(PurchaseTender.model_validate(order.tender), now)
    order.supplier = await saved_supplier(db, ctx.workspace_id)
    order.identity_status = await identity_status(
        db, ctx.workspace_id, order.supplier["contact"], now
    )
    order.status = payment_status(order.status, payload.outcome)
    order.updated_at = now
    if order.status == "purchased":
        order.purchased_at = now
    await db.commit()
    return public_purchase(order)
