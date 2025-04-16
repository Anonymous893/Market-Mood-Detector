from flask import Flask, jsonify, request
import os
from datetime import datetime
from stock_news import StockNews
from composite import get_composite_score, get_historical
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['DB_URI'] = 'sqlite:///stock_news.db'

@app.route('/news', methods=['POST'])
def fetch_news():
    try:
        stocks = request.json.get('stocks', [])
        stock_news = StockNews(
            stocks=stocks,
            wt_key=os.getenv('WT_KEY'),
            db_uri=app.config['DB_URI']
        )
        stock_news.read_rss()
        return jsonify({"status": "success", "message": "News updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/summary', methods=['GET'])
def get_summary():
    try:
        stock_news = StockNews(
            stocks=[],
            db_uri=app.config['DB_URI']
        )
        summary_df = stock_news.get_summary()
        return jsonify(summary_df.to_dict(orient='records'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/composite-score', methods=['GET'])
def composite_score():
    try:
        df = get_composite_score(
            db_uri=app.config['DB_URI'],
            fred_key=os.getenv('FRED_KEY'),
            save=True
        )
        
        if df.empty:
            return jsonify({"message": "No composite scores available for today"}), 404
            
        return jsonify({
            "date": datetime.today().strftime('%Y-%m-%d'),
            "scores": df.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/historical-scores', methods=['GET'])
def historical_scores():
    try:
        days = request.args.get('days', default=7, type=int)
        
        historical_df = get_historical_composite_scores(
            db_uri=app.config['DB_URI'],
            days=days
        )
        
        if historical_df.empty:
            return jsonify({"message": "No historical scores found"}), 404
            
        return jsonify({
            "lookback_days": days,
            "scores": historical_df.to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/run-analysis', methods=['POST'])
def run_full_analysis():
    try:
        stocks = request.json.get('stocks', ['AAPL','MSFT','NVDA','META','TSLA','AMZN','GOOG'])
        
        stock_news = StockNews(
            stocks=stocks,
            wt_key=os.getenv('WT_KEY'),
            db_uri=app.config['DB_URI']
        )
        
        stock_news.read_rss()
        requests_made = stock_news.summarize()
        
        composite_df = get_composite_score(
            db_uri=app.config['DB_URI'],
            fred_key=os.getenv('FRED_KEY'),
            save=True
        )
        
        historical_df = get_historical_composite_scores(
            db_uri=app.config['DB_URI'],
            days=7
        )

        return jsonify({
            "status": "success",
            "requests_used": requests_made,
            "composite_scores": composite_df.to_dict(orient='records'),
            "historical_scores": historical_df.to_dict(orient='records')
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)