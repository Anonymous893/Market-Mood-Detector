from .stock_news import StockNews
from .composite import get_composite_score, get_historical

def main():
    sn = StockNews(
        stocks=['AAPL','MSFT', 'NVDA', 'META', 'TSLA', 'AMZN', 'GOOG'],
        wt_key='c7715110619adf30614fdb3f2973327d',
    )
    
    sn.read_rss()
    requests_made = sn.summarize()
    print(f"\nMade {requests_made} API requests to World Trading Data")
    
    print("\nNews Summary:")
    sn.get_summary()
    
    print("\nComposite Scores:")
    result = get_composite_score(
        db_uri='sqlite:///stock_news.db',
        fred_key='6cc5c48512bcfe2f2fa215546f0a7add'
    )
    print(result.to_string(index=False))

    print("\nHistorical Scores:")
    historical_scores = get_historical(
        db_uri='sqlite:///stock_news.db', 
        days=7)
    print(historical_scores.to_string(index=False))

if __name__ == "__main__":
    main()