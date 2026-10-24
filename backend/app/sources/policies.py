"""Source policies and host allowlist enforcement."""

from urllib.parse import urlparse

from app.core.errors import AppError
from app.sources.iiitd import APPROVED_HOSTS


def enforce_approved_source_url(url: str, allowed_hosts: list[str] | None = None) -> str:
    if not url or not isinstance(url, str):
        raise AppError("INVALID_SOURCE_URL", "A source URL is missing or invalid.")

    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise AppError("INVALID_SOURCE_SCHEME", "Source URL must use HTTPS.")

    if parsed.username or parsed.password or parsed.port:
        raise AppError(
            "INVALID_SOURCE_CREDENTIALS", "Source URL cannot include credentials or custom ports."
        )

    hosts = allowed_hosts if allowed_hosts is not None else APPROVED_HOSTS
    if not parsed.hostname or parsed.hostname.lower() not in [h.lower() for h in hosts]:
        raise AppError(
            "UNAPPROVED_SOURCE_HOST", f"Source URL host '{parsed.hostname}' is not approved."
        )

    return url
