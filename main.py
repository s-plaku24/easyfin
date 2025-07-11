import sys
import time
from datetime import datetime

from config import STOCK_SYMBOLS
from data_extraction.fmp_fetcher import fetch_fmp_stock_data, test_fmp_connection
from database.stocks_handler import insert_or_update_stock, extract_stock_info_from_fmp
from database.questions_handler import get_all_questions, initialize_default_questions
from database.raw_data_handler import insert_raw_data, get_combined_raw_data
from database.answers_handler import insert_or_update_answer
from llm_analysis.groq_analyzer import analyze_stock_batch_groq, test_groq_connection
from dotenv import load_dotenv
load_dotenv()

# Add at the top of main.py
import logging
import os

# Configure logging for GitHub Actions
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stock_analysis.log') if os.path.exists('logs') else logging.StreamHandler()
    ]
)

def main():
    try:
        logging.info("Starting automated stock analysis...")
        # Your existing main() code here
        logging.info("Stock analysis completed successfully")
    except Exception as e:
        logging.error(f"Stock analysis failed: {e}")
        sys.exit(1)  # This will mark the GitHub Action as failed

def test_connections():
    """Test both FMP and Groq connections"""
    print("[INFO] Testing FMP connection...")
    if not test_fmp_connection():
        print("[ERROR] FMP connection failed.")
        return False
    
    print("[INFO] Testing Groq connection...")
    if not test_groq_connection():
        print("[ERROR] Groq connection failed.")
        return False

    print("[INFO] All connections successful.")
    return True

def setup_database():
    """Initialize default questions in database"""
    if not initialize_default_questions():
        print("[ERROR] Failed to initialize default questions.")
        return False
    
    print("[INFO] Database setup completed.")
    return True

def process_stock_data(symbol):
    """Process stock data from FMP and store in database"""
    try:
        print(f"[INFO] Processing FMP data for {symbol}")
        
        # Fetch data from FMP
        fmp_data = fetch_fmp_stock_data(symbol)
        
        if not fmp_data:
            print(f"[ERROR] Failed to fetch FMP data for {symbol}")
            return False
        
        # Extract stock info from FMP data
        stock_info = extract_stock_info_from_fmp(fmp_data)
        if not insert_or_update_stock(symbol, **stock_info):
            print(f"[ERROR] Failed to insert/update stock info for {symbol}")
            return False
        
        # Store raw FMP data (combining quote and historical)
        raw_data_success = insert_raw_data(symbol, None, fmp_data)
        
        if not raw_data_success:
            print(f"[ERROR] Failed to insert raw data for {symbol}")
            return False
        
        print(f"[INFO] Successfully processed FMP data for {symbol}")
        return True
        
    except Exception as e:
        print(f"[MAIN ERROR] process_stock_data for {symbol}: {e}")
        return False

def analyze_stock_questions(symbol):
    """Analyze stock using Groq with FMP data"""
    try:
        print(f"[INFO] Starting batch analysis for {symbol}")
        
        # Get raw FMP data from database
        raw_data = get_combined_raw_data(symbol)
        
        if not raw_data:
            print(f"[ERROR] No raw data found for {symbol}")
            return False
        
        # Get all answers at once using batch analysis
        answers = analyze_stock_batch_groq(symbol, raw_data)
        
        if not answers:
            print(f"[ERROR] No answers received for {symbol}")
            return False
        
        # Store all answers in database
        successful_analyses = 0
        for question_id, answer_text in answers.items():
            if insert_or_update_answer(symbol, question_id, answer_text):
                successful_analyses += 1
                print(f"[INFO] Stored answer for {symbol} question {question_id}")
            else:
                print(f"[ERROR] Failed to store answer for {symbol} question {question_id}")
        
        print(f"[INFO] Completed analysis for {symbol}: {successful_analyses}/{len(answers)} answers stored")
        return successful_analyses > 0
        
    except Exception as e:
        print(f"[MAIN ERROR] analyze_stock_questions for {symbol}: {e}")
        return False

def process_single_stock(symbol):
    """Process a single stock: fetch data and analyze"""
    try:
        print(f"\n[INFO] Processing {symbol}...")
        
        if not process_stock_data(symbol):
            print(f"[ERROR] Failed to process stock data for {symbol}")
            return False
        
        if not analyze_stock_questions(symbol):
            print(f"[ERROR] Failed to analyze questions for {symbol}")
            return False
        
        print(f"[INFO] Successfully completed processing for {symbol}")
        return True
        
    except Exception as e:
        print(f"[MAIN ERROR] process_single_stock for {symbol}: {e}")
        return False

def main():
    """Main execution function"""
    try:
        print("[INFO] Starting FMP Stock Analysis Project...")
        print(f"[INFO] Updated to use FMP API with {len(STOCK_SYMBOLS)} stocks")
        
        # Test connections
        print("[INFO] Testing connections...")
        if not test_connections():
            print("[ERROR] Connection test failed.")
            sys.exit(1)
        
        # Setup database
        print("[INFO] Setting up database...")
        if not setup_database():
            print("[ERROR] Database setup failed.")
            sys.exit(1)
        
        total_stocks = len(STOCK_SYMBOLS)
        successful_stocks = 0
        failed_stocks = []
        
        print(f"[INFO] Processing {total_stocks} stocks: {', '.join(STOCK_SYMBOLS)}")
        
        start_time = datetime.now()
        
        for i, symbol in enumerate(STOCK_SYMBOLS, 1):
            print(f"\n[INFO] Processing stock {i}/{total_stocks}: {symbol}")
            
            if process_single_stock(symbol):
                successful_stocks += 1
                print(f"[SUCCESS] {symbol} completed successfully")
            else:
                failed_stocks.append(symbol)
                print(f"[FAILED] {symbol} processing failed")
            
            # Add delay between stocks (except for the last one)
            if i < total_stocks:
                delay = 5  # 5 seconds between stocks
                print(f"[INFO] Waiting {delay} seconds before next stock...")
                time.sleep(delay)
        
        end_time = datetime.now()
        total_duration = end_time - start_time
        
        # Final summary
        print(f"\n{'='*60}")
        print("[FINAL SUMMARY]")
        print(f"{'='*60}")
        print(f"⏱️  Total Duration: {total_duration}")
        print(f"📊 Total Stocks: {total_stocks}")
        print(f"✅ Successful: {successful_stocks}")
        print(f"❌ Failed: {len(failed_stocks)}")
        print(f"📈 Success Rate: {(successful_stocks/total_stocks)*100:.1f}%")
        
        if failed_stocks:
            print(f"Failed stocks: {', '.join(failed_stocks)}")
        else:
            print("🎉 All stocks processed successfully!")
        
        print(f"\n🔗 FMP API calls used: {total_stocks * 2} (Quote + Historical per stock)")
        print(f"🔗 Remaining daily limit: {250 - (total_stocks * 2)} calls")
    
    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted by user.")
        sys.exit(1)
    
    except Exception as e:
        print(f"[MAIN ERROR] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()