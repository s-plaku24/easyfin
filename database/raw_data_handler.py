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

def cleanup_old_raw_data(days_to_keep=7):
    """Clean up old raw data"""
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
        print(f"[ERROR] Failed to cleanup old raw data: {e}")
        return False

def get_data_size_stats():
    """Get statistics about data sizes in database"""
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return {}
            
            query = """
                SELECT 
                    symbol,
                    LENGTH(raw_data) as data_size,
                    created_at
                FROM raw_data 
                ORDER BY created_at DESC
            """
            
            results = db.fetch_all(query)
            
            stats = {}
            for row in results:
                symbol = row['symbol']
                stats[symbol] = {
                    'size_bytes': row['data_size'],
                    'size_kb': round(row['data_size'] / 1024, 2),
                    'created_at': row['created_at']
                }
            
            return stats
                
    except Exception as e:
        print(f"[ERROR] Failed to get data size stats: {e}")
        return {}

def validate_fmp_data_structure(data):
    """Validate that FMP data has expected structure"""
    try:
        if not isinstance(data, dict):
            return False
        
        # Check for required FMP structure
        if 'symbol' not in data:
            return False
        
        # Should have either quote or historical data
        has_quote = 'quote' in data and data['quote'] is not None
        has_historical = 'historical' in data and data['historical'] is not None
        
        if not (has_quote or has_historical):
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to validate FMP data structure: {e}")
        return False