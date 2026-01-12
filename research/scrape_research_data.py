#!/usr/bin/env python3
"""
Research Scraper: Full Leaderboards for Sampling Analysis.

Targets specific events (Anaheim 2025, Maastricht 2025) to scrape
complete leaderboards (Men/Women Open) for determining optimal sample sizes.
"""

import argparse
import csv
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

BASE_URL = 'https://results.hyrox.com'
DATA_DIR = Path('research/data')
OUTPUT_FILE = DATA_DIR / 'full_leaderboards.csv'

# Specific events for this research
RESEARCH_EVENTS = {
    'anaheim': {
        'name': 'Anaheim 2025',
        'event_id': 'H_LR3MS4JI11AC',
        'season_path': 'season-8',
    },
    'maastricht': {
        'name': 'Maastricht 2025',
        'event_id': 'H_MAASTRICHT25_OVERALL',
        'season_path': 'season-8',
    },
}

DIVISIONS = {
    'men': 'M',
    'women': 'W',
}


def build_url(event_config: Dict, gender: str, page: int = 1) -> str:
    """Build results page URL."""
    params = {
        'page': page,
        'event': event_config['event_id'],
        'num_results': 100,
        'pid': 'list',
        'ranking': 'time_finish_netto',
        'search[sex]': gender,
        'search[age_class]': '%',
        'search[nation]': '%',
    }
    
    base = f"{BASE_URL}/{event_config['season_path']}/"
    return base + '?' + urlencode(params)


def parse_time(time_str: str) -> float:
    """Parse HH:MM:SS to seconds."""
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


def scrape_page(url: str, event_name: str, gender: str) -> List[Dict]:
    """Scrape a single page."""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(resp.content, 'html.parser')
    rows = soup.find_all('li', class_='list-active')
    results = []

    for row in rows:
        try:
            # Rank
            rank_elem = row.find('div', class_='type-place')
            rank = rank_elem.text.strip().replace('.', '') if rank_elem else None
            
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
                    'rank': int(rank) if rank and rank.isdigit() else None,
                    'name': name,
                    'finish_time': time_str,
                    'finish_seconds': seconds
                })
        except Exception:
            continue
            
    return results


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []
    
    print("Starting full leaderboard scrape for research...")
    
    for key, config in RESEARCH_EVENTS.items():
        print(f"\nScraping {config['name']}...")
        
        for div_name, gender_code in DIVISIONS.items():
            print(f"  Division: {div_name.capitalize()}")
            page = 1
            while True:
                url = build_url(config, gender_code, page)
                # print(f"    Fetching {url}") 
                results = scrape_page(url, config['name'], gender_code)
                
                if not results:
                    break
                    
                all_results.extend(results)
                print(f"    Page {page}: Found {len(results)} results")
                
                # Safety break if we get 0 results (already handled) or just seemingly valid end
                if len(results) == 0:  
                    break
                    
                page += 1
                if page > 150: # Increased limit
                    print("    reached max page limit")
                    break
                    
                time.sleep(1) # Be nice
                
    # Save to CSV
    keys = ['venue', 'gender', 'rank', 'name', 'finish_time', 'finish_seconds']
    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_results)
        
    print(f"\nSaved {len(all_results)} total records to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
