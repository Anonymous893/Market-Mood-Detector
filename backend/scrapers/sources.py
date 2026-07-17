from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

MAX_ARTICLES_PER_SOURCE = 20
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=None)

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────
def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _parse_struct_time(st: Any) -> datetime:
    if st is None: return _utcnow()
    try:
        return datetime(*st[:6], tzinfo=timezone.utc)
    except Exception:
        return _utcnow()

async def _fetch_rss(client: httpx.AsyncClient, url: str) -> feedparser.FeedParserDict:
    resp = await client.get(url, headers={"User-Agent": _UA})
    resp.raise_for_status()
    return feedparser.parse(resp.content)

# ── Yahoo Finance Fetchers ─────────────────────────────────────
async def fetch_yahoo_finance_news(client: httpx.AsyncClient, ticker: str) -> list[dict]:
    """Fetches news from Yahoo Finance RSS"""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    
    try:
        feed = await _fetch_rss(client, url)
    except Exception as exc:
        logger.error("RSS fetch failed for %s: %s", ticker, exc)
        return []
    
    articles = []
    for e in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        published_dt = _parse_struct_time(e.get("published_parsed"))
        
        articles.append({
            "guid":      e.get("id") or e.get("guid"),
            "ticker":    ticker.upper(),
            "title":     e.get("title"),
            "summary":   e.get("summary", ""),
            "url":       e.get("link"),
            "published": published_dt,
        })
    return articles

async def fetch_stock_info(client: httpx.AsyncClient, ticker: str) -> dict:
    """Fetches ticker metadata (price, name)"""
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
    fallback = {"ticker": ticker, "name": ticker, "sector": "Unknown", "current_price": 0.0}
    
    try:
        resp = await client.get(url, headers={"User-Agent": _UA})
        resp.raise_for_status()
        result = resp.json().get("quoteResponse", {}).get("result", [])
        if result:
            info = result[0]
            return {
                "ticker":        ticker.upper(),
                "name":          info.get("longName") or info.get("shortName") or ticker,
                "sector":        info.get("sector", "Unknown"),
                "current_price": float(info.get("regularMarketPrice", 0)),
            }
    except Exception as exc:
        logger.warning("Stock info failed for %s: %s", ticker, exc)
    
    return fallback

# ── Orchestration ──────────────────────────────────────────────

async def get_yahoo_data(ticker: str) -> dict:
    """
    The main entry point. Fetches both Price Info and News Feed.
    """
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Run info fetch and news fetch concurrently
        info_task = fetch_stock_info(client, ticker)
        news_task = fetch_yahoo_finance_news(client, ticker)
        
        info, news = await asyncio.gather(info_task, news_task)
        
        return {
            "metadata": info,
            "articles": news,
            "count": len(news)
        }