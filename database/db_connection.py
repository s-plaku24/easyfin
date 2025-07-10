"""
Database connection handler for PostgreSQL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """
        Establish connection to PostgreSQL database
        """
        try:
            self.connection = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            return True
        except Exception as e:
            return False
    
    def disconnect(self):
        """
        Close database connection
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """
        Execute a query with optional parameters
        """
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except Exception as e:
            self.connection.rollback()
            return False
    
    def fetch_all(self, query, params=None):
        """
        Execute a SELECT query and return all results
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            return []
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()