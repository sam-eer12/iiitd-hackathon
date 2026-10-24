"""Read authoritative certificate receipts for readiness checks."""

from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.certificates import normalized_name
from app.models.certificates import CertificateVerification


async def verified_certificate_types(
    db: AsyncSession, workspace_id: UUID, company: str, now: datetime
) -> frozenset[str]:
    if not normalized_name(company):
        return frozenset()
    rows = (
        (
            await db.execute(
                sa.select(CertificateVerification).where(
                    CertificateVerification.workspace_id == workspace_id,
                    CertificateVerification.kind == "gst",
                    CertificateVerification.provider == "entitylocker",
                    CertificateVerification.environment == "live",
                    CertificateVerification.status == "verified",
                    CertificateVerification.verified_at <= now,
                    CertificateVerification.document_sha256.is_not(None),
                    CertificateVerification.valid_until > now,
                )
            )
        )
        .scalars()
        .all()
    )
    return (
        frozenset({"gst"})
        if any(normalized_name(row.subject_name) == normalized_name(company) for row in rows)
        else frozenset()
    )
