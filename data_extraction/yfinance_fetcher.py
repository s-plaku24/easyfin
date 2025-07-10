"""
YFinance data fetcher for stock ticker and market data
"""

import yfinance as yf

def fetch_ticker_data(symbol):
    """
    Fetch ticker data for a stock symbol
    """
    try:        
        ticker = yf.Ticker(symbol)
        
        # Get basic data that usually works
        ticker_data = {
            'symbol': symbol,
            'info': ticker.info,
            'history': ticker.history(period="1mo").to_dict()
        }
        
        # Try to get additional data but don't fail if it doesn't work
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
        print(f"Error in fetch_ticker_data for {symbol}: {str(e)}")
        return None

def fetch_market_data(symbol):
    """
    Fetch market data for a stock symbol
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Get basic market data
        market_data = {
            'symbol': symbol,
            'info': ticker.info,
            'history_5d': ticker.history(period="5d").to_dict()
        }
        
        # Try to get fast_info if available
        try:
            if hasattr(ticker, 'fast_info'):
                market_data['fast_info'] = dict(ticker.fast_info)
        except:
            market_data['fast_info'] = {}
        
        return market_data
        
    except Exception as e:
        print(f"Error in fetch_market_data for {symbol}: {str(e)}")
        return None

def fetch_all_stock_data(symbol):
    """
    Fetch both ticker and market data for a stock symbol
    
    Args:
        symbol (str): Stock symbol
    
    Returns:
        tuple: (ticker_data, market_data) or (None, None) if failed
    """
    ticker_data = fetch_ticker_data(symbol)
    market_data = fetch_market_data(symbol)
    
    return ticker_data, market_data

def test_connection():
    """
    Test the yfinance connection with a simple query
    
    Returns:
        bool: True if connection works, False otherwise
    """
    try:
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        
        if info and 'symbol' in info:
            return True
        else:
            return False
            
    except Exception as e:
        return False