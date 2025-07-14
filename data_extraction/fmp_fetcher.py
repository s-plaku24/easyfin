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
                quote = data[0]
                return {
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
        return None
    except Exception:
        return None

def fetch_fmp_historical(symbol):
    """Fetch historical price data from FMP Historical endpoint"""
    try:
        url = f"{FMP_CONFIG['base_url']}/historical-price-full/{symbol}"
        params = {
            'apikey': FMP_CONFIG['api_key'],
            'timeseries': DATA_LIMITS['historical_days']
        }
        
        response = requests.get(url, params=params, timeout=FMP_CONFIG['timeout'])
        
        if response.status_code == 200:
            data = response.json()
            if data and 'historical' in data:
                historical = data['historical']
                
                essential_historical = []
                for record in historical:
                    essential_historical.append({
                        'date': record.get('date'),
                        'open': record.get('open'),
                        'high': record.get('high'),
                        'low': record.get('low'),
                        'close': record.get('close'),
                        'volume': record.get('volume'),
                        'change': record.get('change'),
                        'changePercent': record.get('changePercent')
                    })
                
                return {
                    'symbol': data.get('symbol'),
                    'historical': essential_historical
                }
        return None
    except Exception:
        return None

def fetch_fmp_stock_data(symbol):
    """Fetch both quote and historical data for a stock"""
    try:
        quote_data = fetch_fmp_quote(symbol)
        time.sleep(1)
        historical_data = fetch_fmp_historical(symbol)
        
        if quote_data or historical_data:
            stock_data = {
                'symbol': symbol,
                'quote': quote_data,
                'historical': historical_data
            }
            
            data_json = json.dumps(stock_data)
            if len(data_json) > DATA_LIMITS['max_json_size']:
                stock_data = truncate_stock_data(stock_data)
            
            return stock_data
        return None
    except Exception:
        return None

def truncate_stock_data(stock_data):
    """Truncate data to fit within token limits"""
    try:
        if stock_data.get('historical') and stock_data['historical'].get('historical'):
            historical_records = stock_data['historical']['historical'][:5]
            stock_data['historical']['historical'] = historical_records
        
        data_json = json.dumps(stock_data)
        if len(data_json) > DATA_LIMITS['truncate_threshold']:
            return {
                'symbol': stock_data['symbol'],
                'quote': stock_data.get('quote'),
                'historical': {
                    'symbol': stock_data['symbol'],
                    'historical': stock_data.get('historical', {}).get('historical', [])[:3]
                }
            }
        return stock_data
    except Exception:
        return stock_data

def test_fmp_connection():
    """Test FMP API connection"""
    try:
        if not FMP_CONFIG['api_key']:
            return False
        
        quote_data = fetch_fmp_quote("AAPL")
        return bool(quote_data)
    except Exception:
        return False

def fetch_multiple_stocks(symbols, delay_between=2):
    """Fetch data for multiple stocks with rate limiting"""
    results = []
    
    for i, symbol in enumerate(symbols):
        data = fetch_fmp_stock_data(symbol)
        if data:
            results.append(data)
        
        if i < len(symbols) - 1:
            time.sleep(delay_between)
    
    return results