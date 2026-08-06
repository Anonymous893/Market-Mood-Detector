from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query

from backend.models.schemas import AnalysisResponse, HealthResponse, HistoryAnalytics
from backend.services import cache as _cache
from backend.services.analyzer import analyze_ticker
from backend.services.score import MODEL_NAME
from db import database

logger = logging.getLogger(__name__)

router = APIRouter()

_TICKER_EXAMPLE = {
    "TSLA": {
        "summary": "Tesla Inc. — electric vehicles",
        "value": {"ticker": "TSLA"},
    },
    "AAPL": {
        "summary": "Apple Inc.",
        "value": {"ticker": "AAPL"},
    },
}


@router.get(
    "/",
    response_model=HealthResponse,
    tags=["Health"],
    summary="API health check",
)
async def health():
    return HealthResponse(
        status="ok",
        version="3.0.0",
        cache_entries=_cache.size(),
        sentiment_model=MODEL_NAME,
    )


@router.get(
    "/analyze/{ticker}",
    response_model=AnalysisResponse,
    tags=["Analysis"],
    summary="Analyze market sentiment for a stock ticker",
)
async def analyze_stock(
    ticker: str = Path(
        ...,
        min_length=1,
        max_length=15,
        description="Stock ticker symbol (e.g. TSLA, RELIANCE.NS)",
        examples=_TICKER_EXAMPLE,
    ),
):
    ticker = ticker.upper().strip()

    invalid_chars = set(ticker) - set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-")
    if invalid_chars:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_TICKER",
                "message": f"Ticker contains invalid characters: {', '.join(sorted(invalid_chars))}",
                "details": None,
            },
        )

    logger.info("Analysis requested: %s", ticker)
    try:
        result = await analyze_ticker(ticker)
        return result
    except Exception as exc:
        logger.exception("Analysis failed for %s", ticker)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ANALYSIS_FAILED",
                "message": f"Analysis failed: {exc}",
                "details": None,
            },
        ) from exc


@router.get(
    "/history/{ticker}",
    tags=["History"],
    summary="Return the last N analysis runs for a ticker",
)
async def get_history(
    ticker: str = Path(..., min_length=1, max_length=15),
    limit: int = Query(8, ge=1, le=50, description="Max history entries to return"),
):
    ticker = ticker.upper().strip()
    # Uses database.get_recent_history from your database.py
    history_data = database.get_recent_history(ticker, limit=limit)
    return {"ticker": ticker, "history": history_data}


@router.get(
    "/analytics/{ticker}",
    response_model=HistoryAnalytics,
    tags=["History"],
    summary="Rolling analytics over historical runs",
)
async def get_analytics(
    ticker: str = Path(..., min_length=1, max_length=15),
):
    ticker = ticker.upper().strip()
    
    # Check if get_analytics exists in your database module
    if hasattr(database, "get_analytics"):
        data = database.get_analytics(ticker)
    else:
        data = None

    if not data:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NO_HISTORY",
                "message": f"No analysis history found for {ticker}",
                "details": None,
            },
        )
    return data


@router.delete(
    "/cache",
    tags=["Admin"],
    summary="Clear the in-memory sentiment cache",
)
async def clear_cache():
    _cache.clear()
    return {"message": "Cache cleared"}


@router.get(
    "/scheduler/status",
    tags=["Admin"],
    summary="Background scheduler state",
)
async def get_scheduler_status():
    try:
        import scheduler
        return scheduler.status()
    except ImportError:
        return {
            "active": False,
            "message": "Scheduler service not configured."
        }