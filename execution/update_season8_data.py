#!/usr/bin/env python3
"""
Update Scraper for Season 8 HYROX Data.

This script:
1. Loads the Season 8 event list from `season_8_events.json`.
2. Checks `data/scraping_state.json` to see which events are new or incomplete.
3. Scrapes the Top 80% of Men's and Women's "HYROX Overall" results for each incomplete event.
   - Calculates the 80% cutoff by first checking the total count.
   - Saves raw data to `.tmp/raw_results`.
   - Updates the state file upon completion.

Usage:
    python update_season8_data.py
"""

import json
import os
import time
import argparse
from pathlib import Path
from urllib.parse import urlencode
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configuration
SEASON_8_FILE = Path(__file__).parent / 'season_8_events.json'
STATE_FILE = Path('data/scraping_state.json')
RAW_DATA_DIR = Path('.tmp/raw_results')
BASE_URL = 'https://results.hyrox.com'

# Ensure directories exist
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

DIVISIONS = {
    'men': 'M',
    'women': 'W',
}

def load_json(filepath):
    if not filepath.exists():
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def build_url(event_config, gender, page=1):
    params = {
        'page': page,
        'event': event_config.get('id'),
        'num_results': 50, # 50 is typical max per page
        'pid': 'list',
        'ranking': 'time_finish_netto',
        'search[sex]': gender,
        'search[age_class]': '%',
        'search[nation]': '%'
    }
    
    # Handle event group param if present (for generic IDs)
    if 'event_group' in event_config:
        params['event_main_group'] = event_config['event_group']
        
    base = f"{BASE_URL}/season-8/"
    return base + '?' + urlencode(params)

def parse_time(time_str):
    if not time_str: return None
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0])*60 + int(parts[1])
    except:
        return None
    return None

