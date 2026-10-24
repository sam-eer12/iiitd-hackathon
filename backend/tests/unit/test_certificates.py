import json
from datetime import UTC, datetime

import httpx
import pytest
import respx
from pydantic import SecretStr, ValidationError

from app.cli.digilocker_callback import callback_handler
from app.core.config import Settings
from app.core.errors import AppError
from app.domain.certificates import (
    CertificateCheckError,
    verify_gst_registration,
    verify_issued_certificate,
)
from app.domain.readiness import evaluate_condition
from app.integrations.sandbox_client import (
    SandboxClient,
    configuration_ready,
    validate_authorization_url,
    validate_document_url,
)
from app.schemas.certificates import VerificationStartRequest
from tests.certificate_fixtures import COMPANY, GSTIN, signed_gst, signed_pan, signing_material


@pytest.fixture(scope="module")
def signer():
    return signing_material()


def test_signed_issuer_document_matches_holder(signer):
    key, certificate = signer
    evidence = verify_issued_certificate(
        signed_gst(key, certificate), certificate, "gst", COMPANY, GSTIN, datetime.now(UTC)
    )
    assert evidence.issuer == "Goods and Services Tax Network"
    assert len(evidence.sha256) == 64


def test_digilocker_pan_verifies_only_its_named_person(signer):
    key, certificate = signer
    content = signed_pan(key, certificate)
    result = verify_issued_certificate(
        content, certificate, "pan", "Example Person", "ABCDE1234F", datetime.now(UTC)
    )
    assert result.issuer == "Income Tax Department"
    with pytest.raises(CertificateCheckError):
        verify_issued_certificate(content, certificate, "gst", COMPANY, GSTIN, datetime.now(UTC))
    with pytest.raises(CertificateCheckError):
        verify_issued_certificate(
            signed_pan(key, certificate, status="I"),
            certificate,
            "pan",
            "Example Person",
            "ABCDE1234F",
            datetime.now(UTC),
        )


@pytest.mark.parametrize(
    "change",
    ["tampered", "wrong_holder", "wrong_number", "wrong_issuer", "untrusted_signer", "unsigned"],
)
def test_forged_or_unrelated_documents_are_not_verified(signer, change):
    key, certificate = signer
    document = signed_gst(key, certificate)
    name, number = COMPANY, GSTIN
    if change == "tampered":
        document = document.replace(b"Example Supplies", b"Attacker Supplies")
    elif change == "wrong_holder":
        name = "Unrelated Company"
    elif change == "wrong_number":
        number = "29ABCDE1234F1Z5"
    elif change == "wrong_issuer":
        document = signed_gst(key, certificate, issuer="Untrusted Upload Portal")
    elif change == "untrusted_signer":
        other_key, other_certificate = signing_material()
        document = signed_gst(other_key, other_certificate)
    else:
        document = b'<Certificate type="GSTND" number="27ABCDE1234F1Z5"/>'
    with pytest.raises(CertificateCheckError):
        verify_issued_certificate(document, certificate, "gst", name, number, datetime.now(UTC))


def test_self_uploaded_xml_cannot_resolve_external_entities(signer):
    with pytest.raises(CertificateCheckError):
        verify_issued_certificate(
            b'<!DOCTYPE Certificate [<!ENTITY secret SYSTEM "file:///etc/passwd">]><Certificate>&secret;</Certificate>',
            signer[1],
            "gst",
            COMPANY,
            GSTIN,
            datetime.now(UTC),
        )


@pytest.mark.parametrize("status", ["Cancelled", "Suspended", None])
def test_inactive_gst_is_not_verified(status):
    with pytest.raises(CertificateCheckError):
        verify_gst_registration(
            {"status_cd": "1", "data": {"gstin": GSTIN, "lgnm": COMPANY, "sts": status}},
            COMPANY,
            GSTIN,
        )


def test_self_declared_certificate_cannot_pass_readiness():
    finding = evaluate_condition(
        {"type": "certificate", "certificate": "gst", "quote": "GST required", "page": 1},
        {"certificates": {"gst": True}},
        datetime.now(UTC),
    )
    assert finding["status"] == "review"


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/a.xml",
        "https://169.254.169.254/a.xml",
        "https://attacker.test/a.xml",
        "https://bucket.s3.ap-south-1.amazonaws.com.attacker.test/a.xml",
        "https://user:pass@bucket.s3.ap-south-1.amazonaws.com/a.xml",
    ],
)
def test_document_urls_cannot_target_private_or_off_provider_hosts(url):
    with pytest.raises(AppError):
        validate_document_url(url)


def test_safe_provider_urls():
    url = "https://bucket.s3.ap-south-1.amazonaws.com/file.xml?signature=test"
    assert validate_document_url(url) == url
    assert validate_authorization_url(
        "https://entity.digilocker.gov.in/public/oauth2/1/authorize", "entitylocker"
    )


def test_client_cannot_submit_verified_status():
    with pytest.raises(ValidationError):
        VerificationStartRequest.model_validate(
            {
                "kind": "gst",
                "subjectName": COMPANY,
                "documentNumber": GSTIN,
                "consent": True,
                "requestKey": "00000000-0000-4000-8000-000000000001",
                "status": "verified",
            }
        )


