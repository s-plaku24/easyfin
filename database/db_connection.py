import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.connection.autocommit = False
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except Exception:
            pass
    
    def execute_query(self, query, params=None):
        try:
            if not self.connection or not self.cursor:
                return False
            
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Query execution failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def fetch_all(self, query, params=None):
        try:
            if not self.connection or not self.cursor:
                return []
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception:
            return []
    
    def __enter__(self):
        return self if self.connect() else None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None and self.connection:
                self.connection.rollback()
            elif self.connection:
                self.connection.commit()
        except Exception:
            pass
        finally:
            self.disconnect()

def test_database_connection():
    """Test database connection"""
    try:
        with DatabaseConnection() as db:
            if not db or not db.connection:
                return False
            
            results = db.fetch_all("SELECT COUNT(*) as count FROM stocks")
            return bool(results)
    except Exception:
        return False