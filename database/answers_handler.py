from database.db_connection import DatabaseConnection

def insert_or_update_answer(symbol, question_id, answer_text):
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return False
            
            # Check if answer already exists
            check_query = """
                SELECT symbol FROM answers 
                WHERE symbol = %s AND question_id = %s
            """
            existing = db.fetch_all(check_query, (symbol, question_id))
            
            if existing:
                update_query = """
                    UPDATE answers 
                    SET answer_text = %s, created_at = CURRENT_TIMESTAMP
                    WHERE symbol = %s AND question_id = %s
                """
                return db.execute_query(update_query, (answer_text, symbol, question_id))
            else:
                insert_query = """
                    INSERT INTO answers (symbol, question_id, answer_text)
                    VALUES (%s, %s, %s)
                """
                return db.execute_query(insert_query, (symbol, question_id, answer_text))
    except Exception:
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
            return results[0]['answer_text'] if results else None
    except Exception:
        return None

def verify_answer_stored(symbol, question_id):
    """Verify that an answer was actually stored in the database"""
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return False
            
            query = """
                SELECT answer_text FROM answers 
                WHERE symbol = %s AND question_id = %s
            """
            
            results = db.fetch_all(query, (symbol, question_id))
            return bool(results)
    except Exception:
        return False