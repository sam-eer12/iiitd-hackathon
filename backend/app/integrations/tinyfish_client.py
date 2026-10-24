"""TinyFish Agent API adapter supporting live metered execution and deterministic fixture mode."""

import uuid
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import AppError, ServiceUnavailableError
from app.core.logging import get_logger
from app.sources.iiitd import START_URL

logger = get_logger(__name__)

TINYFISH_DISCOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {"type": "string", "enum": ["success", "no_matches", "failed"]},
        "failure_reason": {"type": "string", "nullable": True},
        "notices": {
            "type": "array",
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "notice_id": {"type": "string", "nullable": True},
                    "title": {"type": "string"},
                    "source_url": {"type": "string"},
                    "deadline_text": {"type": "string", "nullable": True},
                    "pdf_urls": {"type": "array", "items": {"type": "string"}},
                    "amendment_urls": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "notice_id",
                    "title",
                    "source_url",
                    "deadline_text",
                    "pdf_urls",
                    "amendment_urls",
                ],
            },
        },
    },
    "required": ["outcome", "failure_reason", "notices"],
}

FIXTURE_NOTICES = [
    {
        "notice_id": "IIITD/S&P/2026/01",
        "title": "Supply and Installation of Campus High-Performance Compute Cluster",
        "source_url": "https://iiitd.ac.in/tenders/hpc-cluster-2026",
        "deadline_text": "06-11-2026 15:00 IST",
        "pdf_urls": ["https://iiitd.ac.in/sites/default/files/tenders/hpc_specifications.pdf"],
        "amendment_urls": [
            "https://iiitd.ac.in/sites/default/files/tenders/corrigendum_hpc_extension.pdf"
        ],
    },
    {
        "notice_id": "IIITD/IT/2026/14",
        "title": "Annual Maintenance Contract for Campus Networking and Core Switches",
        "source_url": "https://iiitd.ac.in/tenders/networking-amc-2026",
        "deadline_text": "12-11-2026 14:00 IST",
        "pdf_urls": ["https://iiitd.ac.in/sites/default/files/tenders/networking_amc.pdf"],
        "amendment_urls": [],
    },
    {
        "notice_id": "IIITD/EST/2026/08",
        "title": "Comprehensive Facility Management and Housekeeping Services",
        "source_url": "https://iiitd.ac.in/tenders/facility-mgmt-2026",
        "deadline_text": "15-11-2026 17:00 IST",
        "pdf_urls": ["https://iiitd.ac.in/sites/default/files/tenders/housekeeping_rfp.pdf"],
        "amendment_urls": [],
    },
]


class TinyFishClient:
    def __init__(self):
        self.settings = get_settings()
        self.mode = self.settings.TINYFISH_MODE
        self.api_key = self.settings.TINYFISH_API_KEY
        self.base_url = self.settings.TINYFISH_BASE_URL.rstrip("/")

        # Memory store for fixture runs
        self._fixture_runs: dict[str, dict[str, Any]] = {}

    async def submit(self, goal: str, correlation_marker: str) -> dict[str, Any]:
        """Submit an async automation run to TinyFish."""
        if self.mode == "fixture":
            run_id = f"fix_tf_{uuid.uuid4().hex[:12]}"
            self._fixture_runs[run_id] = {
                "run_id": run_id,
                "correlation_marker": correlation_marker,
                "status": "COMPLETED",
                "result": {
                    "outcome": "success",
                    "failure_reason": None,
                    "notices": FIXTURE_NOTICES,
                },
                "error": None,
            }
            logger.info("Created fixture TinyFish run: %s", run_id)
            return {"run_id": run_id, "status": "COMPLETED"}

        if not self.api_key:
            raise AppError(
                "MISSING_TINYFISH_KEY",
                "TINYFISH_API_KEY is required for live collection mode.",
                status_code=500,
            )

        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "url": START_URL,
            "goal": f"{goal} Correlation marker: {correlation_marker}",
            "browser_profile": "lite",
            "output_schema": TINYFISH_DISCOVERY_SCHEMA,
            "agent_config": {"max_duration_seconds": self.settings.TINYFISH_MAX_DURATION_SECONDS},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/v1/automation/run-async",
                    json=payload,
                    headers=headers,
                )
                if resp.status_code in (401, 403):
                    raise AppError(
                        "TINYFISH_AUTH_FAILED",
                        "TinyFish API rejected credentials.",
                        status_code=502,
                    )
                if resp.status_code == 429:
                    raise AppError(
                        "TINYFISH_RATE_LIMIT",
                        "TinyFish rate limit exceeded.",
                        status_code=429,
                        retryable=True,
                    )
                if resp.status_code >= 400:
                    raise AppError(
                        "TINYFISH_SUBMIT_FAILED",
                        f"TinyFish error: HTTP {resp.status_code}",
                        status_code=502,
                    )

                data = resp.json()
                return {
                    "run_id": data.get("run_id") or data.get("id"),
                    "status": data.get("status", "PENDING"),
                }
            except httpx.RequestError as exc:
                raise ServiceUnavailableError(f"Network error connecting to TinyFish: {exc}")

    async def get_run(self, run_id: str) -> dict[str, Any]:
        """Check status and retrieve result of an active or finished run."""
        if self.mode == "fixture":
            if run_id in self._fixture_runs:
                return self._fixture_runs[run_id]
            # Return standard completed fixture
            return {
                "run_id": run_id,
                "status": "COMPLETED",
                "result": {
                    "outcome": "success",
                    "failure_reason": None,
                    "notices": FIXTURE_NOTICES,
                },
                "error": None,
            }

        headers = {"X-API-Key": self.api_key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(f"{self.base_url}/v1/runs/{run_id}", headers=headers)
                if resp.status_code != 200:
                    raise AppError(
                        "TINYFISH_POLL_FAILED",
                        f"Failed to check run status: HTTP {resp.status_code}",
                        status_code=502,
                    )
                data = resp.json()
                return {
                    "run_id": run_id,
                    "status": data.get("status", "PENDING"),
                    "result": data.get("result"),
                    "error": data.get("error"),
                }
            except httpx.RequestError as exc:
                raise ServiceUnavailableError(f"Network error polling TinyFish: {exc}")

    async def cancel(self, run_id: str) -> dict[str, Any]:
        """Cancel an ongoing run."""
        if self.mode == "fixture":
            if run_id in self._fixture_runs:
                self._fixture_runs[run_id]["status"] = "CANCELLED"
            return {"run_id": run_id, "status": "CANCELLED"}

        headers = {"X-API-Key": self.api_key}
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}/v1/runs/{run_id}/cancel", headers=headers
                )
                return {
                    "run_id": run_id,
                    "status": "CANCELLED" if resp.status_code == 200 else "RUNNING",
                }
            except httpx.RequestError:
                return {"run_id": run_id, "status": "CANCEL_UNKNOWN"}


_tinyfish_client_instance: TinyFishClient | None = None


def get_tinyfish_client() -> TinyFishClient:
    global _tinyfish_client_instance
    if _tinyfish_client_instance is None:
        _tinyfish_client_instance = TinyFishClient()
    return _tinyfish_client_instance
