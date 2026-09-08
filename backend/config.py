"""Central configuration for the Market Mood Detector."""
from __future__ import annotations

import os

# ── Server / CORS ─────────────────────────────────────────────
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if origin.strip()
]

# ── Yahoo Finance fetcher ─────────────────────────────────────
NEWS_FETCH_TIMEOUT_CONNECT: float = float(os.getenv("FETCH_TIMEOUT_CONNECT", "4"))
NEWS_FETCH_TIMEOUT_READ: float = float(os.getenv("FETCH_TIMEOUT_READ", "7"))
MAX_ARTICLES_PER_SOURCE: int = int(os.getenv("MAX_ARTICLES_PER_SOURCE", "20"))

# ── Scoring ───────────────────────────────────────────────────
# Articles whose FinBERT score is too close to neutral are omitted from
# the aggregate mood calculation.
MIN_SENTIMENT_THRESHOLD: float = float(os.getenv("MIN_SENTIMENT_THRESHOLD", "0.02"))

# FinBERT is the only sentiment model in this project.
FINBERT_DEVICE: int = int(os.getenv("FINBERT_DEVICE", "-1"))  # -1 = CPU, 0+ = CUDA GPU
FINBERT_MODEL: str = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")

# Yahoo Finance is the only news source, so there is no source selection
# or per-provider reliability configuration to maintain.
YAHOO_SOURCE_NAME = "Yahoo Finance"
YAHOO_SOURCE_WEIGHT: float = 1.0

# ── Cache ─────────────────────────────────────────────────────
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes

# ── Persistence ───────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "sentiment_history.db")
