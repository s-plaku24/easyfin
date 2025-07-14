from database.db_connection import DatabaseConnection

def insert_or_update_stock(symbol, name=None, country=None, sector=None, region=None, 
                          industry=None, exchange=None, currency=None, ipo_year=None, isin=None):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            check_query = "SELECT symbol FROM stocks WHERE symbol = %s"
            existing = db.fetch_all(check_query, (symbol,))
            
            if existing:
                update_query = """
                    UPDATE stocks SET 
                        name = COALESCE(%s, name),
                        country = COALESCE(%s, country),
                        sector = COALESCE(%s, sector),
                        region = COALESCE(%s, region),
                        industry = COALESCE(%s, industry),
                        exchange = COALESCE(%s, exchange),
                        currency = COALESCE(%s, currency),
                        ipo_year = COALESCE(%s, ipo_year),
                        isin = COALESCE(%s, isin)
                    WHERE symbol = %s
                """
                params = (name, country, sector, region, industry, exchange, 
                         currency, ipo_year, isin, symbol)
                return db.execute_query(update_query, params)
            else:
                insert_query = """
                    INSERT INTO stocks (symbol, name, country, sector, region, industry, 
                                      exchange, currency, ipo_year, isin)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (symbol, name, country, sector, region, industry, 
                         exchange, currency, ipo_year, isin)
                return db.execute_query(insert_query, params)
                
    except Exception as e:
        print(f"[ERROR] Failed to insert/update stock {symbol}: {e}")
        return False

def get_stock_info(symbol):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return None
            
            query = "SELECT * FROM stocks WHERE symbol = %s"
            results = db.fetch_all(query, (symbol,))
            
            if results:
                return dict(results[0])
            return None
                
    except Exception as e:
        print(f"[ERROR] Failed to get stock info for {symbol}: {e}")
        return None

def get_all_stocks():
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return []
            
            query = "SELECT * FROM stocks ORDER BY symbol"
            results = db.fetch_all(query)
            
            return [dict(row) for row in results]
                
    except Exception as e:
        print(f"[ERROR] Failed to get all stocks: {e}")
        return []

def extract_stock_info_from_fmp(fmp_data):
    """Extract stock information from FMP data structure"""
    try:
        if not fmp_data or 'quote' not in fmp_data:
            return {}
        
        quote = fmp_data['quote']
        
        if not quote:
            return {}
        
        extracted = {
            'name': quote.get('name'),
            'country': None,  # FMP doesn't provide country in quote endpoint
            'sector': None,   # Would need profile endpoint (not used to save tokens)
            'industry': None, # Would need profile endpoint (not used to save tokens)
            'exchange': quote.get('exchange'),
            'currency': None, # Not provided in quote endpoint
            'ipo_year': None, # Not provided in quote endpoint  
            'isin': None      # Not provided in quote endpoint
        }
        
        return extracted
        
    except Exception as e:
        print(f"[ERROR] Failed to extract stock info from FMP data: {e}")
        return {}