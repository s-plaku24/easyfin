from database.db_connection import DatabaseConnection

def insert_question(question_text):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return False
            
            query = """
                INSERT INTO questions_templates (question_text)
                VALUES (%s)
                RETURNING id
            """
            
            db.cursor.execute(query, (question_text,))
            result = db.cursor.fetchone()
            db.connection.commit()
            
            if result:
                return result['id']
            return None
                
    except Exception as e:
        return None

def get_all_questions():
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return []
            
            query = "SELECT * FROM questions_templates ORDER BY id"
            results = db.fetch_all(query)
            
            return [dict(row) for row in results]
                
    except Exception as e:
        return []

def get_question_by_id(question_id):
    try:
        with DatabaseConnection() as db:
            if not db.connection:
                return None
            
            query = "SELECT * FROM questions_templates WHERE id = %s"
            results = db.fetch_all(query, (question_id,))
            
            if results:
                return dict(results[0])
            return None
                
    except Exception as e:
        return None

def initialize_default_questions():
    try:
        questions = get_all_questions()
        
        if not questions:
            default_questions = [
                "What is the current performance of this stock compared to its recent historical trend?",
                "Is this stock considered overvalued or undervalued based on current analyst targets and earnings data?",
                "What are the key financial strengths or weaknesses of this company based on its latest financial statements?",
                "What do recent insider and institutional activities suggest about confidence in this stock?",
                "How does the stock's volatility and risk profile compare to the broader market?"
            ]
            
            for question in default_questions:
                insert_question(question)
            
            return True
        
        return True
        
    except Exception as e:
        return False