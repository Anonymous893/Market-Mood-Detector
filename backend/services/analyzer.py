from __future__ import annotations

import asyncio
import logging
import math
import time
from datetime import datetime, timezone
from typing import Any

# Import your custom modules
from backend.scrapers import sources
from backend.services import score
from backend.db import database
from backend.services import dedup
from backend.services import cache

logger = logging.getLogger(__name__)

MIN_SENTIMENT_THRESHOLD = 0.05 
CACHE_TTL_SECONDS = 3600 # 1 hour

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

# ── 1. Confidence Logic (Kept from your inspiration) ───────────

def _confidence(avg_sentiment, volatility, consensus, total, articles_24h, articles_7d):
    magnitude  = min(abs(avg_sentiment) * 2.0, 1.0)
    vol_factor = max(0.0, 1.0 - volatility * 2.0)
    volume     = min(total / 20.0, 1.0) # Adjusted for single-source Yahoo
    recency    = min((articles_24h / max(articles_7d, 1)) * 2.0, 1.0)

    raw = (magnitude * 0.40 + consensus * 0.30 + volume * 0.15 + recency * 0.10 + vol_factor * 0.05) * 100.0
    return round(min(raw, 100.0), 2)

# ── 2. Trend Logic (Plugs into database.py) ─────────────────────

def _compute_trend(avg_sentiment, confidence, verdict, prev_history):
    if not prev_history:
        return {"direction": "new", "sentiment_delta": 0.0, "verdict_changed": False}

    prev = prev_history[0] # Get the most recent run
    sentiment_delta = avg_sentiment - prev.get("avg_sentiment", 0)
    
    if sentiment_delta > 0.03: direction = "improving"
    elif sentiment_delta < -0.03: direction = "deteriorating"
    else: direction = "stable"

    return {
        "direction": direction,
        "sentiment_delta": round(sentiment_delta, 4),
        "prev_verdict": prev.get("verdict"),
        "verdict_changed": prev.get("verdict") != verdict,
    }

# ── 3. Main Entry Point ────────────────────────────────────────

async def analyze_ticker(ticker: str) -> dict[str, Any]:
    ticker = ticker.upper()
    t_total = time.perf_counter()
    
    # 1. Cache Check
    cached = cache.get(ticker)
    if cached:
        logger.info(f"Cache hit for {ticker}")
        return cached

    # Initialize DB and Analyzer
    database.init_db()
    bert = analyzer.FinBertManager()

    # 2. Previous History (for Trend)
    try:
        prev_history = database.get_recent_history(ticker, limit=1)
    except:
        prev_history = []

    # 3. Fetch Stock Info + Yahoo News
    t0 = time.perf_counter()
    data = await fetcher.get_yahoo_data(ticker)
    fetch_s = time.perf_counter() - t0
    
    stock_info = data['metadata']
    raw_articles = data['articles']
    articles_raw_count = len(raw_articles)

    # 4. Remove duplicate
    articles, dupes_removed = deduplicator.deduplicate(raw_articles)
    
    if not articles:
        return {"error": "No articles found"}

    # 5. Batch-Score Articles (FinBERT)
    t0 = time.perf_counter()
    titles = [a['title'] for a in articles]
    compounds = bert.score_batch(titles)
    
    scored_data = []
    for i, art in enumerate(articles):
        compound = compounds[i]
        weighted = bert.apply_recency_weight(compound, art['published'])
        
        hours_old = (datetime.now(timezone.utc) - art['published']).total_seconds() / 3600.0
        
        scored_data.append({
            "title": art['title'],
            "compound": compound,
            "weighted": weighted,
            "sentiment": "bullish" if compound > 0.05 else "bearish" if compound < -0.05 else "neutral",
            "hours_old": hours_old,
            "url": art['url'],
            "published": art['published']
        })
    score_ms = (time.perf_counter() - t0) * 1000

    # 6. Aggregate Metrics
    total = len(scored_data)
    avg_sentiment = sum(c for c in compounds) / total
    weighted_sentiment = sum(s['weighted'] for s in scored_data) / total
    
    variance = sum((x - avg_sentiment)**2 for x in compounds) / total
    volatility = math.sqrt(variance)

    bullish_count = sum(1 for s in scored_data if s['sentiment'] == "bullish")
    bearish_count = sum(1 for s in scored_data if s['sentiment'] == "bearish")
    consensus = max(bullish_count, bearish_count) / total
    
    articles_24h = sum(1 for s in scored_data if s['hours_old'] <= 24)
    articles_7d = sum(1 for s in scored_data if s['hours_old'] <= 168)

    # 7. Confidence & Verdict
    confidence = _confidence(avg_sentiment, volatility, consensus, total, articles_24h, articles_7d)
    verdict = bert.get_verdict(weighted_sentiment)
    
    # 8. Trend
    trend = _compute_trend(avg_sentiment, confidence, verdict, prev_history)

    # 9. Build Final Result Object
    result = {
        "ticker": ticker,
        "verdict": verdict,
        "confidence_score": confidence,
        "sentiment_score": round(weighted_sentiment, 4),
        "stock_info": stock_info,
        "stats": {
            "total_articles": total,
            "bullish": bullish_count,
            "bearish": bearish_count,
            "volatility": round(volatility, 3),
            "articles_24h": articles_24h
        },
        "trend": trend,
        "top_articles": sorted(scored_data, key=lambda x: abs(x['weighted']), reverse=True)[:5],
        "timing": {
            "fetch_s": round(fetch_s, 2),
            "score_ms": round(score_ms, 1),
            "total_s": round(time.perf_counter() - t_total, 2)
        }
    }

    # 10. Return to Database
    for art in articles:
        idx = articles.index(art)
        art['sentiment_title'] = compounds[idx] 
        
    database.save_news_items(articles)
    database.save_analysis(ticker, verdict, weighted_sentiment, total)

    # 11. Cache and Return
    cache.set(ticker, result)
    return result