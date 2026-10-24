"""Sandbox's documented consent APIs. Credentials and downloaded documents stay server-side."""

import logging
import re
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import httpx

from app.core.config import Settings, get_settings
from app.core.errors import AppError, ServiceUnavailableError

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024

# HTTP request logs can otherwise expose short-lived signed document URLs.
logging.getLogger("httpx").setLevel(logging.WARNING)


def signing_certificate_path(settings: Settings, provider: str) -> str | None:
    return (
        settings.ENTITYLOCKER_SIGNING_CERTIFICATE_PATH
        if provider == "entitylocker"
        else settings.DIGILOCKER_SIGNING_CERTIFICATE_PATH
    )


def configuration_ready(settings: Settings, provider: str | None = None) -> bool:
    key = settings.SANDBOX_API_KEY.get_secret_value() if settings.SANDBOX_API_KEY else ""
    secret = settings.SANDBOX_API_SECRET.get_secret_value() if settings.SANDBOX_API_SECRET else ""
    try:
        url = urlparse(settings.SANDBOX_RETURN_URL or "")
        valid_url = (
            url.scheme == "https"
            and bool(url.hostname)
            and not url.username
            and not url.password
            and not url.query
            and not url.fragment
        )
        paths = (
            [signing_certificate_path(settings, provider)]
            if provider
            else [
                settings.DIGILOCKER_SIGNING_CERTIFICATE_PATH,
                settings.ENTITYLOCKER_SIGNING_CERTIFICATE_PATH,
            ]
        )
        return bool(
            key
            and secret
            and key != secret
            and key.startswith(f"key_{settings.SANDBOX_ENVIRONMENT}_")
            and valid_url
            and any(path and Path(path).is_file() for path in paths)
        )
    except (ValueError, OSError):
        return False


