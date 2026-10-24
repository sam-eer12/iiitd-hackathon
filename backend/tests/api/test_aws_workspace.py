"""Account provisioning and public source publication on PostgreSQL."""

import asyncio
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient

from app.database import async_session_factory
from app.main import app
from app.models.models import RefreshJob, SourceObservation, User, Workspace


@pytest.mark.asyncio
async def test_concurrent_first_login_has_one_rds_workspace():
    uid = f"aws_concurrent_{uuid4().hex}"
    headers = {"Authorization": f"Bearer dev_account:{uid}"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        responses = await asyncio.gather(
            *[client.put("/api/v1/me", headers=headers) for _ in range(5)]
        )
        assert [response.status_code for response in responses] == [200] * 5
        workspace_ids = {response.json()["workspace"]["id"] for response in responses}
        assert len(workspace_ids) == 1
    async with async_session_factory() as db:
        await db.execute(
            sa.delete(Workspace).where(Workspace.id == UUID(next(iter(workspace_ids))))
        )
        await db.execute(sa.delete(User).where(User.firebase_uid == uid))
        await db.commit()


@pytest.mark.asyncio
async def test_public_catalog_exposes_only_validated_public_notice_fields():
    uid = f"aws_catalog_{uuid4().hex}"
    headers = {"Authorization": f"Bearer dev_account:{uid}"}
    job_id = None
    workspace_id = None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        identity = (await client.put("/api/v1/me", headers=headers)).json()
        workspace_id = UUID(identity["workspace"]["id"])
        response = await client.post(
            "/api/v1/refreshes", headers=headers, json={"sourceId": "iiitd"}
        )
        job_id = UUID(response.json()["job"]["id"])
        async with async_session_factory() as db:
            job = await db.get(RefreshJob, job_id)
            job.status = "completed"
            db.add(
                SourceObservation(
                    job_id=job_id,
                    observed_at=datetime.now(UTC),
                    raw_payload={"private_debug": "must never leave the API"},
                    validated_notices=[
                        {"title": "Official notice", "source_url": "https://iiitd.ac.in/tenders"}
                    ],
                )
            )
            await db.commit()
        result = await client.get("/api/v1/catalog")
        assert result.status_code == 200
        assert result.json()["payload"]["notices"][0]["title"] == "Official notice"
        assert "private_debug" not in result.text
        async with async_session_factory() as db:
            job = await db.get(RefreshJob, job_id)
            job.mode = "manual_import"
            await db.commit()
        assert (await client.get("/api/v1/catalog")).json()["payload"] is None
    async with async_session_factory() as db:
        await db.execute(sa.delete(Workspace).where(Workspace.id == workspace_id))
        await db.execute(sa.delete(User).where(User.firebase_uid == uid))
        await db.commit()
