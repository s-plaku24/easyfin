import json
from datetime import datetime, date
import decimal
from database.db_connection import DatabaseConnection

def insert_raw_data(symbol, data_type, raw_data):
    """Insert raw FMP data into database"""
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            converted_data = convert_data(raw_data)
            json_data = json.dumps(converted_data)
            
            # Delete existing data for this symbol
            delete_query = "DELETE FROM raw_data WHERE symbol = %s"
            db.execute_query(delete_query, (symbol,))
            
            # Insert new data
            insert_query = """
                INSERT INTO raw_data (symbol, raw_data)
                VALUES (%s, %s)
            """
            
            return db.execute_query(insert_query, (symbol, json_data))
    except Exception:
        return False

def get_latest_raw_data(symbol, data_type=None):
    """Get latest raw data for a symbol"""
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return None
            
            query = """
                SELECT raw_data FROM raw_data 
                WHERE symbol = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            """
            
            results = db.fetch_all(query, (symbol,))
            
            if results:
                raw_data = results[0]['raw_data']
                
                if isinstance(raw_data, dict):
                    return raw_data
                elif isinstance(raw_data, str):
                    return json.loads(raw_data)
                else:
                    return raw_data
            return None
    except Exception:
        return None

def get_combined_raw_data(symbol):
    """Get FMP data for a symbol"""
    try:
        return get_latest_raw_data(symbol)
    except Exception:
        return None

def convert_data(obj):
    """Convert data to JSON-serializable format"""
    if isinstance(obj, dict):
        return {str(key): convert_data(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_data(item) for item in obj]
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    elif obj is None:
        return None
    else:
        return obj