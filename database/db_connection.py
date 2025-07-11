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
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        try:
            if not self.connection or not self.cursor:
                print("[ERROR] No database connection")
                return False
                
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def fetch_all(self, query, params=None):
        try:
            if not self.connection or not self.cursor:
                print("[ERROR] No database connection")
                return []
                
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Query fetch failed: {e}")
            return []
    
    def __enter__(self):
        if self.connect():
            return self
        else:
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()