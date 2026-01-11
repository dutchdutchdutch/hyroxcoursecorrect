"""
Automated HYROX venue data scraper using Selenium.

This script:
1. Loads venue configuration from venues.json
2. For each venue, scrapes top 100 Men and top 100 Women results
3. Saves raw data to JSON
4. Processes and exports to CSV

Usage:
    python scrape_venues.py [--venues VENUE1,VENUE2] [--limit N]
    
Examples:
    python scrape_venues.py  # Scrape all venues
    python scrape_venues.py --venues anaheim,london --limit 50  # Scrape 2 venues, 50 results each
"""

import json
import time
import argparse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class HyroxScraper:
    """Scraper for HYROX results data."""
    
    BASE_URL = "https://results.hyrox.com/season-8/"
    
    def __init__(self, headless=True):
        """Initialize the scraper with Selenium WebDriver."""
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def scrape_venue(self, event_id, venue_name, gender, limit=100):
        """
        Scrape results for a specific venue and gender.
        
        Args:
            event_id: HYROX event ID
            venue_name: Human-readable venue name
            gender: 'M' or 'W'
            limit: Number of results to scrape (default 100)
            
        Returns:
            list: List of result dictionaries
        """
        print(f"  Scraping {venue_name} - {gender} ({limit} results)...")
        
        all_results = []
        results_per_page = 25  # HYROX shows 25 results per page
        pages_needed = (limit + results_per_page - 1) // results_per_page  # Ceiling division
        
        for page in range(1, pages_needed + 1):
            url = (
                f"{self.BASE_URL}?page={page}&event={event_id}&num_results={results_per_page}"
                f"&pid=list&ranking=time_finish_netto&search[sex]={gender}"
                "&search[age_class]=%&search[nation]=%"
            )
            
            try:
                self.driver.get(url)
                
                # Wait for results to load
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'li.list-group-item'))
                )
                
                # Give extra time for all results to render
                time.sleep(1)
                
                # Extract results using JavaScript
                results = self.driver.execute_script("""
                    const results = [];
                    const rows = document.querySelectorAll('li.list-group-item');
                    
                    rows.forEach(row => {
                        const nameLink = row.querySelector('a[href*="idp="]');
                        if (!nameLink) return;
                        
                        const rankElem = row.querySelector('.list-field.type-place.place-primary');
                        const rank = rankElem ? rankElem.innerText.trim() : null;
                        
                        const name = nameLink.innerText.trim();
                        
                        const natElem = row.querySelector('.nation__abbr');
                        const nationality = natElem ? natElem.innerText.trim() : null;
                        
                        const ageElem = row.querySelector('.list-field.type-age_class');
                        const ageGroup = ageElem ? ageElem.innerText.trim() : null;
                        
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
                """)
                
                if results:
                    all_results.extend(results)
                    if len(all_results) >= limit:
                        all_results = all_results[:limit]  # Trim to exact limit
                        break
                else:
                    # No results on this page, stop pagination
                    break
                
                # Be polite to the server between pages
                time.sleep(0.5)
                
            except TimeoutException:
                print(f"    ✗ Timeout loading page {page} for {venue_name} - {gender}")
                break
            except Exception as e:
                print(f"    ✗ Error scraping page {page} for {venue_name} - {gender}: {e}")
                break
        
        print(f"    ✓ Scraped {len(all_results)} results")
        return all_results
    
    def scrape_all_venues(self, venues_config, venue_filter=None, limit=100):
        """
        Scrape all venues from configuration.
        
        Args:
            venues_config: Dictionary of venue configurations
            venue_filter: Optional list of venue keys to scrape
            limit: Number of results per gender per venue
            
        Returns:
            list: Combined results from all venues
        """
        all_results = []
        
        for venue_key, venue_info in venues_config.items():
            # Skip if filtering and venue not in filter
            if venue_filter and venue_key not in venue_filter:
                continue
            
            venue_name = venue_info['name']
            event_id = venue_info['event_id']
            
            print(f"\n📍 {venue_name}")
            
            # Scrape Men's results
            men_results = self.scrape_venue(event_id, venue_name, 'M', limit)
            if men_results:
                all_results.append({
                    'venue': venue_name,
                    'gender': 'M',
                    'results': men_results
                })
            
            # Scrape Women's results
            women_results = self.scrape_venue(event_id, venue_name, 'W', limit)
            if women_results:
                all_results.append({
                    'venue': venue_name,
                    'gender': 'W',
                    'results': women_results
                })
            
            # Be polite to the server
            time.sleep(1)
        
        return all_results
    
    def close(self):
        """Close the WebDriver."""
        self.driver.quit()


def load_venues_config():
    """Load venue configuration from venues.json."""
    config_file = Path(__file__).parent / 'venues.json'
    
    with open(config_file, 'r') as f:
        data = json.load(f)
    
    # Return Season 8 venues
    return data['season_8_2025_2026']


def main():
    """Main scraping workflow."""
    parser = argparse.ArgumentParser(description='Scrape HYROX venue results')
    parser.add_argument('--venues', type=str, help='Comma-separated list of venue keys to scrape')
    parser.add_argument('--limit', type=int, default=100, help='Number of results per gender per venue')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode')
    
    args = parser.parse_args()
    
    # Load venue configuration
    venues_config = load_venues_config()
    
    # Parse venue filter
    venue_filter = None
    if args.venues:
        venue_filter = [v.strip() for v in args.venues.split(',')]
    
    # Initialize scraper
    scraper = HyroxScraper(headless=args.headless)
    
    try:
        print("🏃 HYROX Venue Data Scraper")
        print("=" * 50)
        
        # Scrape all venues
        results = scraper.scrape_all_venues(venues_config, venue_filter, args.limit)
        
        # Save raw data
        output_file = Path(__file__).parent.parent / '.tmp' / 'hyrox_scraped_raw.json'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Scraping complete!")
        print(f"   Total venues: {len(set(r['venue'] for r in results))}")
        print(f"   Total results: {sum(len(r['results']) for r in results)}")
        print(f"   Saved to: {output_file}")
        
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
