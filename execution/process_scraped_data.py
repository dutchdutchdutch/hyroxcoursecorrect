"""
Process scraped HYROX venue data from browser subagent output.

This script:
1. Reads the raw JSON data from browser scraping
2. Flattens the nested structure
3. Parses finish times to seconds
4. Adds venue metadata
5. Exports to CSV for analysis
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime


def parse_time_to_seconds(time_str):
    """
    Parse HYROX finish time string to total seconds.
    
    Args:
        time_str: Time string in format HH:MM:SS or MM:SS
        
    Returns:
        int: Total seconds, or None if invalid
    """
    if not time_str or pd.isna(time_str):
        return None
        
    try:
        parts = time_str.strip().split(':')
        
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


def load_venue_metadata():
    """Load venue metadata from venues.json."""
    venues_file = Path(__file__).parent / 'venues.json'
    
    with open(venues_file, 'r') as f:
        data = json.load(f)
    
    # Flatten the nested structure
    venues = {}
    for season, season_venues in data.items():
        for key, venue_info in season_venues.items():
            venues[venue_info['name']] = {
                'event_id': venue_info['event_id'],
                'location': venue_info['location'],
                'region': venue_info['region']
            }
    
    return venues


def process_scraped_data(input_file, output_file):
    """
    Process scraped venue data and export to CSV.
    
    Args:
        input_file: Path to raw JSON file from browser scraping
        output_file: Path to output CSV file
    """
    print(f"Loading scraped data from {input_file}...")
    
    with open(input_file, 'r') as f:
        raw_data = json.load(f)
    
    # Load venue metadata
    venue_metadata = load_venue_metadata()
    
    # Flatten the data structure
    all_results = []
    
    for venue_data in raw_data:
        venue_name = venue_data['venue']
        gender = venue_data['gender']
        results = venue_data['results']
        
        # Get venue metadata
        metadata = venue_metadata.get(venue_name, {})
        
        for result in results:
            # Clean finish time (remove "Total\n" prefix if present)
            finish_time_raw = result.get('finish_time', '')
            if finish_time_raw.startswith('Total\n'):
                finish_time_clean = finish_time_raw.replace('Total\n', '').strip()
            else:
                finish_time_clean = finish_time_raw.strip()
            
            # Clean age group (remove "Age Group\n" prefix if present)
            age_group_raw = result.get('age_group', '')
            if age_group_raw.startswith('Age Group\n'):
                age_group_clean = age_group_raw.replace('Age Group\n', '').strip()
            else:
                age_group_clean = age_group_raw.strip()
            
            # Parse finish time
            finish_seconds = parse_time_to_seconds(finish_time_clean)
            
            if finish_seconds is None:
                print(f"Warning: Invalid time for {result.get('name')} at {venue_name}: {finish_time_clean}")
                continue
            
            all_results.append({
                'venue': venue_name,
                'event_id': metadata.get('event_id', ''),
                'location': metadata.get('location', ''),
                'region': metadata.get('region', ''),
                'gender': gender,
                'rank': result.get('rank'),
                'name': result.get('name'),
                'nationality': result.get('nationality'),
                'age_group': age_group_clean,
                'finish_time': finish_time_clean,
                'finish_seconds': finish_seconds
            })
    
    # Create DataFrame
    df = pd.DataFrame(all_results)
    
    # Sort by venue, gender, and rank
    df = df.sort_values(['venue', 'gender', 'rank'])
    
    # Export to CSV
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Processed {len(df)} results from {df['venue'].nunique()} venues")
    print(f"   Saved to: {output_file}")
    
    # Print summary statistics
    print("\n📊 Summary by Venue:")
    summary = df.groupby(['venue', 'gender']).size().unstack(fill_value=0)
    print(summary)
    
    print("\n📊 Summary by Region:")
    region_summary = df.groupby(['region', 'gender']).size().unstack(fill_value=0)
    print(region_summary)
    
    return df


if __name__ == '__main__':
    # File paths
    input_file = Path(__file__).parent.parent / '.tmp' / 'hyrox_scraped_raw.json'
    output_file = Path(__file__).parent.parent / 'data' / 'hyrox_9venues_100each.csv'
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Process the data
    df = process_scraped_data(input_file, output_file)
    
    print("\n✨ Data processing complete!")
