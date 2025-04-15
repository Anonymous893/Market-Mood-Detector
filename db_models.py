from sqlalchemy import Column, String, Float, DateTime, Integer, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class News(Base):
    __tablename__ = 'news'
    guid = Column(String, primary_key=True)
    stock = Column(String)
    title = Column(String)
    summary = Column(String)
    published = Column(DateTime)
    p_date = Column(String)
    sentiment_summary = Column(Float)
    sentiment_title = Column(Float)

class Summary(Base):
    __tablename__ = 'summary'
    id = Column(String, primary_key=True)
    stock = Column(String)
    news_dt = Column(DateTime)
    check_day = Column(DateTime)
    open = Column(Float)
    close = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    change = Column(String)
    sentiment_summary_avg = Column(Float)
    sentiment_summary_med = Column(Float)
    sentiment_title_avg = Column(Float)
    sentiment_title_med = Column(Float)