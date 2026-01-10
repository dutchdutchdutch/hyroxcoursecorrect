#!/usr/bin/env python3
"""
HYROX Results Web Scraper

Scrapes event results from HYROX results website for Season 8 (2025/2026).
Saves raw data and outputs consolidated CSV for analysis.

Usage:
    python scrape_hyrox_results.py --venues anaheim london --top-n 200
    python scrape_hyrox_results.py --all-venues  # Future: scrape all Season 8 venues
"""

import argparse
import csv
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tqdm import tqdm


# Load environment variables
load_dotenv()

BASE_URL = 'https://results.hyrox.com'
RAW_DATA_DIR = Path('.tmp/raw_results')
OUTPUT_FILE = Path('.tmp/raw_results_combined.csv')

# Event configurations for Season 8 (2025/2026)
SEASON_8_EVENTS = {
    'anaheim': {
        'name': 'Anaheim 2025',
        'event_id': 'H_LR3MS4JI11AC',
        'season_path': 'season-8',
    },
    'london': {
        'name': 'London Excel 2025',
        'event_id': 'H_Excel25_OVERALL',
        'season_path': '',  # Uses root path
    },
}

DIVISIONS = {
    'men': 'M',
    'women': 'W',
}


def build_results_url(event_config: Dict, gender: str, page: int = 1, 
                     num_results: int = 100) -> str:
    """
    Build URL for results page.
    
    Args:
        event_config: Event configuration dict
        gender: 'M' or 'W'
        page: Page number (1-indexed)
        num_results: Results per page (max 100)
    
    Returns:
        Full URL for results page
    """
    params = {
        'page': page,
        'event': event_config['event_id'],
        'num_results': num_results,
        'pid': 'list',
        'ranking': 'time_finish_netto',
        'search[sex]': gender,
        'search[age_class]': '%',
        'search[nation]': '%',
    }
    
    # Build URL
    if event_config['season_path']:
        base = f"{BASE_URL}/{event_config['season_path']}/"
    else:
        base = f"{BASE_URL}/"
    
    url = base + '?' + urlencode(params)
    return url


def parse_time_to_seconds(time_str: str) -> float:
    """
    Parse HYROX time format (HH:MM:SS or MM:SS) to seconds.
    
    Args:
        time_str: Time string (e.g., "1:15:30" or "45:30")
    
    Returns:
        Time in seconds
    """
    if not time_str or time_str.strip() == '':
        return None
    
    time_str = time_str.strip()
    parts = time_str.split(':')
    
    try:
        if len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return None
    except (ValueError, AttributeError):
        return None


