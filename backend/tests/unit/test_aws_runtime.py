"""Deployment behavior: TLS, expiring IAM tokens and private S3 objects."""

import io
from unittest.mock import Mock

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.core.database import configure_iam_auth, connection_options
from app.integrations.storage import S3StorageBackend


def test_production_refuses_unverified_database_tls():
    with pytest.raises(ValueError, match="verified TLS"):
        connection_options(Settings(APP_ENV="production", DATABASE_SSL_CA_FILE=None))
    assert connection_options(Settings(APP_ENV="test", DATABASE_SSL_CA_FILE=None)) == {}


def test_rds_iam_tokens_are_generated_for_each_connection(monkeypatch):
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://tl_app@database.example:5432/tenderlens",
        DATABASE_IAM_AUTH=True,
        AWS_REGION="ap-south-1",
    )
    client = Mock()
    client.generate_db_auth_token.side_effect = ["short-lived-token-1", "short-lived-token-2"]
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: client)
    engine = create_async_engine(settings.DATABASE_URL)
    configure_iam_auth(engine, settings)
    first, second = {}, {}
    engine.sync_engine.dialect.dispatch.do_connect(None, None, [], first)
    engine.sync_engine.dialect.dispatch.do_connect(None, None, [], second)
    assert first["password"] != second["password"]
    assert client.generate_db_auth_token.call_count == 2
    client.generate_db_auth_token.assert_called_with(
        DBHostname="database.example", Port=5432, DBUsername="tl_app"
    )


@pytest.mark.asyncio
async def test_s3_storage_writes_reads_and_handles_missing_objects(monkeypatch):
    client = boto3.client(
        "s3", region_name="ap-south-1", aws_access_key_id="test", aws_secret_access_key="test"
    )
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: client)
    storage = S3StorageBackend("private-evidence", "ap-south-1")
    with Stubber(client) as stub:
        stub.add_response(
            "put_object", {}, {"Bucket": "private-evidence", "Key": "pdf/test.pdf", "Body": b"pdf"}
        )
        assert (
            await storage.save_file("pdf/test.pdf", b"pdf") == "s3://private-evidence/pdf/test.pdf"
        )
        stub.add_response(
            "get_object",
            {"Body": StreamingBody(io.BytesIO(b"pdf"), 3)},
            {"Bucket": "private-evidence", "Key": "pdf/test.pdf"},
        )
        assert await storage.get_file("pdf/test.pdf") == b"pdf"
        stub.add_client_error("head_object", service_error_code="404", http_status_code=404)
        assert not await storage.exists("pdf/missing.pdf")
        stub.add_client_error("get_object", service_error_code="NoSuchKey", http_status_code=404)
        with pytest.raises(FileNotFoundError):
            await storage.get_file("pdf/missing.pdf")


@pytest.mark.parametrize("key", ["../escape", "/absolute", "pdf/../../escape", "pdf\\escape", ""])
def test_s3_rejects_unsafe_object_keys(key):
    with pytest.raises(ValueError):
        S3StorageBackend._key(key)


def test_firebase_verifies_public_certificates_without_google_credentials(monkeypatch):
    import google.oauth2.id_token

    from app.core import auth

    settings = Settings(
        APP_ENV="production",
        FIREBASE_PROJECT_ID="test-project",
        GOOGLE_APPLICATION_CREDENTIALS=None,
        FIREBASE_AUTH_EMULATOR_HOST=None,
    )
    monkeypatch.setattr(auth, "get_settings", lambda: settings)
    verifier = Mock(
        return_value={"sub": "valid-user", "iss": "https://securetoken.google.com/test-project"}
    )
    monkeypatch.setattr(google.oauth2.id_token, "verify_firebase_token", verifier)
    assert auth.verify_id_token("signed-test-token").uid == "valid-user"
    assert verifier.call_args.kwargs["audience"] == "test-project"
    verifier.return_value = {"sub": "valid-user", "iss": "https://untrusted.example"}
    with pytest.raises(auth.AuthenticationError):
        auth.verify_id_token("wrong-issuer-token")
