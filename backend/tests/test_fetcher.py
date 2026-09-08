"""Tests for Yahoo Finance RSS parsing and the single-source fetcher."""
from datetime import datetime, timezone

from fetchers.sources import _parse_datetime_entry, fetch_yahoo_finance


class FakeResponse:
    content = b""

    def raise_for_status(self):
        pass


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.url = None

    async def get(self, url, headers=None):
        self.url = url
        return self.response


def test_parse_datetime_entry_uses_parsed_value():
    dt = _parse_datetime_entry({
        "published_parsed": (2026, 9, 7, 12, 30, 0),
    })
    assert dt == datetime(2026, 9, 7, 12, 30, tzinfo=timezone.utc)


async def test_fetch_yahoo_finance_uses_ticker_rss(monkeypatch):
    captured = {}

    async def fake_fetch_rss(client, url):
        captured["url"] = url
        return type("Feed", (), {
            "entries": [
                {
                    "title": "Tesla beats earnings expectations",
                    "summary": "Tesla reported strong profits.",
                    "link": "https://finance.yahoo.com/example",
                    "published_parsed": (2026, 9, 7, 12, 0, 0),
                }
            ],
            "bozo": False,
        })()

    monkeypatch.setattr("fetchers.sources._fetch_rss", fake_fetch_rss)

    client = FakeClient(FakeResponse())
    articles = await fetch_yahoo_finance(client, "BRK-B")

    assert "feeds.finance.yahoo.com/rss/2.0/headline" in captured["url"]
    assert "s=BRK-B" in captured["url"]
    assert articles[0]["source"] == "Yahoo Finance"
    assert articles[0]["title"] == "Tesla beats earnings expectations"
    assert articles[0]["url"] == "https://finance.yahoo.com/example"
