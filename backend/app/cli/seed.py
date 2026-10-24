"""Database seed utility for default sources and sample demo data."""

import asyncio
import hashlib
from datetime import UTC, datetime

from app.core.logging import get_logger, setup_logging
from app.database import async_session_factory
from app.models.models import Condition, Tender, TenderSnapshot
from app.repositories.sources import upsert_source
from app.sources.iiitd import APPROVED_HOSTS, SOURCE_ID, SOURCE_NAME, START_URL

logger = get_logger("seed")

SAMPLE_NOTICES = [
    {
        "ref": "IIITD/S&P/2026/01",
        "title": "Supply and Installation of Campus High-Performance Compute Cluster",
        "desc": "High-performance GPU cluster with InfiniBand networking for AI research labs.",
        "issuer": "IIIT-Delhi",
        "cat": "Electronics",
        "val": "₹45,00,000",
        "deadline_text": "06-11-2026 15:00 IST",
        "deadline_dt": datetime(2026, 11, 6, 15, 0, 0, tzinfo=UTC),
        "source_url": "https://iiitd.ac.in/tenders/hpc-cluster-2026",
        "conditions": [
            {
                "type": "turnover",
                "label": "Annual Turnover",
                "requirement": "Average annual turnover of at least ₹35,00,000 across 2023–24, 2024–25, and 2025–26.",
                "clause": "Clause 3.1",
                "page": 2,
                "quote": "The bidder must have an average annual financial turnover of at least ₹35 Lakh during the last three financial years.",
                "threshold": 3500000.0,
                "years": ["2023–24", "2024–25", "2025–26"],
            },
            {
                "type": "experience",
                "label": "Past Performance",
                "requirement": "Declared completion of at least 3 supply orders of similar scale.",
                "clause": "Clause 3.2",
                "page": 3,
                "quote": "Bidder should have successfully executed at least 3 completed supply orders for similar hardware equipment.",
                "threshold": 3.0,
            },
            {
                "type": "certificate",
                "label": "GST Registration",
                "requirement": "Valid GST registration certificate.",
                "clause": "Clause 4.1",
                "page": 4,
                "quote": "The tenderer must submit a self-attested copy of valid GST registration certificate.",
                "cert": "gst",
            },
            {
                "type": "deposit",
                "label": "Earnest Money Deposit (EMD)",
                "requirement": "Earnest Money Deposit of ₹50,000.",
                "clause": "Clause 5.1",
                "page": 5,
                "quote": "An Earnest Money Deposit (EMD) of ₹50,000 must be deposited with the tender.",
                "threshold": 50000.0,
            },
            {
                "type": "deadline",
                "label": "Submission Deadline",
                "requirement": "Bids must be submitted before 06-11-2026 15:00 IST.",
                "clause": "Clause 1.2",
                "page": 1,
                "quote": "Last date and time for online submission of technical and commercial bids is 06-11-2026 up to 15:00 IST.",
                "deadline": datetime(2026, 11, 6, 15, 0, 0, tzinfo=UTC),
            },
        ],
    },
    {
        "ref": "IIITD/IT/2026/14",
        "title": "Annual Maintenance Contract for Campus Core Switches",
        "desc": "Comprehensive 24x7 AMC for Arista core and distribution switches.",
        "issuer": "IIIT-Delhi",
        "cat": "IT Services",
        "val": "₹18,00,000",
        "deadline_text": "12-11-2026 14:00 IST",
        "deadline_dt": datetime(2026, 11, 12, 14, 0, 0, tzinfo=UTC),
        "source_url": "https://iiitd.ac.in/tenders/networking-amc-2026",
        "conditions": [
            {
                "type": "turnover",
                "label": "Turnover",
                "requirement": "Average turnover of at least ₹15,00,000.",
                "clause": "Clause 2.1",
                "page": 2,
                "quote": "Average turnover of at least ₹15 Lakh for the last 3 financial years.",
                "threshold": 1500000.0,
                "years": ["2023–24", "2024–25", "2025–26"],
            },
            {
                "type": "experience",
                "label": "Experience",
                "requirement": "Completed at least 2 network AMC contracts.",
                "clause": "Clause 2.2",
                "page": 2,
                "quote": "Completed at least 2 network AMC contracts in universities or institutes.",
                "threshold": 2.0,
            },
            {
                "type": "certificate",
                "label": "ISO 9001",
                "requirement": "Valid ISO 9001 quality management certification.",
                "clause": "Clause 4.2",
                "page": 4,
                "quote": "The vendor must hold valid ISO 9001 certification at the time of bid submission.",
                "cert": "iso",
            },
            {
                "type": "deposit",
                "label": "EMD",
                "requirement": "EMD of ₹25,000.",
                "clause": "Clause 5.1",
                "page": 5,
                "quote": "EMD of ₹25,000 is required.",
                "threshold": 25000.0,
            },
            {
                "type": "deadline",
                "label": "Deadline",
                "requirement": "Submission deadline 12-11-2026 14:00 IST.",
                "clause": "Clause 1.1",
                "page": 1,
                "quote": "Tenders must be uploaded before 12-11-2026 14:00 IST.",
                "deadline": datetime(2026, 11, 12, 14, 0, 0, tzinfo=UTC),
            },
        ],
    },
]


async def seed_database() -> None:
    setup_logging()
    logger.info("Starting database seeding...")

    async with async_session_factory() as db:
        # Seed Source
        await upsert_source(
            db,
            source_id=SOURCE_ID,
            name=SOURCE_NAME,
            start_url=START_URL,
            approved_hosts=APPROVED_HOSTS,
        )

        # Seed Sample Notices
        now = datetime.now(UTC)
        for s in SAMPLE_NOTICES:
            tender = Tender(
                source_id=SOURCE_ID,
                external_reference=s["ref"],
                title=s["title"],
                description=s["desc"],
                issuer=s["issuer"],
                category=s["cat"],
                estimated_value=s["val"],
                deadline_text=s["deadline_text"],
                deadline_at=s["deadline_dt"],
                source_url=s["source_url"],
                provenance="sample",
                amended=False,
                created_at=now,
                updated_at=now,
            )
            db.add(tender)
            await db.flush()

            # Snapshot
            snap = TenderSnapshot(
                tender_id=tender.id,
                snapshot_fingerprint=hashlib.sha256(s["ref"].encode()).hexdigest()[:16],
                is_current=True,
                created_at=now,
            )
            db.add(snap)
            await db.flush()

            for c in s["conditions"]:
                cond = Condition(
                    snapshot_id=snap.id,
                    type=c["type"],
                    label=c["label"],
                    requirement=c["requirement"],
                    clause_reference=c["clause"],
                    page_number=c["page"],
                    exact_quote=c["quote"],
                    threshold_amount=c.get("threshold"),
                    years=c.get("years"),
                    certificate_type=c.get("cert"),
                    deadline_timestamp=c.get("deadline"),
                    mandatory=True,
                    created_at=now,
                )
                db.add(cond)

        await db.commit()
        logger.info("Database seeding completed successfully.")


if __name__ == "__main__":
    asyncio.run(seed_database())
