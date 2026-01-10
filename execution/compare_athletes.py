#!/usr/bin/env python3
"""
Compare Athletes Across Venues

Tool to compare specific athletes' performances across different venues
using handicap-adjusted times.

Usage:
    python compare_athletes.py --athlete "John Doe"
    python compare_athletes.py --athlete-id athlete123
"""

import argparse
from pathlib import Path

import pandas as pd


def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    if pd.isna(seconds):
        return ""
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours}:{minutes:02d}:{secs:02d}"


def compare_athlete(df: pd.DataFrame, athlete_name: str = None, 
                   athlete_id: str = None) -> pd.DataFrame:
    """
    Compare a specific athlete's performances across venues.
    
    Args:
        df: Results with adjusted times
        athlete_name: Athlete name to search for
        athlete_id: Athlete ID to search for
    
    Returns:
        Comparison DataFrame
    """
    if athlete_id:
        athlete_results = df[df['athlete_id'] == athlete_id]
    elif athlete_name:
        # Case-insensitive partial match
        athlete_results = df[df['athlete_name'].str.contains(athlete_name, case=False, na=False)]
    else:
        print("❌ Must provide either --athlete or --athlete-id")
        return pd.DataFrame()
    
    if len(athlete_results) == 0:
        print(f"❌ No results found for athlete: {athlete_name or athlete_id}")
        return pd.DataFrame()
    
    # Sort by date
    if 'event_date' in athlete_results.columns:
        athlete_results = athlete_results.sort_values('event_date')
    
    # Create comparison table
    comparison = athlete_results[[
        'athlete_name', 'venue', 'event_date', 'event_name',
        'finish_time_seconds', 'handicap_factor', 'adjusted_time_seconds'
    ]].copy()
    
    # Add formatted times
    comparison['raw_time'] = comparison['finish_time_seconds'].apply(format_time)
    comparison['adjusted_time'] = comparison['adjusted_time_seconds'].apply(format_time)
    
    # Calculate time saved/lost due to venue
    comparison['venue_effect_seconds'] = comparison['finish_time_seconds'] - comparison['adjusted_time_seconds']
    comparison['venue_effect_formatted'] = comparison['venue_effect_seconds'].apply(
        lambda x: f"+{format_time(abs(x))}" if x > 0 else f"-{format_time(abs(x))}"
    )
    
    # Calculate improvement from best adjusted time
    best_adjusted = comparison['adjusted_time_seconds'].min()
    comparison['vs_best_seconds'] = comparison['adjusted_time_seconds'] - best_adjusted
    comparison['vs_best'] = comparison['vs_best_seconds'].apply(
        lambda x: f"+{format_time(x)}" if x > 0 else "BEST"
    )
    
    return comparison


def find_top_improvers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Find athletes with biggest improvements (adjusted time basis).
    
    Args:
        df: Results with adjusted times
        n: Number of top improvers to return
    
    Returns:
        DataFrame of top improvers
    """
    # Find athletes with 2+ results
    athlete_counts = df.groupby('athlete_id').size()
    repeat_athletes = athlete_counts[athlete_counts >= 2].index
    
    improvements = []
    
    for athlete_id in repeat_athletes:
        athlete_data = df[df['athlete_id'] == athlete_id].sort_values('event_date')
        
        if len(athlete_data) < 2:
            continue
        
        first_time = athlete_data.iloc[0]['adjusted_time_seconds']
        best_time = athlete_data['adjusted_time_seconds'].min()
        improvement = first_time - best_time
        
        improvements.append({
            'athlete_id': athlete_id,
            'athlete_name': athlete_data.iloc[0]['athlete_name'],
            'first_time': first_time,
            'best_time': best_time,
            'improvement_seconds': improvement,
            'improvement_pct': (improvement / first_time) * 100,
            'num_events': len(athlete_data),
        })
    
    improvers_df = pd.DataFrame(improvements)
    improvers_df = improvers_df.sort_values('improvement_seconds', ascending=False).head(n)
    
    return improvers_df


def main():
    parser = argparse.ArgumentParser(description='Compare athlete performances')
    parser.add_argument('--athlete', type=str, help='Athlete name to search for')
    parser.add_argument('--athlete-id', type=str, help='Athlete ID')
    parser.add_argument('--top-improvers', type=int, help='Show top N improvers')
    parser.add_argument('--input', type=Path, default=Path('.tmp/adjusted_results.csv'))
    
    args = parser.parse_args()
    
    # Load data
    if not args.input.exists():
        print(f"❌ Adjusted results not found: {args.input}")
        print("   Run apply_handicap.py first")
        return
    
    df = pd.read_csv(args.input)
    print(f"Loaded {len(df)} adjusted results")
    
    if args.top_improvers:
        # Show top improvers
        improvers = find_top_improvers(df, args.top_improvers)
        
        print("\n" + "="*80)
        print(f"TOP {args.top_improvers} IMPROVERS (Adjusted Time Basis)")
        print("="*80)
        print(improvers.to_string(index=False))
        print("="*80)
        
    elif args.athlete or args.athlete_id:
        # Compare specific athlete
        comparison = compare_athlete(df, args.athlete, args.athlete_id)
        
        if len(comparison) > 0:
            print("\n" + "="*80)
            print(f"ATHLETE COMPARISON: {comparison.iloc[0]['athlete_name']}")
            print("="*80)
            
            # Select columns to display
            display_cols = [
                'venue', 'event_date', 'raw_time', 'handicap_factor',
                'adjusted_time', 'venue_effect_formatted', 'vs_best'
            ]
            
            print(comparison[display_cols].to_string(index=False))
            print("="*80)
            
            # Summary
            print(f"\nBest Adjusted Time: {format_time(comparison['adjusted_time_seconds'].min())}")
            print(f"Worst Adjusted Time: {format_time(comparison['adjusted_time_seconds'].max())}")
            print(f"Average Adjusted Time: {format_time(comparison['adjusted_time_seconds'].mean())}")
            print(f"Total Events: {len(comparison)}")
            print(f"Venues Competed: {comparison['venue'].nunique()}")
    
    else:
        print("❌ Must provide --athlete, --athlete-id, or --top-improvers")
        parser.print_help()


if __name__ == '__main__':
    main()
