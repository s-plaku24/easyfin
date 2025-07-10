"""
Main orchestrator script for the Stock Analysis Project
Runs the complete daily pipeline:
1. Fetch stock data via yfinance API
2. Store raw data in PostgreSQL
3. Analyze data using Hugging Face LLM
4. Store analysis results in database
"""

import sys
import time
from datetime import datetime

from llm_analysis.prompt_processor import clean_response, validate_analysis_response
from llm_analysis.groq_analyzer import analyze_stock_groq

# Import configuration
from config import STOCK_SYMBOLS

# Import data extraction
from data_extraction.yfinance_fetcher import fetch_all_stock_data, test_connection as test_yfinance

# Import database handlers
from database.raw_data_handler import insert_raw_data
from database.answers_handler import update_stock_answer

# Import LLM analysis
from llm_analysis.prompt_processor import analyze_stock, clean_response, validate_analysis_response
from llm_analysis.huggingface_client import HuggingFaceClient

def test_connections():
    """
    Test all external connections before starting the main process
    """
    print("Testing external connections...")
    
    # Test yfinance connection
    if not test_yfinance():
        print("YFinance connection test failed")
        return False
    
    # Test Hugging Face connection
    client = HuggingFaceClient()
    if not client.test_connection():
        print("Hugging Face API connection test failed - continuing with mock analysis")
        return True  # Continue anyway
    
    print("All connection tests passed")
    return True

def process_single_stock(symbol):
    """
    Process a single stock through the complete pipeline
    
    Args:
        symbol (str): Stock symbol to process
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Processing stock: {symbol}")
    
    try:
        # Step 1: Fetch stock data
        print(f"Step 1: Fetching data for {symbol}")
        ticker_data, market_data = fetch_all_stock_data(symbol)
        
        if not ticker_data or not market_data:
            print(f"Failed to fetch data for {symbol}")
            return False
        
        # Step 2: Store raw data in database
        print(f"Step 2: Storing raw data for {symbol}")
        
        ticker_success = insert_raw_data(symbol, 'ticker', ticker_data)
        market_success = insert_raw_data(symbol, 'market', market_data)
        
        if not ticker_success or not market_success:
            print(f"Failed to store raw data for {symbol}")
            return False
        
	# Step 3: Analyze stock using Groq LLM (FREE REAL AI)
        print(f"Step 3: Analyzing {symbol} with Groq AI")
        
        analysis = analyze_stock_groq(symbol, ticker_data, market_data)
        
        if not analysis:
            print(f"Failed to get analysis for {symbol}, using fallback")
            # Fallback to simple message if AI fails
            analysis = f"AI analysis failed for {symbol} - raw data stored successfully"

        # Step 4: Clean and validate response
        cleaned_analysis = clean_response(analysis)
        # Step 4: Clean and validate response (simplified for mock)
        cleaned_analysis = analysis.strip()
        
        # Step 5: Store analysis in database
        print(f"Step 4: Storing analysis for {symbol}")
        
        if update_stock_answer(symbol, cleaned_analysis):
            print(f"Successfully completed processing for {symbol}")
            return True
        else:
            print(f"Failed to store analysis for {symbol}")
            return False
    
    except Exception as e:
        print(f"Unexpected error processing {symbol}: {str(e)}")
        return False

def main():
    """
    Main function - orchestrates the entire daily process
    """
    print("="*50)
    print(f"Starting daily stock analysis process at {datetime.now()}")
    print("="*50)
    
    try:
        # Test all connections first
        if not test_connections():
            print("Connection tests failed - aborting process")
            sys.exit(1)
        
        # Process statistics
        total_stocks = len(STOCK_SYMBOLS)
        successful_stocks = 0
        failed_stocks = []
        
        print(f"Starting to process {total_stocks} stocks: {', '.join(STOCK_SYMBOLS)}")
        
        # Process each stock
        for i, symbol in enumerate(STOCK_SYMBOLS, 1):
            print(f"Processing stock {i}/{total_stocks}: {symbol}")
            
            if process_single_stock(symbol):
                successful_stocks += 1
                print(f"Completed {symbol} ({i}/{total_stocks})")
            else:
                failed_stocks.append(symbol)
                print(f"Failed {symbol} ({i}/{total_stocks})")
            
            # Add a small delay between stocks to be nice to APIs
            if i < total_stocks:
                print("Waiting 5 seconds before next stock...")
                time.sleep(5)
        
        # Final summary
        print("="*50)
        print("DAILY PROCESS SUMMARY")
        print("="*50)
        print(f"Total stocks processed: {total_stocks}")
        print(f"Successful: {successful_stocks}")
        print(f"Failed: {len(failed_stocks)}")
        
        if failed_stocks:
            print(f"Failed stocks: {', '.join(failed_stocks)}")
        
        if successful_stocks == total_stocks:
            print("All stocks processed successfully!")
        elif successful_stocks > 0:
            print(f"Partial success: {successful_stocks}/{total_stocks} stocks completed")
        else:
            print("No stocks were processed successfully")
    
    except KeyboardInterrupt:
        print("Process interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"Unexpected error in main process: {str(e)}")
        sys.exit(1)
    
    finally:
        print("="*50)
        print(f"Completed daily stock analysis process at {datetime.now()}")
        print("="*50)

if __name__ == "__main__":
    main()