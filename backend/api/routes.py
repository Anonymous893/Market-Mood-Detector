"""FastAPI routes for the Market Mood Detector."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Path, Query

from db import history as db
from models.schemas import AnalysisResponse, HealthResponse, HistoryAnalytics
from services import cache as _cache
from services.analyser import analyse_ticker
from services.sentiment import get_model_name

logger = logging.getLogger(__name__)
router = APIRouter()

_TICKER_EXAMPLE = {
    "TSLA": {"summary": "Tesla Inc. — electric vehicles", "value": {"ticker": "TSLA"}},
    "AAPL": {"summary": "Apple Inc.", "value": {"ticker": "AAPL"}},
}


@router.get("/", response_model=HealthResponse, tags=["Health"], summary="API health check")
async def health():
    return HealthResponse(
        status="ok",
        version="4.0.0",
        cache_entries=_cache.size(),
        sentiment_model=get_model_name(),
    )


@router.get(
    "/analyse/{ticker}",
    response_model=AnalysisResponse,
    tags=["Analysis"],
    summary="Analyse market mood from Yahoo Finance news",
    responses={
        400: {"description": "Invalid ticker symbol"},
        500: {"description": "Analysis pipeline failed"},
    },
    openapi_extra={
        "responses": {
            "200": {
                "content": {
                    "application/json": {
                        "example": {
                            "ticker": "TSLA",
                            "verdict": "BUY",
                            "confidence_score": 61.4,
                            "model_used": "finbert",
                            "verdict_reasons": [
                                "72% of analysed Yahoo Finance articles are bullish",
                                "Average FinBERT sentiment is moderately positive (+0.18)",
                            ],
                            "cached": False,
                            "cache_meta": {"age_s": 0.0, "expires_in_s": 300.0},
                        }
                    }
                }
            }
        }
    },
)
async def analyse_stock(
    ticker: str = Path(
        ...,
        min_length=1,
        max_length=15,
        description="Stock ticker symbol (e.g. TSLA, AAPL, BRK-B)",
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

    logger.info("Market mood analysis requested: %s", ticker)
    try:
        return await analyse_ticker(ticker)
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
    summary="Return the last N market mood runs for a ticker",
)
async def get_history(
    ticker: str = Path(..., min_length=1, max_length=15),
    limit: int = Query(8, ge=1, le=50, description="Max number of history entries to return"),
):
    ticker = ticker.upper().strip()
    return {"ticker": ticker, "history": db.get_history(ticker, limit=limit)}


@router.get(
    "/analytics/{ticker}",
    response_model=HistoryAnalytics,
    tags=["History"],
    summary="Rolling market mood analytics over historical runs",
    responses={404: {"description": "No history found for ticker"}},
)
async def get_analytics(ticker: str = Path(..., min_length=1, max_length=15)):
    ticker = ticker.upper().strip()
    data = db.get_analytics(ticker)
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


@router.delete("/cache", tags=["Admin"], summary="Clear the in-memory market mood cache")
async def clear_cache():
    _cache.clear()
    return {"message": "Cache cleared"}
