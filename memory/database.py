"""
memory/database.py
Handles all persistent storage using SQLite.
Includes tables for facts, tasks, preferences, and conversations.
"""
import sqlite3
import os

DB_PATH = "jarvis_memory.db"

def init_db():
    """Initializes the database and creates necessary tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Facts table (e.g. name, preferences)
    cursor.execute('''CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT)''')
    # Tasks table
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT, status TEXT)''')
    # Conversations table
    cursor.execute('''CREATE TABLE IF NOT EXISTS conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT)''')
    conn.commit()
    conn.close()

def save_fact(key, value):
    """Saves a fact (key-value pair) to memory."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('REPLACE INTO facts (key, value) VALUES (?, ?)', (key, str(value)))
    conn.commit()
    conn.close()

def get_fact(key):
    """Retrieves a fact by its key."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM facts WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def get_all_facts():
    """Returns all facts as a string for AI context."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT key, value FROM facts')
    results = cursor.fetchall()
    conn.close()
    return ", ".join([f"{k}: {v}" for k, v in results])

def add_task(task_text):
    """Adds a new task to the to-do list."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task, status) VALUES (?, ?)', (task_text, 'pending'))
    conn.commit()
    conn.close()

def get_tasks():
    """Retrieves all pending tasks."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT task FROM tasks WHERE status = "pending"')
    results = cursor.fetchall()
    conn.close()
    return [r[0] for r in results]
