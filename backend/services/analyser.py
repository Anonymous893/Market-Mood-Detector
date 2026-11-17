"""Main Market Mood Detector analysis orchestrator."""
from __future__ import annotations

import logging
import math
import time
from datetime import datetime, timezone
from typing import Any

from config import (
    CACHE_TTL_SECONDS,
    MIN_SENTIMENT_THRESHOLD,
    YAHOO_SOURCE_NAME,
    YAHOO_SOURCE_WEIGHT,
)
from db import history as db
from fetchers.sources import fetch_all, fetch_stock_info_async
from services import cache as _cache_module
from services.dedup import deduplicate
from services.sentiment import batch_score, get_model_name, get_verdict, weighted_score

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _confidence(
    avg_sentiment: float,
    volatility: float,
    consensus: float,
    total: int,
    articles_24h: int,
    articles_7d: int,
    avg_src_weight: float,
) -> float:
    """Estimate confidence from signal strength, agreement, volume, quality and recency."""
    magnitude = min(abs(avg_sentiment) * 2.0, 1.0)
    vol_factor = max(0.0, 1.0 - volatility * 2.0)
    volume = min(total / 30.0, 1.0)
    recency = min((articles_24h / max(articles_7d, 1)) * 2.0, 1.0)

    raw = (
        magnitude * 0.35
        + consensus * 0.25
        + volume * 0.15
        + avg_src_weight * 0.10
        + recency * 0.10
        + vol_factor * 0.05
    ) * 100.0

    return round(min(raw, 100.0), 2)


def _compute_trend(
    avg_sentiment: float,
    confidence: float,
    verdict: str,
    prev_history: list[dict],
) -> dict:
    if not prev_history:
        return {
            "direction": "new",
            "sentiment_delta": 0.0,
            "confidence_delta": 0.0,
            "prev_verdict": None,
            "verdict_changed": False,
        }

    prev = prev_history[0]
    sentiment_delta = avg_sentiment - prev["avg_sentiment"]
    confidence_delta = confidence - prev["confidence_score"]

    if sentiment_delta > 0.03:
        direction = "improving"
    elif sentiment_delta < -0.03:
        direction = "deteriorating"
    else:
        direction = "stable"

    return {
        "direction": direction,
        "sentiment_delta": round(sentiment_delta, 4),
        "confidence_delta": round(confidence_delta, 2),
        "prev_verdict": prev["verdict"],
        "verdict_changed": prev["verdict"] != verdict,
    }


def _reasons(
    verdict: str,
    bullish_ratio: float,
    bearish_ratio: float,
    neutral_ratio: float,
    momentum: float,
    consensus: float,
    volatility: float,
    articles_24h: int,
    avg_sentiment: float,
) -> list[str]:
    out: list[str] = []

    if bullish_ratio > 0.60:
        out.append(f"{bullish_ratio * 100:.0f}% of analysed Yahoo Finance articles are bullish")
    elif bearish_ratio > 0.60:
        out.append(f"{bearish_ratio * 100:.0f}% of analysed Yahoo Finance articles are bearish")
    elif neutral_ratio > 0.50:
        out.append(f"Majority of analysed coverage is neutral ({neutral_ratio * 100:.0f}%)")

    if abs(avg_sentiment) > 0.25:
        direction = "strongly positive" if avg_sentiment > 0 else "strongly negative"
        out.append(f"Average FinBERT sentiment is {direction} ({avg_sentiment:+.2f})")
    elif abs(avg_sentiment) > 0.10:
        direction = "moderately positive" if avg_sentiment > 0 else "moderately negative"
        out.append(f"Average FinBERT sentiment is {direction} ({avg_sentiment:+.2f})")

    if momentum > 0.08:
        out.append("Positive momentum — recent Yahoo Finance articles are more bullish than older ones")
    elif momentum < -0.08:
        out.append("Negative momentum — recent Yahoo Finance articles are more bearish than older ones")

    if consensus > 0.75:
        out.append("Strong agreement among the analysed articles")
    elif consensus < 0.45:
        out.append("Mixed signals — Yahoo Finance coverage is split on direction")

    if volatility < 0.12:
        out.append("Low volatility — the FinBERT signal is relatively consistent")
    elif volatility > 0.30:
        out.append("High volatility — the analysed headlines have conflicting sentiment")

    if articles_24h >= 8:
        out.append(f"Active recent coverage ({articles_24h} Yahoo Finance articles in the last 24 h)")
    elif articles_24h == 0:
        out.append("No analysed articles were published in the last 24 hours")

    if not out:
        out.append(f"Current market mood: {verdict}")

    return out


