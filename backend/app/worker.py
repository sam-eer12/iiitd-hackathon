"""Durable background worker for processing discovery, ingestion, and evaluation jobs."""

import asyncio
import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

import sqlalchemy as sa

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.database import async_session_factory
from app.integrations.storage import get_storage
from app.integrations.tinyfish_client import get_tinyfish_client
from app.models.models import (
    Document,
    ProviderAttempt,
    RefreshJob,
    SourceObservation,
    Tender,
    TenderSnapshot,
)
from app.repositories.refreshes import claim_due_job, complete_job, fail_job, heartbeat_job
from app.sources.iiitd import DEFAULT_GOAL_PROMPT, validate_discovery_result

logger = get_logger("worker")


async def process_job(job_id: uuid.UUID, lease_token: str) -> None:
    settings = get_settings()
    tf_client = get_tinyfish_client()
    get_storage()
    now = datetime.now(UTC)

    logger.info("Processing job %s (token: %s)", job_id, lease_token[:8])

    async with async_session_factory() as db:
        stmt = sa.select(RefreshJob).where(RefreshJob.id == job_id)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if not job or job.status != "running":
            logger.warning("Job %s not found or no longer running.", job_id)
            return

        correlation_marker = f"corr_{job.id}_{uuid.uuid4().hex[:8]}"

        # 1. Submitting to provider
        job.stage = "submitting"
        await db.commit()

        submission = await tf_client.submit(DEFAULT_GOAL_PROMPT, correlation_marker)
        run_id = submission.get("run_id")

        attempt = ProviderAttempt(
            job_id=job.id,
            attempt_number=job.retry_count + 1,
            provider_run_id=run_id,
            correlation_marker=correlation_marker,
            provider_status=submission.get("status", "PENDING"),
            submitted_at=now,
        )
        db.add(attempt)
        job.provider_run_id = run_id
        job.stage = "discovering"
        await db.commit()

    # 2. Polling for discovery results with bounded budget
    observation_budget = settings.PROVIDER_OBSERVATION_BUDGET_SECONDS
    poll_interval = (
        2.0 if settings.TINYFISH_MODE == "fixture" else settings.PROVIDER_POLL_INTERVAL_SECONDS
    )
    start_time = datetime.now(UTC)

    run_data: dict[str, Any] = {}
    while (datetime.now(UTC) - start_time).total_seconds() < observation_budget:
        await asyncio.sleep(poll_interval)
        async with async_session_factory() as db:
            await heartbeat_job(db, job_id, lease_token)

        run_data = await tf_client.get_run(run_id)
        status = run_data.get("status")
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            break

    if run_data.get("status") != "COMPLETED":
        async with async_session_factory() as db:
            await fail_job(
                db,
                job_id,
                "PROVIDER_FAILED",
                f"TinyFish run ended with status: {run_data.get('status')}",
            )
        return

    # 3. Validating discovery results
    result_payload = run_data.get("result", {})
    try:
        notices = validate_discovery_result(result_payload)
    except ValueError as exc:
        async with async_session_factory() as db:
            await fail_job(db, job_id, "INVALID_SOURCE_RESULT", str(exc))
        return
    logger.info("Discovered %d notices for job %s", len(notices), job_id)

    async with async_session_factory() as db:
        obs = SourceObservation(
            job_id=job_id,
            observed_at=datetime.now(UTC),
            raw_payload=result_payload,
            validated_notices=notices,
            completeness="complete" if result_payload.get("outcome") == "success" else "empty",
        )
        db.add(obs)
        await db.commit()

    # 4. Ingesting notices, creating tender records, documents, and snapshots
    processed_count = 0
    for notice in notices:
        async with async_session_factory() as db:
            ref = notice.get("notice_id") or "Reference not provided"
            title = notice.get("title", "Untitled Notice")
            source_url = notice.get("source_url")
            deadline_text = notice.get("deadline_text")

            # Check if tender already exists
            t_stmt = sa.select(Tender).where(
                Tender.source_id == "iiitd",
                Tender.external_reference == ref,
                *([] if notice.get("notice_id") else [Tender.title == title]),
            )
            t_res = await db.execute(t_stmt)
            tender = t_res.scalar_one_or_none()

            t_now = datetime.now(UTC)
            if not tender:
                tender = Tender(
                    source_id="iiitd",
                    external_reference=ref,
                    title=title,
                    description="Discovered via automated public source refresh.",
                    issuer="IIIT-Delhi",
                    category="Unclassified",
                    estimated_value="Not extracted",
                    deadline_text=deadline_text,
                    source_url=source_url,
                    provenance="live" if settings.TINYFISH_MODE == "live" else "sample",
                    amended=len(notice.get("amendment_urls", [])) > 0,
                    created_at=t_now,
                    updated_at=t_now,
                )
                db.add(tender)
                await db.flush()

            else:
                tender.title = title
                tender.deadline_text = deadline_text
                tender.source_url = source_url
                tender.estimated_value = "Not extracted"
                tender.amended = bool(notice.get("amendment_urls"))
                tender.updated_at = t_now
                tender.provenance = "live" if settings.TINYFISH_MODE == "live" else "sample"

            # Store documents
            pdf_urls = notice.get("pdf_urls", [])
            for p_url in pdf_urls:
                doc_stmt = sa.select(Document).where(
                    Document.tender_id == tender.id, Document.source_url == p_url
                )
                if not (await db.execute(doc_stmt)).scalar_one_or_none():
                    doc = Document(
                        tender_id=tender.id,
                        workspace_id=None,  # Public
                        source_url=p_url,
                        role="main_notice",
                        visibility="public",
                        created_at=t_now,
                    )
                    db.add(doc)
                    await db.flush()

            amend_urls = notice.get("amendment_urls", [])
            for a_url in amend_urls:
                doc_stmt = sa.select(Document).where(
                    Document.tender_id == tender.id, Document.source_url == a_url
                )
                if not (await db.execute(doc_stmt)).scalar_one_or_none():
                    doc = Document(
                        tender_id=tender.id,
                        workspace_id=None,
                        source_url=a_url,
                        role="corrigendum",
                        visibility="public",
                        created_at=t_now,
                    )
                    db.add(doc)
                    await db.flush()

            # Keep source observations without fabricating eligibility clauses or diffs.
            # PDF extraction must provide verified quotes before conditions can be added.
            snap_stmt = sa.select(TenderSnapshot).where(
                TenderSnapshot.tender_id == tender.id, TenderSnapshot.is_current
            )
            old_snap = (await db.execute(snap_stmt)).scalar_one_or_none()
            fingerprint = hashlib.sha256(json.dumps(notice, sort_keys=True).encode()).hexdigest()
            if not old_snap or old_snap.snapshot_fingerprint != fingerprint:
                if old_snap:
                    old_snap.is_current = False
                db.add(
                    TenderSnapshot(
                        tender_id=tender.id,
                        snapshot_fingerprint=fingerprint,
                        is_current=True,
                        created_at=t_now,
                    )
                )

            await db.commit()
            processed_count += 1

    # 6. Mark job completed
    async with async_session_factory() as db:
        await complete_job(
            db,
            job_id=job_id,
            lease_token=lease_token,
            provider_status="COMPLETED",
            provider_run_id=run_id,
            progress={"documentsDiscovered": len(notices), "documentsProcessed": processed_count},
        )
    logger.info("Job %s completed successfully (%d notices processed).", job_id, processed_count)


async def run_worker_loop(single_run: bool = False) -> None:
    """Continuously claim and process jobs."""
    setup_logging()
    logger.info("TenderLens worker started.")

    while True:
        try:
            claimed = None
            async with async_session_factory() as db:
                claimed = await claim_due_job(db, lease_seconds=90)

            if claimed:
                job, lease_token = claimed
                await process_job(job.id, lease_token)
            else:
                if single_run:
                    break
                await asyncio.sleep(2.0)
        except Exception as exc:
            logger.error("Error in worker loop: %s", exc, exc_info=True)
            if single_run:
                break
            await asyncio.sleep(5.0)


if __name__ == "__main__":
    asyncio.run(run_worker_loop())
