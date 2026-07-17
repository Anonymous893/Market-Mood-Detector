import logging
import re
import unicodedata
from typing import Optional
import torch
from transformers import pipeline

FINBERT_DEVICE = 0 if torch.cuda.is_available() else -1 # Use GPU if available, else CPU
MODEL_NAME = "ProsusAI/finbert"

logger = logging.getLogger(__name__)

class FinBertManager:
    """Manages the FinBERT model"""
    
    def __init__(self):
        self._pipe = None

    def _get_pipe(self):
        """Lazy-load the model only when first needed"""
        if self._pipe is None:
            logger.info(f"Loading FinBERT ({MODEL_NAME}) on device {FINBERT_DEVICE}...")
            self._pipe = pipeline(
                "text-classification",
                model=MODEL_NAME,
                device=FINBERT_DEVICE,
                truncation=True,
                max_length=512
            )
        return self._pipe

    def clean_text(self, text: str) -> str:
        """Normalize text and remove URLs/HTML."""
        if not text: return ""
        text = unicodedata.normalize("NFKC", text)
        text = re.sub(r"https?://\S+|www\.\S+", "", text)
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text

    def _convert_to_score(self, result: dict) -> float:
        """Convert FinBERT label + confidence to a -1 to 1 scale."""
        label = result["label"].lower()
        conf = float(result["score"])
        if label == "positive": return conf
        if label == "negative": return -conf
        return 0.0 # Neutral

    def score_batch(self, texts: list[str]) -> list[float]:
        """Scores a list of strings efficiently."""
        if not texts: return []
        
        cleaned = [self.clean_text(t)[:512] for t in texts]
        pipe = self._get_pipe()
        
        try:
            results = pipe(cleaned, batch_size=8)
            return [self._convert_to_score(r) for r in results]
        except Exception as exc:
            logger.error(f"FinBERT batch scoring failed: {exc}")
            return [0.0] * len(texts)

    # ── THE RECENCY MULTIPLIER ──────────────────────────────────
    def apply_recency_weight(self, raw_score: float, published_date: datetime) -> float:
        """
        Boosts recent news, de-prioritizes old news.
        Today (0d) → multiplier ~2.08
        7+ days ago → multiplier ~0.69
        """
        now = datetime.now(timezone.utc)
        diff = now - published_date
        days_old = max(0, diff.days)
        
        effective_days = min(days_old, 7)
        weight = max(1, 7 - effective_days)
        multiplier = math.log(weight + 1)
        
        return raw_score * multiplier

    def get_verdict(self, score: float) -> str:
        """Translates the average sentiment into a recommendation."""
        if score > 0.30: return "STRONG BUY"
        if score > 0.10: return "BUY"
        if score < -0.30: return "STRONG SELL"
        if score < -0.10: return "SELL"
        return "HOLD"