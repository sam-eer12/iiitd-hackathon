"""Authenticated consent sessions and server-owned verification receipts."""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_authenticated_context
from app.core.authorization import AuthenticatedContext
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitExceededError,
)
from app.database import get_db
from app.domain.certificates import (
    CertificateCheckError,
    verify_gst_registration,
    verify_issued_certificate,
)
from app.integrations.sandbox_client import (
    configuration_ready,
    get_sandbox_client,
    signing_certificate_path,
)
from app.models.certificates import CertificateVerification
from app.models.models import Workspace
from app.schemas.certificates import (
    VerificationListResponse,
    VerificationStartRequest,
    VerificationStartResponse,
    VerificationSummary,
)

router = APIRouter(prefix="/certificate-verifications", tags=["Certificate verification"])


def require_live_principal(ctx: AuthenticatedContext) -> None:
    if get_settings().SANDBOX_ENVIRONMENT == "live" and ctx.principal.claims.get("dev"):
        raise ForbiddenError("Sign in with a real Firebase account to verify live documents.")


def public_verification(row: CertificateVerification) -> VerificationSummary:
    status = row.status
    if status in {"verified", "test_passed"} and (
        row.valid_until is None or row.valid_until <= datetime.now(UTC)
    ):
        status = "expired"
    return VerificationSummary(
        id=row.id,
        kind=row.kind,
        provider=row.provider,
        environment=row.environment,
        subject_name=row.subject_name,
        masked_number=f"{'•' * (len(row.document_number) - 4)}{row.document_number[-4:]}",
        status=status,
        message="This verification has expired. Verify again."
        if status == "expired"
        else row.message,
        issuer=row.issuer,
        created_at=row.created_at,
        verified_at=row.verified_at,
        valid_until=row.valid_until,
    )


@router.get("", response_model=VerificationListResponse)
async def list_verifications(
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
):
    require_live_principal(ctx)
    rows = (
        (
            await db.execute(
                sa.select(CertificateVerification)
                .where(
                    CertificateVerification.workspace_id == ctx.workspace_id,
                    CertificateVerification.user_id == ctx.user_id,
                )
                .order_by(CertificateVerification.created_at.desc())
                .limit(30)
            )
        )
        .scalars()
        .all()
    )
    settings = get_settings()
    return VerificationListResponse(
        configured=configuration_ready(settings),
        available_kinds=[
            kind
            for kind, provider in (("gst", "entitylocker"), ("pan", "digilocker"))
            if configuration_ready(settings, provider)
        ],
        environment=settings.SANDBOX_ENVIRONMENT,
        verifications=[public_verification(row) for row in rows],
    )


