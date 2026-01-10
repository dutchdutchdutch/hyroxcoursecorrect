#!/usr/bin/env python3
"""
HYROX Data Cleaning and Validation

Cleans raw HYROX results data, handles missing values, standardizes formats,
and removes outliers.

Usage:
    python clean_hyrox_data.py --input .tmp/raw_results_combined.csv --output .tmp/cleaned_results.csv
    python clean_hyrox_data.py --test-mode  # Run with test data
"""

import argparse
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np
from dotenv import load_dotenv


load_dotenv()


# Venue name standardization mapping
VENUE_MAPPING = {
    'NYC': 'New York City',
    'Javits Center': 'New York City',
    'Jacob K. Javits Convention Center': 'New York City',
    'LA': 'Los Angeles',
    'Los Angeles Convention Center': 'Los Angeles',
    'Chicago McCormick Place': 'Chicago',
    'McCormick Place': 'Chicago',
    'ExCeL London': 'London',
    'London ExCeL': 'London',
    # Add more mappings as discovered
}


def parse_time_to_seconds(time_str: str) -> Optional[float]:
    """
    Parse time string to seconds.
    
    Handles formats:
    - HH:MM:SS (e.g., "1:23:45")
    - MM:SS (e.g., "45:30")
    - Seconds (e.g., "3825")
    
    Args:
        time_str: Time string to parse
    
    Returns:
        Time in seconds, or None if invalid
    """
    if pd.isna(time_str):
        return None
    
    time_str = str(time_str).strip()
    
    # Already in seconds
    if time_str.isdigit():
        return float(time_str)
    
    # HH:MM:SS or MM:SS format
    parts = time_str.split(':')
    
    try:
        if len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
        else:
            return None
    except ValueError:
        return None


def standardize_venue_name(venue: str) -> str:
    """Standardize venue names using mapping dictionary."""
    if pd.isna(venue):
        return 'Unknown'
    
    venue = str(venue).strip()
    return VENUE_MAPPING.get(venue, venue)


def generate_athlete_id(row: pd.Series) -> str:
    """
    Generate unique athlete ID from name and other identifiers.
    
    IMPORTANT: Only creates an ID if we have a unique identifier (bib number or DOB).
    Name-only matches are NOT considered the same athlete to avoid false positives.
    """
    name = str(row.get('athlete_name', '')).strip().lower()
    name = re.sub(r'[^a-z0-9]', '', name)  # Remove special chars
    
    # Require DOB or bib number for unique identification
    dob = row.get('dob', '')
    bib = row.get('bib_number', '')
    
    if dob and not pd.isna(dob):
        return f"{name}_{dob}"
    elif bib and not pd.isna(bib):
        return f"{name}_{bib}"
    else:
        # No unique identifier - create event-specific ID to prevent false matches
        # This ensures athletes are NOT treated as the same person across events
        event = str(row.get('event_name', '')).strip().lower()
        event = re.sub(r'[^a-z0-9]', '', event)
        return f"{name}_{event}_{row.name}"  # row.name is the index


def remove_outliers(df: pd.DataFrame, column: str, n_std: float = 3.0) -> pd.DataFrame:
    """
    Remove outliers beyond n standard deviations from mean.
    
    Args:
        df: DataFrame
        column: Column to check for outliers
        n_std: Number of standard deviations threshold
    
    Returns:
        DataFrame with outliers removed
    """
    mean = df[column].mean()
    std = df[column].std()
    
    lower_bound = mean - n_std * std
    upper_bound = mean + n_std * std
    
    before_count = len(df)
    df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
    after_count = len(df)
    
    removed = before_count - after_count
    if removed > 0:
        print(f"  Removed {removed} outliers from {column} (>{n_std}σ)")
    
    return df


