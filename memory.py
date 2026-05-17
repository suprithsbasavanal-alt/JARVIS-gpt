"""
memory.py
This file handles the SQLite database for permanent memory storage.
"""
import sqlite3
import logging

logging.basicConfig(filename='jarvis_log.txt', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_database():
    """
    Creates the database and tables if they don't exist.
    """
    try:
        # Connect to the SQLite database file (it will be created if it doesn't exist)
        conn = sqlite3.connect('jarvis_memory.db')
        # Create a cursor object to execute SQL commands
        cursor = conn.cursor()
        
        # Create a table for facts with key-value pairs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facts (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Save the changes and close the connection
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error setting up database: {e}")

def save_memory(key, value):
    """
    Saves a fact into the database.
    
    Args:
        key (str): The name or category of the fact (e.g., 'name').
        value (str): The actual information (e.g., 'Arjun').
    """
    try:
        conn = sqlite3.connect('jarvis_memory.db')
        cursor = conn.cursor()
        # Insert or replace the fact in the database
        cursor.execute('REPLACE INTO facts (key, value) VALUES (?, ?)', (key, value))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving memory: {e}")

def get_memory(key):
    """
    Retrieves a specific fact from the database.
    
    Args:
        key (str): The name of the fact to retrieve.
        
    Returns:
        str: The saved information, or None if not found.
    """
    try:
        conn = sqlite3.connect('jarvis_memory.db')
        cursor = conn.cursor()
        # Search for the key in the database
        cursor.execute('SELECT value FROM facts WHERE key = ?', (key,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting memory: {e}")
        return None

def get_all_memories():
    """
    Retrieves all saved facts to pass to the AI context.
    
    Returns:
        str: A string summarizing all memories.
    """
    try:
        conn = sqlite3.connect('jarvis_memory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM facts')
        results = cursor.fetchall()
        conn.close()
        
        memory_str = ""
        for row in results:
            memory_str += f"{row[0]}: {row[1]}. "
        return memory_str
    except Exception as e:
        logging.error(f"Error getting all memories: {e}")
        return ""

def delete_memory(key):
    """
    Deletes a specific fact from the database.
    
    Args:
        key (str): The name of the fact to delete.
    """
    try:
        conn = sqlite3.connect('jarvis_memory.db')
        cursor = conn.cursor()
        # Delete the row where the key matches
        cursor.execute('DELETE FROM facts WHERE key = ?', (key,))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error deleting memory: {e}")
