from flask import Flask, jsonify, request
import os
from datetime import datetime
from stock_news import StockNews
from composite import get_composite_score, get_historical
from dotenv import load_dotenv
from flask_cors import CORS
from sqlalchemy import create_engine
import traceback
from db_models import Base 
from pathlib import Path

load_dotenv()

BASEDIR = Path(__file__).parent.resolve()
app = Flask(__name__)
app.config['DB_URI'] = f'sqlite:///{BASEDIR}/stock_news.db'
CORS(app)

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
        days = int(request.args.get('days', 7))
        stock = request.args.get('stock')
    except ValueError:
        return jsonify({"error": "Invalid days parameter"}), 400
    
    try:
        df = get_historical(
            db_uri=app.config['DB_URI'], 
            days=days, stock=stock.upper() if stock else None
        )
        return jsonify({
            "lookback_days": days,
            "scores": df.to_dict(orient='records')
        })
    except Exception as e:
        app.logger.error(f"Historical scores error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/run-analysis', methods=['POST'])
def run_full_analysis():
    try:
        stocks = request.json.get('stocks', ['AAPL','MSFT','NVDA','META','TSLA','AMZN','GOOG'])
        
        engine = create_engine(app.config['DB_URI'])
        Base.metadata.create_all(engine)
        
        stock_news = StockNews(
            stocks=stocks,
            wt_key=os.getenv('WT_KEY'),
            db_uri=app.config['DB_URI']
        )
        stock_news.read_rss()
        stock_news.summarize()
        composite_df = get_composite_score(
            db_uri=app.config['DB_URI'],
            fred_key=os.getenv('FRED_KEY'),
            save=True
        )
        
        return jsonify({
            "status": "success",
            "composite_scores": composite_df.to_dict(orient='records')
        })
        
    except Exception as e:
        app.logger.error(f"Analysis failed: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)