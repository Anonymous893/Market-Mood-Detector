import datetime as dt
from ..scrapers.sources import fetch_rss_data
from ..ml.finbert import FinBertAnalyzer
from ..database import session_scope
from ..db_models import News

def process_and_save_news(stock_symbol, engine):
    """Orchestrates fetching, analyzing, and saving."""
    raw_entries = fetch_rss_data(stock_symbol)
    analyzer = FinBertAnalyzer()
    
    with session_scope(engine) as session:
        for entry in raw_entries:
            if session.query(News).filter_by(guid=entry['guid']).first():
                continue
                
            sentiment = analyzer.calculate_sentiment(entry['summary'])
            
            news_item = News(
                guid=entry['guid'],
                stock=stock_symbol,
                title=entry['title'],
                summary=entry['summary'],
                published=dt.datetime.strptime(entry['published'], '%a, %d %b %Y %H:%M:%S +0000'),
                sentiment_summary=sentiment
            )
            session.add(news_item)