import sys
import time
from datetime import datetime

from config import STOCK_SYMBOLS
from data_extraction.yfinance_fetcher import fetch_all_stock_data, test_connection as test_yfinance
from database.stocks_handler import insert_or_update_stock, extract_stock_info_from_ticker
from database.questions_handler import get_all_questions, initialize_default_questions
from database.raw_data_handler import insert_raw_data, get_combined_raw_data
from database.answers_handler import insert_or_update_answer
from llm_analysis.groq_analyzer import analyze_stock_question_groq, test_groq_connection

def test_connections():
    if not test_yfinance():
        return False
    
    if not test_groq_connection():
        return True
    
    return True

def setup_database():
    if not initialize_default_questions():
        return False
    
    return True

def process_stock_data(symbol):
    try:
        ticker_data, market_data = fetch_all_stock_data(symbol)
        
        if not ticker_data or not market_data:
            return False
        
        stock_info = extract_stock_info_from_ticker(ticker_data)
        if not insert_or_update_stock(symbol, **stock_info):
            return False
        
        ticker_success = insert_raw_data(symbol, 'ticker', ticker_data)
        market_success = insert_raw_data(symbol, 'market', market_data)
        
        if not ticker_success or not market_success:
            return False
        
        return True
        
    except Exception as e:
        return False

def analyze_stock_questions(symbol):
    try:
        questions = get_all_questions()
        
        if not questions:
            return False
        
        raw_data = get_combined_raw_data(symbol)
        
        if not raw_data:
            return False
        
        successful_analyses = 0
        total_questions = len(questions)
        
        for question in questions:
            question_id = question['id']
            question_text = question['question_text']
            
            analysis = analyze_stock_question_groq(symbol, question_text, raw_data)
            
            if analysis:
                if insert_or_update_answer(symbol, question_id, analysis):
                    successful_analyses += 1
            else:
                fallback_answer = f"Analysis unavailable for this question at this time. Raw data was successfully collected for {symbol}."
                insert_or_update_answer(symbol, question_id, fallback_answer)
        
        return successful_analyses > 0
        
    except Exception as e:
        return False

def process_single_stock(symbol):
    try:
        if not process_stock_data(symbol):
            return False
        
        if not analyze_stock_questions(symbol):
            return False
        
        return True
        
    except Exception as e:
        return False

def main():
    try:
        if not test_connections():
            sys.exit(1)
        
        if not setup_database():
            sys.exit(1)
        
        total_stocks = len(STOCK_SYMBOLS)
        successful_stocks = 0
        failed_stocks = []
        
        for i, symbol in enumerate(STOCK_SYMBOLS, 1):
            if process_single_stock(symbol):
                successful_stocks += 1
            else:
                failed_stocks.append(symbol)
            
            if i < total_stocks:
                time.sleep(5)
        
        print(f"Total: {total_stocks}, Successful: {successful_stocks}, Failed: {len(failed_stocks)}")
        
        if failed_stocks:
            print(f"Failed: {', '.join(failed_stocks)}")
    
    except KeyboardInterrupt:
        sys.exit(1)
    
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    main()