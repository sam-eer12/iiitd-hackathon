"""Sources and policies package."""

from app.sources.iiitd import APPROVED_HOSTS, DEFAULT_GOAL_PROMPT, SOURCE_ID, SOURCE_NAME, START_URL
from app.sources.policies import enforce_approved_source_url

__all__ = [
    "APPROVED_HOSTS",
    "DEFAULT_GOAL_PROMPT",
    "SOURCE_ID",
    "SOURCE_NAME",
    "START_URL",
    "enforce_approved_source_url",
]
