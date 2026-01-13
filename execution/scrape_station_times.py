#!/usr/bin/env python3
"""
Scrape workout station times at specific rank intervals for field strength analysis.

Stations: Row (time_15), Burpee (time_14), Farmers Carry (time_16), Wall Balls (time_18)
Ranks: 50, 100, 150, 200
Venues: 1 EU (London), 1 NA (Chicago), 4 slow (Johannesburg, Singapore, Mumbai, Delhi)
"""

import time
import sqlite3
import csv
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

DB_PATH = Path('data/hyrox_results.db')
CSV_OUTPUT = Path('data/station_times_comparison.csv')
BASE_URL = 'https://results.hyrox.com/season-8/'

# Station ranking codes
STATIONS = {
    'Row': 'time_15',
    'Burpee': 'time_14',
    'Farmers_Carry': 'time_16',
    'Wall_Balls': 'time_18'
}

# Target ranks to sample (include smaller ranks for venues with smaller fields)
SAMPLE_RANKS = [1, 5, 10, 25, 50, 100]

# Venues to analyze
VENUES = [
    # Reference venues
    {'name': 'London Excel', 'event_group': '2025 London Excel', 'type': 'fast'},
    {'name': 'Chicago', 'event_group': '2025 Chicago', 'type': 'fast'},
    # Slow venues
    {'name': 'Johannesburg', 'event_group': '2025 Johannesburg', 'type': 'slow'},
    {'name': 'Singapore', 'event_group': '2025 Singapore', 'type': 'slow'},
    {'name': 'Mumbai', 'event_group': '2025 Mumbai', 'type': 'slow'},
    {'name': 'Delhi', 'event_group': '2025 Delhi', 'type': 'slow'},
]


def parse_time_to_seconds(time_str):
    """Convert MM:SS or HH:MM:SS to seconds."""
    if not time_str:
        return None
    try:
        time_str = time_str.strip()
        parts = time_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except:
        return None
    return None


def discover_event_id(driver, event_group):
    """Navigate to venue and find the HYROX Individual event ID (H_*, not HWC_*)."""
    url = f"{BASE_URL}index.php?event_main_group={event_group.replace(' ', '+')}&pid=list"
    driver.get(url)
    time.sleep(3)
    
    try:
        dropdown = driver.find_element(By.ID, 'event')
        options = dropdown.find_elements(By.TAG_NAME, 'option')
        
        # First priority: Find "H_*_OVERALL" (regular HYROX Individual Overall)
        for opt in options:
            text = opt.text.strip()
            value = opt.get_attribute('value')
            if text == 'HYROX - Overall' and value.startswith('H_') and not value.startswith('HWC'):
                return value
        
        # Second priority: Any H_* that's not Pro, Doubles, or World Championship
        for opt in options:
            value = opt.get_attribute('value')
            text = opt.text.strip()
            if value.startswith('H_') and not value.startswith('HWC') and not value.startswith('HDP') and 'DOUBLES' not in text and 'PRO' not in text:
                return value
                
    except Exception as e:
        print(f"  Error discovering event ID: {e}")
    
    return None


def scrape_station_results(driver, event_id, station_code, gender='M', max_results=250):
    """Scrape station leaderboard and extract times at target ranks."""
    url = f"{BASE_URL}index.php?event={event_id}&ranking={station_code}&num_results={max_results}&search[sex]={gender}&pid=list"
    
    driver.get(url)
    time.sleep(2.5)
    
    results = {}
    
    try:
        # Data rows have class 'list-active' (header has 'list-group-header')
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.list-active"))
        )
        
        rows = driver.find_elements(By.CSS_SELECTOR, "li.list-active")
        
        for i, row in enumerate(rows, 1):
            if i in SAMPLE_RANKS:
                try:
                    # Station time is in div.type-actual_ranking_time
                    time_elem = row.find_element(By.CSS_SELECTOR, "div.type-actual_ranking_time")
                    time_str = time_elem.text.strip()
                    # Remove "Time" label if present
                    time_str = time_str.replace('Time', '').strip()
                    time_seconds = parse_time_to_seconds(time_str)
                    results[i] = time_seconds
                except Exception as e:
                    results[i] = None
                    
    except TimeoutException:
        print(f"    Timeout")
    except Exception as e:
        print(f"    Error: {e}")
    
    return results


def scrape_venue(driver, venue_config):
    """Scrape all stations for a venue."""
    venue_name = venue_config['name']
    venue_type = venue_config['type']
    event_group = venue_config['event_group']
    
    print(f"\n{'='*50}")
    print(f"Scraping: {venue_name} ({venue_type})")
    print(f"{'='*50}")
    
    # Discover event ID
    event_id = discover_event_id(driver, event_group)
    if not event_id:
        print(f"  No event ID found. Skipping.")
        return []
    
    print(f"  Event ID: {event_id}")
    
    results = []
    
    for gender in ['M', 'W']:
        gender_label = 'Men' if gender == 'M' else 'Women'
        
        for station_name, station_code in STATIONS.items():
            print(f"  {gender_label} {station_name}...")
            
            station_results = scrape_station_results(driver, event_id, station_code, gender)
            
            for rank, time_seconds in station_results.items():
                results.append({
                    'venue': venue_name,
                    'venue_type': venue_type,
                    'gender': gender,
                    'station': station_name,
                    'rank': rank,
                    'time_seconds': time_seconds
                })
            
            time.sleep(1.5)
    
    return results


def save_results(all_results):
    """Save results to CSV."""
    if not all_results:
        return
    
    with open(CSV_OUTPUT, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['venue', 'venue_type', 'gender', 'station', 'rank', 'time_seconds'])
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\nSaved {len(all_results)} records to {CSV_OUTPUT}")


def main():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    
    all_results = []
    
    try:
        for venue_config in VENUES:
            venue_results = scrape_venue(driver, venue_config)
            all_results.extend(venue_results)
            
    finally:
        driver.quit()
    
    save_results(all_results)
    
    print(f"\n{'='*50}")
    print(f"=== STATION SCRAPING COMPLETE ===")
    print(f"Total records: {len(all_results)}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
