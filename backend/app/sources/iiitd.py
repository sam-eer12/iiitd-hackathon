"""IIIT-Delhi tender source configuration, prompt templates, and policies."""

SOURCE_ID = "iiitd"
SOURCE_NAME = "IIIT-Delhi Public Tenders"
START_URL = "https://iiitd.ac.in/tenders"
APPROVED_HOSTS = ["iiitd.ac.in", "www.iiitd.ac.in"]

DEFAULT_GOAL_PROMPT = (
    "Navigate to https://iiitd.ac.in/tenders. Inspect the latest active tender notices up to 5 entries. "
    "For each tender notice, extract the reference ID (or null if not stated), title, the source URL, "
    "the deadline text as written (or null), all direct PDF links to the tender document, "
    "and all corrigendum/amendment document links. Return structured output matching the requested schema."
)