def validate_authorization_url(url: str, provider: str) -> str:
    parsed = urlparse(url)
    hosts = (
        {"entity.digilocker.gov.in"}
        if provider == "entitylocker"
        else {"digilocker.meripehchaan.gov.in", "digilocker.gov.in", "api.digitallocker.gov.in"}
    )
    if (
        parsed.scheme != "https"
        or parsed.hostname not in hosts
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ServiceUnavailableError("The provider returned an unrecognized consent destination.")
    return url


def validate_document_url(url: str) -> str:
    parsed = urlparse(url)
    # Only provider-returned S3 objects are accepted, never user-supplied URLs.
    if (
        parsed.scheme != "https"
        or not re.fullmatch(
            r"[a-z0-9][a-z0-9.-]*\.s3(?:[.-][a-z0-9-]+)?\.amazonaws\.com", parsed.hostname or ""
        )
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ServiceUnavailableError("The provider returned an unrecognized document location.")
    return url


class SandboxClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = (
            "https://api.sandbox.co.in"
            if settings.SANDBOX_ENVIRONMENT == "live"
            else "https://test-api.sandbox.co.in"
        )
        self._access_token: str | None = None
        self._token_expires = 0.0

    def require_configuration(self, provider: str | None = None) -> None:
        if not configuration_ready(self.settings, provider):
            raise AppError(
                "VERIFICATION_NOT_CONFIGURED",
                "Document verification needs separate Sandbox server credentials, an HTTPS return URL, and the trusted issuer signing certificate.",
                503,
            )

    async def _call(self, method: str, path: str, payload: dict | None = None) -> dict:
        self.require_configuration()
        key = self.settings.SANDBOX_API_KEY.get_secret_value()
        secret = self.settings.SANDBOX_API_SECRET.get_secret_value()
        try:
            async with httpx.AsyncClient(
                timeout=20, follow_redirects=False, trust_env=False
            ) as client:
                if self._access_token is None or time.monotonic() >= self._token_expires:
                    auth = await client.post(
                        f"{self.base_url}/authenticate",
                        headers={
                            "x-api-key": key,
                            "x-api-secret": secret,
                            "x-api-version": "1.0.0",
                        },
                    )
                    envelope = auth.json()
                    token = envelope.get("data", {}).get("access_token")
                    if (
                        auth.status_code != 200
                        or envelope.get("code") != 200
                        or not isinstance(token, str)
                        or not token
                    ):
                        raise AppError(
                            "SANDBOX_AUTHENTICATION_FAILED",
                            "Sandbox rejected the server credentials. Check the API key, separate API secret, and selected environment.",
                            503,
                        )
                    self._access_token = token
                    self._token_expires = time.monotonic() + 23 * 60 * 60
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    json=payload,
                    headers={
                        "authorization": self._access_token,
                        "x-api-key": key,
                        "x-api-version": "1.0.0",
                        "x-accept-cache": "false",
                    },
                )
                envelope = response.json()
                if response.status_code == 401:
                    self._access_token = None
                if response.status_code != 200 or envelope.get("code") != 200:
                    raise AppError(
                        "SANDBOX_REQUEST_FAILED",
                        "The issuer service could not complete this check. Confirm that the required Sandbox product and document consent are enabled.",
                        503,
                        retryable=True,
                    )
                data = envelope.get("data")
                if not isinstance(data, dict):
                    raise ValueError("Invalid provider response")
                return data
        except AppError:
            raise
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            raise ServiceUnavailableError(
                "The document provider could not be reached or returned an invalid response."
            ) from None

    async def initiate(
        self, provider: str, redirect_url: str, expires_at: int, flow: str
    ) -> tuple[str, str]:
        self.require_configuration(provider)
        payload = {
            "@entity": f"in.co.sandbox.kyc.{provider}.session.request",
            "flow": flow,
            "redirect_url": redirect_url,
        }
        if provider == "entitylocker":
            payload["consent_expiry"] = expires_at
        else:
            payload["doc_types"] = ["pan"]
        data = await self._call("POST", f"/kyc/{provider}/sessions/init", payload)
        try:
            session_id = str(UUID(data["session_id"]))
            url = validate_authorization_url(data["authorization_url"], provider)
        except (KeyError, ValueError, TypeError):
            raise ServiceUnavailableError(
                "The provider returned an invalid verification session."
            ) from None
        return session_id, url

    async def session_status(self, provider: str, session_id: str) -> dict:
        return await self._call("GET", f"/kyc/{provider}/sessions/{session_id}/status")

    async def gst_registration(self, gstin: str) -> dict:
        return await self._call("POST", "/gst/compliance/public/gstin/search", {"gstin": gstin})

    async def document(self, provider: str, session_id: str, document_type: str) -> bytes:
        data = await self._call(
            "GET", f"/kyc/{provider}/sessions/{session_id}/documents/{document_type}"
        )
        files = data.get("files")
        if not isinstance(files, list) or not 1 <= len(files) <= 5:
            raise ServiceUnavailableError("No issuer document was returned for verification.")
        document = next(
            (
                f
                for f in files
                if isinstance(f, dict)
                and isinstance(f.get("metadata"), dict)
                and isinstance(f["metadata"].get("ContentType"), str)
                and f.get("metadata", {}).get("ContentType", "").split(";")[0]
                in {"application/xml", "text/xml"}
            ),
            None,
        )
        if document is None:
            raise AppError(
                "SIGNED_XML_REQUIRED",
                "A signed issuer XML document is required. A PDF or a self-uploaded scan cannot receive the verified badge.",
                422,
            )
        if (
            not isinstance(document.get("size"), int)
            or not 0 < document["size"] <= MAX_DOCUMENT_BYTES
        ):
            raise ServiceUnavailableError(
                "The issuer document exceeds the verification size limit."
            )
        try:
            url = validate_document_url(document["url"])
            async with httpx.AsyncClient(
                timeout=20, follow_redirects=False, trust_env=False
            ) as client:
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        raise ServiceUnavailableError(
                            "The issuer document is unavailable or its download link expired."
                        )
                    chunks = bytearray()
                    async for chunk in response.aiter_bytes():
                        chunks.extend(chunk)
                        if len(chunks) > MAX_DOCUMENT_BYTES:
                            raise ServiceUnavailableError(
                                "The issuer document exceeds the verification size limit."
                            )
                    return bytes(chunks)
        except AppError:
            raise
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise ServiceUnavailableError("The issuer document could not be retrieved.") from None


@lru_cache
def get_sandbox_client() -> SandboxClient:
    return SandboxClient(get_settings())
