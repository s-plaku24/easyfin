import sys
import time
from datetime import datetime

# Import configuration
from config import STOCK_SYMBOLS

# Import data extraction
from data_extraction.yfinance_fetcher import fetch_all_stock_data, test_connection as test_yfinance

# Import database handlers
from database.stocks_handler import insert_or_update_stock, extract_stock_info_from_ticker
from database.questions_handler import get_all_questions, initialize_default_questions
from database.raw_data_handler import insert_raw_data, get_combined_raw_data
from database.answers_handler import insert_or_update_answer

# Import LLM analysis
from llm_analysis.groq_analyzer import analyze_stock_question_groq, test_groq_connection

def test_connections():
    """
    Test all external connections before starting the main process
    """
    print("Testing external connections...")
    
    # Test yfinance connection
    if not test_yfinance():
        print("YFinance connection test failed")
        return False
    
    # Test Groq connection
    if not test_groq_connection():
        print("Groq API connection test failed - continuing with fallback")
        return True  # Continue anyway
    
    print("All connection tests passed")
    return True

def setup_database():
    """
    Initialize database with default questions if needed
    """
    print("Setting up database...")
    
    if not initialize_default_questions():
        print("Failed to initialize default questions")
        return False
    
    print("Database setup completed")
    return True

def process_stock_data(symbol):
    """
    Process stock data: fetch, store, and update stock info
    """
    print(f"Processing stock data for {symbol}")
    
    try:
        # Step 1: Fetch stock data
        ticker_data, market_data = fetch_all_stock_data(symbol)
        
        if not ticker_data or not market_data:
            print(f"Failed to fetch data for {symbol}")
            return False
        
        # Step 2: Extract and store stock information
        stock_info = extract_stock_info_from_ticker(ticker_data)
        if not insert_or_update_stock(symbol, **stock_info):
            print(f"Failed to store stock info for {symbol}")
            return False
        
        # Step 3: Store raw data
        ticker_success = insert_raw_data(symbol, 'ticker', ticker_data)
        market_success = insert_raw_data(symbol, 'market', market_data)
        
        if not ticker_success or not market_success:
            print(f"Failed to store raw data for {symbol}")
            return False
        
        print(f"Successfully processed stock data for {symbol}")
        return True
        
    except Exception as e:
        print(f"Error processing stock data for {symbol}: {str(e)}")
        return False

def analyze_stock_questions(symbol):
    """
    Analyze all questions for a specific stock
    """
    print(f"Analyzing questions for {symbol}")
    
    try:
        # Get all questions from database
        questions = get_all_questions()
        
        if not questions:
            print(f"No questions found in database for {symbol}")
            return False
        
        # Get raw data for this stock
        raw_data = get_combined_raw_data(symbol)
        
        if not raw_data:
            print(f"No raw data found for {symbol}")
            return False
        
        successful_analyses = 0
        total_questions = len(questions)
        
        # Process each question
        for question in questions:
            question_id = question['id']
            question_text = question['question_text']
            
            print(f"  Analyzing question {question_id}: {question_text[:50]}...")
            
            # Get analysis from LLM
            analysis = analyze_stock_question_groq(symbol, question_text, raw_data)
            
            if analysis:
                # Store the answer
                if insert_or_update_answer(symbol, question_id, analysis):
                    successful_analyses += 1
                    print(f"    Successfully analyzed question {question_id}")
                else:
                    print(f"    Failed to store answer for question {question_id}")
            else:
                print(f"    Failed to get analysis for question {question_id}")
                # Store a fallback answer
                fallback_answer = f"Analysis unavailable for this question at this time. Raw data was successfully collected for {symbol}."
                insert_or_update_answer(symbol, question_id, fallback_answer)
        
        print(f"Completed {successful_analyses}/{total_questions} question analyses for {symbol}")
        return successful_analyses > 0
        
    except Exception as e:
        print(f"Error analyzing questions for {symbol}: {str(e)}")
        return False

def process_single_stock(symbol):
    """
    Process a single stock through the complete pipeline
    """
    print(f"Processing stock: {symbol}")
    
    try:
        # Step 1: Process stock data (fetch, store, update info)
        if not process_stock_data(symbol):
            return False
        
        # Step 2: Analyze all questions for this stock
        if not analyze_stock_questions(symbol):
            return False
        
        print(f"Successfully completed processing for {symbol}")
        return True
        
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
        # Step 1: Test all connections
        if not test_connections():
            print("Connection tests failed - aborting process")
            sys.exit(1)
        
        # Step 2: Setup database (initialize questions if needed)
        if not setup_database():
            print("Database setup failed - aborting process")
            sys.exit(1)
        
        # Step 3: Process statistics
        total_stocks = len(STOCK_SYMBOLS)
        successful_stocks = 0
        failed_stocks = []
        
        print(f"Starting to process {total_stocks} stocks: {', '.join(STOCK_SYMBOLS)}")
        
        # Step 4: Process each stock
        for i, symbol in enumerate(STOCK_SYMBOLS, 1):
            print(f"\nProcessing stock {i}/{total_stocks}: {symbol}")
            print("-" * 30)
            
            if process_single_stock(symbol):
                successful_stocks += 1
                print(f"✓ Completed {symbol} ({i}/{total_stocks})")
            else:
                failed_stocks.append(symbol)
                print(f"✗ Failed {symbol} ({i}/{total_stocks})")
            
            # Add a small delay between stocks to be nice to APIs
            if i < total_stocks:
                print("Waiting 5 seconds before next stock...")
                time.sleep(5)
        
        # Step 5: Final summary
        print("\n" + "="*50)
        print("DAILY PROCESS SUMMARY")
        print("="*50)
        print(f"Total stocks processed: {total_stocks}")
        print(f"Successful: {successful_stocks}")
        print(f"Failed: {len(failed_stocks)}")
        
        if failed_stocks:
            print(f"Failed stocks: {', '.join(failed_stocks)}")
        
        if successful_stocks == total_stocks:
            print("🎉 All stocks processed successfully!")
        elif successful_stocks > 0:
            print(f"⚠️  Partial success: {successful_stocks}/{total_stocks} stocks completed")
        else:
            print("❌ No stocks were processed successfully")
    
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"Unexpected error in main process: {str(e)}")
        sys.exit(1)
    
    finally:
        print("\n" + "="*50)
        print(f"Completed daily stock analysis process at {datetime.now()}")
        print("="*50)

if __name__ == "__main__":
    main()