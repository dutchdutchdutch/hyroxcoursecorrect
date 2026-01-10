#!/usr/bin/env python3
"""
HYROX Results Browser-Based Scraper

Uses browser automation to scrape HYROX results (JavaScript-rendered content).
This version uses the browser_subagent approach to extract data.

Usage:
    python scrape_hyrox_browser.py --venues anaheim london --top-n 200
"""

import argparse
import csv
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any

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

RAW_DATA_DIR = Path('.tmp/raw_results')
OUTPUT_FILE = Path('.tmp/raw_results_combined.csv')


def build_results_url(event_config: Dict, gender: str, page: int = 1, 
                     num_results: int = 100) -> str:
    """Build URL for results page."""
    from urllib.parse import urlencode
    
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
    
    if event_config['season_path']:
        base = f"https://results.hyrox.com/{event_config['season_path']}/"
    else:
        base = "https://results.hyrox.com/"
    
    return base + '?' + urlencode(params)


def scrape_page_with_javascript(url: str) -> List[Dict]:
    """
    Scrape a page using JavaScript extraction.
    
    This creates a temporary JavaScript file that extracts the data
    and can be run in a browser context.
    """
    # JavaScript to extract results from the page
    js_code = """
    (() => {
        const results = [];
        const rows = document.querySelectorAll('li.list-group-item');
        
        rows.forEach(row => {
            // Check if this is a data row (has athlete link)
            const nameLink = row.querySelector('a[href*="idp="]');
            if (!nameLink) return;
            
            // Extract rank
            const rankElem = row.querySelector('.list-field.type-place.place-primary');
            const rank = rankElem ? rankElem.innerText.trim() : null;
            
            // Extract name
            const name = nameLink.innerText.trim();
            
            // Extract nationality
            const natElem = row.querySelector('.nation__abbr');
            const nationality = natElem ? natElem.innerText.trim() : null;
            
            // Extract age group
            const ageElem = row.querySelector('.list-field.type-age_class');
            const ageGroup = ageElem ? ageElem.innerText.trim() : null;
            
            // Extract finish time
            const timeElem = row.querySelector('.list-field.type-time');
            const finishTime = timeElem ? timeElem.innerText.trim() : null;
            
            if (name && finishTime) {
                results.push({
                    rank: rank,
                    name: name,
                    nationality: nationality,
                    age_group: ageGroup,
                    finish_time: finishTime
                });
            }
        });
        
        return results;
    })()
    """
    
    return js_code


def scrape_with_browser_subagent(event_key: str, top_n: int = 200) -> List[Dict]:
    """
    Scrape using browser subagent approach.
    
    This is a placeholder - in practice, you would use the browser_subagent
    tool from the main orchestration layer.
    """
    print(f"\n⚠️  Browser-based scraping requires manual execution")
    print(f"   Use the browser_subagent tool to navigate to URLs and extract data")
    print(f"   Or use Playwright/Selenium for automated browser scraping")
    
    return []


def save_raw_data(event_key: str, data: List[Dict]) -> None:
    """Save raw scraped data to JSON file."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    filepath = RAW_DATA_DIR / f"{event_key}_raw.json"
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Raw data saved: {filepath}")


def consolidate_results(all_results: List[Dict[str, Any]]) -> None:
    """Consolidate all results into single CSV file."""
    if not all_results:
        print("⚠️  No results to consolidate")
        return
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
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
    parser = argparse.ArgumentParser(description='Scrape HYROX Season 8 results (browser-based)')
    parser.add_argument('--venues', nargs='+', 
                       choices=['anaheim', 'london', 'all'],
                       default=['anaheim', 'london'])
    parser.add_argument('--top-n', type=int, default=200)
    
    args = parser.parse_args()
    
    print("="*60)
    print("HYROX BROWSER-BASED SCRAPER")
    print("="*60)
    print("\nThis scraper requires browser automation.")
    print("The HYROX results site uses JavaScript to render content.")
    print("\nRecommended approach:")
    print("1. Use browser_subagent tool from main orchestration")
    print("2. Or install Playwright: pip install playwright && playwright install")
    print("3. Then use scrape_hyrox_playwright.py (to be created)")
    print("\n" + "="*60)
    
    # Print URLs that need to be scraped
    venues = args.venues if 'all' not in args.venues else list(SEASON_8_EVENTS.keys())
    
    print("\nURLs to scrape:")
    for venue in venues:
        if venue not in SEASON_8_EVENTS:
            continue
        
        event_config = SEASON_8_EVENTS[venue]
        print(f"\n{event_config['name']}:")
        
        for div_name, gender_code in DIVISIONS.items():
            pages_needed = (args.top_n + 99) // 100
            for page in range(1, pages_needed + 1):
                url = build_results_url(event_config, gender_code, page, 100)
                print(f"  {div_name.capitalize()} page {page}: {url}")
    
    print("\n" + "="*60)
    print("JavaScript extraction code:")
    print("="*60)
    print(scrape_page_with_javascript(""))
    print("="*60)


if __name__ == '__main__':
    main()
