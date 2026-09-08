"""Yahoo Finance RSS and stock metadata fetchers."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import feedparser
import httpx

from config import (
    MAX_ARTICLES_PER_SOURCE,
    NEWS_FETCH_TIMEOUT_CONNECT,
    NEWS_FETCH_TIMEOUT_READ,
    YAHOO_SOURCE_NAME,
)

logger = logging.getLogger(__name__)


# This is intentionally the simple User-Agent that has already been
# demonstrated to work with Yahoo Finance in this environment.
_UA = "Mozilla/5.0"

_TIMEOUT = httpx.Timeout(
    connect=NEWS_FETCH_TIMEOUT_CONNECT,
    read=NEWS_FETCH_TIMEOUT_READ,
    write=5.0,
    pool=None,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_struct_time(st: Any) -> datetime:
    if st is None:
        return _utcnow()

    try:
        return datetime(*st[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return _utcnow()


def _parse_datetime_entry(entry: Any) -> datetime:
    """Parse Yahoo/feedparser publication dates."""
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")

    if parsed is not None:
        return _parse_struct_time(parsed)

    for key in ("published", "updated"):
        value = entry.get(key)

        if not value:
            continue

        try:
            return (
                datetime.fromisoformat(
                    str(value).replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            )
        except ValueError:
            continue

    return _utcnow()


def _entry_summary(entry: Any) -> str:
    return str(
        entry.get("summary")
        or entry.get("description")
        or ""
    )


async def _fetch_rss(
    client: httpx.AsyncClient,
    url: str,
) -> feedparser.FeedParserDict:
    """Fetch a Yahoo RSS feed using the same simple pattern as the working test."""
    response = await client.get(
        url,
        headers={"User-Agent": _UA},
    )

    logger.info(
        "Yahoo RSS response: %s (%d bytes)",
        response.status_code,
        len(response.content),
    )

    response.raise_for_status()

    feed = feedparser.parse(response.content)

    if getattr(feed, "bozo", False) and not feed.entries:
        raise ValueError(
            "Yahoo Finance returned an invalid RSS feed"
        )

    if not feed.entries:
        raise ValueError(
            "Yahoo Finance returned no RSS articles"
        )

    return feed


async def fetch_yahoo_finance(
    client: httpx.AsyncClient,
    ticker: str,
) -> list[dict[str, Any]]:
    """Fetch ticker-specific Yahoo Finance headlines."""
    normalized_ticker = ticker.strip().upper()

    url = (
        "https://feeds.finance.yahoo.com/rss/2.0/headline"
        f"?s={quote_plus(normalized_ticker)}"
        "&region=US&lang=en-US"
    )

    try:
        feed = await _fetch_rss(client, url)
    except Exception as exc:
        logger.warning(
            "Yahoo RSS fetch failed for %s: %s",
            normalized_ticker,
            exc,
        )
        raise

    articles: list[dict[str, Any]] = []

    for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        title = str(entry.get("title") or "").strip()

        if not title:
            continue

        articles.append(
            {
                "guid": entry.get("id") or entry.get("guid"),
                "ticker": normalized_ticker,
                "title": title,
                "summary": _entry_summary(entry),
                "url": entry.get("link"),
                "source": YAHOO_SOURCE_NAME,
                "published": _parse_datetime_entry(entry),
            }
        )

    logger.info(
        "Yahoo RSS parsed %d articles for %s",
        len(articles),
        normalized_ticker,
    )

    return articles


async def fetch_all(
    ticker: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch Yahoo Finance RSS and return articles plus health metadata."""
    import time

    started = time.monotonic()

    async with httpx.AsyncClient(
        timeout=_TIMEOUT,
        follow_redirects=True,
    ) as client:
        try:
            articles = await fetch_yahoo_finance(
                client,
                ticker,
            )

            duration_ms = round(
                (time.monotonic() - started) * 1000
            )

            health = {
                "name": YAHOO_SOURCE_NAME,
                "status": "ok",
                "duration_ms": duration_ms,
                "articles": len(articles),
            }

            logger.info(
                "%s → ok: %d articles in %d ms",
                YAHOO_SOURCE_NAME,
                len(articles),
                duration_ms,
            )

            return articles, [health]

        except Exception as exc:
            duration_ms = round(
                (time.monotonic() - started) * 1000
            )

            logger.warning(
                "%s failed in %d ms: %s",
                YAHOO_SOURCE_NAME,
                duration_ms,
                exc,
            )

            return [], [
                {
                    "name": YAHOO_SOURCE_NAME,
                    "status": "error",
                    "duration_ms": duration_ms,
                    "articles": 0,
                    "error": type(exc).__name__,
                }
            ]


async def fetch_stock_info_async(
    ticker: str,
) -> dict[str, Any]:
    """Fetch lightweight stock metadata.

    Stock metadata is optional. A failure here must not affect news sentiment.
    """
    normalized_ticker = ticker.strip().upper()

    fallback = {
        "name": normalized_ticker,
        "sector": "Unknown",
        "current_price": 0.0,
    }

    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{quote_plus(normalized_ticker)}"
        "?range=1d&interval=1d"
    )

    try:
        async with httpx.AsyncClient(
            timeout=_TIMEOUT,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                url,
                headers={"User-Agent": _UA},
            )

        logger.info(
            "Yahoo Chart response for %s: %s",
            normalized_ticker,
            response.status_code,
        )

        response.raise_for_status()

        payload = response.json()

        results = (
            payload
            .get("chart", {})
            .get("result")
            or []
        )

        if not results:
            return fallback

        meta = results[0].get("meta", {})

        current_price = meta.get(
            "regularMarketPrice",
            0.0,
        )

        try:
            current_price = float(current_price or 0.0)
        except (TypeError, ValueError):
            current_price = 0.0

        name = (
            meta.get("longName")
            or meta.get("shortName")
            or meta.get("symbol")
            or normalized_ticker
        )

        return {
            "name": str(name),
            "sector": "Unknown",
            "current_price": current_price,
        }

    except Exception as exc:
        logger.warning(
            "Yahoo stock info unavailable for %s: %s",
            normalized_ticker,
            exc,
        )

        return fallback


async def fetch_stock_info(
    client: httpx.AsyncClient,
    ticker: str,
) -> dict[str, Any]:
    """Compatibility wrapper for existing backend code."""
    del client
    return await fetch_stock_info_async(ticker)
