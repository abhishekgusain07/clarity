"""VCR configuration for agent tests.

Records real LLM + MCP responses on first run; replays them afterward.
Filters sensitive headers so cassettes are safe to commit.
"""
from pathlib import Path

import pytest


@pytest.fixture
def vcr_config():
    return {
        "filter_headers": [
            "authorization",
            "x-api-key",
            "anthropic-api-key",
            "cookie",
        ],
        "filter_query_parameters": [
            "api_key",
            "token",
        ],
        "match_on": ["method", "scheme", "host", "port", "path", "query"],
        "record_mode": "once",
    }


@pytest.fixture
def vcr_cassette_dir(request):
    return str(Path(__file__).parent / "cassettes")
