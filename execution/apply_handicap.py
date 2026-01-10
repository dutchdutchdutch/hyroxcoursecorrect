#!/usr/bin/env python3
"""
Apply Venue Handicap Factors

Applies handicap factors to athlete times for fair cross-venue comparison.

Usage:
    python apply_handicap.py --results .tmp/cleaned_results.csv --handicaps .tmp/venue_handicaps.csv
    python apply_handicap.py --sample-data  # Test with sample data
"""

import argparse
from pathlib import Path

import pandas as pd
import numpy as np


def apply_handicaps(results_df: pd.DataFrame, handicaps_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply venue handicap factors to athlete results.
    
    Args:
        results_df: Athlete results with finish times
        handicaps_df: Venue handicap factors
    
    Returns:
        Results with adjusted times and re-calculated rankings
    """
    print("Applying handicap factors...")
    
    # Merge handicaps with results
    df = results_df.merge(
        handicaps_df[['venue', 'handicap_factor']], 
        on='venue', 
        how='left'
    )
    
    # Check for missing handicaps
    missing_handicaps = df['handicap_factor'].isna().sum()
    if missing_handicaps > 0:
        print(f"⚠️  Warning: {missing_handicaps} results have no handicap factor")
        print("    These venues may not have met minimum sample size")
        # Fill with 1.0 (no adjustment)
        df['handicap_factor'].fillna(1.0, inplace=True)
    
    # Calculate adjusted time
    df['adjusted_time_seconds'] = df['finish_time_seconds'] / df['handicap_factor']
    
    # Re-calculate rankings based on adjusted times
    if 'division' in df.columns:
        # Rank within division
        df['adjusted_rank_overall'] = df.groupby('division')['adjusted_time_seconds'].rank(method='min')
    else:
        # Overall ranking
        df['adjusted_rank_overall'] = df['adjusted_time_seconds'].rank(method='min')
    
    print(f"  Applied handicaps to {len(df)} results")
    print(f"  Handicap range: {df['handicap_factor'].min():.3f} to {df['handicap_factor'].max():.3f}")
    
    return df


def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    if pd.isna(seconds):
        return ""
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours}:{minutes:02d}:{secs:02d}"


def compare_athletes(df: pd.DataFrame, athlete_ids: list = None) -> pd.DataFrame:
    """
    Compare specific athletes across venues.
    
    Args:
        df: Results with adjusted times
        athlete_ids: List of athlete IDs to compare (None = all repeat athletes)
    
    Returns:
        Comparison DataFrame
    """
    if athlete_ids is None:
        # Find athletes who competed at multiple venues
        athlete_venue_counts = df.groupby('athlete_id')['venue'].nunique()
        athlete_ids = athlete_venue_counts[athlete_venue_counts >= 2].index.tolist()
    
    comparison_data = []
    
    for athlete_id in athlete_ids:
        athlete_results = df[df['athlete_id'] == athlete_id].sort_values('event_date')
        
        if len(athlete_results) < 2:
            continue
        
        for idx, row in athlete_results.iterrows():
            comparison_data.append({
                'athlete_id': athlete_id,
                'athlete_name': row.get('athlete_name', ''),
                'venue': row['venue'],
                'event_date': row.get('event_date', ''),
                'raw_time': row['finish_time_seconds'],
                'raw_time_formatted': format_time(row['finish_time_seconds']),
                'handicap_factor': row['handicap_factor'],
                'adjusted_time': row['adjusted_time_seconds'],
                'adjusted_time_formatted': format_time(row['adjusted_time_seconds']),
                'time_saved': row['finish_time_seconds'] - row['adjusted_time_seconds'],
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    return comparison_df


def generate_sample_data() -> tuple:
    """Generate sample data for testing."""
    print("Generating sample data...")
    
    # Sample results
    results = pd.DataFrame({
        'athlete_id': ['athlete1', 'athlete1', 'athlete2', 'athlete2', 'athlete3'],
        'athlete_name': ['John Doe', 'John Doe', 'Jane Smith', 'Jane Smith', 'Bob Wilson'],
        'venue': ['New York City', 'Los Angeles', 'New York City', 'Chicago', 'Los Angeles'],
        'event_date': ['2024-03-15', '2024-06-20', '2024-03-15', '2024-05-10', '2024-06-20'],
        'division': ['Men Individual'] * 5,
        'finish_time_seconds': [4500, 4650, 4800, 4920, 4700],
    })
    
    # Sample handicaps
    handicaps = pd.DataFrame({
        'venue': ['New York City', 'Los Angeles', 'Chicago'],
        'handicap_factor': [0.98, 1.02, 1.05],  # NYC easiest, Chicago hardest
    })
    
    return results, handicaps


def main():
    parser = argparse.ArgumentParser(description='Apply venue handicap factors')
    parser.add_argument('--results', type=Path, default=Path('.tmp/cleaned_results.csv'))
    parser.add_argument('--handicaps', type=Path, default=Path('.tmp/venue_handicaps.csv'))
    parser.add_argument('--output', type=Path, default=Path('.tmp/adjusted_results.csv'))
    parser.add_argument('--sample-data', action='store_true', help='Use sample data for testing')
    
    args = parser.parse_args()
    
    # Load data
    if args.sample_data:
        results_df, handicaps_df = generate_sample_data()
    else:
        if not args.results.exists():
            print(f"❌ Results file not found: {args.results}")
            return
        
        if not args.handicaps.exists():
            print(f"❌ Handicaps file not found: {args.handicaps}")
            return
        
        results_df = pd.read_csv(args.results)
        handicaps_df = pd.read_csv(args.handicaps)
    
    print(f"Loaded {len(results_df)} results and {len(handicaps_df)} venue handicaps")
    
    # Apply handicaps
    adjusted_df = apply_handicaps(results_df, handicaps_df)
    
    # Save adjusted results
    args.output.parent.mkdir(parents=True, exist_ok=True)
    adjusted_df.to_csv(args.output, index=False)
    print(f"\n✓ Adjusted results saved to {args.output}")
    
    # Generate comparison for repeat athletes
    comparison_df = compare_athletes(adjusted_df)
    
    if len(comparison_df) > 0:
        comparison_file = args.output.parent / 'athlete_comparisons.csv'
        comparison_df.to_csv(comparison_file, index=False)
        print(f"✓ Athlete comparisons saved to {comparison_file}")
        
        # Print sample comparisons
        print("\n" + "="*80)
        print("SAMPLE ATHLETE COMPARISONS (First 10)")
        print("="*80)
        print(comparison_df.head(10).to_string(index=False))
        print("="*80)
    
    # Summary statistics
    print("\nADJUSTMENT SUMMARY")
    print("-"*80)
    print(f"Mean raw time: {format_time(adjusted_df['finish_time_seconds'].mean())}")
    print(f"Mean adjusted time: {format_time(adjusted_df['adjusted_time_seconds'].mean())}")
    print(f"Mean time difference: {(adjusted_df['finish_time_seconds'] - adjusted_df['adjusted_time_seconds']).mean():.1f} seconds")
    print(f"Largest adjustment: {(adjusted_df['finish_time_seconds'] - adjusted_df['adjusted_time_seconds']).abs().max():.1f} seconds")


if __name__ == '__main__':
    main()
