"""Shared RDS TLS and per-connection IAM authentication for API, worker and migrations."""

import ssl

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings


def connection_options(settings: Settings) -> dict:
    if settings.DATABASE_SSL_CA_FILE:
        return {"ssl": ssl.create_default_context(cafile=settings.DATABASE_SSL_CA_FILE)}
    if settings.APP_ENV == "production":
        raise ValueError("Production PostgreSQL requires DATABASE_SSL_CA_FILE for verified TLS.")
    return {}


def configure_iam_auth(engine: AsyncEngine, settings: Settings) -> None:
    if not settings.DATABASE_IAM_AUTH:
        return
    import boto3

    url = make_url(settings.DATABASE_URL)
    if not settings.AWS_REGION or not url.host or not url.username:
        raise ValueError("RDS IAM authentication requires AWS_REGION, database host and username.")
    client = boto3.client("rds", region_name=settings.AWS_REGION)

    @event.listens_for(engine.sync_engine, "do_connect")
    def provide_token(dialect, connection_record, args, kwargs):
        # Tokens expire after 15 minutes. Generate one for each new connection,
        # rather than fixing a token in DATABASE_URL at process startup.
        kwargs["password"] = client.generate_db_auth_token(
            DBHostname=url.host,
            Port=url.port or 5432,
            DBUsername=url.username,
        )
