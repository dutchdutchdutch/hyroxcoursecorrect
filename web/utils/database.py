"""
SQLite Database Utility for HYROX Course Correct.

Handles database connections and schema initialization.
"""

import sqlite3
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'hyrox_results.db'


def get_db_connection():
    """
    Create a database connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DB_PATH)
    # Enable accessing columns by name
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initialize the database schema.
    """
    # Ensure data directory exists
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create the race_results table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS race_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venue TEXT,
        event_id TEXT,
        location TEXT,
        region TEXT,
        gender TEXT, -- 'M' or 'W'
        rank INTEGER,
        name TEXT,
        nationality TEXT,
        age_group TEXT,
        finish_time TEXT, -- HH:MM:SS format
        finish_seconds INTEGER
    )
    ''')
    
    # Create index for common queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_venue_gender ON race_results(venue, gender)')

    # Create the feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rating INTEGER,
        comments TEXT,
        liked TEXT,
        learned TEXT,
        lacking TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    print(f"Initializing database at {DB_PATH}...")
    init_db()
    print("Database initialized successfully.")