def scrape_results_page(url: str, event_name: str, division_name: str) -> List[Dict[str, Any]]:
    """
    Scrape a single results page.
    
    Args:
        url: URL to scrape
        event_name: Event name for record keeping
        division_name: Division name (Men/Women Individual)
    
    Returns:
        List of athlete result dictionaries
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error fetching {url}: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find results table
    results_table = soup.find('div', class_='list-box')
    if not results_table:
        print(f"⚠️  No results table found at {url}")
        return []
    
    # Find all result rows
    result_rows = results_table.find_all('li', class_='list-active')
    
    results = []
    
    for row in result_rows:
        try:
            # Extract data from row
            # Rank
            rank_div_elem = row.find('div', class_='list-field type-field')
            rank_div = rank_div_elem.text.strip() if rank_div_elem else None
            
            # Name
            name_elem = row.find('div', class_='list-field type-fullname')
            if name_elem:
                name_link = name_elem.find('a')
                athlete_name = name_link.text.strip() if name_link else name_elem.text.strip()
            else:
                athlete_name = None
            
            # Nationality
            nat_elem = row.find('div', class_='list-field type-nation')
            nationality = nat_elem.text.strip() if nat_elem else None
            
            # Age Group
            age_elem = row.find('div', class_='list-field type-age_class')
            age_group = age_elem.text.strip() if age_elem else None
            
            # Total Time (finish time)
            time_elem = row.find('div', class_='list-field type-time')
            finish_time_str = time_elem.text.strip() if time_elem else None
            finish_time_seconds = parse_time_to_seconds(finish_time_str)
            
            if athlete_name and finish_time_seconds:
                results.append({
                    'event_name': event_name,
                    'division': division_name,
                    'rank_overall': rank_div,
                    'athlete_name': athlete_name,
                    'nationality': nationality,
                    'age_group': age_group,
                    'finish_time': finish_time_str,
                    'finish_time_seconds': finish_time_seconds,
                })
        
        except Exception as e:
            print(f"⚠️  Error parsing row: {e}")
            continue
    
    return results


def scrape_event(event_key: str, top_n: int = 200) -> List[Dict[str, Any]]:
    """
    Scrape results for a specific event (both men and women).
    
    Args:
        event_key: Event key from SEASON_8_EVENTS
        top_n: Number of top results to scrape per division
    
    Returns:
        List of all results for this event
    """
    event_config = SEASON_8_EVENTS[event_key]
    event_name = event_config['name']
    
    print(f"\n{'='*60}")
    print(f"Scraping: {event_name}")
    print(f"{'='*60}")
    
    all_results = []
    
    # Calculate pages needed (100 results per page max)
    pages_needed = (top_n + 99) // 100  # Ceiling division
    
    for division_key, gender_code in DIVISIONS.items():
        division_name = f"{division_key.capitalize()} Individual"
        print(f"\n{division_name}:")
        
        division_results = []
        
        for page in range(1, pages_needed + 1):
            url = build_results_url(event_config, gender_code, page, num_results=100)
            print(f"  Page {page}: {url}")
            
            page_results = scrape_results_page(url, event_name, division_name)
            division_results.extend(page_results)
            
            print(f"    Found {len(page_results)} results")
            
            # Rate limiting
            time.sleep(1.5)
            
            # Stop if we have enough results
            if len(division_results) >= top_n:
                division_results = division_results[:top_n]
                break
        
        print(f"  Total {division_name}: {len(division_results)} results")
        all_results.extend(division_results)
    
    return all_results


def save_raw_data(event_key: str, data: List[Dict]) -> None:
    """Save raw scraped data to JSON file."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    filepath = RAW_DATA_DIR / f"{event_key}_raw.json"
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Raw data saved: {filepath}")


def consolidate_results(all_results: List[Dict[str, Any]]) -> None:
    """
    Consolidate all results into single CSV file.
    
    Args:
        all_results: List of all athlete results across events
    """
    if not all_results:
        print("⚠️  No results to consolidate")
        return
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        'event_name',
        'division',
        'rank_overall',
        'athlete_name',
        'nationality',
        'age_group',
        'finish_time',
        'finish_time_seconds',
    ]
    
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\n{'='*60}")
    print(f"✓ Consolidated {len(all_results)} results to {OUTPUT_FILE}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='Scrape HYROX Season 8 results')
    parser.add_argument('--venues', nargs='+', 
                       choices=['anaheim', 'london', 'all'],
                       default=['anaheim', 'london'],
                       help='Venues to scrape')
    parser.add_argument('--top-n', type=int, default=200,
                       help='Number of top results per division (default: 200)')
    
    args = parser.parse_args()
    
    # Determine which venues to scrape
    if 'all' in args.venues:
        venues = list(SEASON_8_EVENTS.keys())
    else:
        venues = args.venues
    
    print(f"Scraping venues: {', '.join(venues)}")
    print(f"Top {args.top_n} results per division (Men/Women Individual)")
    
    # Scrape each venue
    all_results = []
    
    for venue in venues:
        if venue not in SEASON_8_EVENTS:
            print(f"⚠️  Unknown venue: {venue}")
            continue
        
        venue_results = scrape_event(venue, args.top_n)
        all_results.extend(venue_results)
        
        # Save raw data for this venue
        save_raw_data(venue, venue_results)
    
    # Consolidate to CSV
    consolidate_results(all_results)
    
    # Summary
    print("\n" + "="*60)
    print("SCRAPING SUMMARY")
    print("="*60)
    print(f"Venues processed: {len(venues)}")
    print(f"Total results: {len(all_results)}")
    
    # Breakdown by event and division
    from collections import Counter
    event_counts = Counter(r['event_name'] for r in all_results)
    division_counts = Counter(r['division'] for r in all_results)
    
    print("\nBy Event:")
    for event, count in event_counts.items():
        print(f"  {event}: {count}")
    
    print("\nBy Division:")
    for division, count in division_counts.items():
        print(f"  {division}: {count}")
    
    print(f"\nOutput: {OUTPUT_FILE}")
    print("="*60)


if __name__ == '__main__':
    main()
