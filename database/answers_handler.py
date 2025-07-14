from database.db_connection import DatabaseConnection

def insert_or_update_answer(symbol, question_id, answer_text):
    try:
        print(f"[DEBUG] Attempting to store answer for {symbol}, question {question_id}")
        
        with DatabaseConnection() as db:
            if not db or not db.connection:
                print(f"[ERROR] No database connection for {symbol}")
                return False
            
            # Check if answer already exists
            check_query = """
                SELECT symbol FROM answers 
                WHERE symbol = %s AND question_id = %s
            """
            existing = db.fetch_all(check_query, (symbol, question_id))
            
            if existing:
                print(f"[DEBUG] Updating existing answer for {symbol}, question {question_id}")
                update_query = """
                    UPDATE answers 
                    SET answer_text = %s, created_at = CURRENT_TIMESTAMP
                    WHERE symbol = %s AND question_id = %s
                """
                params = (answer_text, symbol, question_id)
                success = db.execute_query(update_query, params)
                
                if success:
                    print(f"[DEBUG] Successfully updated answer for {symbol}, question {question_id}")
                else:
                    print(f"[ERROR] Failed to update answer for {symbol}, question {question_id}")
                
                return success
            else:
                print(f"[DEBUG] Inserting new answer for {symbol}, question {question_id}")
                insert_query = """
                    INSERT INTO answers (symbol, question_id, answer_text)
                    VALUES (%s, %s, %s)
                """
                params = (symbol, question_id, answer_text)
                success = db.execute_query(insert_query, params)
                
                if success:
                    print(f"[DEBUG] Successfully inserted answer for {symbol}, question {question_id}")
                else:
                    print(f"[ERROR] Failed to insert answer for {symbol}, question {question_id}")
                
                return success
                
    except Exception as e:
        print(f"[ERROR] Exception in insert_or_update_answer for {symbol}: {e}")
        return False

def get_answer(symbol, question_id):
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return None
            
            query = """
                SELECT answer_text FROM answers 
                WHERE symbol = %s AND question_id = %s
            """
            
            results = db.fetch_all(query, (symbol, question_id))
            
            if results:
                return results[0]['answer_text']
            return None
                
    except Exception as e:
        print(f"[ERROR] Failed to get answer for {symbol}, question {question_id}: {e}")
        return None

# Add verification function
def verify_answer_stored(symbol, question_id):
    """Verify that an answer was actually stored in the database"""
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return False
            
            query = """
                SELECT answer_text, created_at FROM answers 
                WHERE symbol = %s AND question_id = %s
            """
            
            results = db.fetch_all(query, (symbol, question_id))
            
            if results:
                print(f"[VERIFY] Answer exists for {symbol}, question {question_id}: {len(results[0]['answer_text'])} chars")
                return True
            else:
                print(f"[VERIFY] No answer found for {symbol}, question {question_id}")
                return False
                
    except Exception as e:
        print(f"[ERROR] Verification failed for {symbol}, question {question_id}: {e}")
        return False