"""Unit tests for the FinBERT-only sentiment service."""
import pytest

import services.sentiment as sentiment
from services.sentiment import (
    batch_score,
    get_model_name,
    get_verdict,
    recency_multiplier,
    score,
    score_article,
    weighted_score,
)


class _FakeFinBERT:
    def __call__(self, texts, **kwargs):
        if isinstance(texts, str):
            texts = [texts]
        results = []
        for text in texts:
            lower = text.lower()
            if "bankruptcy" in lower or "loss" in lower or "downgrade" in lower:
                results.append({"label": "negative", "score": 0.9})
            elif "beat" in lower or "profits" in lower or "bullish" in lower:
                results.append({"label": "positive", "score": 0.8})
            else:
                results.append({"label": "neutral", "score": 0.95})
        return results


@pytest.fixture(autouse=True)
def fake_finbert(monkeypatch):
    monkeypatch.setattr(sentiment, "_finbert", _FakeFinBERT())


def test_finbert_is_only_model():
    assert get_model_name() == "finbert"


def test_positive_headline():
    assert score("Tesla beats earnings estimates and reports record profits") > 0.2


def test_negative_headline():
    assert score("Company announces bankruptcy after major losses") < -0.3


def test_neutral_headline():
    assert -0.1 <= score("Company reports quarterly results") <= 0.1


def test_score_article_combines_headline_and_summary():
    s = score_article(
        "Company reports quarterly results",
        "Management announces record profits and expects strong growth",
    )
    assert s == pytest.approx(0.8)


def test_batch_score():
    results = batch_score([
        ("Tesla beats estimates", "profits grow"),
        ("Company announces losses", "downgrade expected"),
        ("Company reports quarterly results", ""),
    ])
    assert results == pytest.approx([0.8, -0.9, 0.0])


def test_finbert_failure_does_not_fallback_to_vader(monkeypatch):
    class BrokenModel:
        def __call__(self, *args, **kwargs):
            raise RuntimeError("inference failed")

    monkeypatch.setattr(sentiment, "_finbert", BrokenModel())
    with pytest.raises(RuntimeError, match="inference failed"):
        score("Tesla beats estimates")


def test_recency_today_vs_week_old():
    assert recency_multiplier(0.0) > recency_multiplier(6.5)


def test_recency_very_old_is_positive():
    assert recency_multiplier(10.0) > 0


def test_recency_decreasing_monotone():
    weights = [recency_multiplier(float(day)) for day in range(8)]
    assert all(weights[i] >= weights[i + 1] for i in range(len(weights) - 1))


def test_weighted_score_preserves_sign():
    assert weighted_score(0.5, 1.0, 1.0) > 0
    assert weighted_score(-0.5, 1.0, 1.0) < 0


def test_get_verdict_thresholds():
    assert get_verdict(0.25) == "STRONG BUY"
    assert get_verdict(0.12) == "BUY"
    assert get_verdict(0.00) == "HOLD"
    assert get_verdict(-0.12) == "SELL"
    assert get_verdict(-0.30) == "STRONG SELL"


def test_get_verdict_strict_boundaries():
    assert get_verdict(0.201) == "STRONG BUY"
    assert get_verdict(0.200) == "BUY"
    assert get_verdict(0.051) == "BUY"
    assert get_verdict(0.050) == "HOLD"
    assert get_verdict(-0.050) == "HOLD"
    assert get_verdict(-0.051) == "SELL"
    assert get_verdict(-0.200) == "SELL"
    assert get_verdict(-0.201) == "STRONG SELL"
