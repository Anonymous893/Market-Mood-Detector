"""FinBERT-only sentiment scoring for financial news."""
from __future__ import annotations

import logging
import math
import re
import threading
import unicodedata
from typing import Any, Optional

from config import FINBERT_DEVICE, FINBERT_MODEL

logger = logging.getLogger(__name__)

_finbert: Optional[Any] = None
_finbert_lock = threading.Lock()


def _load_finbert() -> Any:
    """Lazily load FinBERT once, raising clearly if it cannot be loaded."""
    global _finbert

    if _finbert is not None:
        return _finbert

    with _finbert_lock:
        if _finbert is not None:
            return _finbert

        try:
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "FinBERT dependencies are missing. Install requirements.txt "
                "or run: pip install torch transformers"
            ) from exc

        logger.info(
            "Loading FinBERT model=%s on device=%d…",
            FINBERT_MODEL,
            FINBERT_DEVICE,
        )
        _finbert = pipeline(
            "text-classification",
            model=FINBERT_MODEL,
            device=FINBERT_DEVICE,
            truncation=True,
            max_length=512,
        )
        logger.info("FinBERT loaded successfully")

    return _finbert


def get_model_name() -> str:
    return "finbert"


def clean_text(text: str) -> str:
    """normalize article text before sending it to FinBERT."""
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^\w\s.,!?%$-]", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _finbert_to_score(result: dict[str, Any]) -> float:
    label = str(result["label"]).lower()
    confidence = float(result["score"])

    if label == "positive":
        return confidence
    if label == "negative":
        return -confidence
    return 0.0


def _combine_text(headline: str, summary: str | None) -> str:
    headline_clean = clean_text(headline)
    summary_clean = clean_text(summary or "")
    if not summary_clean:
        return headline_clean
    # Keep enough description to give FinBERT context without overwhelming the headline.
    return f"{headline_clean}. {summary_clean[:1500]}".strip()


def score(text: str) -> float:
    """Score a single financial text with FinBERT."""
    cleaned = clean_text(text)
    if not cleaned:
        return 0.0

    model = _load_finbert()
    result = model(cleaned[:4000])[0]
    return _finbert_to_score(result)


def score_article(headline: str, summary: str | None) -> float:
    """Score an article using its headline and optional RSS summary."""
    combined = _combine_text(headline, summary)
    return score(combined)


def batch_score(articles: list[tuple[str, str | None]]) -> list[float]:
    """Run FinBERT inference on a list of articles in batches."""
    if not articles:
        return []

    model = _load_finbert()
    texts = [_combine_text(headline, summary) for headline, summary in articles]
    texts = [text[:4000] for text in texts]

    # One model call lets transformers batch the work efficiently.
    try:
        results = model(texts, batch_size=8)
    except Exception:
        logger.exception("FinBERT batch inference failed")
        raise

    return [_finbert_to_score(result) for result in results]


def recency_multiplier(days_old: float) -> float:
    """Logarithmic recency decay used to emphasize newer Yahoo articles."""
    effective = min(max(int(days_old), 0), 7)
    weight = max(1, 7 - effective)
    return math.log(weight + 1)


def weighted_score(compound: float, days_old: float, source_weight: float = 1.0) -> float:
    """Combine FinBERT score with recency and Yahoo's fixed source weight."""
    return compound * recency_multiplier(days_old) * source_weight


def get_verdict(metric: float) -> str:
    if metric > 0.20:
        return "STRONG BUY"
    if metric > 0.05:
        return "BUY"
    if metric < -0.20:
        return "STRONG SELL"
    if metric < -0.05:
        return "SELL"
    return "HOLD"
