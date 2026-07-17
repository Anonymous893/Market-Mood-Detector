from celery import Celery
from .scrapers.rss import fetch_rss_data
from .ml.finbert import FinBertAnalyzer
from .services.persistence import save_sentiment

# Point to Redis running in Docker
celery_app = Celery('tasks', broker='redis://localhost:6379/0')

@celery_app.task
def process_stock_sentiment(stock_symbol):
    raw_data = fetch_rss_data(stock_symbol)
    
    analyzer = FinBertAnalyzer()
    sentiment_score = analyzer.calculate_sentiment(raw_data)
    
    save_sentiment(stock_symbol, sentiment_score)
    
    return f"Completed analysis for {stock_symbol}"