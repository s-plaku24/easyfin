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
            self.connection.autocommit = False  # Explicitly set autocommit to False
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False
    
    def disconnect(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except Exception as e:
            print(f"[WARN] Error during disconnect: {e}")
    
    def execute_query(self, query, params=None):
        try:
            if not self.connection or not self.cursor:
                print("[ERROR] No database connection")
                return False
            
            print(f"[DEBUG] Executing query: {query[:100]}...")
            self.cursor.execute(query, params)
            
            # CRITICAL: Always commit after execute
            self.connection.commit()
            print(f"[DEBUG] Query committed successfully")
            
            return True
        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            if self.connection:
                try:
                    self.connection.rollback()
                    print(f"[DEBUG] Transaction rolled back")
                except:
                    pass
            return False
    
    def fetch_all(self, query, params=None):
        try:
            if not self.connection or not self.cursor:
                print("[ERROR] No database connection")
                return []
            
            self.cursor.execute(query, params)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"[ERROR] Query fetch failed: {e}")
            return []
    
    def __enter__(self):
        if self.connect():
            return self
        else:
            return None
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # If there was an exception, rollback
            if exc_type is not None and self.connection:
                print(f"[DEBUG] Exception occurred, rolling back transaction")
                self.connection.rollback()
            else:
                # No exception, ensure final commit
                if self.connection:
                    self.connection.commit()
                    print(f"[DEBUG] Final commit on context exit")
        except Exception as e:
            print(f"[WARN] Error during context exit: {e}")
        finally:
            self.disconnect()

# Add a simple test function
def test_database_connection():
    """Test database connection and basic operations"""
    try:
        print("[INFO] Testing database connection...")
        
        with DatabaseConnection() as db:
            if not db or not db.connection:
                print("[ERROR] Failed to connect to database")
                return False
            
            # Test simple query
            test_query = "SELECT COUNT(*) as count FROM stocks"
            results = db.fetch_all(test_query)
            
            if results:
                print(f"[SUCCESS] Database connection test passed. Found {results[0]['count']} stocks")
                return True
            else:
                print("[ERROR] Database query test failed")
                return False
                
    except Exception as e:
        print(f"[ERROR] Database test failed: {e}")
        return False