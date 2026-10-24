"""Firebase ID token verification and authenticated principal definition."""

import os
from dataclasses import dataclass, field
from typing import Any

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.core.config import get_settings
from app.core.errors import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)

_firebase_app_initialized = False


def init_firebase_app() -> None:
    global _firebase_app_initialized
    if _firebase_app_initialized:
        return

    settings = get_settings()
    try:
        if settings.FIREBASE_AUTH_EMULATOR_HOST:
            os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = settings.FIREBASE_AUTH_EMULATOR_HOST

        if settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(
            settings.GOOGLE_APPLICATION_CREDENTIALS
        ):
            cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
            firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
        else:
            # Initialize with default options / emulator
            firebase_admin.initialize_app(options={"projectId": settings.FIREBASE_PROJECT_ID})
        _firebase_app_initialized = True
        logger.info("Firebase Admin initialized for project: %s", settings.FIREBASE_PROJECT_ID)
    except Exception as exc:
        logger.warning(
            "Could not initialize live Firebase Admin SDK (%s). Local/test mock available.", exc
        )
        _firebase_app_initialized = False


@dataclass
class Principal:
    uid: str
    email: str | None = None
    display_name: str | None = None
    claims: dict[str, Any] = field(default_factory=dict)


def verify_id_token(token: str) -> Principal:
    if not token or not token.strip():
        raise AuthenticationError("Authorization token required")

    settings = get_settings()

    # Support development/test tokens when running in dev or test mode
    if settings.APP_ENV in ("development", "test"):
        if token.startswith("dev_") or token.startswith("test_") or token == "sample_token":
            uid = token.split(":", 1)[1] if ":" in token else f"usr_{token}"
            return Principal(
                uid=uid,
                email=f"{uid}@example.com",
                display_name=f"User {uid}",
                claims={"sub": uid, "dev": True},
            )

    try:
        if settings.GOOGLE_APPLICATION_CREDENTIALS or settings.FIREBASE_AUTH_EMULATOR_HOST:
            init_firebase_app()
            decoded = firebase_auth.verify_id_token(token)
        else:
            # Public signing certificates verify Firebase ID tokens on AWS without
            # provisioning a Google service-account private key or Cloud SQL.
            from google.auth.transport.requests import Request
            from google.oauth2.id_token import verify_firebase_token

            decoded = verify_firebase_token(token, Request(), audience=settings.FIREBASE_PROJECT_ID)
            if (
                decoded.get("iss")
                != f"https://securetoken.google.com/{settings.FIREBASE_PROJECT_ID}"
            ):
                raise ValueError("Invalid Firebase token issuer")
            subject = decoded.get("sub")
            if not isinstance(subject, str) or not subject or len(subject) > 128:
                raise ValueError("Invalid Firebase token subject")
            decoded["uid"] = subject
        return Principal(
            uid=decoded["uid"],
            email=decoded.get("email"),
            display_name=decoded.get("name"),
            claims=decoded,
        )
    except Exception as exc:
        logger.warning("Token verification failed (%s)", type(exc).__name__)
        raise AuthenticationError("Token verification failed.") from exc
