"""
Migration script to import HYROX race results from CSV to SQLite database.
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path so we can import our utility
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Adjust path to import from web.utils
from web.utils.database import init_db, get_db_connection

CSV_PATH = PROJECT_ROOT / 'data' / 'hyrox_9venues_100each.csv'


def migrate():
    """
    Read CSV and insert into SQLite.
    """
    if not CSV_PATH.exists():
        print(f"Error: CSV file not found at {CSV_PATH}")
        return

    print("Initializing database...")
    init_db()

    print(f"Reading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # Clean up column names just in case
    df.columns = [c.strip() for c in df.columns]

    print(f"Loaded {len(df)} records. Starting import to SQLite...")
    
    conn = get_db_connection()
    
    try:
        # We can use pandas to_sql for efficient bulk insertion
        # 'if_exists'='append' because table is already created by init_db
        df.to_sql('race_results', conn, if_exists='append', index=False)
        print("Data insertion complete.")
        
        # Verify the count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM race_results")
        count = cursor.fetchone()[0]
        print(f"Verification: Found {count} records in database.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
