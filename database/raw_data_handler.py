import json
from datetime import datetime
from database.db_connection import DatabaseConnection

def insert_raw_data(symbol, data_type, raw_data):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            def convert_data(obj):
                import pandas as pd
                import numpy as np
                from datetime import datetime, date
                
                if isinstance(obj, dict):
                    new_dict = {}
                    for key, value in obj.items():
                        if isinstance(key, (pd.Timestamp, datetime, date)):
                            new_key = key.isoformat()
                        else:
                            new_key = str(key)
                        new_dict[new_key] = convert_data(value)
                    return new_dict
                elif isinstance(obj, (list, tuple)):
                    return [convert_data(item) for item in obj]
                elif isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
                    return obj.isoformat()
                elif isinstance(obj, (datetime, date)):
                    return obj.isoformat()
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif pd.isna(obj):
                    return None
                else:
                    return obj
            
            converted_data = convert_data(raw_data)
            json_data = json.dumps(converted_data)
            
            delete_query = "DELETE FROM raw_data WHERE symbol = %s AND type = %s"
            db.execute_query(delete_query, (symbol, data_type))
            
            insert_query = """
                INSERT INTO raw_data (symbol, type, raw_data)
                VALUES (%s, %s, %s)
            """
            
            params = (symbol, data_type, json_data)
            
            return db.execute_query(insert_query, params)
                
    except Exception as e:
        return False

def get_latest_raw_data(symbol, data_type):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return None
            
            query = """
                SELECT raw_data FROM raw_data 
                WHERE symbol = %s AND type = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            
            results = db.fetch_all(query, (symbol, data_type))
            
            if results:
                return json.loads(results[0]['raw_data'])
            else:
                return None
                
    except Exception as e:
        return None

def get_combined_raw_data(symbol):
    try:
        ticker_data = get_latest_raw_data(symbol, 'ticker')
        market_data = get_latest_raw_data(symbol, 'market')
        
        if ticker_data and market_data:
            return {
                'symbol': symbol,
                'ticker_data': ticker_data,
                'market_data': market_data
            }
        
        return None
                
    except Exception as e:
        return None

def cleanup_old_raw_data(days_to_keep=7):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            query = """
                DELETE FROM raw_data 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """
            
            return db.execute_query(query, (days_to_keep,))
                
    except Exception as e:
        return False