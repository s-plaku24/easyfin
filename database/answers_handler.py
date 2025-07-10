"""
Handler for answers table operations
"""

from datetime import datetime
from database.db_connection import DatabaseConnection

def update_stock_answer(symbol, answer_text):
    """
    Update or insert answer for a stock symbol
    Replaces any existing answer for the day
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL')
        answer_text (str): LLM analysis response
    """
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            # First, delete any existing answer for this symbol today
            delete_query = """
                DELETE FROM answers 
                WHERE symbol = %s 
                AND DATE(updated_at) = CURRENT_DATE
            """
            
            db.execute_query(delete_query, (symbol,))
            
            # Insert the new answer
            insert_query = """
                INSERT INTO answers (symbol, answer_text, updated_at)
                VALUES (%s, %s, %s)
            """
            
            params = (symbol, answer_text, datetime.now())
            
            if db.execute_query(insert_query, params):
                return True
            else:
                return False
                
    except Exception as e:
        return False

def get_stock_answer(symbol):
    """
    Get the latest answer for a stock symbol
    
    Args:
        symbol (str): Stock symbol
    
    Returns:
        str: Answer text or None if not found
    """
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return None
            
            query = """
                SELECT answer_text FROM answers 
                WHERE symbol = %s 
                ORDER BY updated_at DESC 
                LIMIT 1
            """
            
            results = db.fetch_all(query, (symbol,))
            
            if results:
                return results[0]['answer_text']
            else:
                return None
                
    except Exception as e:
        return None

def get_all_latest_answers():
    """
    Get all latest answers for dashboard display
    
    Returns:
        list: List of dictionaries with symbol and answer_text
    """
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return []
            
            query = """
                SELECT symbol, answer_text, updated_at 
                FROM answers 
                WHERE DATE(updated_at) = CURRENT_DATE
                ORDER BY symbol
            """
            
            results = db.fetch_all(query)
            return results
                
    except Exception as e:
        return []

def cleanup_old_answers(days_to_keep=30):
    """
    Clean up old answers (optional function for maintenance)
    
    Args:
        days_to_keep (int): Number of days to keep answers
    """
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            query = """
                DELETE FROM answers 
                WHERE updated_at < NOW() - INTERVAL '%s days'
            """
            
            if db.execute_query(query, (days_to_keep,)):
                return True
            else:
                return False
                
    except Exception as e:
        return False