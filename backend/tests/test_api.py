"""Integration tests for the FastAPI routes.

Uses httpx.AsyncClient + ASGITransport (no live server needed).
Mocks analyse_ticker to avoid real HTTP calls in CI.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock


_MOCK_RESULT = {
    "ticker": "TSLA",
    "verdict": "BUY",
    "confidence_score": 65.0,
    "verdict_reasons": ["71% of articles are bullish"],
    "stats": {"bullish": 7, "bearish": 2, "neutral": 1},
    "top_comments": [],
    "stock_info": {"name": "Tesla Inc.", "sector": "Consumer Cyclical", "current_price": 250.0},
    "advanced_stats": None,
    "trend": {
        "direction": "new", "sentiment_delta": 0.0, "confidence_delta": 0.0,
        "prev_verdict": None, "verdict_changed": False,
    },
    "source_contributions": {},
    "source_health": [],
    "meta": {"articles_raw": 50, "duplicates_removed": 5, "sources_succeeded": 6, "sources_total": 7, "cached": False},
    "timing": {"fetch_s": 3.2, "dedup_ms": 2.1, "scoring_ms": 12.0, "aggregation_ms": 1.0, "total_s": 3.8},
    "history": [],
    "cached": False,
}


async def test_health_check():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "cache_entries" in data


async def test_health_version():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/")
    assert r.json()["version"] == "4.0.0"
    assert r.json()["sentiment_model"] == "finbert"


async def test_invalid_ticker_characters():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/analyse/INVALID$TICKER!")
    assert r.status_code == 400
    data = r.json()
    assert data["success"] is False
    assert "code" in data["error"]
    assert "invalid characters" in data["error"]["message"].lower()


async def test_ticker_too_long():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/analyse/TOOLONGTICKER1234")
    assert r.status_code == 422  # FastAPI path validation


async def test_analyse_mocked():
    from main import app
    with patch("api.routes.analyse_ticker", new_callable=AsyncMock, return_value=_MOCK_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/analyse/TSLA")
    assert r.status_code == 200
    data = r.json()
    assert data["ticker"] == "TSLA"
    assert data["verdict"] == "BUY"
    assert data["confidence_score"] == 65.0


async def test_analyse_response_has_new_fields():
    from main import app
    with patch("api.routes.analyse_ticker", new_callable=AsyncMock, return_value=_MOCK_RESULT):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/analyse/TSLA")
    data = r.json()
    assert "trend" in data
    assert "source_contributions" in data
    assert "source_health" in data
    assert "meta" in data
    assert "timing" in data


async def test_history_endpoint():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/history/TSLA")
    assert r.status_code == 200
    assert "history" in r.json()


async def test_clear_cache():
    from main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.delete("/cache")
    assert r.status_code == 200
    assert "cleared" in r.json()["message"].lower()

