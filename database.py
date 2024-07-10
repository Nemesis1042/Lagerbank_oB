import sqlite3
from typing import List, Tuple

class Database:
    def __init__(self, db_name="Lagerbank2024.db"):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
        
    def execute_select(self, query: str, values: tuple = ()) -> List[Tuple]:
        try:
            self.cursor.execute(query, values)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            raise Exception(f"Error executing select: {e}")
        
    def execute_insert(self, query: str, values: tuple) -> int:
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            raise Exception(f"Error executing insert: {e}")
    
    def execute_update(self, query: str, values: tuple) -> int:
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            raise Exception(f"Error executing update: {e}")
        
    def execute_delete(self, query: str, values: tuple) -> int:
        try:
            self.cursor.execute(query, values)
            self.connection.commit()
            return self.cursor.rowcount
        except sqlite3.Error as e:
            raise Exception(f"Error executing delete: {e}")
        
    def delete_database(self):
        try:
            self.cursor.execute("DROP TABLE IF EXISTS Teilnehmer")
            self.cursor.execute("DROP TABLE IF EXISTS Produkt")
            self.cursor.execute("DROP TABLE IF EXISTS Konto")
            self.cursor.execute("DROP TABLE IF EXISTS Transaktion")
            self.cursor.execute("DROP TABLE IF EXISTS Produkt_Barcode")
            self.connection.commit()
        except sqlite3.Error as e:
            raise Exception(f"Error deleting database: {e}")

def get_db_connection():
    conn = sqlite3.connect("Lagerbank2024.db")
    conn.row_factory = sqlite3.Row
    return conn
