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