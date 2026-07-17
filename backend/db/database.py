import sqlite3
import logging
from datetime import datetime, timezone
from typing import Any

DB_PATH = "stock_data.db"
logger = logging.getLogger(__name__)

# SQL Schema
_CREATE_NEWS_TABLE = """
CREATE TABLE IF NOT EXISTS news (
    guid              TEXT PRIMARY KEY,
    ticker            TEXT NOT NULL,
    title             TEXT,
    summary           TEXT,
    url               TEXT,
    published         TEXT,
    sentiment_title   REAL,
    sentiment_summary REAL
)
"""

_CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS analysis_history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker           TEXT    NOT NULL,
    timestamp        TEXT    NOT NULL,
    verdict          TEXT,
    confidence_score REAL,
    avg_sentiment    REAL,
    articles_count   INTEGER
)
"""

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    """Initialize tables."""
    try:
        with _conn() as c:
            c.execute(_CREATE_NEWS_TABLE)
            c.execute(_CREATE_HISTORY_TABLE)
            # Index for faster lookups by ticker
            c.execute("CREATE INDEX IF NOT EXISTS idx_news_ticker ON news (ticker)")
    except Exception as exc:
        logger.error("DB init failed: %s", exc)

def save_news_items(articles: list[dict]):
    """
    Saves a list of articles. 
    Uses 'INSERT OR IGNORE' so duplicate GUIDs are silently skipped.
    """
    sql = """
    INSERT OR IGNORE INTO news (guid, ticker, title, summary, url, published, sentiment_title, sentiment_summary)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        with _conn() as c:
            data = [
                (
                    a['guid'], a['ticker'], a['title'], a['summary'], 
                    a['url'], a['published'].isoformat(),
                    a.get('sentiment_title'), a.get('sentiment_summary')
                )
                for a in articles
            ]
            c.executemany(sql, data)
    except Exception as exc:
        logger.warning("Failed to bulk save news: %s", exc)

def save_analysis(ticker: str, verdict: str, confidence: float, sentiment: float, count: int):
    """Saves a summary verdict of a single analysis run."""
    sql = """
    INSERT INTO analysis_history (ticker, timestamp, verdict, confidence_score, avg_sentiment, articles_count)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    ts = datetime.now(timezone.utc).isoformat()
    try:
        with _conn() as c:
            c.execute(sql, (ticker, ts, verdict, confidence, sentiment, count))
    except Exception as exc:
        logger.warning("Failed to save analysis: %s", exc)

def get_recent_news(ticker: str, limit: int = 10):
    """Fetch news for a ticker to display or analyze."""
    sql = "SELECT * FROM news WHERE ticker = ? ORDER BY published DESC LIMIT ?"
    with _conn() as c:
        rows = c.execute(sql, (ticker, limit)).fetchall()
        return [dict(r) for r in rows]

def get_recent_history(ticker, limit=1):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        sql = "SELECT * FROM analysis_history WHERE ticker = ? ORDER BY timestamp DESC LIMIT ?"
        rows = conn.execute(sql, (ticker, limit)).fetchall()
        return [dict(r) for r in rows]