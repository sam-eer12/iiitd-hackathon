"""IIIT-Delhi tender source configuration, prompt templates, and policies."""

from urllib.parse import urlparse

SOURCE_ID = "iiitd"
SOURCE_NAME = "IIIT-Delhi Public Tenders"
START_URL = "https://iiitd.ac.in/tenders"
APPROVED_HOSTS = ["iiitd.ac.in", "www.iiitd.ac.in"]

DEFAULT_GOAL_PROMPT = (
    "Navigate to https://iiitd.ac.in/tenders. Wait for the tender table to load, not just navigation. "
    "Inspect up to 5 of the most recent lab equipment, electronics or IT notices, prioritizing open deadlines. "
    "Preserve actual dates for any recently closed notices included. Use read-only navigation on approved hosts. "
    "For each tender notice, extract the reference ID (or null if not stated), title, the source URL, "
    "the deadline text as written (or null), all direct PDF links to the tender document, "
    "and all corrigendum/amendment document links. Return structured output matching the requested schema."
)


def validate_discovery_result(result: object) -> list[dict]:
    """Reject failed, fabricated-shape or off-source results before ingestion."""
    if not isinstance(result, dict) or result.get("outcome") not in {"success", "no_matches"}:
        raise ValueError("TinyFish could not inspect the public tender content.")
    notices = result.get("notices")
    if not isinstance(notices, list) or len(notices) > 5:
        raise ValueError("Expected at most five source notices.")
    if bool(notices) != (result["outcome"] == "success"):
        raise ValueError("Source outcome does not match the returned notice list.")
    seen = set()
    for notice in notices:
        if (
            not isinstance(notice, dict)
            or not isinstance(notice.get("title"), str)
            or not notice["title"].strip()
        ):
            raise ValueError("A notice title is missing or invalid.")
        for field in ("notice_id", "deadline_text"):
            if field not in notice or (
                notice[field] is not None and not isinstance(notice[field], str)
            ):
                raise ValueError(f"Invalid notice {field}.")
        urls = [notice.get("source_url")]
        for field in ("pdf_urls", "amendment_urls"):
            if not isinstance(notice.get(field), list):
                raise ValueError(f"Invalid notice {field}.")
            urls.extend(notice[field])
        for url in urls:
            if not isinstance(url, str):
                raise ValueError("Missing source URL.")
            parsed = urlparse(url)
            if (
                parsed.scheme != "https"
                or parsed.hostname not in APPROVED_HOSTS
                or parsed.username
                or parsed.password
                or parsed.port
            ):
                raise ValueError("Notice URL is outside the approved HTTPS source hosts.")
        identity = notice["notice_id"] or (notice["source_url"], notice["title"])
        if identity in seen:
            raise ValueError("Duplicate source notice.")
        seen.add(identity)
    return notices
