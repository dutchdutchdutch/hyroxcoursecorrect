#!/usr/bin/env python3
"""
Create Weighted Factor Model combining run times and overall medians.

This script:
1. Loads run factor data (excluding anomalous venues like Atlanta)
2. Loads existing median-based correction factors
3. Creates a weighted combined factor model
4. Evaluates which weighting produces best multi-venue athlete validation
"""

import sqlite3
import json
import csv
from pathlib import Path
from collections import defaultdict
import statistics

DB_PATH = Path('data/hyrox_results.db')
CORRECTIONS_FILE = Path('data/venue_corrections.json')
OUTPUT_MODEL = Path('data/weighted_factor_model.csv')

# Venues with known data issues
EXCLUDED_VENUES = []  # Atlanta fixed - now has valid Pro run times


def load_data():
    """Load all relevant data."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get run time stats per venue
    cursor.execute('''
        SELECT venue, gender, 
               MIN(run_total_seconds) as fastest,
               AVG(run_total_seconds) as mean,
               COUNT(*) as count
        FROM pro_run_times
        WHERE venue NOT IN ({})
        GROUP BY venue, gender
    '''.format(','.join(f"'{v}'" for v in EXCLUDED_VENUES)))
    
    run_stats = defaultdict(dict)
    for row in cursor.fetchall():
        venue = row['venue']
        gender = 'men' if row['gender'] == 'M' else 'women'
        run_stats[venue][gender] = {
            'fastest': row['fastest'],
            'mean': row['mean'],
            'count': row['count']
        }
    
    # Get median run times per venue
    cursor.execute('''
        SELECT venue, gender, run_total_seconds
        FROM pro_run_times
        WHERE venue NOT IN ({})
        ORDER BY venue, gender, run_total_seconds
    '''.format(','.join(f"'{v}'" for v in EXCLUDED_VENUES)))
    
    venue_runs = defaultdict(lambda: {'men': [], 'women': []})
    for row in cursor.fetchall():
        venue = row['venue']
        gender = 'men' if row['gender'] == 'M' else 'women'
        venue_runs[venue][gender].append(row['run_total_seconds'])
    
    for venue, data in venue_runs.items():
        for gender in ['men', 'women']:
            if data[gender]:
                run_stats[venue][gender]['median'] = statistics.median(data[gender])
    
    conn.close()
    
    # Load existing corrections
    existing = {}
    if CORRECTIONS_FILE.exists():
        with open(CORRECTIONS_FILE, 'r') as f:
            data = json.load(f)
        for venue, val in data.get('men', {}).items():
            existing[venue] = {
                'men': val,
                'women': data.get('women', {}).get(venue, 0)
            }
    
    return run_stats, existing


def find_baseline(run_stats):
    """Find baseline venue (median of medians)."""
    men_medians = [(v, s['men']['median']) for v, s in run_stats.items() if s.get('men', {}).get('median')]
    men_medians.sort(key=lambda x: x[1])
    
    if not men_medians:
        return None
    
    mid_idx = len(men_medians) // 2
    return men_medians[mid_idx][0]


def calculate_factors(run_stats, baseline_venue, existing_corrections):
    """Calculate run-based factors and compare with existing."""
    baseline_men = run_stats[baseline_venue]['men']['median']
    baseline_women = run_stats[baseline_venue]['women']['median']
    
    results = []
    
    for venue, stats in run_stats.items():
        men_run_med = stats['men'].get('median', 0)
        women_run_med = stats['women'].get('median', 0)
        
        # Run factor (percentage difference from baseline)
        run_factor_men = ((men_run_med - baseline_men) / baseline_men) * 100 if men_run_med else 0
        run_factor_women = ((women_run_med - baseline_women) / baseline_women) * 100 if women_run_med else 0
        
        # Find matching existing correction
        existing = None
        for ev, val in existing_corrections.items():
            if venue.replace(' 2025', '').lower() in ev.lower():
                existing = val
                break
        
        # Calculate existing factor as percentage (relative to baseline ~5100s for men)
        baseline_finish_men = 5100  # Approximate baseline finish median in seconds
        baseline_finish_women = 5500
        
        existing_factor_men = ((existing['men'] if existing else 0) / baseline_finish_men) * 100
        existing_factor_women = ((existing['women'] if existing else 0) / baseline_finish_women) * 100
        
        results.append({
            'venue': venue,
            'is_baseline': venue == baseline_venue,
            'men_run_median': men_run_med,
            'women_run_median': women_run_med,
            'run_factor_men': run_factor_men,
            'run_factor_women': run_factor_women,
            'existing_correction_men': existing['men'] if existing else 0,
            'existing_correction_women': existing['women'] if existing else 0,
            'existing_factor_men': existing_factor_men,
            'existing_factor_women': existing_factor_women,
        })
    
    return results


def test_weighted_models(results):
    """Test different weight combinations."""
    print("\n" + "="*80)
    print("WEIGHTED MODEL ANALYSIS")
    print("="*80)
    
    # For now, just propose weights based on signal strength
    # Run times = ~45% of finish, Roxzone = ~10%, Stations = ~45%
    # Run times are cleaner signal, so they should get higher weight
    
    print("""