@pytest.mark.asyncio
async def test_sandbox_authentication_and_session_contract(tmp_path, signer):
    path = tmp_path / "issuer.pem"
    path.write_bytes(signer[1])
    settings = Settings(
        _env_file=None,
        SANDBOX_API_KEY=SecretStr("key_test_fixture"),
        SANDBOX_API_SECRET=SecretStr("secret_test_fixture"),
        SANDBOX_RETURN_URL="https://example.test/dashboard/profile",
        DIGILOCKER_SIGNING_CERTIFICATE_PATH=str(path),
        ENTITYLOCKER_SIGNING_CERTIFICATE_PATH=str(path),
    )
    client = SandboxClient(settings)
    with respx.mock as mock:
        auth = mock.post("https://test-api.sandbox.co.in/authenticate").respond(
            200, json={"code": 200, "data": {"access_token": "provider-test-token"}}
        )
        session = mock.post(
            "https://test-api.sandbox.co.in/kyc/entitylocker/sessions/init"
        ).respond(
            200,
            json={
                "code": 200,
                "data": {
                    "session_id": "00000000-0000-4000-8000-000000000001",
                    "authorization_url": "https://entity.digilocker.gov.in/public/oauth2/1/authorize",
                },
            },
        )
        await client.initiate("entitylocker", settings.SANDBOX_RETURN_URL, 2000000000000, "signin")
        assert auth.calls[0].request.headers["x-api-secret"] == "secret_test_fixture"
        assert session.calls[0].request.headers["authorization"] == "provider-test-token"
        assert "x-api-secret" not in session.calls[0].request.headers
        assert "consent_expiry" in session.calls[0].request.content.decode()
    settings.SANDBOX_API_SECRET = settings.SANDBOX_API_KEY
    assert not configuration_ready(settings)


@pytest.mark.asyncio
async def test_provider_authentication_errors_do_not_disclose_credentials(tmp_path, signer):
    path = tmp_path / "issuer.pem"
    path.write_bytes(signer[1])
    settings = Settings(
        _env_file=None,
        SANDBOX_API_KEY=SecretStr("key_test_fixture"),
        SANDBOX_API_SECRET=SecretStr("secret_test_fixture"),
        SANDBOX_RETURN_URL="https://example.test/profile",
        DIGILOCKER_SIGNING_CERTIFICATE_PATH=str(path),
    )
    with respx.mock as mock:
        mock.post("https://test-api.sandbox.co.in/authenticate").mock(
            return_value=httpx.Response(401, json={"message": "secret_test_fixture"})
        )
        with pytest.raises(AppError) as error:
            await SandboxClient(settings).session_status("entitylocker", "session")
    assert "secret_test_fixture" not in error.value.message


@pytest.mark.asyncio
async def test_digilocker_consent_can_start_without_issuer_certificate():
    settings = Settings(
        _env_file=None,
        SANDBOX_API_KEY=SecretStr("key_test_fixture"),
        SANDBOX_API_SECRET=SecretStr("secret_test_fixture"),
        SANDBOX_RETURN_URL="https://example.test/callback",
    )
    assert configuration_ready(settings, "digilocker")
    with respx.mock as mock:
        mock.post("https://test-api.sandbox.co.in/authenticate").respond(
            200, json={"code": 200, "data": {"access_token": "provider-test-token"}}
        )
        session = mock.post("https://test-api.sandbox.co.in/kyc/digilocker/sessions/init").respond(
            200,
            json={
                "code": 200,
                "data": {
                    "session_id": "00000000-0000-4000-8000-000000000001",
                    "authorization_url": "https://digilocker.meripehchaan.gov.in/public/oauth2/1/authorize",
                },
            },
        )
        session_id, url = await SandboxClient(settings).initiate(
            "digilocker", settings.SANDBOX_RETURN_URL, 2000000000000, "signin"
        )
    assert session_id == "00000000-0000-4000-8000-000000000001"
    assert url.startswith("https://digilocker.meripehchaan.gov.in/")
    payload = json.loads(session.calls[0].request.content)
    assert payload["doc_types"] == ["pan"]
    assert payload["consent_expiry"] == 2000000000000


@pytest.mark.parametrize(
    "url", ["", "http://localhost:3000/profile", "https://user:pass@example.test/profile"]
)
def test_digilocker_consent_requires_https_callback(url):
    settings = Settings(
        _env_file=None,
        SANDBOX_API_KEY=SecretStr("key_test_fixture"),
        SANDBOX_API_SECRET=SecretStr("secret_test_fixture"),
        SANDBOX_RETURN_URL=url,
    )
    assert not configuration_ready(settings, "digilocker")


@pytest.mark.parametrize(
    "url", ["http://attacker.test/profile", "http://user:pass@localhost/profile"]
)
def test_demo_callback_cannot_redirect_to_an_arbitrary_host(url):
    with pytest.raises(ValueError):
        callback_handler(url)
