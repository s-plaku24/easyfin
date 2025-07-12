import sys
import time
from datetime import datetime

from config import STOCK_SYMBOLS
from data_extraction.fmp_fetcher import fetch_fmp_stock_data, test_fmp_connection
from database.stocks_handler import insert_or_update_stock, extract_stock_info_from_fmp
from database.questions_handler import get_all_questions, initialize_default_questions
from database.raw_data_handler import insert_raw_data, get_combined_raw_data
from database.answers_handler import insert_or_update_answer, verify_answer_stored
from llm_analysis.groq_analyzer import analyze_stock_batch_groq, test_groq_connection
from database.db_connection import test_database_connection
from dotenv import load_dotenv
load_dotenv()

import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stock_analysis.log') if os.path.exists('logs') else logging.StreamHandler()
    ]
)

def test_connections():
    """Test both FMP and Groq connections"""
    print("[INFO] Testing connections...")
    
    # Test database first
    db_ok = test_database_connection()
    if not db_ok:
        print("[ERROR] Database connection failed. Cannot proceed.")
        return False
    
    fmp_ok = test_fmp_connection()
    if not fmp_ok:
        print("[WARN] FMP connection failed - will skip data fetching")
    
    groq_ok = test_groq_connection()
    if not groq_ok:
        print("[WARN] Groq connection failed - will only process existing data")
    
    if not fmp_ok and not groq_ok:
        print("[ERROR] Both FMP and Groq connections failed. Cannot proceed.")
        return False
    
    print("[INFO] Connections successful - proceeding.")
    return True

def setup_database():
    """Initialize default questions in database"""
    try:
        if not initialize_default_questions():
            print("[ERROR] Failed to initialize default questions.")
            return False
        
        print("[INFO] Database setup completed.")
        return True
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        return False

def try_fetch_stock_data(symbol):
    """Try to fetch and store stock data - returns success/failure"""
    try:
        print(f"[INFO] Attempting to fetch FMP data for {symbol}")
        
        # Fetch data from FMP
        fmp_data = fetch_fmp_stock_data(symbol)
        
        if not fmp_data:
            print(f"[SKIP] Failed to fetch FMP data for {symbol} - will use existing data")
            return False
        
        # CRITICAL: Insert stock info FIRST (required for foreign keys)
        stock_info = extract_stock_info_from_fmp(fmp_data)
        stock_insert_success = insert_or_update_stock(symbol, **stock_info)
        
        if not stock_insert_success:
            print(f"[ERROR] Failed to insert stock info for {symbol}")
            return False
        
        print(f"[DEBUG] Stock info inserted/updated for {symbol}")
        
        # Now store raw FMP data (depends on stock existing)
        raw_data_success = insert_raw_data(symbol, None, fmp_data)
        
        if raw_data_success:
            print(f"[SUCCESS] Updated data for {symbol}")
            return True
        else:
            print(f"[SKIP] Failed to store raw data for {symbol}")
            return False
        
    except Exception as e:
        print(f"[SKIP] Error fetching data for {symbol}: {e}")
        return False

def try_analyze_stock(symbol):
    """Try to analyze stock using existing data in DB - returns success/failure"""
    try:
        print(f"[INFO] Starting analysis for {symbol}")
        
        # CRITICAL: Ensure stock exists in stocks table before inserting answers
        from database.stocks_handler import get_stock_info
        stock_info = get_stock_info(symbol)
        
        if not stock_info:
            print(f"[ERROR] Stock {symbol} not found in stocks table - cannot insert answers")
            
            # Try to create minimal stock entry
            print(f"[INFO] Attempting to create minimal stock entry for {symbol}")
            from database.stocks_handler import insert_or_update_stock
            minimal_success = insert_or_update_stock(symbol, name=symbol)
            
            if not minimal_success:
                print(f"[SKIP] Cannot create stock entry for {symbol}")
                return False
            else:
                print(f"[DEBUG] Created minimal stock entry for {symbol}")
        
        # Get raw data from database (could be today's or historical)
        raw_data = get_combined_raw_data(symbol)
        
        if not raw_data:
            print(f"[SKIP] No data found in database for {symbol}")
            return False
        
        # Analyze using Groq
        answers = analyze_stock_batch_groq(symbol, raw_data)
        
        if not answers:
            print(f"[SKIP] No answers generated for {symbol}")
            return False
        
        # Store answers with verification
        successful_answers = 0
        for question_id, answer_text in answers.items():
            print(f"[DEBUG] Storing answer for {symbol}, question {question_id}")
            
            if insert_or_update_answer(symbol, question_id, answer_text):
                # Verify the answer was actually stored
                if verify_answer_stored(symbol, question_id):
                    successful_answers += 1
                    print(f"[SUCCESS] Verified answer stored for {symbol} question {question_id}")
                else:
                    print(f"[ERROR] Answer not found after insert for {symbol} question {question_id}")
            else:
                print(f"[ERROR] Failed to store answer for {symbol} question {question_id}")
        
        if successful_answers > 0:
            print(f"[SUCCESS] Analysis completed for {symbol}: {successful_answers}/{len(answers)} answers stored")
            return True
        else:
            print(f"[SKIP] No answers stored for {symbol}")
            return False
        
    except Exception as e:
        print(f"[SKIP] Error analyzing {symbol}: {e}")
        return False

