import yfinance as yf

def fetch_ticker_data(symbol):
    try:        
        ticker = yf.Ticker(symbol)
        
        # Sicheres Einlesen von info
        try:
            info = ticker.info
        except Exception as e:
            print(f"[WARN] Failed to fetch 'info' for {symbol}: {e}")
            info = {}

        # Historische Kursdaten
        try:
            history = ticker.history(period="1mo")
            history_data = history.to_dict() if not history.empty else {}
        except Exception as e:
            print(f"[WARN] Failed to fetch 'history' for {symbol}: {e}")
            history_data = {}

        ticker_data = {
            'symbol': symbol,
            'info': info,
            'history': history_data
        }

        # Optional: Finanzdaten
        try:
            if hasattr(ticker, 'financials') and not ticker.financials.empty:
                ticker_data['financials'] = ticker.financials.to_dict()
            else:
                ticker_data['financials'] = {}
        except Exception as e:
            print(f"[WARN] Failed to fetch 'financials' for {symbol}: {e}")
            ticker_data['financials'] = {}

        try:
            if hasattr(ticker, 'balance_sheet') and not ticker.balance_sheet.empty:
                ticker_data['balance_sheet'] = ticker.balance_sheet.to_dict()
            else:
                ticker_data['balance_sheet'] = {}
        except Exception as e:
            print(f"[WARN] Failed to fetch 'balance_sheet' for {symbol}: {e}")
            ticker_data['balance_sheet'] = {}

        return ticker_data
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch ticker data for {symbol}: {e}")
        return None


def fetch_market_data(symbol):
    try:
        ticker = yf.Ticker(symbol)

        # Sicheres Einlesen von info
        try:
            info = ticker.info
        except Exception as e:
            print(f"[WARN] Failed to fetch 'info' for {symbol}: {e}")
            info = {}

        # Historische Kursdaten
        try:
            history = ticker.history(period="5d")
            history_5d = history.to_dict() if not history.empty else {}
        except Exception as e:
            print(f"[WARN] Failed to fetch 'history_5d' for {symbol}: {e}")
            history_5d = {}

        # Optional: fast_info
        try:
            fast_info = dict(ticker.fast_info)
        except Exception as e:
            print(f"[WARN] Failed to fetch 'fast_info' for {symbol}: {e}")
            fast_info = {}

        market_data = {
            'symbol': symbol,
            'info': info,
            'history_5d': history_5d,
            'fast_info': fast_info
        }

        return market_data

    except Exception as e:
        print(f"[ERROR] Failed to fetch market data for {symbol}: {e}")
        return None


def fetch_all_stock_data(symbol):
    ticker_data = fetch_ticker_data(symbol)
    market_data = fetch_market_data(symbol)
    return ticker_data, market_data


def test_connection():
    try:
        ticker = yf.Ticker("MSFT")
        data = ticker.history(period="5d")

        if data is not None and not data.empty:
            print("[INFO] yFinance connection successful.")
            return True
        else:
            print("[ERROR] yFinance returned no data.")
            return False
    except Exception as e:
        print(f"[ERROR] yFinance test failed: {e}")
        return False
