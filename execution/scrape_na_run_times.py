#!/usr/bin/env python3
"""
Scrape ONLY North American venues (incremental update).
"""

import json
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
from selenium.common.exceptions import TimeoutException, NoSuchElementException

DB_PATH = Path('data/hyrox_results.db')
CSV_OUTPUT = Path('data/pro_run_times.csv')
BASE_URL = 'https://results.hyrox.com/season-8/'

# North America only (excluding Mexico)
NA_VENUES = [
    {'name': 'Atlanta 2025', 'event_group': '2025 Atlanta'},
    {'name': 'Anaheim 2025', 'event_group': '2025 Anaheim'},
    {'name': 'Chicago 2025', 'event_group': '2025 Chicago'},
    {'name': 'Boston 2025', 'event_group': '2025 Boston'},
    {'name': 'Dallas 2025', 'event_group': '2025 Dallas'},
    {'name': 'Toronto 2025', 'event_group': '2025 Toronto'},
]


def parse_time_to_seconds(time_str):
    if not time_str:
        return None
    try:
        time_str = time_str.strip().replace('Run Total', '').replace('Total', '').strip()
        parts = time_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
    except:
        return None
    return None


def discover_event_ids(driver, venue_config):
    event_group = venue_config['event_group']
    url = f"{BASE_URL}index.php?event_main_group={event_group.replace(' ', '+')}&pid=list"
    
    print(f"  Discovering event IDs from: {url}")
    
    driver.get(url)
    time.sleep(3)
    
    event_ids = {'pro': None, 'individual': None}
    
    try:
        dropdown = driver.find_element(By.ID, 'event')
        options = dropdown.find_elements(By.TAG_NAME, 'option')
        
        for opt in options:
            value = opt.get_attribute('value')
            text = opt.text.strip()
            
            if 'HYROX PRO - Overall' in text and 'DOUBLES' not in text:
                event_ids['pro'] = value
                print(f"    Found Pro: {value}")
            
            if text == 'HYROX - Overall':
                event_ids['individual'] = value
                print(f"    Found Individual: {value}")
                
    except Exception as e:
        print(f"    Error discovering event IDs: {e}")
    
    return event_ids


def scrape_run_times_page(driver, url, venue_name, division, gender):
    results = []
    
    try:
        driver.get(url)
        time.sleep(2.5)
        
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.list-active"))
            )
        except TimeoutException:
            return []
        
        rows = driver.find_elements(By.CSS_SELECTOR, "li.list-active")
        
        for row in rows:
            try:
                try:
                    rank_elem = row.find_element(By.CSS_SELECTOR, "div.type-place")
                    rank_text = rank_elem.text.strip().replace('.', '')
                    rank = int(rank_text) if rank_text.isdigit() else None
                except:
                    rank = None
                
                try:
                    name_elem = row.find_element(By.CSS_SELECTOR, "h4.type-fullname")
                    name = name_elem.text.strip()
                except:
                    name = None
                
                if not name:
                    continue
                
                try:
                    nat_elem = row.find_element(By.CSS_SELECTOR, "span.type-nat")
                    nationality = nat_elem.text.strip()
                except:
                    nationality = "N/A"
                
                try:
                    age_elem = row.find_element(By.CSS_SELECTOR, "span.type-age_class")
                    age_group = age_elem.text.strip()
                except:
                    age_group = "N/A"
                
                time_elems = row.find_elements(By.CSS_SELECTOR, "div.type-time")
                
                run_total_str = None
                finish_total_str = None
                
                if len(time_elems) >= 2:
                    run_total_str = time_elems[0].text
                    finish_total_str = time_elems[1].text
                elif len(time_elems) == 1:
                    run_total_str = time_elems[0].text
                
                run_seconds = parse_time_to_seconds(run_total_str)
                finish_seconds = parse_time_to_seconds(finish_total_str)
                
                if name and run_seconds:
                    results.append({
                        'venue': venue_name,
                        'division': division,
                        'gender': 'M' if gender == 'M' else 'W',
                        'rank': rank,
                        'athlete_name': name,
                        'nationality': nationality,
                        'age_group': age_group,
                        'run_total_seconds': run_seconds,
                        'finish_total_seconds': finish_seconds
                    })
                    
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"    Error: {e}")
    
    return results


def scrape_division(driver, venue_name, division_name, event_id, max_results=200):
    if not event_id:
        print(f"  Skipping {division_name} (no event ID found)")
        return []
    
    all_results = []
    
    for gender in ['M', 'W']:
        gender_label = 'Men' if gender == 'M' else 'Women'
        print(f"  {division_name} {gender_label}...")
        
        pages_to_scrape = max_results // 100
        
        for page in range(1, pages_to_scrape + 1):
            url = f"{BASE_URL}index.php?event={event_id}&ranking=time_49&num_results=100&search[sex]={gender}&page={page}&pid=list"
            
            page_results = scrape_run_times_page(driver, url, venue_name, division_name, gender)
            
            if not page_results:
                print(f"    Page {page}: No results")
                break
            
            all_results.extend(page_results)
            print(f"    Page {page}: {len(page_results)} results")
            
            time.sleep(1.5)
    
    return all_results


def scrape_venue(driver, venue_config):
    venue_name = venue_config['name']
    print(f"\n{'='*50}")
    print(f"Scraping: {venue_name}")
    print(f"{'='*50}")
    
    event_ids = discover_event_ids(driver, venue_config)
    
    if not event_ids['pro'] and not event_ids['individual']:
        print(f"  No event IDs found for {venue_name}. Skipping.")
        return []
    
    all_results = []
    
    pro_results = scrape_division(driver, venue_name, 'Pro', event_ids['pro'], max_results=200)
    all_results.extend(pro_results)
    
    individual_results = scrape_division(driver, venue_name, 'Individual', event_ids['individual'], max_results=200)
    all_results.extend(individual_results)
    
    print(f"  Total for {venue_name}: {len(all_results)} records")
    return all_results


def save_to_db(results):
    if not results:
        return 0
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    rows = [(
        r['venue'],
        r['division'],
        r['gender'],
        r['rank'],
        r['athlete_name'],
        r['nationality'],
        r['age_group'],
        r['run_total_seconds'],
        r['finish_total_seconds'],
        datetime.now().isoformat()
    ) for r in results]
    
    cursor.executemany('''
        INSERT INTO pro_run_times (
            venue, division, gender, rank, athlete_name, nationality, age_group,
            run_total_seconds, finish_total_seconds, scraped_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', rows)
    
    conn.commit()
    conn.close()
    return len(rows)


def save_to_csv(results):
    if not results:
        return
    
    # Append to existing CSV
    with open(CSV_OUTPUT, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'venue', 'division', 'gender', 'rank', 'athlete_name', 
            'nationality', 'age_group', 'run_total_seconds', 'finish_total_seconds'
        ])
        writer.writerows(results)


def main():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(options=options)
    
    total_results = 0
    
    try:
        for venue_config in NA_VENUES:
            venue_results = scrape_venue(driver, venue_config)
            
            if venue_results:
                count = save_to_db(venue_results)
                save_to_csv(venue_results)
                total_results += count
                print(f"  Saved {count} records.")
            
    finally:
        driver.quit()
    
    print(f"\n{'='*50}")
    print(f"=== NA SCRAPING COMPLETE ===")
    print(f"Total new records: {total_results}")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()
