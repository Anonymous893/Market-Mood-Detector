import datetime as dt
import requests
from numpy import median
from ..db_models import Summary, News
from ..database import session_scope

class MarketAnalyzer:
    TRADING_URL = 'https://api.worldtradingdata.com/api/v1/history'

    def __init__(self, engine, wt_key):
        self.engine = engine
        self.wt_key = wt_key

    def perform_daily_summary(self):
        with session_scope(self.engine) as session:
            for news_item in session.query(News).all():
                """Parse the Date and Find ID"""
                check_date = self._get_check_date(news_item.published)
                summary_id = f"{news_item.stock}_{news_item.published.strftime('%Y-%m-%d')}"

                if session.query(Summary).filter_by(id=summary_id).first():
                    continue

                same_day_news = session.query(News).filter(News.p_date == news_item.p_date).all()

                """Make Median and AVG"""
                avg_summary, med_summary = self._median_avg([n.sentiment_summary for n in same_day_news])
                avg_title, med_title = self._median_avg([n.sentiment_title for n in same_day_news])

                """Add new entry"""
                summary = Summary(
                    id=summary_id,
                    stock=news_item.stock,
                    news_dt=news_item.published,
                    check_day=check_date,
                    change='UNCHECKED',
                    sentiment_summary_avg=avg_summary,
                    sentiment_summary_med=med_summary,
                    sentiment_title_avg=avg_title,
                    sentiment_title_med=med_title
                )
                session.add(summary)

            """Update all 'UNCHECKED' columns"""
            unchecked = session.query(Summary).filter(Summary.change == 'UNCHECKED').all()

            """Go through all unchecked"""
            for summary in unchecked:
                """If the check_day is not today, continue"""
                if summary.check_day.date() >= dt.date.today():
                    continue

                market_data = self.fetch_market_data(summary)
                history = market_data.get('history', {})

                if history:
                    day_data = history.get(summary.check_day.strftime('%Y-%m-%d'), {})
                    if day_data:
                        summary.open = float(day_data['open'])
                        summary.close = float(day_data['close'])
                        summary.change = 'win' if summary.close > summary.open else 'loss'

    def fetch_market_data(self, summary_item):
        """Handles the external API request."""
        params = {
            'symbol': summary_item.stock,
            'date_from': summary_item.check_day.strftime('%Y-%m-%d'),
            'date_to': summary_item.check_day.strftime('%Y-%m-%d'),
            'api_token': self.wt_key
        }
        r = requests.get(url=self.TRADING_URL, params=params)
        return r.json() if r.status_code == 200 else {}

    @staticmethod
    def calculate_stats(values):
        ######
        if not values: return 0.0, 0.0
        return sum(values) / len(values), median(values)