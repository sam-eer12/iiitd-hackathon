"""Safe document downloader with SSRF protection, host allowlisting, and size bounds."""

import ipaddress
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.errors import AppError, PayloadTooLargeError

DEFAULT_APPROVED_HOSTS = [
    "iiitd.ac.in",
    "www.iiitd.ac.in",
    "tenderlens.local",
]


def validate_url_and_host(url: str, approved_hosts: list[str] | None = None) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname == "tenderlens.local"
    ):
        raise AppError(
            "INVALID_URL_SCHEME", "Only HTTPS URLs are permitted for document downloads."
        )

    if parsed.username or parsed.password:
        raise AppError(
            "EMBEDDED_CREDENTIALS", "URLs containing embedded credentials are not allowed."
        )

    hostname = parsed.hostname
    if not hostname:
        raise AppError("MISSING_HOSTNAME", "Invalid URL: missing hostname.")

    allowed = approved_hosts if approved_hosts is not None else DEFAULT_APPROVED_HOSTS
    if hostname.lower() not in [h.lower() for h in allowed]:
        raise AppError(
            "UNAPPROVED_HOST", f"Host '{hostname}' is not in the approved download allowlist."
        )

    # Check for IP address literals to prevent SSRF
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise AppError(
                "FORBIDDEN_DESTINATION", "Private or loopback IP addresses are strictly forbidden."
            )
    except ValueError:
        # Not an IP literal, it's a domain name
        pass


async def download_document(
    url: str,
    approved_hosts: list[str] | None = None,
    max_bytes: int | None = None,
    timeout_seconds: float = 30.0,
) -> bytes:
    validate_url_and_host(url, approved_hosts)
    settings = get_settings()
    byte_limit = max_bytes or settings.MAX_PDF_BYTES

    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    timeout = httpx.Timeout(timeout_seconds, connect=10.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout, follow_redirects=True) as client:
        try:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    raise AppError(
                        "DOWNLOAD_HTTP_ERROR",
                        f"Failed to fetch document: HTTP {response.status_code}",
                        status_code=502,
                    )

                # Check Content-Length if present
                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > byte_limit:
                    raise PayloadTooLargeError(
                        f"Document size exceeds maximum allowed limit of {byte_limit} bytes."
                    )

                chunks: list[bytes] = []
                total_bytes = 0
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    total_bytes += len(chunk)
                    if total_bytes > byte_limit:
                        raise PayloadTooLargeError(
                            f"Document size exceeds maximum allowed limit of {byte_limit} bytes."
                        )
                    chunks.append(chunk)

                data = b"".join(chunks)

                # Verify PDF magic signature (%PDF-)
                if not data.startswith(b"%PDF-"):
                    raise AppError(
                        "INVALID_PDF_FORMAT",
                        "The downloaded document does not have a valid PDF header.",
                    )

                return data

        except httpx.RequestError as exc:
            raise AppError(
                "DOWNLOAD_NETWORK_ERROR",
                f"Network error during document download: {exc}",
                status_code=502,
            )