def process_single_stock(symbol):
    """Process a single stock: try to fetch data, then analyze with whatever data exists"""
    try:
        print(f"\n[INFO] Processing {symbol}...")
        
        # Step 1: Try to fetch fresh data (optional - skip if fails)
        data_updated = try_fetch_stock_data(symbol)
        if data_updated:
            print(f"[INFO] Fresh data obtained for {symbol}")
        else:
            print(f"[INFO] Will use existing data for {symbol}")
        
        # Step 2: Try to analyze with whatever data we have
        analysis_success = try_analyze_stock(symbol)
        
        if analysis_success:
            print(f"[SUCCESS] {symbol} analysis completed")
            return True
        else:
            print(f"[FAILED] {symbol} analysis failed")
            return False
        
    except Exception as e:
        print(f"[FAILED] Unexpected error processing {symbol}: {e}")
        return False

def get_stocks_with_data():
    """Get list of stocks that have data in the database"""
    try:
        from database.stocks_handler import get_all_stocks
        stocks_in_db = get_all_stocks()
        return [stock['symbol'] for stock in stocks_in_db]
    except:
        return []

def main():
    """Main execution function - failure resilient"""
    try:
        print("[INFO] Starting FMP Stock Analysis Project...")
        print(f"[INFO] Processing {len(STOCK_SYMBOLS)} stocks: {', '.join(STOCK_SYMBOLS)}")
        
        # Test connections (continue even if some fail)
        if not test_connections():
            print("[ERROR] No working connections. Exiting.")
            sys.exit(1)
        
        # Setup database
        print("[INFO] Setting up database...")
        if not setup_database():
            print("[ERROR] Database setup failed. Exiting.")
            sys.exit(1)
        
        # Processing stats
        total_stocks = len(STOCK_SYMBOLS)
        successful_analyses = 0
        failed_stocks = []
        skipped_stocks = []
        
        start_time = datetime.now()
        
        # Process each stock independently
        for i, symbol in enumerate(STOCK_SYMBOLS, 1):
            print(f"\n[INFO] Processing stock {i}/{total_stocks}: {symbol}")
            
            try:
                if process_single_stock(symbol):
                    successful_analyses += 1
                else:
                    failed_stocks.append(symbol)
                
            except Exception as e:
                print(f"[ERROR] Critical error with {symbol}: {e}")
                failed_stocks.append(symbol)
            
            # Add delay between stocks (except for the last one)
            if i < total_stocks:
                delay = 5
                print(f"[INFO] Waiting {delay} seconds before next stock...")
                time.sleep(delay)
        
        end_time = datetime.now()
        total_duration = end_time - start_time
        
        # Check what stocks have data in DB
        stocks_with_data = get_stocks_with_data()
        
        # Final summary
        print(f"\n{'='*60}")
        print("[FINAL SUMMARY]")
        print(f"{'='*60}")
        print(f"⏱️  Total Duration: {total_duration}")
        print(f"📊 Total Stocks Processed: {total_stocks}")
        print(f"✅ Successful Analyses: {successful_analyses}")
        print(f"❌ Failed Analyses: {len(failed_stocks)}")
        print(f"📈 Analysis Success Rate: {(successful_analyses/total_stocks)*100:.1f}%")
        print(f"💾 Stocks with Data in DB: {len(stocks_with_data)}")
        
        if failed_stocks:
            print(f"Failed stocks: {', '.join(failed_stocks)}")
        
        if stocks_with_data:
            print(f"Stocks with data: {', '.join(stocks_with_data)}")
        
        print(f"\n🔗 FMP API calls attempted: {total_stocks * 2} (Quote + Historical per stock)")
        
        # Success if we got at least some analyses done
        if successful_analyses > 0:
            print("🎉 Process completed with some successful analyses!")
            logging.info(f"Stock analysis completed successfully: {successful_analyses}/{total_stocks} stocks analyzed")
        else:
            print("⚠️  No successful analyses completed")
            logging.warning("Stock analysis completed but no stocks were successfully analyzed")
    
    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted by user.")
        sys.exit(1)
    
    except Exception as e:
        print(f"[MAIN ERROR] {e}")
        logging.error(f"Stock analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()