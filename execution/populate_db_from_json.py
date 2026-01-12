import json
import sqlite3
from pathlib import Path

DB_PATH = Path('data/hyrox_results.db')
RAW_DATA_DIR = Path('data/backup_raw_results')

def populate_db():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Clear existing data
    print("Clearing existing data from race_results...")
    cursor.execute("DELETE FROM race_results")
    conn.commit()
    
    # Get all JSON files
    json_files = list(RAW_DATA_DIR.glob('*.json'))
    print(f"Found {len(json_files)} JSON files to import.")
    
    total_records = 0
    venues_processed = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            if not data:
                print(f"Skipping empty file: {json_file.name}")
                continue
                
            # Assume data is a list of result dicts
            # venue name might stay consistent within file
            if isinstance(data, list) and len(data) > 0:
                rows = []
                venue_name = data[0].get('venue', 'Unknown Venue')
                
                for r in data:
                    rows.append((
                        venue_name,
                        r.get('event_id', 'UNKNOWN'),
                        'Unknown', # Location
                        'Unknown', # Region
                        r['gender'],
                        r['rank'],
                        r['name'],
                        r.get('nationality', 'N/A'),
                        r.get('age_group', 'N/A'),
                        r['finish_time'],
                        r['finish_seconds']
                    ))
                
                cursor.executemany('''
                    INSERT INTO race_results (
                        venue, event_id, location, region, gender, rank, name, nationality, age_group, finish_time, finish_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', rows)
                
                print(f"  Imported {len(rows)} records for {venue_name} ({json_file.name})")
                total_records += len(rows)
                venues_processed += 1
                
        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")

    conn.commit()
    conn.close()
    
    print("="*50)
    print(f"Database population complete.")
    print(f"Total Venues: {venues_processed}")
    print(f"Total Records: {total_records}")

if __name__ == "__main__":
    populate_db()
