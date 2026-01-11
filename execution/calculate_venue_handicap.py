"""
Calculate venue handicap factors from scraped results data.

This script:
1. Loads processed venue results
2. Calculates median finish times by venue and gender
3. Computes handicap factors relative to a reference venue
4. Exports handicap factors to CSV

Methodology:
- Uses median finish time as the venue difficulty metric
- Reference venue (handicap = 1.000) is the venue with median finish time
- Handicap factor = venue_median / reference_median
- Higher handicap = slower venue (more difficult)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse


def calculate_venue_handicaps(df, reference_venue=None):
    """
    Calculate handicap factors for each venue.
    
    Args:
        df: DataFrame with venue results
        reference_venue: Optional venue name to use as reference (handicap = 1.0)
                        If None, uses the median venue
    
    Returns:
        DataFrame with venue handicaps
    """
    print("\n📊 Calculating Venue Handicaps")
    print("=" * 60)
    
    # Calculate median finish time by venue and gender
    venue_stats = df.groupby(['venue', 'gender']).agg({
        'finish_seconds': ['median', 'mean', 'std', 'count']
    }).reset_index()
    
    venue_stats.columns = ['venue', 'gender', 'median_time', 'mean_time', 'std_time', 'count']
    
    # Calculate overall median (combining M and W)
    overall_medians = df.groupby('venue')['finish_seconds'].median().reset_index()
    overall_medians.columns = ['venue', 'overall_median']
    
    # Merge overall medians
    venue_stats = venue_stats.merge(overall_medians, on='venue')
    
    # Determine reference venue
    if reference_venue is None:
        # Use venue with median overall_median as reference
        sorted_venues = overall_medians.sort_values('overall_median')
        mid_idx = len(sorted_venues) // 2
        reference_venue = sorted_venues.iloc[mid_idx]['venue']
        print(f"\n🎯 Reference Venue (auto-selected): {reference_venue}")
    else:
        print(f"\n🎯 Reference Venue (user-specified): {reference_venue}")
    
    reference_median = overall_medians[overall_medians['venue'] == reference_venue]['overall_median'].values[0]
    print(f"   Reference Median Time: {reference_median / 60:.2f} minutes")
    
    # Calculate handicap factors
    venue_stats['handicap_factor'] = venue_stats['overall_median'] / reference_median
    
    # Calculate difficulty percentage
    venue_stats['difficulty_pct'] = (venue_stats['handicap_factor'] - 1.0) * 100
    
    # Sort by handicap factor
    venue_stats = venue_stats.sort_values('handicap_factor')
    
    return venue_stats, reference_venue


def print_handicap_summary(venue_stats):
    """Print a summary of venue handicaps."""
    print("\n📋 Venue Handicap Summary")
    print("=" * 60)
    print(f"{'Venue':<25} {'Handicap':<10} {'Difficulty':<12} {'Median (min)':<12}")
    print("-" * 60)
    
    for _, row in venue_stats.iterrows():
        difficulty_str = f"{row['difficulty_pct']:+.1f}%"
        median_min = row['overall_median'] / 60
        
        print(f"{row['venue']:<25} {row['handicap_factor']:<10.3f} {difficulty_str:<12} {median_min:<12.1f}")
    
    print("\n💡 Interpretation:")
    print("   - Handicap = 1.000: Reference venue (baseline difficulty)")
    print("   - Handicap > 1.000: Slower/harder venue")
    print("   - Handicap < 1.000: Faster/easier venue")
    print("   - Difficulty %: Percentage slower (+) or faster (-) than reference")


def export_handicaps(venue_stats, output_file):
    """Export handicap factors to CSV."""
    # Create simplified export with just venue and handicap
    export_df = venue_stats[['venue', 'handicap_factor', 'difficulty_pct', 'overall_median']].drop_duplicates()
    export_df = export_df.sort_values('handicap_factor')
    
    export_df.to_csv(output_file, index=False)
    print(f"\n✅ Handicaps exported to: {output_file}")


def main():
    """Main handicap calculation workflow."""
    parser = argparse.ArgumentParser(description='Calculate HYROX venue handicaps')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file with venue results')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file for handicaps')
    parser.add_argument('--reference', type=str, help='Reference venue name (optional)')
    
    args = parser.parse_args()
    
    # Load data
    print(f"📂 Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    
    print(f"   Loaded {len(df)} results from {df['venue'].nunique()} venues")
    print(f"   Gender split: {df['gender'].value_counts().to_dict()}")
    
    # Calculate handicaps
    venue_stats, reference_venue = calculate_venue_handicaps(df, args.reference)
    
    # Print summary
    print_handicap_summary(venue_stats)
    
    # Export
    export_handicaps(venue_stats, args.output)
    
    print("\n✨ Handicap calculation complete!")


if __name__ == '__main__':
    main()