def clean_data(input_file: Path, output_file: Path, test_mode: bool = False) -> None:
    """
    Main data cleaning pipeline.
    
    Args:
        input_file: Path to raw CSV
        output_file: Path to save cleaned CSV
        test_mode: If True, use test data instead of input file
    """
    print("Starting data cleaning...")
    
    if test_mode:
        print("⚠️  Running in test mode with sample data")
        # Create test data
        df = pd.DataFrame({
            'athlete_name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'event_name': ['HYROX NYC 2024', 'HYROX LA 2024', 'HYROX NYC 2024'],
            'event_date': ['2024-03-15', '2024-04-20', '2024-03-15'],
            'venue': ['NYC', 'Los Angeles', 'Javits Center'],
            'division': ['Men Individual', 'Women Individual', 'Men Individual'],
            'finish_time': ['1:15:30', '1:22:45', '1:18:00'],
            'run_time': ['45:30', '48:20', '46:15'],
            'workout_time': ['25:00', '28:30', '26:45'],
            'roxzone_time': ['5:00', '5:55', '5:00'],
        })
    else:
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            return
        
        df = pd.read_csv(input_file)
    
    print(f"  Loaded {len(df)} raw records")
    
    # 1. Parse time columns
    print("\n1. Parsing time columns...")
    time_columns = ['finish_time', 'run_time', 'workout_time', 'roxzone_time']
    
    for col in time_columns:
        if col in df.columns:
            df[f'{col}_seconds'] = df[col].apply(parse_time_to_seconds)
    
    # 2. Standardize venue names
    print("2. Standardizing venue names...")
    if 'event_name' in df.columns:
        # Use event_name as venue
        df['venue'] = df['event_name'].apply(standardize_venue_name)
        print(f"  Found {df['venue'].nunique()} unique venues")
    elif 'venue' in df.columns:
        df['venue'] = df['venue'].apply(standardize_venue_name)
        print(f"  Found {df['venue'].nunique()} unique venues")
    else:
        print("  ⚠️  No venue or event_name column found")
    
    # 3. Generate athlete IDs
    print("3. Generating athlete IDs...")
    df['athlete_id'] = df.apply(generate_athlete_id, axis=1)
    
    # 4. Handle missing values
    print("4. Handling missing values...")
    required_columns = ['athlete_name', 'venue', 'finish_time_seconds']
    
    before = len(df)
    df = df.dropna(subset=[col for col in required_columns if col in df.columns])
    after = len(df)
    
    if before > after:
        print(f"  Removed {before - after} records with missing required fields")
    
    # 5. Remove DNF/DNS entries
    print("5. Filtering DNF/DNS entries...")
    if 'finish_time_seconds' in df.columns:
        before = len(df)
        df = df[df['finish_time_seconds'] > 0]
        after = len(df)
        
        if before > after:
            print(f"  Removed {before - after} DNF/DNS entries")
    
    # 6. Remove outliers
    print("6. Removing outliers...")
    if 'finish_time_seconds' in df.columns:
        df = remove_outliers(df, 'finish_time_seconds', n_std=3.0)
    
    # 7. Remove duplicates
    print("7. Removing duplicates...")
    duplicate_cols = ['athlete_id', 'event_name']
    before = len(df)
    df = df.drop_duplicates(subset=[col for col in duplicate_cols if col in df.columns])
    after = len(df)
    
    if before > after:
        print(f"  Removed {before - after} duplicate athlete-event combinations")
    
    # 8. Sort and reset index
    if 'event_date' in df.columns and 'finish_time_seconds' in df.columns:
        df = df.sort_values(['event_date', 'finish_time_seconds'])
    df = df.reset_index(drop=True)
    
    # Save cleaned data
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Cleaning complete!")
    print(f"  Final record count: {len(df)}")
    print(f"  Unique athletes: {df['athlete_id'].nunique()}")
    print(f"  Unique venues: {df['venue'].nunique()}")
    print(f"  Output: {output_file}")
    
    # Data quality report
    print("\nData Quality Summary:")
    print(f"  Completeness (finish_time): {(~df['finish_time_seconds'].isna()).mean():.1%}")
    if 'run_time_seconds' in df.columns:
        print(f"  Completeness (run_time): {(~df['run_time_seconds'].isna()).mean():.1%}")
    if 'roxzone_time_seconds' in df.columns:
        print(f"  Completeness (roxzone_time): {(~df['roxzone_time_seconds'].isna()).mean():.1%}")


def main():
    parser = argparse.ArgumentParser(description='Clean HYROX results data')
    parser.add_argument('--input', type=Path, default=Path('.tmp/raw_results_combined.csv'),
                       help='Input CSV file')
    parser.add_argument('--output', type=Path, default=Path('.tmp/cleaned_results.csv'),
                       help='Output CSV file')
    parser.add_argument('--test-mode', action='store_true',
                       help='Run with test data')
    
    args = parser.parse_args()
    
    clean_data(args.input, args.output, test_mode=args.test_mode)


if __name__ == '__main__':
    main()
