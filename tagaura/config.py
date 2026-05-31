import os
import sqlite3
import json
from pathlib import Path

# ~/.tagaura/ klasörünü belirle
HOME_DIR = Path.home()
TAGAURA_DIR = HOME_DIR / ".tagaura"
DB_PATH = TAGAURA_DIR / "tagaura.db"
MEMORY_PATH = TAGAURA_DIR / "memory.json"

def get_memory():
    if not MEMORY_PATH.exists():
        return []
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def add_to_memory(fact: str):
    TAGAURA_DIR.mkdir(parents=True, exist_ok=True)
    memory = get_memory()
    if fact not in memory:
        memory.append(fact)
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)

def init_db():
    if not TAGAURA_DIR.exists():
        TAGAURA_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Config tablosu (Provider, Model, API Key için)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Log tablosu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            details TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_config(key):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def set_config(key, value):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def log_action(action, details):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (action, details) VALUES (?, ?)", (action, details))
    conn.commit()
    conn.close()