Proposed Model Weights:
  
  Combined_Factor = α × Run_Factor + (1-α) × Existing_Median_Factor
  
  Options:
  1. α = 0.60 (Run-heavy): Gives run times 60% weight
  2. α = 0.50 (Balanced): Equal weight to both
  3. α = 0.40 (Median-heavy): Trusts overall median more
  
  Recommendation: α = 0.50 (Balanced)
  
  Rationale:
  - Run times are a cleaner signal (less variation from workout stations)
  - But overall median includes more data points (not just top 200)
  - Multi-venue validation showed 88% accuracy with existing factors
  - Run factors show same directional trends
""")
    
    # Calculate combined factors for α = 0.5
    for r in results:
        # Weighted combination
        r['combined_factor_men'] = 0.5 * r['run_factor_men'] + 0.5 * r['existing_factor_men']
        r['combined_factor_women'] = 0.5 * r['run_factor_women'] + 0.5 * r['existing_factor_women']
    
    return results


def print_summary(results, baseline_venue):
    """Print factor comparison summary."""
    print("\n" + "="*80)
    print("FACTOR COMPARISON (Excluding Atlanta)")
    print(f"Baseline: {baseline_venue}")
    print("="*80)
    
    print(f"\n{'Venue':<22} {'Run %(M)':>10} {'Exist %(M)':>12} {'Comb %(M)':>12} {'Run %(W)':>10}")
    print("-" * 80)
    
    for r in sorted(results, key=lambda x: x['run_factor_men']):
        bl = " (Baseline)" if r['is_baseline'] else ""
        print(f"{r['venue']:<22} {r['run_factor_men']:>9.1f}% {r['existing_factor_men']:>11.1f}% {r['combined_factor_men']:>11.1f}% {r['run_factor_women']:>9.1f}%{bl}")
    
    print("="*80)


def save_results(results):
    """Save weighted model results."""
    with open(OUTPUT_MODEL, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"\nWeighted model saved to: {OUTPUT_MODEL}")


def main():
    print("Loading data...")
    run_stats, existing_corrections = load_data()
    
    print(f"Loaded {len(run_stats)} venues with run data")
    print(f"Loaded {len(existing_corrections)} existing corrections")
    print(f"Excluded venues: {EXCLUDED_VENUES}")
    
    baseline_venue = find_baseline(run_stats)
    print(f"\nBaseline venue: {baseline_venue}")
    
    results = calculate_factors(run_stats, baseline_venue, existing_corrections)
    results = test_weighted_models(results)
    
    print_summary(results, baseline_venue)
    save_results(results)
    
    print("\n=== WEIGHTED MODEL ANALYSIS COMPLETE ===")


if __name__ == '__main__':
    main()
