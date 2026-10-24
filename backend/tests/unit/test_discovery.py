"""Source validation and the live TinyFish request contract."""

import json
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import respx

from app.integrations import tinyfish_client
from app.sources.iiitd import START_URL, validate_discovery_result


def real_result():
    path = Path(__file__).resolve().parents[3] / "frontend/lib/data/iiitd-tenders.json"
    return json.loads(path.read_text())["result"]


def test_real_source_snapshot_validates():
    result = real_result()
    assert validate_discovery_result(result) == result["notices"]


@pytest.mark.parametrize(
    "result",
    [
        None,
        {},
        {"outcome": "failed", "notices": []},
        {"outcome": "success", "notices": []},
        {"outcome": "no_matches", "notices": [{}]},
    ],
)
def test_failed_or_inconsistent_results_rejected(result):
    with pytest.raises(ValueError):
        validate_discovery_result(result)


def test_no_matches_does_not_create_sample_notices():
    assert validate_discovery_result({"outcome": "no_matches", "notices": []}) == []


@pytest.mark.parametrize(
    "url",
    [
        "http://iiitd.ac.in/test.pdf",
        "https://iiitd.ac.in.evil.test/test.pdf",
        "https://user:pass@iiitd.ac.in/test.pdf",
        "https://iiitd.ac.in:8443/test.pdf",
    ],
)
def test_off_source_document_urls_rejected(url):
    result = real_result()
    result["notices"][0]["pdf_urls"] = [url]
    with pytest.raises(ValueError):
        validate_discovery_result(result)


def test_duplicate_source_references_rejected():
    result = real_result()
    result["notices"][1]["notice_id"] = result["notices"][0]["notice_id"]
    with pytest.raises(ValueError):
        validate_discovery_result(result)


@pytest.mark.asyncio
async def test_live_request_supplies_url_schema_and_duration(monkeypatch):
    monkeypatch.setattr(
        tinyfish_client,
        "get_settings",
        lambda: SimpleNamespace(
            TINYFISH_MODE="live",
            TINYFISH_API_KEY="test-key",
            TINYFISH_BASE_URL="https://agent.tinyfish.ai",
            TINYFISH_MAX_DURATION_SECONDS=300,
        ),
    )
    with respx.mock as mock:
        route = mock.post("https://agent.tinyfish.ai/v1/automation/run-async").mock(
            return_value=httpx.Response(200, json={"run_id": "test-run", "status": "PENDING"})
        )
        response = await tinyfish_client.TinyFishClient().submit(
            "Read source notices.", "correlation-1"
        )
    payload = json.loads(route.calls[0].request.content)
    assert response["run_id"] == "test-run"
    assert payload["url"] == START_URL
    assert payload["output_schema"] == tinyfish_client.TINYFISH_DISCOVERY_SCHEMA
    assert payload["agent_config"]["max_duration_seconds"] == 300
    assert "correlation-1" in payload["goal"]
