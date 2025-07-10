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
        return []

def extract_stock_info_from_ticker(ticker_data):
    try:
        if not ticker_data or 'info' not in ticker_data:
            return {}
        
        info = ticker_data['info']
        
        extracted = {
            'name': info.get('longName') or info.get('shortName'),
            'country': info.get('country'),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'exchange': info.get('exchange'),
            'currency': info.get('currency'),
            'ipo_year': info.get('ipoYear'),
            'isin': info.get('isin')
        }
        
        return extracted
        
    except Exception as e:
        return {}