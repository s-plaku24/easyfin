import json
from datetime import datetime
from database.db_connection import DatabaseConnection

def insert_raw_data(symbol, data_type, raw_data):
    """
    Insert raw data from yfinance API into raw_data table
    """
    try:
        print(f"DEBUG: Attempting to insert {data_type} data for {symbol}")
        
        with DatabaseConnection() as db:
            if not db.connection:
                print("DEBUG: Database connection failed in insert_raw_data")
                return False
            
            print("DEBUG: Database connection successful")
            
            # Convert pandas objects to JSON-serializable format
            def convert_data(obj):
                """Recursively convert pandas objects to JSON-serializable format"""
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
            
            # Convert the entire data structure
            converted_data = convert_data(raw_data)
            
            # Convert to JSON string
            json_data = json.dumps(converted_data)
            print(f"DEBUG: JSON data length: {len(json_data)} characters")
            
            # Delete existing data for this symbol and type (replace strategy)
            delete_query = "DELETE FROM raw_data WHERE symbol = %s AND type = %s"
            db.execute_query(delete_query, (symbol, data_type))
            
            # Insert new data
            insert_query = """
                INSERT INTO raw_data (symbol, type, raw_data)
                VALUES (%s, %s, %s)
            """
            
            params = (symbol, data_type, json_data)
            print(f"DEBUG: About to execute query with symbol={symbol}, type={data_type}")
            
            if db.execute_query(insert_query, params):
                print(f"DEBUG: Successfully inserted {data_type} data for {symbol}")
                return True
            else:
                print(f"DEBUG: Failed to execute query for {symbol}")
                return False
                
    except Exception as e:
        print(f"DEBUG: Exception in insert_raw_data for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_latest_raw_data(symbol, data_type):
    """
    Get the latest raw data for a symbol and type
    """
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
        print(f"Error getting raw data for {symbol}: {str(e)}")
        return None

def get_combined_raw_data(symbol):
    """
    Get both ticker and market data for a symbol
    """
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
        print(f"Error getting combined data for {symbol}: {str(e)}")
        return None

def cleanup_old_raw_data(days_to_keep=7):
    """
    Clean up old raw data
    """
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
        print(f"Error cleaning up old data: {str(e)}")
        return False