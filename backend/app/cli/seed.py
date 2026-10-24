"""Idempotently register official sources without creating synthetic tenders."""

import asyncio

from app.core.logging import get_logger, setup_logging
from app.database import async_session_factory
from app.repositories.sources import upsert_source
from app.sources.iiitd import APPROVED_HOSTS, SOURCE_ID, SOURCE_NAME, START_URL

logger = get_logger("seed")


async def seed_database() -> None:
    setup_logging()
    async with async_session_factory() as db:
        await upsert_source(
            db,
            source_id=SOURCE_ID,
            name=SOURCE_NAME,
            start_url=START_URL,
            approved_hosts=APPROVED_HOSTS,
        )
        await db.commit()
    logger.info("Official sources registered. Run a TinyFish refresh to collect real notices.")


if __name__ == "__main__":
    asyncio.run(seed_database())
