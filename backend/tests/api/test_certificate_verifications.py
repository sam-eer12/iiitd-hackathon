"""Real database tests with a mocked provider; never call paid or identity services."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.api.dependencies import get_authenticated_context
from app.api.routes import certificates
from app.core.auth import Principal
from app.core.authorization import AuthenticatedContext
from app.core.config import Settings
from app.database import async_session_factory
from app.main import app
from app.models.certificates import CertificateVerification
from app.repositories.certificates import verified_certificate_types
from app.repositories.users import provision_user_and_workspace
from tests.certificate_fixtures import COMPANY, GSTIN, signed_gst, signed_pan, signing_material


@pytest.fixture
async def verification_environment(tmp_path, monkeypatch):
    key, certificate = signing_material()
    path = tmp_path / "trusted-test-issuer.pem"
    path.write_bytes(certificate)
    settings = Settings(
        _env_file=None,
        SANDBOX_ENVIRONMENT="live",
        SANDBOX_API_KEY=SecretStr("key_live_test_fixture"),
        SANDBOX_API_SECRET=SecretStr("secret_live_test_fixture"),
        SANDBOX_RETURN_URL="https://example.test/dashboard/profile",
        DIGILOCKER_SIGNING_CERTIFICATE_PATH=str(path),
        ENTITYLOCKER_SIGNING_CERTIFICATE_PATH=str(path),
    )

    class Provider:
        calls = 0
        consented = ["gstn_details"]
        document_bytes = signed_gst(key, certificate)
        pan_document = signed_pan(key, certificate)

        def require_configuration(self, provider=None):
            pass

        async def initiate(self, provider, redirect_url, expires_at, flow):
            self.calls += 1
            self.session_id = str(uuid.uuid4())
            return self.session_id, "https://entity.digilocker.gov.in/public/oauth2/1/authorize"

        async def session_status(self, provider, session_id):
            return {
                "id": session_id,
                "@entity": f"in.co.sandbox.kyc.{provider}.session",
                "status": "succeeded",
                "documents_consented": self.consented,
            }

        async def document(self, *args):
            return self.document_bytes

        async def gst_registration(self, gstin):
            return {"status_cd": "1", "data": {"gstin": gstin, "lgnm": COMPANY, "sts": "Active"}}

    provider = Provider()
    contexts = []
    async with async_session_factory() as db:
        for _ in range(2):
            uid = f"cert-test-{uuid.uuid4()}"
            user, workspace = await provision_user_and_workspace(db, firebase_uid=uid)
            contexts.append(
                AuthenticatedContext(
                    principal=Principal(uid=uid), user_id=user.id, workspace_id=workspace.id
                )
            )
    holder = {"context": contexts[0]}
    app.dependency_overrides[get_authenticated_context] = lambda: holder["context"]
    monkeypatch.setattr(certificates, "get_settings", lambda: settings)
    monkeypatch.setattr(certificates, "get_sandbox_client", lambda: provider)
    try:
        yield settings, provider, holder, contexts
    finally:
        app.dependency_overrides.pop(get_authenticated_context, None)


def request_body():
    return {
        "kind": "gst",
        "subjectName": COMPANY,
        "documentNumber": GSTIN,
        "consent": True,
        "requestKey": str(uuid.uuid4()),
    }


@pytest.mark.asyncio
async def test_live_receipt_requires_server_signature_and_registry_check(verification_environment):
    _, provider, _, contexts = verification_environment
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start = await client.post("/api/v1/certificate-verifications", json=request_body())
        assert start.status_code == 201
        session = start.json()["verification"]
        assert session["status"] == "pending"
        checked = await client.post(f"/api/v1/certificate-verifications/{session['id']}/check")
        assert checked.status_code == 200
        assert checked.json()["status"] == "verified"
        assert checked.json()["provider"] == "entitylocker"
        assert GSTIN not in checked.text
        assert provider.session_id not in checked.text
        assert "documentSha256" not in checked.text
        await client.post(f"/api/v1/certificate-verifications/{session['id']}/check")
        assert provider.calls == 1
    async with async_session_factory() as db:
        assert await verified_certificate_types(
            db, contexts[0].workspace_id, COMPANY, datetime.now(UTC)
        ) == frozenset({"gst"})
        assert not await verified_certificate_types(
            db, contexts[0].workspace_id, "Different Company", datetime.now(UTC)
        )


@pytest.mark.asyncio
async def test_test_mode_receipt_cannot_produce_live_badge(verification_environment):
    settings, _, _, contexts = verification_environment
    settings.SANDBOX_ENVIRONMENT = "test"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        start = await client.post("/api/v1/certificate-verifications", json=request_body())
        checked = await client.post(
            f"/api/v1/certificate-verifications/{start.json()['verification']['id']}/check"
        )
        assert checked.json()["status"] == "test_passed"
    async with async_session_factory() as db:
        assert not await verified_certificate_types(
            db, contexts[0].workspace_id, COMPANY, datetime.now(UTC)
        )


@pytest.mark.asyncio
async def test_personal_pan_receipt_does_not_verify_business_gst(verification_environment):
    _, provider, _, contexts = verification_environment
    provider.consented = ["pan"]
    provider.document_bytes = provider.pan_document
    payload = {
        **request_body(),
        "kind": "pan",
        "subjectName": "Example Person",
        "documentNumber": "ABCDE1234F",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        started = await client.post("/api/v1/certificate-verifications", json=payload)
        checked = await client.post(
            f"/api/v1/certificate-verifications/{started.json()['verification']['id']}/check"
        )
        assert checked.json()["status"] == "verified"
        assert checked.json()["provider"] == "digilocker"
    async with async_session_factory() as db:
        assert not await verified_certificate_types(
            db, contexts[0].workspace_id, COMPANY, datetime.now(UTC)
        )


@pytest.mark.asyncio
async def test_other_workspace_cannot_access_or_complete_session(verification_environment):
    _, _, holder, contexts = verification_environment
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        started = await client.post("/api/v1/certificate-verifications", json=request_body())
        holder["context"] = contexts[1]
        response = await client.post(
            f"/api/v1/certificate-verifications/{started.json()['verification']['id']}/check"
        )
        assert response.status_code == 404
        assert (await client.get("/api/v1/certificate-verifications")).json()["verifications"] == []


@pytest.mark.asyncio
async def test_duplicate_request_does_not_create_another_metered_session(verification_environment):
    _, provider, _, _ = verification_environment
    payload = request_body()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.post("/api/v1/certificate-verifications", json=payload)
        second = await client.post("/api/v1/certificate-verifications", json=payload)
        assert first.json()["verification"]["id"] == second.json()["verification"]["id"]
        assert provider.calls == 1
        assert (
            await client.post("/api/v1/certificate-verifications", json=request_body())
        ).status_code == 409


@pytest.mark.asyncio
@pytest.mark.parametrize("problem", ["unsigned", "missing_consent"])
async def test_unverified_documents_never_award_badges(verification_environment, problem):
    _, provider, _, _ = verification_environment
    if problem == "unsigned":
        provider.document_bytes = b"<Certificate/>"
    else:
        provider.consented = []
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        started = await client.post("/api/v1/certificate-verifications", json=request_body())
        response = await client.post(
            f"/api/v1/certificate-verifications/{started.json()['verification']['id']}/check"
        )
        assert response.json()["status"] == "review"


@pytest.mark.asyncio
async def test_expired_receipts_stop_verifying_the_profile(verification_environment):
    _, _, _, contexts = verification_environment
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        started = await client.post("/api/v1/certificate-verifications", json=request_body())
        verification_id = started.json()["verification"]["id"]
        await client.post(f"/api/v1/certificate-verifications/{verification_id}/check")
        async with async_session_factory() as db:
            await db.execute(
                sa.update(CertificateVerification)
                .where(CertificateVerification.id == uuid.UUID(verification_id))
                .values(valid_until=datetime.now(UTC) - timedelta(seconds=1))
            )
            await db.commit()
            assert not await verified_certificate_types(
                db, contexts[0].workspace_id, COMPANY, datetime.now(UTC)
            )
        response = await client.post(f"/api/v1/certificate-verifications/{verification_id}/check")
        assert response.json()["status"] == "expired"


@pytest.mark.asyncio
async def test_client_cannot_claim_verified_profile_provenance(verification_environment):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/api/v1/profile", json={"facts": {}, "provenance": "digilocker-verified"}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_unsigned_document_session_request_is_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/v1/certificate-verifications")).status_code == 401
