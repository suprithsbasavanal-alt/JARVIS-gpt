"""
memory/rag.py
Retrieval-Augmented Generation (RAG) System.
Uses Ollama to generate local embeddings and stores them in SQLite for semantic search.
This allows JARVIS to have infinite, searchable long-term knowledge.
"""
import sqlite3
import json
import numpy as np
import ollama
import os

DB_PATH = 'jarvis_rag.db'
EMBED_MODEL = 'nomic-embed-text' # Extremely fast, lightweight local embedding model

def init_rag_db():
    """Initializes the vector database for RAG."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_content TEXT,
            embedding TEXT,
            metadata TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_embedding(text):
    """Generates an embedding vector for the text using Ollama."""
    try:
        response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
        return response['embedding']
    except Exception as e:
        print(f"RAG Embedding Error (make sure nomic-embed-text is pulled): {e}")
        return None

def cosine_similarity(vec1, vec2):
    """Calculates cosine similarity between two vectors."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def add_document(text, metadata="User Input"):
    """Adds a document to the RAG memory."""
    embedding = get_embedding(text)
    if not embedding:
        return False
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO documents (text_content, embedding, metadata) VALUES (?, ?, ?)',
        (text, json.dumps(embedding), metadata)
    )
    conn.commit()
    conn.close()
    return True

def search_memory(query, top_k=2):
    """Searches the RAG database for the most semantically relevant memories."""
    query_emb = get_embedding(query)
    if not query_emb:
        return []
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT text_content, embedding FROM documents')
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
        
    results = []
    for row in rows:
        text = row[0]
        emb = json.loads(row[1])
        sim = cosine_similarity(query_emb, emb)
        results.append((sim, text))
        
    # Sort by highest similarity
    results.sort(key=lambda x: x[0], reverse=True)
    
    # Return the top_k texts
    return [res[1] for res in results[:top_k] if res[0] > 0.5] # Threshold

# Initialize on import
if not os.path.exists(DB_PATH):
    init_rag_db()
