"""
Calculate venue course correction factors from scraped results data.

This script:
1. Loads processed venue results
2. Calculates median finish times by venue and gender
3. Computes course correction factors relative to median venue (separately for M/W)
4. Exports correction factors to JSON

Methodology:
- Uses median finish time as the venue difficulty metric
- Reference venue (correction = 0.0) is the MEDIAN venue by count (middle venue when sorted)
- Course correction = venue_gender_median - reference_gender_median (in seconds)
- Positive correction = slower venue (adds time)
- Negative correction = faster venue (subtracts time)
- Separate corrections calculated for men and women
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import argparse


def calculate_course_corrections(df, reference_venue=None):
    """
    Calculate course correction factors using median venue baseline with gender adjustments.
    
    Methodology:
    1. Calculate overall median for each venue (combining M/W)
    2. Sort venues by overall median and select MIDDLE venue by count as baseline
    3. Calculate time-based corrections (in seconds) relative to baseline
    4. Apply gender-specific corrections
    
    Result: Faster venues have negative corrections, Slower venues have positive corrections
    
    Args:
        df: DataFrame with venue results
        reference_venue: Optional venue name to use as reference (correction = 0.0)
                        If None, uses the median venue by count
    
    Returns:
        Tuple of (men_corrections dict, women_corrections dict, reference_venue, stats_df)
    """
    print("\n📊 Calculating Course Correction Factors")
    print("=" * 80)
    print("Methodology: Median venue baseline (0.0) with gender-specific time corrections")
    
    # Calculate median finish time by venue and gender
    venue_stats = df.groupby(['venue', 'gender']).agg({
        'finish_seconds': ['median', 'mean', 'std', 'count']
    }).reset_index()
    
    venue_stats.columns = ['venue', 'gender', 'median_time', 'mean_time', 'std_time', 'count']
    
    # Calculate overall median (combining M and W) for each venue
    overall_medians = df.groupby('venue')['finish_seconds'].median().reset_index()
    overall_medians.columns = ['venue', 'overall_median']
    
    # Determine reference venue (MEDIAN venue by count)
    if reference_venue is None:
        # Sort venues by overall median and select middle venue by count
        overall_medians_sorted = overall_medians.sort_values('overall_median')
        median_idx = len(overall_medians_sorted) // 2
        reference_venue = overall_medians_sorted.iloc[median_idx]['venue']
        print(f"\n🎯 Reference Venue (median by count): {reference_venue}")
        print(f"   Position: {median_idx + 1} of {len(overall_medians_sorted)} venues")
    else:
        print(f"\n🎯 Reference Venue (user-specified): {reference_venue}")
    
    # Get baseline gender-specific medians
    baseline_men_median = venue_stats[(venue_stats['venue'] == reference_venue) & 
                                      (venue_stats['gender'] == 'M')]['median_time'].values[0]
    baseline_women_median = venue_stats[(venue_stats['venue'] == reference_venue) & 
                                        (venue_stats['gender'] == 'W')]['median_time'].values[0]
    
    print(f"   Baseline Men's Median: {baseline_men_median / 60:.2f} minutes")
    print(f"   Baseline Women's Median: {baseline_women_median / 60:.2f} minutes")
    
    # Calculate course corrections for each venue
    men_corrections = {}
    women_corrections = {}
    
    for venue in df['venue'].unique():
        # Get gender-specific medians
        men_median = venue_stats[(venue_stats['venue'] == venue) & 
                                 (venue_stats['gender'] == 'M')]['median_time'].values
        women_median = venue_stats[(venue_stats['venue'] == venue) & 
                                   (venue_stats['gender'] == 'W')]['median_time'].values
        
        if len(men_median) > 0 and len(women_median) > 0:
            # Calculate time-based corrections (in seconds)
            # Positive = slower course, Negative = faster course
            men_corrections[venue] = float(men_median[0] - baseline_men_median)
            women_corrections[venue] = float(women_median[0] - baseline_women_median)
    
    # Add corrections to stats dataframe
    venue_stats['correction_seconds'] = venue_stats.apply(
        lambda row: men_corrections.get(row['venue']) if row['gender'] == 'M' 
                   else women_corrections.get(row['venue']), axis=1
    )
    
    venue_stats['correction_minutes'] = venue_stats['correction_seconds'] / 60
    
    print(f"\n✅ Calculated corrections for {len(men_corrections)} venues")
    print(f"   Reference venue correction: {men_corrections[reference_venue]:.1f}s (Men), {women_corrections[reference_venue]:.1f}s (Women)")
    
    return men_corrections, women_corrections, reference_venue, venue_stats


def print_correction_summary(venue_stats, men_corrections, women_corrections):
    """Print a summary of venue course corrections by gender."""
    print("\n📋 Gender-Specific Course Correction Summary")
    print("=" * 80)
    print(f"{'Venue':<25} {'Men Correction':<18} {'Women Correction':<20} {'Difference':<12}")
    print("-" * 80)
    
    # Sort by men's correction (negative to positive)
    sorted_venues = sorted(men_corrections.keys(), key=lambda v: men_corrections[v])
    
    for venue in sorted_venues:
        men_c = men_corrections.get(venue, 0)
        women_c = women_corrections.get(venue, 0)
        diff = abs(men_c - women_c)
        
        # Format as time (minutes:seconds)
        men_str = f"{int(men_c // 60):+3d}:{abs(int(men_c % 60)):02d}"
        women_str = f"{int(women_c // 60):+3d}:{abs(int(women_c % 60)):02d}"
        diff_str = f"{int(diff // 60):3d}:{int(diff % 60):02d}"
        
        print(f"{venue:<25} {men_str:<18} {women_str:<20} {diff_str:<12}")
    
    # Calculate average difference
    differences = [abs(men_corrections[v] - women_corrections[v]) for v in men_corrections.keys()]
    avg_diff = sum(differences) / len(differences)
    max_diff = max(differences)
    
    print("\n📊 Gender Difference Analysis:")
    print(f"   Average difference: {int(avg_diff // 60)}:{int(avg_diff % 60):02d} ({avg_diff:.1f} seconds)")
    print(f"   Maximum difference: {int(max_diff // 60)}:{int(max_diff % 60):02d} ({max_diff:.1f} seconds)")
    
    print("\n💡 Interpretation:")
    print("   - Correction = 0:00: Reference venue (median difficulty)")
    print("   - Correction > 0:00: Slower course (adds time)")
    print("   - Correction < 0:00: Faster course (subtracts time)")
    print("   - Separate corrections account for gender-specific venue difficulty")


def export_corrections_json(men_corrections, women_corrections, output_file):
    """Export course correction factors to JSON."""
    corrections_data = {
        "men": men_corrections,
        "women": women_corrections
    }
    
    output_path = Path(output_file)
    with open(output_path, 'w') as f:
        json.dump(corrections_data, f, indent=2)
    
    print(f"\n✅ Gender-specific course corrections exported to: {output_file}")


def export_corrections_csv(venue_stats, output_file):
    """Export detailed stats to CSV for reference."""
    csv_file = output_file.replace('.json', '_detailed.csv')
    venue_stats.to_csv(csv_file, index=False)
    print(f"✅ Detailed stats exported to: {csv_file}")


def main():
    """Main course correction calculation workflow."""
    parser = argparse.ArgumentParser(description='Calculate HYROX venue course corrections by gender')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file with venue results')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file for course corrections')
    parser.add_argument('--reference', type=str, help='Reference venue name (optional)')
    
    args = parser.parse_args()
    
    # Load data
    print(f"📂 Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    
    print(f"   Loaded {len(df)} results from {df['venue'].nunique()} venues")
    print(f"   Gender split: {df['gender'].value_counts().to_dict()}")
    
    # Calculate gender-specific course corrections
    men_corrections, women_corrections, reference_venue, venue_stats = \
        calculate_course_corrections(df, args.reference)
    
    # Print summary
    print_correction_summary(venue_stats, men_corrections, women_corrections)
    
    # Export to JSON
    export_corrections_json(men_corrections, women_corrections, args.output)
    
    # Export detailed CSV
    export_corrections_csv(venue_stats, args.output)
    
    print("\n✨ Gender-specific course correction calculation complete!")


if __name__ == '__main__':
    main()

