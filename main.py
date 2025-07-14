import sys
import time
from datetime import datetime
from dotenv import load_dotenv

from config import STOCK_SYMBOLS
from data_extraction.fmp_fetcher import fetch_fmp_stock_data, test_fmp_connection
from database.stocks_handler import insert_or_update_stock, extract_stock_info_from_fmp, get_stock_info, get_all_stocks
from database.questions_handler import initialize_default_questions
from database.raw_data_handler import insert_raw_data, get_combined_raw_data
from database.answers_handler import insert_or_update_answer, verify_answer_stored
from llm_analysis.groq_analyzer import analyze_stock_batch_groq, test_groq_connection
from database.db_connection import test_database_connection

load_dotenv()

def test_connections():
    """Test all required connections"""
    db_ok = test_database_connection()
    if not db_ok:
        print("Database connection failed. Cannot proceed.")
        return False
    
    fmp_ok = test_fmp_connection()
    groq_ok = test_groq_connection()
    
    if not fmp_ok and not groq_ok:
        print("Both FMP and Groq connections failed. Cannot proceed.")
        return False
    
    return True

def setup_database():
    """Initialize default questions in database"""
    try:
        return initialize_default_questions()
    except Exception:
        return False

def try_fetch_stock_data(symbol):
    """Try to fetch and store stock data"""
    try:
        fmp_data = fetch_fmp_stock_data(symbol)
        if not fmp_data:
            return False
        
        stock_info = extract_stock_info_from_fmp(fmp_data)
        stock_insert_success = insert_or_update_stock(symbol, **stock_info)
        
        if not stock_insert_success:
            return False
        
        return insert_raw_data(symbol, None, fmp_data)
    except Exception:
        return False

def try_analyze_stock(symbol):
    """Try to analyze stock using existing data in DB"""
    try:
        stock_info = get_stock_info(symbol)
        if not stock_info:
            minimal_success = insert_or_update_stock(symbol, name=symbol)
            if not minimal_success:
                return False
        
        raw_data = get_combined_raw_data(symbol)
        if not raw_data:
            return False
        
        answers = analyze_stock_batch_groq(symbol, raw_data)
        if not answers:
            return False
        
        successful_answers = 0
        for question_id, answer_text in answers.items():
            if insert_or_update_answer(symbol, question_id, answer_text):
                if verify_answer_stored(symbol, question_id):
                    successful_answers += 1
        
        return successful_answers > 0
    except Exception:
        return False

def process_single_stock(symbol):
    """Process a single stock: try to fetch data, then analyze"""
    try:
        print(f"Processing {symbol}...")
        
        data_updated = try_fetch_stock_data(symbol)
        analysis_success = try_analyze_stock(symbol)
        
        if analysis_success:
            print(f"✅ {symbol} completed")
            return True
        else:
            print(f"❌ {symbol} failed")
            return False
    except Exception:
        return False

def get_stocks_with_data():
    """Get list of stocks that have data in the database"""
    try:
        stocks_in_db = get_all_stocks()
        return [stock['symbol'] for stock in stocks_in_db]
    except:
        return []

def main():
    """Main execution function"""
    try:
        print("Starting FMP Stock Analysis Project...")
        print(f"Processing {len(STOCK_SYMBOLS)} stocks: {', '.join(STOCK_SYMBOLS)}")
        
        if not test_connections():
            print("Connection tests failed. Exiting.")
            sys.exit(1)
        
        if not setup_database():
            print("Database setup failed. Exiting.")
            sys.exit(1)
        
        total_stocks = len(STOCK_SYMBOLS)
        successful_analyses = 0
        failed_stocks = []
        start_time = datetime.now()
        
        for i, symbol in enumerate(STOCK_SYMBOLS, 1):
            print(f"\n[{i}/{total_stocks}] Processing {symbol}")
            
            try:
                if process_single_stock(symbol):
                    successful_analyses += 1
                else:
                    failed_stocks.append(symbol)
            except Exception:
                failed_stocks.append(symbol)
            
            if i < total_stocks:
                time.sleep(5)
        
        end_time = datetime.now()
        total_duration = end_time - start_time
        stocks_with_data = get_stocks_with_data()
        
        print(f"\n{'='*60}")
        print("FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"⏱️  Duration: {total_duration}")
        print(f"📊 Total Stocks: {total_stocks}")
        print(f"✅ Successful: {successful_analyses}")
        print(f"❌ Failed: {len(failed_stocks)}")
        print(f"📈 Success Rate: {(successful_analyses/total_stocks)*100:.1f}%")
        print(f"💾 Stocks with Data: {len(stocks_with_data)}")
        
        if failed_stocks:
            print(f"Failed: {', '.join(failed_stocks)}")
        
        if successful_analyses > 0:
            print("🎉 Process completed successfully!")
        else:
            print("⚠️  No successful analyses completed")
    
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()