import pandas as pd
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from db_models import Base, CompositeScore
from sqlalchemy.exc import SQLAlchemyError

def get_composite_score(db_uri, fred_key, weights=None, save=True):
    """
    Get composite score using today's sentiment and FRED macro data
    :param db_uri: Database connection string
    :param fred_key: FRED API key
    :param weights: Dictionary of weights for composite score
    :return: DataFrame with composite scores
    """

    '''Weights'''
    weights = weights or {
        'sentiment': 0.8,
        #'interest_rates': 0.2,
        'vix': 0.2,
        #'unemployment': 0.05
    }

    '''Get sentiment from database'''
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    today = datetime.today().strftime('%Y-%m-%d')

    query = f"""
    SELECT stock, sentiment_summary_avg
    FROM summary
    WHERE DATE(check_day) = '{today}'
    """
    sentiment_df = pd.read_sql(query, engine)

    if sentiment_df.empty:
        print("No sentiment data for today")
        return pd.DataFrame()

    '''Get FRED data'''
    fred_series = {
        #'interest_rates': 'FEDFUNDS',
        'vix': 'VIXCLS',
        #'unemployment': 'UNRATE'
    }

    def get_fred_value(series_id):
      """Helper to get FRED data with daily values for VIX"""
      today = datetime.today()
      start = today.replace(day=1).strftime('%Y-%m-%d')
      end = today.strftime('%Y-%m-%d')

      params = {
          'series_id': series_id,
          'api_key': fred_key,
          'file_type': 'json',
          'observation_start': start,
          'observation_end': end,
      }

      '''Configure frequency based on series'''
      if series_id == 'VIXCLS':
          params['frequency'] = 'd'
      #else:
          #params['frequency'] = 'm'
          #params['aggregation_method'] = 'avg'

      try:
          response = requests.get('https://api.stlouisfed.org/fred/series/observations', params=params)
          response.raise_for_status()
          data = response.json()

          if not data.get('observations'):
              print(f"No data found for {series_id} between {start} and {end}")
              return 0.0

          '''Get all valid numerical values (skip '.' and empty strings)'''
          valid_observations = [
              float(obs['value'])
              for obs in data['observations']
              if obs['value'] not in {'.', ''}
          ]

          if not valid_observations:
              print(f"No valid numerical data for {series_id}")
              return 0.0

          '''Return most recent value for daily series, average for monthly'''
          if series_id == 'VIXCLS':
              return valid_observations[-1]  # Latest daily value
          else:
              return sum(valid_observations)/len(valid_observations)  # Monthly average

      except Exception as e:
          print(f"Error getting {series_id}: {str(e)}")
          return 0.0

    '''Get all FRED values'''
    macro_data = {
        #'interest_rates': get_fred_value(fred_series['interest_rates']),
        'vix': get_fred_value(fred_series['vix']),
        #'unemployment': get_fred_value(fred_series['unemployment'])
    }

    '''Calculate composite score'''
    composite_scores = []
    for _, row in sentiment_df.iterrows():
        normalised_sentiment = (row['sentiment_summary_avg'] + 1) / 2 * 100
        vix_value = macro_data['vix']
        normalised_vix = max(0, min(100, (vix_value - 10) / (80 - 10) * 100))
        score = (
            normalised_sentiment * weights['sentiment'] +
            normalised_vix * weights['vix']
            #row['sentiment_summary_avg'] * weights['sentiment'] +
            #macro_data['interest_rates'] * weights['interest_rates'] +
            #macro_data['vix'] * weights['vix'] +
            #macro_data['unemployment'] * weights['unemployment']
        )
        final_score = max(0, min(100, score))
        composite_scores.append({
            'stock': row['stock'],
            'date': today,
            'sentiment': row['sentiment_summary_avg'],
            **macro_data,
            'composite_score': final_score
        })
    composite_df = pd.DataFrame(composite_scores)
    grouped_df = composite_df.groupby('stock').agg({
        'date': 'first',
        'vix': 'first',
        'sentiment': 'mean',
        'composite_score': 'mean'
    }).reset_index()

    if save and not grouped_df.empty:
        save_composite_score(db_uri, grouped_df)

    return grouped_df

def save_composite_score(db_uri, composite_df):
    """Save composite scores to database"""
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(db_uri)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    try:
        session = Session()
        today = datetime.today().date()
        
        '''Delete existing entries for today - prevent duplicates'''
        session.query(CompositeScore)\
            .filter(CompositeScore.date == today)\
            .delete()
            
        '''Convert DataFrame to database objects'''
        records = []
        for _, row in composite_df.iterrows():
            records.append(CompositeScore(
                stock=row['stock'],
                date=today,
                sentiment=row['sentiment'],
                vix=row['vix'],
                composite_score=row['composite_score']
            ))
        
        session.add_all(records)
        session.commit()
        print(f"Saved {len(records)} composite scores for {today}")
        
    except Exception as e:
        session.rollback()
        print(f"Error saving scores: {str(e)}")
    finally:
        session.close()

def get_historical(db_uri, days=30, stock=None):
    """Retrieve historical composite scores with daily averages"""
    engine = create_engine(db_uri)
    
    base_query = """
        SELECT 
            stock,
            date,
            AVG(sentiment) as sentiment,
            AVG(composite_score) as composite_score,
            AVG(vix) as vix
        FROM composite_scores
        WHERE date >= date('now', '-%d days')
    """ % days
    
    if stock:
        base_query += f" AND stock = '{stock}'"
    
    base_query += """
        GROUP BY stock, date
        ORDER BY date DESC, stock
    """
    
    try:
        return pd.read_sql(base_query, engine)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Database error: {str(e)}") from e