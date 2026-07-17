import feedparser

def fetch_rss_data(stock_symbol):
    """
    Fetches raw RSS data for a given stock symbol.
    Returns a list of dicts: [{'title': ..., 'summary': ..., 'guid': ..., 'published': ...}]
    """
    url = f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={stock_symbol}&region=US&lang=en-US'
    feed = feedparser.parse(url)
    
    return [
        {
            "guid": entry.guid,
            "title": entry.title,
            "summary": entry.summary,
            "published": entry.published
        } 
        for entry in feed.entries
    ]