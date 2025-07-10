from database.db_connection import DatabaseConnection

def insert_or_update_answer(symbol, question_id, answer_text):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            check_query = """
                SELECT symbol FROM answers 
                WHERE symbol = %s AND question_id = %s
            """
            existing = db.fetch_all(check_query, (symbol, question_id))
            
            if existing:
                update_query = """
                    UPDATE answers 
                    SET answer_text = %s 
                    WHERE symbol = %s AND question_id = %s
                """
                params = (answer_text, symbol, question_id)
                return db.execute_query(update_query, params)
            else:
                insert_query = """
                    INSERT INTO answers (symbol, question_id, answer_text)
                    VALUES (%s, %s, %s)
                """
                params = (symbol, question_id, answer_text)
                return db.execute_query(insert_query, params)
                
    except Exception as e:
        return False

def get_answer(symbol, question_id):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
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
        return None

def get_all_answers_for_stock(symbol):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
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
        return []

def get_all_answers_for_question(question_id):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
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
        return []

def get_dashboard_data():
    try:
        with DatabaseConnection() as db:
            if not db.connection:
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
        return {}

def cleanup_old_answers(days_to_keep=30):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            query = """
                DELETE FROM answers 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """
            
            return db.execute_query(query, (days_to_keep,))
                
    except Exception as e:
        return False