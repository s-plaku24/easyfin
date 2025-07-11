import requests
import time
import json
from config import FMP_CONFIG, DATA_LIMITS

def fetch_fmp_quote(symbol):
    """Fetch current market data from FMP Quote endpoint"""
    try:
        url = f"{FMP_CONFIG['base_url']}/quote/{symbol}"
        params = {'apikey': FMP_CONFIG['api_key']}
        
        response = requests.get(url, params=params, timeout=FMP_CONFIG['timeout'])
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                # Extract essential fields to minimize token usage
                quote = data[0]
                essential_quote = {
                    'symbol': quote.get('symbol'),
                    'name': quote.get('name'),
                    'price': quote.get('price'),
                    'change': quote.get('change'),
                    'changesPercentage': quote.get('changesPercentage'),
                    'dayLow': quote.get('dayLow'),
                    'dayHigh': quote.get('dayHigh'),
                    'yearHigh': quote.get('yearHigh'),
                    'yearLow': quote.get('yearLow'),
                    'marketCap': quote.get('marketCap'),
                    'volume': quote.get('volume'),
                    'avgVolume': quote.get('avgVolume'),
                    'open': quote.get('open'),
                    'previousClose': quote.get('previousClose'),
                    'eps': quote.get('eps'),
                    'pe': quote.get('pe'),
                    'exchange': quote.get('exchange'),
                    'priceAvg50': quote.get('priceAvg50'),
                    'priceAvg200': quote.get('priceAvg200'),
                    'sharesOutstanding': quote.get('sharesOutstanding')
                }
                return essential_quote
            else:
                print(f"[WARN] Empty quote response for {symbol}")
                return None
        else:
            print(f"[ERROR] Quote API failed for {symbol}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Failed to fetch quote for {symbol}: {e}")
        return None

def fetch_fmp_historical(symbol):
    """Fetch historical price data from FMP Historical endpoint"""
    try:
        url = f"{FMP_CONFIG['base_url']}/historical-price-full/{symbol}"
        params = {
            'apikey': FMP_CONFIG['api_key'],
            'timeseries': DATA_LIMITS['historical_days']  # Limited to save tokens
        }
        
        response = requests.get(url, params=params, timeout=FMP_CONFIG['timeout'])
        
        if response.status_code == 200:
            data = response.json()
            if data and 'historical' in data:
                historical = data['historical']
                
                # Keep essential fields only to minimize tokens
                essential_historical = []
                for record in historical:
                    essential_record = {
                        'date': record.get('date'),
                        'open': record.get('open'),
                        'high': record.get('high'),
                        'low': record.get('low'),
                        'close': record.get('close'),
                        'volume': record.get('volume'),
                        'change': record.get('change'),
                        'changePercent': record.get('changePercent')
                    }
                    essential_historical.append(essential_record)
                
                return {
                    'symbol': data.get('symbol'),
                    'historical': essential_historical
                }
            else:
                print(f"[WARN] No historical data for {symbol}")
                return None
        else:
            print(f"[ERROR] Historical API failed for {symbol}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Failed to fetch historical data for {symbol}: {e}")
        return None

def fetch_fmp_stock_data(symbol):
    """Fetch both quote and historical data for a stock"""
    try:
        print(f"[INFO] Fetching FMP data for {symbol}")
        
        # Fetch quote data (current market data)
        quote_data = fetch_fmp_quote(symbol)
        
        # Small delay to respect rate limits
        time.sleep(1)
        
        # Fetch historical data
        historical_data = fetch_fmp_historical(symbol)
        
        if quote_data or historical_data:
            stock_data = {
                'symbol': symbol,
                'quote': quote_data,
                'historical': historical_data
            }
            
            # Check data size and truncate if needed for Groq token limits
            data_json = json.dumps(stock_data)
            if len(data_json) > DATA_LIMITS['max_json_size']:
                print(f"[WARN] Data for {symbol} too large ({len(data_json)} chars), truncating...")
                stock_data = truncate_stock_data(stock_data)
            
            print(f"[SUCCESS] Fetched FMP data for {symbol}")
            return stock_data
        else:
            print(f"[ERROR] No data returned for {symbol}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Failed to fetch FMP data for {symbol}: {e}")
        return None

def truncate_stock_data(stock_data):
    """Truncate data to fit within token limits"""
    try:
        # First, reduce historical data
        if stock_data.get('historical') and stock_data['historical'].get('historical'):
            # Keep only last 5 days if still too large
            historical_records = stock_data['historical']['historical'][:5]
            stock_data['historical']['historical'] = historical_records
        
        # Check size again
        data_json = json.dumps(stock_data)
        if len(data_json) > DATA_LIMITS['truncate_threshold']:
            # Further reduce to essential quote data only
            essential_data = {
                'symbol': stock_data['symbol'],
                'quote': stock_data.get('quote'),
                'historical': {
                    'symbol': stock_data['symbol'],
                    'historical': stock_data.get('historical', {}).get('historical', [])[:3]
                }
            }
            return essential_data
        
        return stock_data
        
    except Exception as e:
        print(f"[ERROR] Failed to truncate data: {e}")
        return stock_data

def test_fmp_connection():
    """Test FMP API connection"""
    try:
        if not FMP_CONFIG['api_key']:
            print("[ERROR] FMP_API_KEY not found in environment variables")
            return False
        
        print("[INFO] Testing FMP connection...")
        test_symbol = "AAPL"
        
        quote_data = fetch_fmp_quote(test_symbol)
        if quote_data:
            print(f"[SUCCESS] FMP connection test passed for {test_symbol}")
            print(f"[INFO] Sample data: Price ${quote_data.get('price')}")
            return True
        else:
            print("[ERROR] FMP connection test failed")
            return False
            
    except Exception as e:
        print(f"[ERROR] FMP connection test failed: {e}")
        return False

def fetch_multiple_stocks(symbols, delay_between=2):
    """Fetch data for multiple stocks with rate limiting"""
    results = []
    
    for i, symbol in enumerate(symbols):
        print(f"[INFO] Processing {symbol} ({i+1}/{len(symbols)})")
        
        data = fetch_fmp_stock_data(symbol)
        if data:
            results.append(data)
        
        # Add delay between stocks (except for last one)
        if i < len(symbols) - 1:
            print(f"[INFO] Waiting {delay_between} seconds...")
            time.sleep(delay_between)
    
    return results

if __name__ == "__main__":
    # Test the FMP fetcher
    if test_fmp_connection():
        print("\n[INFO] Testing with sample stock...")
        sample_data = fetch_fmp_stock_data("AAPL")
        if sample_data:
            print(f"[SUCCESS] Sample data size: {len(json.dumps(sample_data))} characters")
            print("[SUCCESS] FMP fetcher is ready for integration!")
        else:
            print("[ERROR] Failed to fetch sample data")
    else:
        print("[ERROR] FMP connection failed")