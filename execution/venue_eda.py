#!/usr/bin/env python3
"""
HYROX Venue Exploratory Data Analysis

Analyzes venue-specific performance patterns and generates visualizations.

Usage:
    python venue_eda.py --input .tmp/cleaned_results.csv --output-dir .tmp/eda_plots
"""

import argparse
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv


load_dotenv()

# Set plotting style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def calculate_venue_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate summary statistics for each venue.
    
    Returns:
        DataFrame with venue-level statistics
    """
    print("Calculating venue statistics...")
    
    stats = df.groupby('venue')['finish_time_seconds'].agg([
        ('count', 'count'),
        ('mean', 'mean'),
        ('median', 'median'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max'),
        ('p10', lambda x: x.quantile(0.10)),
        ('p25', lambda x: x.quantile(0.25)),
        ('p75', lambda x: x.quantile(0.75)),
        ('p90', lambda x: x.quantile(0.90)),
    ]).round(2)
    
    stats = stats.sort_values('mean')
    
    print(f"  Analyzed {len(stats)} venues")
    print(f"  Sample sizes range: {stats['count'].min():.0f} to {stats['count'].max():.0f}")
    
    return stats


def analyze_repeat_athletes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze athletes who competed at multiple venues.
    
    Returns:
        DataFrame with repeat athlete analysis
    """
    print("\nAnalyzing repeat athletes...")
    
    # Count venues per athlete
    athlete_venue_counts = df.groupby('athlete_id')['venue'].nunique()
    repeat_athletes = athlete_venue_counts[athlete_venue_counts >= 2]
    
    print(f"  Found {len(repeat_athletes)} athletes who competed at 2+ venues")
    
    if len(repeat_athletes) == 0:
        return pd.DataFrame()
    
    # For repeat athletes, calculate variance across venues
    repeat_data = []
    
    for athlete_id in repeat_athletes.index:
        athlete_results = df[df['athlete_id'] == athlete_id]
        
        repeat_data.append({
            'athlete_id': athlete_id,
            'num_venues': len(athlete_results['venue'].unique()),
            'mean_time': athlete_results['finish_time_seconds'].mean(),
            'std_time': athlete_results['finish_time_seconds'].std(),
            'min_time': athlete_results['finish_time_seconds'].min(),
            'max_time': athlete_results['finish_time_seconds'].max(),
            'time_range': athlete_results['finish_time_seconds'].max() - 
                         athlete_results['finish_time_seconds'].min(),
        })
    
    repeat_df = pd.DataFrame(repeat_data)
    
    print(f"  Mean time variance across venues: {repeat_df['std_time'].mean():.1f} seconds")
    print(f"  Mean time range (max-min): {repeat_df['time_range'].mean():.1f} seconds")
    
    return repeat_df


def plot_venue_distributions(df: pd.DataFrame, output_dir: Path, min_sample_size: int = 20):
    """Create box plot of finish times by venue."""
    print("\nGenerating venue distribution plot...")
    
    # Filter venues with sufficient sample size
    venue_counts = df['venue'].value_counts()
    valid_venues = venue_counts[venue_counts >= min_sample_size].index
    plot_df = df[df['venue'].isin(valid_venues)]
    
    # Sort venues by median time
    venue_order = plot_df.groupby('venue')['finish_time_seconds'].median().sort_values().index
    
    plt.figure(figsize=(14, 8))
    sns.boxplot(data=plot_df, x='venue', y='finish_time_seconds', order=venue_order)
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Venue')
    plt.ylabel('Finish Time (seconds)')
    plt.title(f'HYROX Finish Time Distribution by Venue (n≥{min_sample_size})')
    plt.tight_layout()
    
    output_file = output_dir / 'venue_time_distributions.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Saved: {output_file}")


def plot_venue_comparison_heatmap(stats: pd.DataFrame, output_dir: Path):
    """Create heatmap comparing venue statistics."""
    print("Generating venue comparison heatmap...")
    
    # Select key metrics for heatmap
    heatmap_data = stats[['mean', 'median', 'std', 'count']].T
    
    # Normalize for better visualization
    heatmap_normalized = (heatmap_data - heatmap_data.min(axis=1).values.reshape(-1, 1)) / \
                        (heatmap_data.max(axis=1) - heatmap_data.min(axis=1)).values.reshape(-1, 1)
    
    plt.figure(figsize=(16, 6))
    sns.heatmap(heatmap_normalized, annot=heatmap_data.round(0), fmt='g', 
                cmap='RdYlGn_r', cbar_kws={'label': 'Normalized Value'})
    plt.xlabel('Venue')
    plt.ylabel('Metric')
    plt.title('HYROX Venue Comparison Heatmap')
    plt.tight_layout()
    
    output_file = output_dir / 'venue_comparison_heatmap.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Saved: {output_file}")


def plot_sample_sizes(stats: pd.DataFrame, output_dir: Path):
    """Create bar chart of sample sizes per venue."""
    print("Generating sample size plot...")
    
    plt.figure(figsize=(14, 6))
    stats_sorted = stats.sort_values('count', ascending=False)
    plt.bar(range(len(stats_sorted)), stats_sorted['count'])
    plt.xticks(range(len(stats_sorted)), stats_sorted.index, rotation=45, ha='right')
    plt.xlabel('Venue')
    plt.ylabel('Number of Athletes')
    plt.title('Sample Size by Venue')
    plt.axhline(y=20, color='r', linestyle='--', label='Minimum threshold (20)')
    plt.legend()
    plt.tight_layout()
    
    output_file = output_dir / 'venue_sample_sizes.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Saved: {output_file}")


