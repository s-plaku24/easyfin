import json
from datetime import datetime
from database.db_connection import DatabaseConnection

def insert_raw_data(symbol, data_type, raw_data):
    """Insert raw FMP data into database (data_type parameter kept for compatibility)"""
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            # Convert data to JSON-serializable format
            def convert_data(obj):
                from datetime import datetime, date
                import decimal
                
                if isinstance(obj, dict):
                    new_dict = {}
                    for key, value in obj.items():
                        new_dict[str(key)] = convert_data(value)
                    return new_dict
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
            
            converted_data = convert_data(raw_data)
            json_data = json.dumps(converted_data)
            
            # Delete existing data for this symbol (since no type column)
            delete_query = "DELETE FROM raw_data WHERE symbol = %s"
            db.execute_query(delete_query, (symbol,))
            
            # Insert new data (no type column)
            insert_query = """
                INSERT INTO raw_data (symbol, raw_data)
                VALUES (%s, %s)
            """
            
            params = (symbol, json_data)
            
            return db.execute_query(insert_query, params)
                
    except Exception as e:
        print(f"[ERROR] Failed to insert raw data for {symbol}: {e}")
        return False

def get_latest_raw_data(symbol, data_type=None):
    """Get latest raw data for a symbol (data_type parameter kept for compatibility)"""
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
                
                # Check if it's already a dict (PostgreSQL JSONB) or needs JSON parsing
                if isinstance(raw_data, dict):
                    return raw_data
                elif isinstance(raw_data, str):
                    return json.loads(raw_data)
                else:
                    print(f"[WARN] Unexpected raw_data type for {symbol}: {type(raw_data)}")
                    return raw_data
            else:
                return None
                
    except Exception as e:
        print(f"[ERROR] Failed to get raw data for {symbol}: {e}")
        return None

def get_combined_raw_data(symbol):
    """Get FMP data for a symbol"""
    try:
        return get_latest_raw_data(symbol)
                
    except Exception as e:
        print(f"[ERROR] Failed to get combined raw data for {symbol}: {e}")
        return None