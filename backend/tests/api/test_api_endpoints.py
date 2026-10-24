"""Integration tests for authenticated API routes and workspace isolation."""

import uuid

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient

from app.cli.seed import seed_database
from app.database import async_session_factory
from app.main import app
from app.models.models import Tender


@pytest.fixture
async def catalog_tender():
    """Provide test notices independently of the source-only production seed."""
    await seed_database()
    live_id, sample_id = uuid.uuid4(), uuid.uuid4()
    async with async_session_factory() as db:
        for tender_id, provenance in ((live_id, "live"), (sample_id, "sample")):
            db.add(
                Tender(
                    id=tender_id,
                    source_id="iiitd",
                    external_reference=f"TEST-{tender_id}",
                    title=f"API test notice ({provenance})",
                    issuer="IIIT-Delhi",
                    source_url="https://iiitd.ac.in/tenders",
                    provenance=provenance,
                )
            )
        await db.commit()
    try:
        yield live_id, sample_id
    finally:
        async with async_session_factory() as db:
            await db.execute(sa.delete(Tender).where(Tender.id.in_([live_id, sample_id])))
            await db.commit()


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/me")
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_user_provisioning_and_me():
    headers = {"Authorization": "Bearer dev_user_alpha"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_put = await client.put("/api/v1/me", headers=headers)
        assert res_put.status_code == 200
        data = res_put.json()
        assert "user" in data
        assert "workspace" in data
        assert "user_alpha" in data["user"]["firebaseUid"]

        res_get = await client.get("/api/v1/me", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["user"]["id"] == data["user"]["id"]


@pytest.mark.asyncio
async def test_profile_read_update_and_version_conflict():
    headers = {"Authorization": "Bearer dev_user_beta_version_test"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Initial profile
        res_get = await client.get("/api/v1/profile", headers=headers)
        assert res_get.status_code == 200
        prof = res_get.json()
        current_version = prof["versionNumber"]

        # Update profile to next version
        update_payload = {
            "facts": {
                "company": "Beta Tech Solutions",
                "contact": "Jane Doe",
                "email": "jane@beta.com",
                "categories": ["Electronics", "IT Services"],
                "turnover": [
                    {"year": "2023–24", "amount": 3200000},
                    {"year": "2024–25", "amount": 3800000},
                    {"year": "2025–26", "amount": 4200000},
                ],
                "completedOrders": 5,
                "depositCapacity": 75000,
                "certificates": {"gst": True, "iso": True, "manufacturer": False},
            },
            "expectedVersion": current_version,
        }
        res_put = await client.put("/api/v1/profile", json=update_payload, headers=headers)
        assert res_put.status_code == 200
        assert res_put.json()["versionNumber"] == current_version + 1
        assert res_put.json()["facts"]["company"] == "Beta Tech Solutions"

        # Stale version update must fail with 409 PROFILE_VERSION_CONFLICT
        stale_payload = {
            "facts": {**update_payload["facts"], "company": "Stale Update"},
            "expectedVersion": current_version,  # Stale!
        }
        res_stale = await client.put("/api/v1/profile", json=stale_payload, headers=headers)
        assert res_stale.status_code == 409
        assert res_stale.json()["error"]["code"] == "PROFILE_VERSION_CONFLICT"


@pytest.mark.asyncio
async def test_sources_and_tenders_listing(catalog_tender):
    headers = {"Authorization": "Bearer dev_user_gamma"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Sources
        res_sources = await client.get("/api/v1/sources", headers=headers)
        assert res_sources.status_code == 200
        sources = res_sources.json()["sources"]
        assert len(sources) >= 1
        assert any(s["id"] == "iiitd" for s in sources)

        # Tenders
        res_tenders = await client.get("/api/v1/tenders", headers=headers)
        assert res_tenders.status_code == 200
        tenders = res_tenders.json()["items"]
        assert len(tenders) >= 1
        live_id, sample_id = catalog_tender
        assert str(live_id) in {tender["id"] for tender in tenders}
        assert str(sample_id) not in {tender["id"] for tender in tenders}

        first_tender = tenders[0]
        assert "evaluation" in first_tender
        assert first_tender["evaluation"]["status"] in ("meets", "review", "blocked")


@pytest.mark.asyncio
async def test_bookmarks_lifecycle(catalog_tender):
    headers = {"Authorization": "Bearer dev_user_delta"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        tender_id = str(catalog_tender[0])

        # Add bookmark
        res_add = await client.put(f"/api/v1/bookmarks/{tender_id}", headers=headers)
        assert res_add.status_code == 200

        # Verify in list
        res_list = await client.get("/api/v1/bookmarks", headers=headers)
        assert res_list.status_code == 200
        saved_ids = [b["tenderId"] for b in res_list.json()["items"]]
        assert tender_id in saved_ids

        # Remove bookmark
        res_del = await client.delete(f"/api/v1/bookmarks/{tender_id}", headers=headers)
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "removed"


@pytest.mark.asyncio
async def test_refresh_job_creation_and_status():
    headers = {"Authorization": "Bearer dev_user_epsilon"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {"sourceId": "iiitd", "mode": "discovery"}
        res_job = await client.post("/api/v1/refreshes", json=payload, headers=headers)
        assert res_job.status_code == 202
        job_data = res_job.json()["job"]
        assert job_data["status"] in ("queued", "running")
        job_id = job_data["id"]

        res_check = await client.get(f"/api/v1/refreshes/{job_id}", headers=headers)
        assert res_check.status_code == 200
        assert res_check.json()["job"]["id"] == job_id


@pytest.mark.asyncio
async def test_local_workspace_import():
    headers = {"Authorization": "Bearer dev_user_zeta"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        import_payload = {
            "importKey": "import_key_001",
            "profile": {
                "company": "Imported Enterprises",
                "contact": "John Doe",
                "email": "john@imported.com",
                "categories": ["Electronics"],
                "turnover": [{"year": "2024–25", "amount": 5000000}],
                "completedOrders": 4,
                "depositCapacity": 60000,
                "certificates": {"gst": True, "iso": True, "manufacturer": True},
            },
            "bookmarkedTenderIds": ["00000000-0000-0000-0000-000000000000"],
        }
        res_import = await client.post(
            "/api/v1/imports/local-workspace", json=import_payload, headers=headers
        )
        assert res_import.status_code == 200
        resp = res_import.json()
        assert resp["importedProfile"] is True
        assert "00000000-0000-0000-0000-000000000000" in resp["rejectedBookmarks"]

        # Verify profile was imported
        res_prof = await client.get("/api/v1/profile", headers=headers)
        assert res_prof.json()["facts"]["company"] == "Imported Enterprises"
