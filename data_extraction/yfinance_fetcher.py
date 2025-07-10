import yfinance as yf

def fetch_ticker_data(symbol):
    try:        
        ticker = yf.Ticker(symbol)
        
        ticker_data = {
            'symbol': symbol,
            'info': ticker.info,
            'history': ticker.history(period="1mo").to_dict()
        }
        
        try:
            if hasattr(ticker, 'financials') and not ticker.financials.empty:
                ticker_data['financials'] = ticker.financials.to_dict()
        except:
            ticker_data['financials'] = {}
            
        try:
            if hasattr(ticker, 'balance_sheet') and not ticker.balance_sheet.empty:
                ticker_data['balance_sheet'] = ticker.balance_sheet.to_dict()
        except:
            ticker_data['balance_sheet'] = {}
        
        return ticker_data
        
    except Exception as e:
        return None

def fetch_market_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        
        market_data = {
            'symbol': symbol,
            'info': ticker.info,
            'history_5d': ticker.history(period="5d").to_dict()
        }
        
        try:
            if hasattr(ticker, 'fast_info'):
                market_data['fast_info'] = dict(ticker.fast_info)
        except:
            market_data['fast_info'] = {}
        
        return market_data
        
    except Exception as e:
        return None

def fetch_all_stock_data(symbol):
    ticker_data = fetch_ticker_data(symbol)
    market_data = fetch_market_data(symbol)
    
    return ticker_data, market_data

def test_connection():
    try:
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        if info and 'symbol' in info:
            return True
        else:
            return False
            
    except Exception as e:
        return False