def plot_repeat_athlete_variance(df: pd.DataFrame, repeat_df: pd.DataFrame, output_dir: Path):
    """Plot variance in repeat athlete performance across venues."""
    print("Generating repeat athlete variance plot...")
    
    if len(repeat_df) == 0:
        print("  Skipped: No repeat athletes found")
        return
    
    # Get top 20 repeat athletes by number of venues
    top_athletes = repeat_df.nlargest(20, 'num_venues')
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Plot 1: Time range distribution
    axes[0].hist(repeat_df['time_range'], bins=30, edgecolor='black')
    axes[0].set_xlabel('Time Range (max - min, seconds)')
    axes[0].set_ylabel('Number of Athletes')
    axes[0].set_title('Distribution of Performance Variance\nAcross Venues (Repeat Athletes)')
    
    # Plot 2: Scatter of mean time vs std
    axes[1].scatter(repeat_df['mean_time'], repeat_df['std_time'], alpha=0.6)
    axes[1].set_xlabel('Mean Finish Time (seconds)')
    axes[1].set_ylabel('Std Dev Across Venues (seconds)')
    axes[1].set_title('Athlete Ability vs Venue Sensitivity')
    
    plt.tight_layout()
    
    output_file = output_dir / 'repeat_athlete_variance.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  Saved: {output_file}")


def generate_report(df: pd.DataFrame, stats: pd.DataFrame, repeat_df: pd.DataFrame, 
                   output_dir: Path):
    """Generate text summary report."""
    print("\nGenerating EDA report...")
    
    report_lines = [
        "="*60,
        "HYROX VENUE EXPLORATORY DATA ANALYSIS REPORT",
        "="*60,
        "",
        f"Total Records: {len(df):,}",
        f"Unique Athletes: {df['athlete_id'].nunique():,}",
        f"Unique Venues: {df['venue'].nunique()}",
        f"Date Range: {df['event_date'].min()} to {df['event_date'].max()}" if 'event_date' in df.columns else "",
        "",
        "VENUE STATISTICS",
        "-"*60,
        "",
        stats.to_string(),
        "",
        "REPEAT ATHLETE ANALYSIS",
        "-"*60,
        f"Athletes at 2+ venues: {len(repeat_df)}",
    ]
    
    if len(repeat_df) > 0:
        report_lines.extend([
            f"Mean performance variance: {repeat_df['std_time'].mean():.1f} seconds",
            f"Mean time range (max-min): {repeat_df['time_range'].mean():.1f} seconds",
            f"Max venues competed: {repeat_df['num_venues'].max()}",
        ])
    
    report_lines.extend([
        "",
        "KEY FINDINGS",
        "-"*60,
        f"Fastest venue (mean): {stats.index[0]} ({stats['mean'].iloc[0]:.0f}s)",
        f"Slowest venue (mean): {stats.index[-1]} ({stats['mean'].iloc[-1]:.0f}s)",
        f"Venue effect range: {stats['mean'].iloc[-1] - stats['mean'].iloc[0]:.0f}s " +
        f"({(stats['mean'].iloc[-1] / stats['mean'].iloc[0] - 1) * 100:.1f}% difference)",
        "",
        "="*60,
    ])
    
    report_text = "\n".join(report_lines)
    
    output_file = output_dir / 'eda_report.txt'
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    print(f"  Saved: {output_file}")
    print("\n" + report_text)


def main():
    parser = argparse.ArgumentParser(description='HYROX venue EDA')
    parser.add_argument('--input', type=Path, default=Path('.tmp/cleaned_results.csv'),
                       help='Cleaned results CSV')
    parser.add_argument('--output-dir', type=Path, default=Path('.tmp/eda_plots'),
                       help='Output directory for plots')
    parser.add_argument('--min-sample-size', type=int, default=20,
                       help='Minimum athletes per venue for analysis')
    
    args = parser.parse_args()
    
    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    if not args.input.exists():
        print(f"❌ Input file not found: {args.input}")
        print("   Run clean_hyrox_data.py first to generate cleaned data")
        return
    
    print(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    print(f"  Loaded {len(df)} records")
    
    # Calculate statistics
    stats = calculate_venue_stats(df)
    stats.to_csv(args.output_dir.parent / 'venue_summary_stats.csv')
    
    # Analyze repeat athletes
    repeat_df = analyze_repeat_athletes(df)
    if len(repeat_df) > 0:
        repeat_df.to_csv(args.output_dir.parent / 'repeat_athlete_analysis.csv', index=False)
    
    # Generate visualizations
    plot_venue_distributions(df, args.output_dir, args.min_sample_size)
    plot_venue_comparison_heatmap(stats, args.output_dir)
    plot_sample_sizes(stats, args.output_dir)
    plot_repeat_athlete_variance(df, repeat_df, args.output_dir)
    
    # Generate report
    generate_report(df, stats, repeat_df, args.output_dir)
    
    print("\n✓ EDA complete!")


if __name__ == '__main__':
    main()
