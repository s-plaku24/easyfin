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

def get_all_answers_for_stock(symbol):
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return []
            
            query = """
                SELECT a.question_id, a.answer_text, q.question_text, a.created_at
                FROM answers a
                JOIN questions_templates q ON a.question_id = q.id
                WHERE a.symbol = %s
                ORDER BY a.question_id
            """
            
            results = db.fetch_all(query, (symbol,))
            return [dict(row) for row in results]
                
    except Exception as e:
        print(f"[ERROR] Failed to get answers for {symbol}: {e}")
        return []

def get_all_answers_for_question(question_id):
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return []
            
            query = """
                SELECT a.symbol, a.answer_text, s.name as stock_name, a.created_at
                FROM answers a
                JOIN stocks s ON a.symbol = s.symbol
                WHERE a.question_id = %s
                ORDER BY a.symbol
            """
            
            results = db.fetch_all(query, (question_id,))
            return [dict(row) for row in results]
                
    except Exception as e:
        print(f"[ERROR] Failed to get answers for question {question_id}: {e}")
        return []

def get_dashboard_data():
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return {}
            
            query = """
                SELECT 
                    s.symbol,
                    s.name as stock_name,
                    a.question_id,
                    q.question_text,
                    a.answer_text,
                    a.created_at
                FROM stocks s
                LEFT JOIN answers a ON s.symbol = a.symbol
                LEFT JOIN questions_templates q ON a.question_id = q.id
                ORDER BY s.symbol, a.question_id
            """
            
            results = db.fetch_all(query)
            
            dashboard_data = {}
            for row in results:
                symbol = row['symbol']
                if symbol not in dashboard_data:
                    dashboard_data[symbol] = {
                        'stock_name': row['stock_name'],
                        'answers': []
                    }
                
                if row['question_id']:
                    dashboard_data[symbol]['answers'].append({
                        'question_id': row['question_id'],
                        'question_text': row['question_text'],
                        'answer_text': row['answer_text'],
                        'created_at': row['created_at']
                    })
            
            return dashboard_data
                
    except Exception as e:
        print(f"[ERROR] Failed to get dashboard data: {e}")
        return {}

def cleanup_old_answers(days_to_keep=30):
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return False
            
            query = """
                DELETE FROM answers 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """
            
            return db.execute_query(query, (days_to_keep,))
                
    except Exception as e:
        print(f"[ERROR] Failed to cleanup old answers: {e}")
        return False

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