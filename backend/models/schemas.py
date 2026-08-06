from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class ArticleResult(BaseModel):
    guid: str
    title: str
    summary: str
    url: Optional[str]
    published: datetime
    sentiment_title: float = 0.0
    sentiment_summary: float = 0.0

class StockInfo(BaseModel):
    ticker: str
    name: str
    sector: str
    current_price: float

class HistoryEntry(BaseModel):
    timestamp: str
    verdict: str
    confidence_score: float
    avg_sentiment: float

class AnalysisResponse(BaseModel):
    ticker: str
    stock_info: StockInfo
    articles: List[ArticleResult]
    verdict: str
    avg_sentiment: float
    history: List[HistoryEntry] = []

class HealthResponse(BaseModel):
    status: str
    version: str
    cache_entries: int
    sentiment_model: str

class BestWorstRun(BaseModel):
    timestamp: str
    sentiment: float
    verdict: str

class HistoryAnalytics(BaseModel):
    total_runs: int
    rolling_7d_avg_sentiment: float
    rolling_30d_avg_sentiment: float
    avg_confidence: float
    best_run: Optional[BestWorstRun] = None
    worst_run: Optional[BestWorstRun] = None
    verdict_distribution: dict[str, int] = {}
    moving_avg_series: list[float] = []