async def analyse_ticker(ticker: str) -> dict[str, Any]:
    ticker = ticker.upper()
    t_total = time.perf_counter()

    # 1. Cache check
    cached = _cache_module.get(ticker)
    if cached is not None:
        logger.info("Cache hit for %s", ticker)
        cache_meta = _cache_module.get_meta(ticker)
        cached["cached"] = True
        cached.setdefault("meta", {})["cached"] = True
        cached["cache_meta"] = cache_meta
        return cached

    logger.info("Starting market mood analysis for %s (model=%s)", ticker, get_model_name())

    # 2. Previous history for trend comparison
    prev_history = db.get_history(ticker, limit=1)

    # 3. Yahoo stock metadata and Yahoo Finance RSS in parallel
    t0 = time.perf_counter()
    raw_articles, source_health = await fetch_all(ticker)
    stock_info = await fetch_stock_info_async(ticker)

    fetch_s = time.perf_counter() - t0
    
    articles_raw = len(raw_articles)
    logger.info("Collected %d raw Yahoo Finance articles for %s", articles_raw, ticker)

    # 4. Deduplicate the RSS results
    t0 = time.perf_counter()
    raw_articles, dupes_removed = deduplicate(raw_articles)
    dedup_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        "Dedup: %d → %d (%d removed)",
        articles_raw,
        len(raw_articles),
        dupes_removed,
    )

    sources_succeeded = sum(1 for health in source_health if health["status"] == "ok")

    if not raw_articles:
        return _empty_result(
            ticker,
            stock_info,
            source_health,
            articles_raw,
            dupes_removed,
            sources_succeeded,
        )

    # 5. FinBERT batch scoring
    t0 = time.perf_counter()
    now = _utcnow()
    article_pairs = [(article["title"], article.get("summary") or "") for article in raw_articles]
    scores = batch_score(article_pairs)
    score_ms = (time.perf_counter() - t0) * 1000

    if len(scores) != len(raw_articles):
        raise RuntimeError(
            f"FinBERT returned {len(scores)} scores for {len(raw_articles)} articles"
        )

    scored: list[dict[str, Any]] = []
    for article, compound in zip(raw_articles, scores):
        if abs(compound) < MIN_SENTIMENT_THRESHOLD:
            continue

        pub = article.get("published", now)
        if not isinstance(pub, datetime):
            pub = now
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        else:
            pub = pub.astimezone(timezone.utc)

        hours_old = max(0.0, (now - pub).total_seconds() / 3600.0)
        days_old = hours_old / 24.0
        weighted = weighted_score(compound, days_old, YAHOO_SOURCE_WEIGHT)

        scored.append(
            {
                "text": article["title"][:200],
                "compound": compound,
                "weighted": weighted,
                "source": YAHOO_SOURCE_NAME,
                "source_weight": YAHOO_SOURCE_WEIGHT,
                "sentiment": "bullish" if compound > 0.05 else "bearish" if compound < -0.05 else "neutral",
                "published": pub,
                "hours_old": hours_old,
                "days_old": days_old,
                "url": article.get("url"),
            }
        )

    if not scored:
        return _empty_result(
            ticker,
            stock_info,
            source_health,
            articles_raw,
            dupes_removed,
            sources_succeeded,
        )

    # 6. Aggregate metrics
    t0 = time.perf_counter()
    total = len(scored)
    compounds = [article["compound"] for article in scored]
    weighted_scores = [article["weighted"] for article in scored]

    avg_sentiment = sum(compounds) / total
    weighted_sentiment = sum(weighted_scores) / total
    final_metric = weighted_sentiment

    variance = sum((score - avg_sentiment) ** 2 for score in compounds) / total
    volatility = math.sqrt(variance)

    bullish_count = sum(1 for article in scored if article["sentiment"] == "bullish")
    bearish_count = sum(1 for article in scored if article["sentiment"] == "bearish")
    neutral_count = sum(1 for article in scored if article["sentiment"] == "neutral")

    bullish_ratio = bullish_count / total
    bearish_ratio = bearish_count / total
    neutral_ratio = neutral_count / total
    consensus = max(bullish_ratio, bearish_ratio)

    recent_24h = [article for article in scored if article["hours_old"] <= 24]
    recent_7d = [article for article in scored if article["days_old"] <= 7]

    sentiment_24h = (
        sum(article["compound"] for article in recent_24h) / len(recent_24h)
        if recent_24h
        else 0.0
    )
    sentiment_7d = (
        sum(article["compound"] for article in recent_7d) / len(recent_7d)
        if recent_7d
        else 0.0
    )

    by_time = sorted(scored, key=lambda article: article["hours_old"])
    if len(by_time) >= 3:
        momentum = (
            sum(article["compound"] for article in by_time[:3]) / 3
            - sum(article["compound"] for article in by_time[-3:]) / 3
        )
    else:
        momentum = 0.0

    avg_age = sum(article["hours_old"] for article in scored) / total

    # Keep source contribution data because it is still useful for the frontend,
    # even though there is intentionally only one source.
    total_weighted_abs = sum(abs(article["weighted"]) for article in scored) or 1.0
    source_sentiment_sum = sum(article["compound"] for article in scored)
    source_weighted_abs = sum(abs(article["weighted"]) for article in scored)
    source_contributions = {
        YAHOO_SOURCE_NAME: {
            "articles": total,
            "avg_sentiment": round(source_sentiment_sum / total, 4),
            "contribution_pct": round(source_weighted_abs / total_weighted_abs * 100, 1),
            "avg_age_hours": round(avg_age, 1),
        }
    }

    agg_ms = (time.perf_counter() - t0) * 1000
    total_s = time.perf_counter() - t_total

    # 7. Confidence
    confidence = _confidence(
        avg_sentiment,
        volatility,
        consensus,
        total,
        len(recent_24h),
        len(recent_7d),
        YAHOO_SOURCE_WEIGHT,
    )

    # 8. Verdict
    verdict = get_verdict(final_metric)

    # 9. Reasons
    reasons = _reasons(
        verdict,
        bullish_ratio,
        bearish_ratio,
        neutral_ratio,
        momentum,
        consensus,
        volatility,
        len(recent_24h),
        avg_sentiment,
    )

    # 10. Trend versus previous stored run
    trend = _compute_trend(avg_sentiment, confidence, verdict, prev_history)

    # 11. Most informative articles
    top_15 = sorted(scored, key=lambda article: abs(article["weighted"]), reverse=True)[:15]
    top_comments: list[dict[str, Any]] = []
    for article in top_15:
        hours = article["hours_old"]
        if hours < 1:
            time_ago = f"{int(hours * 60)}m ago"
        elif hours < 24:
            time_ago = f"{int(hours)}h ago"
        else:
            time_ago = f"{int(article['days_old'])}d ago"

        top_comments.append(
            {
                "text": article["text"],
                "score": round(article["compound"], 3),
                "sentiment": article["sentiment"],
                "source": article["source"],
                "source_weight": round(article["source_weight"], 2),
                "time_ago": time_ago,
                "hours_old": round(hours, 1),
                "url": article.get("url"),
            }
        )

    # 12. Persist
    db.save(ticker, verdict, confidence, avg_sentiment, total)

    result: dict[str, Any] = {
        "ticker": ticker,
        "verdict": verdict,
        "confidence_score": confidence,
        "verdict_reasons": reasons,
        "model_used": get_model_name(),
        "stats": {
            "bullish": bullish_count,
            "bearish": bearish_count,
            "neutral": neutral_count,
        },
        "top_comments": top_comments,
        "stock_info": stock_info,
        "advanced_stats": {
            "avg_sentiment": round(avg_sentiment, 4),
            "weighted_sentiment": round(weighted_sentiment, 4),
            "volatility": round(volatility, 4),
            "momentum": round(momentum, 4),
            "sentiment_24h": round(sentiment_24h, 4),
            "sentiment_7d": round(sentiment_7d, 4),
            "articles_24h": len(recent_24h),
            "articles_7d": len(recent_7d),
            "bullish_ratio": round(bullish_ratio, 3),
            "bearish_ratio": round(bearish_ratio, 3),
            "neutral_ratio": round(neutral_ratio, 3),
            "consensus_strength": round(consensus, 3),
            "avg_article_age_hours": round(avg_age, 1),
            "total_articles": total,
            "deduplicated_count": total,
        },
        "trend": trend,
        "source_contributions": source_contributions,
        "source_health": source_health,
        "meta": {
            "articles_raw": articles_raw,
            "duplicates_removed": dupes_removed,
            "sources_succeeded": sources_succeeded,
            "sources_total": len(source_health),
            "cached": False,
        },
        "cache_meta": {
            "age_s": 0.0,
            "expires_in_s": float(CACHE_TTL_SECONDS),
        },
        "timing": {
            "fetch_s": round(fetch_s, 3),
            "dedup_ms": round(dedup_ms, 1),
            "scoring_ms": round(score_ms, 1),
            "aggregation_ms": round(agg_ms, 1),
            "total_s": round(total_s, 3),
        },
        "history": db.get_history(ticker),
        "cached": False,
    }

    _cache_module.set(ticker, result)
    return result


def _empty_result(
    ticker: str,
    stock_info: dict,
    source_health: list,
    articles_raw: int = 0,
    dupes_removed: int = 0,
    sources_succeeded: int = 0,
) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "verdict": "INSUFFICIENT DATA",
        "confidence_score": 0.0,
        "verdict_reasons": ["No Yahoo Finance articles with meaningful sentiment were found"],
        "model_used": get_model_name(),
        "stats": {"bullish": 0, "bearish": 0, "neutral": 0},
        "top_comments": [],
        "stock_info": stock_info,
        "advanced_stats": None,
        "trend": {
            "direction": "new",
            "sentiment_delta": 0.0,
            "confidence_delta": 0.0,
            "prev_verdict": None,
            "verdict_changed": False,
        },
        "source_contributions": {},
        "source_health": source_health,
        "meta": {
            "articles_raw": articles_raw,
            "duplicates_removed": dupes_removed,
            "sources_succeeded": sources_succeeded,
            "sources_total": len(source_health),
            "cached": False,
        },
        "cache_meta": None,
        "timing": None,
        "history": db.get_history(ticker),
        "cached": False,
    }