@router.post("", response_model=VerificationStartResponse, status_code=201)
async def start_verification(
    payload: VerificationStartRequest,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
):
    require_live_principal(ctx)
    client = get_sandbox_client()
    client.require_configuration("entitylocker" if payload.kind == "gst" else "digilocker")
    settings = get_settings()
    now = datetime.now(UTC)
    # Serialize reservations for this workspace to prevent duplicate metered submissions.
    await db.execute(
        sa.select(Workspace.id).where(Workspace.id == ctx.workspace_id).with_for_update()
    )
    existing = (
        await db.execute(
            sa.select(CertificateVerification).where(
                CertificateVerification.workspace_id == ctx.workspace_id,
                CertificateVerification.request_key == payload.request_key,
            )
        )
    ).scalar_one_or_none()
    if existing:
        if existing.user_id != ctx.user_id or (
            existing.kind,
            existing.subject_name,
            existing.document_number,
        ) != (payload.kind, payload.subject_name, payload.document_number):
            raise ConflictError(
                "VERIFICATION_REQUEST_CONFLICT",
                "This request key was already used for a different document.",
            )
        return VerificationStartResponse(verification=public_verification(existing))
    active = (
        await db.execute(
            sa.select(CertificateVerification.id).where(
                CertificateVerification.workspace_id == ctx.workspace_id,
                CertificateVerification.kind == payload.kind,
                CertificateVerification.status.in_(["pending", "submitting", "submission_unknown"]),
                CertificateVerification.expires_at > now,
            )
        )
    ).first()
    if active:
        raise ConflictError(
            "VERIFICATION_ALREADY_PENDING",
            "A verification is already pending. Complete or check that session first.",
        )
    recent = (
        await db.execute(
            sa.select(sa.func.count())
            .select_from(CertificateVerification)
            .where(
                CertificateVerification.workspace_id == ctx.workspace_id,
                CertificateVerification.created_at > now - timedelta(days=1),
            )
        )
    ).scalar_one()
    if recent >= 10:
        raise RateLimitExceededError("The daily document-verification limit has been reached.")
    row = CertificateVerification(
        workspace_id=ctx.workspace_id,
        user_id=ctx.user_id,
        request_key=payload.request_key,
        kind=payload.kind,
        provider="entitylocker" if payload.kind == "gst" else "digilocker",
        environment=settings.SANDBOX_ENVIRONMENT,
        subject_name=payload.subject_name,
        document_number=payload.document_number,
        status="submitting",
        message="Creating a secure document-consent session.",
        expires_at=now + timedelta(minutes=65),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    try:
        callback = f"{settings.SANDBOX_RETURN_URL}?verification={row.id}"
        provider_id, authorization_url = await client.initiate(
            row.provider, callback, int(row.expires_at.timestamp() * 1000), payload.flow
        )
    except AppError:
        # A timeout may follow a successful upstream submission. Do not blindly resubmit.
        row.status = "submission_unknown"
        row.message = "The consent session could not be confirmed. An operator must reconcile it before another submission."
        await db.commit()
        raise
    row.provider_session_id = provider_id
    row.status = "pending"
    row.message = "Waiting for consent to share the issuer document."
    await db.commit()
    return VerificationStartResponse(
        verification=public_verification(row), authorization_url=authorization_url
    )


@router.post("/{verification_id}/check", response_model=VerificationSummary)
async def check_verification(
    verification_id: UUID,
    ctx: AuthenticatedContext = Depends(get_authenticated_context),
    db: AsyncSession = Depends(get_db),
):
    require_live_principal(ctx)
    row = (
        await db.execute(
            sa.select(CertificateVerification)
            .where(
                CertificateVerification.id == verification_id,
                CertificateVerification.workspace_id == ctx.workspace_id,
                CertificateVerification.user_id == ctx.user_id,
            )
            .with_for_update()
        )
    ).scalar_one_or_none()
    if row is None:
        raise NotFoundError("Verification session not found.")
    now = datetime.now(UTC)
    if row.status != "pending":
        return public_verification(row)
    if row.expires_at <= now:
        row.status, row.message = (
            "expired",
            "The consent session expired. Start a new verification.",
        )
        await db.commit()
        return public_verification(row)
    if row.environment != get_settings().SANDBOX_ENVIRONMENT:
        row.status, row.message = (
            "review",
            "The provider environment changed. Start a new verification.",
        )
        await db.commit()
        return public_verification(row)
    if row.last_checked_at and now - row.last_checked_at < timedelta(seconds=5):
        return public_verification(row)
    client = get_sandbox_client()
    row.last_checked_at = now
    try:
        status = await client.session_status(row.provider, row.provider_session_id)
        if (
            status.get("id") != row.provider_session_id
            or status.get("@entity") != f"in.co.sandbox.kyc.{row.provider}.session"
        ):
            raise CertificateCheckError("The provider returned a different verification session.")
        provider_status = status.get("status")
        if provider_status in {"created", "initialized", "authorized"}:
            await db.commit()
            return public_verification(row)
        if provider_status in {"failed", "expired"}:
            row.status, row.message = (
                provider_status,
                "Document consent was unsuccessful or expired.",
            )
            await db.commit()
            return public_verification(row)
        document_type = "gstn_details" if row.kind == "gst" else "pan"
        consented = status.get("documents_consented")
        if (
            provider_status != "succeeded"
            or not isinstance(consented, list)
            or document_type not in consented
        ):
            raise CertificateCheckError("Consent for the required document could not be confirmed.")
        content = await client.document(row.provider, row.provider_session_id, document_type)
        certificate_path = signing_certificate_path(get_settings(), row.provider)
        if not certificate_path:
            raise CertificateCheckError(
                "The trusted issuer signing certificate is not configured for this document type."
            )
        signing_certificate = Path(certificate_path).read_bytes()
        evidence = await asyncio.to_thread(
            verify_issued_certificate,
            content,
            signing_certificate,
            row.kind,
            row.subject_name,
            row.document_number,
            now,
        )
        if row.kind == "gst":
            registration = await client.gst_registration(row.document_number)
            verify_gst_registration(registration, row.subject_name, row.document_number)
        row.issuer = evidence.issuer
        row.document_sha256 = evidence.sha256
        row.verified_at = now
        row.valid_until = now + timedelta(
            hours=min(max(get_settings().CERTIFICATE_VERIFICATION_TTL_HOURS, 1), 168)
        )
        if evidence.valid_until:
            row.valid_until = min(row.valid_until, evidence.valid_until)
        row.status = "verified" if row.environment == "live" else "test_passed"
        row.message = (
            "Issuer signature and holder details verified."
            if row.environment == "live"
            else "Test check passed. This is not a live document verification."
        )
    except CertificateCheckError as exc:
        row.status, row.message = "review", str(exc)
    except OSError:
        row.status, row.message = "review", "The trusted issuer signing certificate is unavailable."
    except AppError as exc:
        row.message = exc.message
        if not exc.retryable:
            row.status = "review"
    await db.commit()
    return public_verification(row)