def get_total_results(event_config, gender):
    """
    Finds the total number of results by checking the last page.
    This is tricky because we don't know the last page number.
    We can try a binary search or just 'search' for the text on the page?
    Actually, usually the text says "Results 1-50 of 1234".
    """
    import re
    url = build_url(event_config, gender, page=1)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Look for the specific element class found by the subagent
        total_elem = soup.find('span', class_='str_num')
        if total_elem:
            text = total_elem.get_text().strip()
            # Text is "1835 Results" or similar
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))

        # Look for "Results X-Y of Z"
        # Often in a div or similar. Or just regex the body text.
        import re
        text = soup.get_text()
        
        # Try finding the "Entries: X" text which is common in Hyrox results
        match = re.search(r'Entries:\s*(\d+)', text)
        if match:
            return int(match.group(1))
            
        match = re.search(r'Results \d+-\d+ of (\d+)', text)
        if match:
            return int(match.group(1))
            
        # Fallback: check pagination
        # Or maybe it's "1234 results found"
        match = re.search(r'(\d+) Results', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
            
        # Check for list items count if small
        results_count = len(soup.find_all('li', class_='list-active'))
        if results_count > 0 and results_count < 50:
            return results_count
            
        return 0
    except Exception as e:
        print(f"    Error getting count: {e}")
        return 0

def scrape_page(url, event_name, gender):
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
    except Exception as e:
        print(f"    Error fetching {url}: {e}")
        return None  # None indicates failure, [] indicates empty page

    soup = BeautifulSoup(resp.content, 'html.parser')
    rows = soup.find_all('li', class_='list-active')
    results = []

    for row in rows:
        try:
            # Rank
            rank_elem = row.find('div', class_='type-place')
            # Handle cases where rank is "DSQ" or "-"
            rank_text = rank_elem.text.strip().replace('.', '') if rank_elem else None
            rank = int(rank_text) if rank_text and rank_text.isdigit() else None
            
            # Name
            name_elem = row.find('h4', class_='type-fullname')
            name = name_elem.text.strip() if name_elem else None
            
            # Time
            time_elem = row.find('div', class_='type-time')
            time_str = time_elem.text.strip().replace('Total', '').strip() if time_elem else None
            seconds = parse_time(time_str)
            
            if name and seconds:
                results.append({
                    'venue': event_name,
                    'gender': 'M' if gender == 'M' else 'W',
                    'rank': rank,
                    'name': name,
                    'finish_time': time_str,
                    'finish_seconds': seconds
                })
        except Exception:
            continue
            
    return results

def scrape_event(event_config, state):
    event_name = event_config['name']
    print(f"\nProcessing: {event_name}")
    
    event_results = []
    
    # Check for multi-day split
    if 'multi_day_split' in event_config:
        splits = event_config['multi_day_split']
        print(f"  Detected Multi-Day Event: {list(splits.keys())}")
        
        for day_name, split_id in splits.items():
            print(f"  > Scraping {day_name} (ID: {split_id})")
            # Create a temporary config for this split
            split_config = event_config.copy()
            split_config['id'] = split_id
            # Remove multi_day_split to avoid recursion (though we are looping)
            if 'multi_day_split' in split_config:
                del split_config['multi_day_split']
                
            # Scrape this specific ID
            # We need to pass a specific state or just let it accumulate
            # But wait, we need to handle gender logic inside.
            # So we can just call the gender loop logic here or refactor.
            # Refactoring is cleaner: extract the gender loop.
            
            day_results = scrape_single_id(split_config, event_name)
            event_results.extend(day_results)
            
    else:
        # Normal single ID event
        day_results = scrape_single_id(event_config, event_name)
        event_results.extend(day_results)

    return event_results

def scrape_single_id(event_config, event_name):
    """
    Scrapes Men and Women for a specific event ID.
    This replaces the logic previously inside scrape_event.
    """
    results = []
    for div_name, gender_code in DIVISIONS.items():
        total_count = get_total_results(event_config, gender_code)
        
        if total_count == 0:
            print(f"    {div_name.capitalize()}: No results found (or failed to load). Skipping.")
            continue
            
        cutoff_rank = int(total_count * 0.8)
        print(f"    {div_name.capitalize()}: {total_count} total. Target (Top 80%): {cutoff_rank}")
        
        page = 1
        consecutive_failures = 0
        
        while True:
            url = build_url(event_config, gender_code, page)
            page_results = scrape_page(url, event_name, gender_code)
            
            if page_results is None:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    print(f"      Failed 3 times on page {page}. Moving to next division.")
                    break
                time.sleep(2)
                continue
            
            consecutive_failures = 0
            
            if not page_results:
                break
                
            filtered_page = [r for r in page_results if r['rank'] is not None and r['rank'] <= cutoff_rank]
            
            # If all results on this page are beyond cutoff, stop
            if not filtered_page and page_results[0]['rank'] and page_results[0]['rank'] > cutoff_rank:
                 print(f"      Reached cutoff ranking at page {page}.")
                 break
            
            if filtered_page:
                results.extend(filtered_page)
            
            # Check last item on page to see if we passed cutoff
            last_rank = page_results[-1]['rank']
            if last_rank and last_rank > cutoff_rank:
                 break
                 
            page += 1
            time.sleep(1) # Rate limit
    return results

def update_database_for_event(event_name, results):
    """
    Updates the SQLite database with the results from a single event.
    """
    db_path = Path('data/hyrox_results.db')
    import sqlite3
    
    if not results:
        return

    print(f"  > Updating Database for {event_name} ({len(results)} records)...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # We need to adhere to the schema: 
        # venue, event_id, location, region, gender, rank, name, nationality, age_group, finish_time, finish_seconds
        
        # First, delete existing entries for this venue to avoid duplicates if we are re-scraping
        cursor.execute("DELETE FROM race_results WHERE venue = ?", (event_name,))
        
        # Prepare data
        rows = []
        for r in results:
            # Enrich/Clean data if needed
            # We don't have location/region in the results dict, but we could pass it from event_config
            # For now, we'll just insert what we have.
            # Wait, the current schema expects specific columns.
            # Let's check `web/utils/database.py` or existing schema.
            # Schema: id, venue, event_id, location, region, gender, rank, name, nationality, age_group, finish_time, finish_seconds
            
            rows.append((
                event_name,
                r.get('event_id', 'UNKNOWN'), # We might need to pass this down
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
        
        conn.commit()
        conn.close()
        print(f"  > Database Updated.")
        
    except Exception as e:
        print(f"  Error updating database: {e}")

def main():
    if not SEASON_8_FILE.exists():
        print(f"Error: {SEASON_8_FILE} not found.")
        return

    season_events = load_json(SEASON_8_FILE)
    state = load_json(STATE_FILE)
    
    if 'completed_events' not in state:
        state['completed_events'] = []
        
    print(f"Found {len(season_events)} events in Season 8 list.")
    
    for event_config in season_events:
        event_name = event_config['name']
        
        if event_name in state['completed_events']:
            print(f"Skipping {event_name} (Already Completed)")
            continue
            
        # Scrape
        results = scrape_event(event_config, state)
        
        if results:
            # Save raw files
            safe_name = event_name.replace(' ', '_').lower()
            outfile = RAW_DATA_DIR / f"{safe_name}_raw.json"
            
            with open(outfile, 'w') as f:
                json.dump(results, f, indent=2)
                
            print(f"  Saved {len(results)} results to {outfile}")
            
            # Update Database IMMEDIATELY
            update_database_for_event(event_name, results)
            
            # Mark complete
            state['completed_events'].append(event_name)
            state['last_updated'] = datetime.now().isoformat()
            save_json(STATE_FILE, state)
        else:
            print(f"  No results saved for {event_name}.")

if __name__ == '__main__':
    main()
