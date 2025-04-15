import datetime as dt
import feedparser
import nltk
from numpy import median
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from db_models import News, Summary
from database import init_db, session_scope
import requests
import pandas as pd

class StockNews:
    YAHOO_URL = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=%s&region=US&lang=en-US'
    TRADING_URL = 'https://api.worldtradingdata.com/api/v1/history'

    def __init__(self, stocks, save_news=True, closing_hour=20,
                 closing_minute=0, wt_key=None,
                 db_uri='sqlite:///stock_news.db'):
        """
        :param stocks: A list of stock symbols
        :param news_file: Filename of saved news data
        :param summary_file: Filename of saved summary (Stock by day)
        :param save_news: Persist the data to csv or not
        :param closing_hour: attach news for the next trading day after this
        :param closing_minute: attach news for the next trading day after this
        :param wt_key: key
        """

        self.stocks = stocks
        self.save_news = save_news
        self.closing_hour = closing_hour
        self.closing_minute = closing_minute
        self.wt_key = wt_key
        self.db_uri = db_uri
        self.engine = init_db(db_uri)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    def read_rss(self):
        """
        :return: True if successful
        """
        with session_scope(self.engine) as session:
            for stock in self.stocks:

                """Init new Parser"""
                feed = feedparser.parse(self.YAHOO_URL % stock)

                for entry in feed.entries:

                    """Check if news exists"""
                    if session.query(News).filter_by(guid=entry.guid).first():
                        continue

                    """Analyze the sentiment"""
                    sia = SentimentIntensityAnalyzer()
                    _summary = sia.polarity_scores(entry.summary)['compound']
                    _title = sia.polarity_scores(entry.title)['compound']

                    """Parse the date"""
                    pub_date = dt.datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S +0000')
                    p_date = f"{stock}_{pub_date.strftime('%Y-%m-%d')}"

                    """Add new entry"""
                    news_item = News(
                        guid=entry.guid,
                        stock=stock,
                        title=entry.title,
                        summary=entry.summary,
                        published=pub_date,
                        p_date=p_date,
                        sentiment_summary=_summary,
                        sentiment_title=_title
                    )
                    session.add(news_item)
        return True

    def summarize(self):
        """
        Summarize news by day and get the Stock Value
        :return: <int> number of requests made
        """

        session = self.Session()

        """Count Requests"""
        r_count = 0

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

                params = {
                    'symbol': summary.stock,
                    'date_from': summary.check_day.strftime('%Y-%m-%d'),
                    'date_to': summary.check_day.strftime('%Y-%m-%d'),
                    'api_token': self.wt_key
                }

                r = requests.get(url=self.TRADING_URL, params=params)
                r_count += 1

                """Extract open and close"""
                if r.status_code == 200:
                    data = r.json()
                    history = data.get('history', {})

                    if history:
                        day_data = history.get(summary.check_day.strftime('%Y-%m-%d'), {})
                        if day_data:
                            summary.open = float(day_data['open'])
                            summary.close = float(day_data['close'])
                            summary.high = float(day_data['high'])
                            summary.low = float(day_data['low'])
                            summary.volume = float(day_data['volume'])
                            summary.change = 'win' if summary.close > summary.open else 'loss'
        return r_count

    @staticmethod
    def _median_avg(values):
        """
        Return AVG and Median
        :param values: Value Name
        :return:
        """
        if not values:
            return 0.0, 0.0
        avg = sum(values) / len(values)
        med = median(values)

        return avg, med

    def _get_check_date(self, dt_check):
        """
        Check which day needs to be checked for a news date
        :param dt_check: datetime
        :return: dt.datetime
        """

        """Get closing date"""
        dt_close = dt.datetime(dt_check.year, dt_check.month, dt_check.day, self.closing_hour, self.closing_minute, 0)

        """If the CheckDate is later than CloseDate, add one day"""
        if dt_check > dt_close:
            dt_check += dt.timedelta(days=1)

        """If the CheckDate is a Saturday, add 2 days"""
        if dt_check.weekday() == 5:
            dt_check += dt.timedelta(days=2)

        """If the CheckDate is a Sunday, add 1 day"""
        if dt_check.weekday() == 6:
            dt_check += dt.timedelta(days=1)

        """return date to check"""
        return dt_check

    def get_summary(self):
        """Retrieve and display summary data from database"""
        with session_scope(self.engine) as session:
            summaries = session.query(Summary).all()
            data = [{
                'id': s.id,
                'stock': s.stock,
                'news_date': s.news_dt.date(),
                'check_date': s.check_day.date(),
                #'open': s.open,
                #'close': s.close,
                #'change': s.change,
                'sentiment_avg': s.sentiment_summary_avg
            } for s in summaries]

            df = pd.DataFrame(data)
            if df.empty:
                print("No summary data available")
            else:
                print(df.to_string(index=False))
            return df