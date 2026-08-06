import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine
from stock_news import StockNews

from app import app

@pytest.fixture
def client():
    """Configure Flask test client with in-memory database."""
    app.config['TESTING'] = True
    app.config['DB_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        yield client

# --------------------------
# Test Cases for Each Endpoint
# --------------------------

def test_fetch_news_success(client):
    """Test successful news fetching with valid stock list."""
    test_data = {'stocks': ['AAPL', 'MSFT']}
    
    with patch('app.StockNews') as mock_stocknews:
        mock_instance = mock_stocknews.return_value
        mock_instance.read_rss.return_value = None
        
        response = client.post('/news', json=test_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == "success"

def test_fetch_news_empty_stocks(client):
    """Test news endpoint with empty stock list."""
    response = client.post('/news', json={'stocks': []})
    assert response.status_code == 200  # Should handle empty list gracefully

def test_fetch_news_error_handling(client):
    """Test error handling in news endpoint."""
    with patch('app.StockNews') as mock_stocknews:
        mock_instance = mock_stocknews.return_value
        mock_instance.read_rss.side_effect = Exception("Test error")
        
        response = client.post('/news', json={'stocks': ['AAPL']})
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Test error" in data['error']

def test_get_summary_success(client):
    """Test successful summary retrieval."""
    mock_summary = pd.DataFrame({
        'stock': ['AAPL'],
        'positive': [5],
        'neutral': [3],
        'negative': [2]
    })
    
    with patch('app.StockNews') as mock_stocknews:
        mock_instance = mock_stocknews.return_value
        mock_instance.get_summary.return_value = mock_summary
        
        response = client.get('/summary')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1

def test_composite_score_success(client):
    """Test successful composite score retrieval."""
    mock_df = pd.DataFrame({
        'stock': ['AAPL'],
        'score': [0.85]
    }, index=[datetime.today()])
    
    with patch('app.get_composite_score') as mock_composite:
        mock_composite.return_value = mock_df
        
        response = client.get('/composite-score')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'scores' in data
        assert len(data['scores']) == 1

def test_historical_scores_success(client):
    """Test historical scores with valid days parameter."""
    mock_data = pd.DataFrame({
        'stock': ['AAPL'],
        'date': [datetime.today().strftime('%Y-%m-%d')],
        'composite_score': [0.85]
    })
    
    with patch('app.get_historical') as mock_historical:
        mock_historical.return_value = mock_data
        
        response = client.get('/historical-scores?days=7')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['lookback_days'] == 7
        assert len(data['scores']) == 1

def test_run_full_analysis(client):
    """Test full analysis workflow."""
    test_stocks = ['AAPL', 'MSFT']
    
    mock_composite = pd.DataFrame({
        'stock': ['AAPL'],
        'composite_score': [0.9],
        'date': [datetime.today().strftime('%Y-%m-%d')]
    })
    
    with patch('app.StockNews') as mock_stocknews, \
         patch('app.get_composite_score') as mock_composite_func:

        mock_instance = mock_stocknews.return_value
        mock_instance.read_rss.return_value = None  # Add this line
        mock_composite_func.return_value = mock_composite

        response = client.post('/run-analysis', json={'stocks': test_stocks})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == "success"
        assert len(data['composite_scores']) == 1

'''def test_run_full_analysis(client):
    """Test full analysis workflow."""
    test_stocks = ['AAPL', 'MSFT']
    
    mock_composite = pd.DataFrame({
        'stock': ['AAPL'],
        'composite_score': [0.9],
        'date': [datetime.today().strftime('%Y-%m-%d')]
    })
    
    mock_historical = pd.DataFrame({
        'stock': ['AAPL'],
        'date': ['2023-01-01'],
        'composite_score': [0.8]
    })
    
    with patch('app.StockNews') as mock_stocknews, \
         patch('app.get_composite_score') as mock_composite_func, \
         patch('app.get_historical') as mock_historical_func:

        mock_instance = mock_stocknews.return_value
        mock_instance.summarize.return_value = 5
        mock_instance.get_summary.return_value = pd.DataFrame()
        mock_composite_func.return_value = mock_composite
        mock_historical_func.return_value = mock_historical

        response = client.post('/run-analysis', json={'stocks': test_stocks})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == "success"
        assert data['requests_used'] == 5
        assert len(data['composite_scores']) == 1
        assert len(data['historical_scores']) == 1'''

# --------------------------
# Error Cases
# --------------------------

def test_composite_score_empty(client):
    """Test composite score endpoint with empty data."""
    with patch('app.get_composite_score') as mock_composite:
        mock_composite.return_value = pd.DataFrame()
        
        response = client.get('/composite-score')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "No composite scores" in data['message']

def test_historical_scores_invalid_days(client):
    """Test historical scores with invalid days parameter."""
    response = client.get('/historical-scores?days=invalid')
    assert response.status_code == 400  # Bad request