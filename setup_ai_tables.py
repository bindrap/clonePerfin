import sqlite3
from datetime import datetime

# Create conversation history table
conn = sqlite3.connect('finance_tracker.db')
cursor = conn.cursor()

# Create conversations table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ai_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )
''')

# Create messages table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS ai_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE CASCADE
    )
''')

conn.commit()
conn.close()

print("✅ AI conversation tables created successfully!")
