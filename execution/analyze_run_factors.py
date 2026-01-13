#!/usr/bin/env python3
"""
Analyze Pro Run Times and Compare with Existing Venue Factors.

This script:
1. Loads scraped run time data from SQLite
2. Calculates run-based venue factors (fastest, median, average)
3. Compares with existing median-based correction factors
4. Creates comparison table in database
5. Identifies multi-venue athletes for validation

Usage:
    python analyze_run_factors.py
"""

import sqlite3
import json
from pathlib import Path
from collections import defaultdict
import statistics

# Configuration
DB_PATH = Path('data/hyrox_results.db')
CORRECTIONS_FILE = Path('data/venue_corrections.json')
OUTPUT_COMPARISON = Path('data/factor_comparison.csv')
OUTPUT_MULTI_VENUE = Path('data/multi_venue_athletes.csv')


def load_existing_corrections():
    """Load existing venue correction factors from JSON."""
    if not CORRECTIONS_FILE.exists():
        print(f"Warning: {CORRECTIONS_FILE} not found")
        return {}
    
    with open(CORRECTIONS_FILE, 'r') as f:
        data = json.load(f)
    
    # Flatten to venue -> correction seconds
    corrections = {}
    for venue, val in data.get('men', {}).items():
        corrections[venue] = {
            'men': val,
            'women': data.get('women', {}).get(venue, 0)
        }
    
    return corrections


def load_run_times():
    """Load scraped run times from database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT venue, division, gender, athlete_name, nationality, age_group,
               run_total_seconds, finish_total_seconds
        FROM pro_run_times
        WHERE run_total_seconds IS NOT NULL
        ORDER BY venue, division, gender, run_total_seconds
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def calculate_run_factors(run_times):
    """Calculate run-based factors for each venue."""
    # Group by venue, division, gender
    grouped = defaultdict(list)
    
    for row in run_times:
        key = (row['venue'], row['division'], row['gender'])
        grouped[key].append(row['run_total_seconds'])
    
    # Calculate stats per venue (aggregate Pro + Individual)
    venue_stats = defaultdict(lambda: {'men_runs': [], 'women_runs': []})
    
    for (venue, division, gender), times in grouped.items():
        if gender == 'M':
            venue_stats[venue]['men_runs'].extend(times)
        else:
            venue_stats[venue]['women_runs'].extend(times)
    
    # Calculate factors
    results = {}
    
    for venue, data in venue_stats.items():
        men_runs = sorted(data['men_runs'])
        women_runs = sorted(data['women_runs'])
        
        results[venue] = {
            'men_count': len(men_runs),
            'women_count': len(women_runs),
            'men_fastest': min(men_runs) if men_runs else None,
            'men_median': statistics.median(men_runs) if men_runs else None,
            'men_mean': statistics.mean(men_runs) if men_runs else None,
            'women_fastest': min(women_runs) if women_runs else None,
            'women_median': statistics.median(women_runs) if women_runs else None,
            'women_mean': statistics.mean(women_runs) if women_runs else None,
        }
    
    return results


def find_baseline_venue(venue_stats):
    """Find baseline venue (median of medians)."""
    men_medians = [(v, s['men_median']) for v, s in venue_stats.items() if s['men_median']]
    men_medians.sort(key=lambda x: x[1])
    
    if not men_medians:
        return None
    
    mid_idx = len(men_medians) // 2
    return men_medians[mid_idx][0]


def calculate_run_correction_factors(venue_stats, baseline_venue):
    """Calculate correction factors relative to baseline."""
    if not baseline_venue or baseline_venue not in venue_stats:
        return {}
    
    baseline = venue_stats[baseline_venue]
    baseline_men = baseline['men_median']
    baseline_women = baseline['women_median']
    
    factors = {}
    
    for venue, stats in venue_stats.items():
        men_diff = stats['men_median'] - baseline_men if stats['men_median'] else None
        women_diff = stats['women_median'] - baseline_women if stats['women_median'] else None
        
        factors[venue] = {
            'men_correction_seconds': men_diff,
            'women_correction_seconds': women_diff,
            'men_correction_pct': (men_diff / baseline_men * 100) if men_diff is not None else None,
            'women_correction_pct': (women_diff / baseline_women * 100) if women_diff is not None else None,
        }
    
    return factors


def find_multi_venue_athletes(run_times):
    """Find athletes who competed at multiple venues."""
    # Group by athlete key (name + nationality)
    athlete_venues = defaultdict(list)
    
    for row in run_times:
        key = f"{row['athlete_name']}|{row['nationality']}"
        athlete_venues[key].append({
            'venue': row['venue'],
            'division': row['division'],
            'gender': row['gender'],
            'run_total': row['run_total_seconds'],
            'finish_total': row['finish_total_seconds']
        })
    
    # Filter to athletes with 2+ venues
    multi_venue = {}
    for athlete_key, venues in athlete_venues.items():
        unique_venues = set(v['venue'] for v in venues)
        if len(unique_venues) >= 2:
            multi_venue[athlete_key] = venues
    
    return multi_venue


def format_time(seconds):
    """Format seconds as H:MM:SS or MM:SS."""
    if seconds is None:
        return "N/A"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def create_comparison_table(venue_stats, run_factors, existing_corrections, baseline_venue):
    """Create and save comparison table."""
    import csv
    
    rows = []
    
    for venue in sorted(venue_stats.keys()):
        stats = venue_stats[venue]
        run_factor = run_factors.get(venue, {})
        
        # Find matching existing correction (fuzzy match on venue name)
        existing = None
        for existing_venue in existing_corrections.keys():
            if venue.replace(' 2025', '').lower() in existing_venue.lower():
                existing = existing_corrections[existing_venue]
                break
        
        row = {
            'venue': venue,
            'is_baseline': 'Yes' if venue == baseline_venue else 'No',
            'men_count': stats['men_count'],
            'women_count': stats['women_count'],
            'men_fastest_run': format_time(stats['men_fastest']),
            'men_median_run': format_time(stats['men_median']),
            'men_mean_run': format_time(stats['men_mean']),
            'women_fastest_run': format_time(stats['women_fastest']),
            'women_median_run': format_time(stats['women_median']),
            'women_mean_run': format_time(stats['women_mean']),
            'run_factor_men_pct': f"{run_factor.get('men_correction_pct', 0):.1f}%" if run_factor.get('men_correction_pct') is not None else 'N/A',
            'run_factor_women_pct': f"{run_factor.get('women_correction_pct', 0):.1f}%" if run_factor.get('women_correction_pct') is not None else 'N/A',
            'existing_men_correction': f"{existing['men']:.0f}s" if existing else 'N/A',
            'existing_women_correction': f"{existing['women']:.0f}s" if existing else 'N/A',
        }
        rows.append(row)
    
    # Save to CSV
    with open(OUTPUT_COMPARISON, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nComparison table saved to: {OUTPUT_COMPARISON}")
    return rows


def create_multi_venue_table(multi_venue_athletes, run_factors):
    """Create and save multi-venue athlete validation table."""
    import csv
    
    rows = []
    
    for athlete_key, venues in multi_venue_athletes.items():
        name, nationality = athlete_key.split('|')
        
        # Get unique venues with run times
        venue_data = {}
        for v in venues:
            venue_name = v['venue']
            if venue_name not in venue_data:
                venue_data[venue_name] = v['run_total']
        
        if len(venue_data) < 2:
            continue
        
        # Create pairwise comparisons
        venue_list = list(venue_data.items())
        for i in range(len(venue_list)):
            for j in range(i + 1, len(venue_list)):
                venue_a, run_a = venue_list[i]
                venue_b, run_b = venue_list[j]
                
                observed_diff = run_b - run_a
                observed_pct = (observed_diff / run_a) * 100
                
                # Get expected difference from run factors
                factor_a = run_factors.get(venue_a, {}).get('men_correction_pct', 0) or 0
                factor_b = run_factors.get(venue_b, {}).get('men_correction_pct', 0) or 0
                expected_pct = factor_b - factor_a
                
                delta = observed_pct - expected_pct
                
                rows.append({
                    'athlete_name': name,
                    'nationality': nationality,
                    'venue_a': venue_a,
                    'run_time_a': format_time(run_a),
                    'venue_b': venue_b,
                    'run_time_b': format_time(run_b),
                    'observed_diff_seconds': observed_diff,
                    'observed_diff_pct': f"{observed_pct:.1f}%",
                    'expected_diff_pct': f"{expected_pct:.1f}%",
                    'delta_pct': f"{delta:.1f}%",
                    'validates': 'Yes' if abs(delta) < 5 else 'No'
                })
    
    # Sort by absolute delta
    rows.sort(key=lambda x: abs(float(x['delta_pct'].replace('%', ''))))
    
    # Save to CSV
    with open(OUTPUT_MULTI_VENUE, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"Multi-venue athlete table saved to: {OUTPUT_MULTI_VENUE}")
    return rows


def save_to_db(venue_stats, run_factors, existing_corrections, baseline_venue):
    """Save comparison data to database table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create comparison table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS factor_comparison (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venue TEXT UNIQUE,
            is_baseline INTEGER,
            men_sample_size INTEGER,
            women_sample_size INTEGER,
            men_median_run_seconds INTEGER,
            women_median_run_seconds INTEGER,
            run_factor_men_pct REAL,
            run_factor_women_pct REAL,
            existing_men_correction_seconds REAL,
            existing_women_correction_seconds REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Clear existing data
    cursor.execute('DELETE FROM factor_comparison')
    
    # Insert new data
    for venue in venue_stats.keys():
        stats = venue_stats[venue]
        run_factor = run_factors.get(venue, {})
        
        existing = None
        for existing_venue in existing_corrections.keys():
            if venue.replace(' 2025', '').lower() in existing_venue.lower():
                existing = existing_corrections[existing_venue]
                break
        
        cursor.execute('''
            INSERT INTO factor_comparison (
                venue, is_baseline, men_sample_size, women_sample_size,
                men_median_run_seconds, women_median_run_seconds,
                run_factor_men_pct, run_factor_women_pct,
                existing_men_correction_seconds, existing_women_correction_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            venue,
            1 if venue == baseline_venue else 0,
            stats['men_count'],
            stats['women_count'],
            stats['men_median'],
            stats['women_median'],
            run_factor.get('men_correction_pct'),
            run_factor.get('women_correction_pct'),
            existing['men'] if existing else None,
            existing['women'] if existing else None
        ))
    
    conn.commit()
    conn.close()
    print(f"Comparison data saved to database table: factor_comparison")


def print_summary(venue_stats, run_factors, baseline_venue):
    """Print analysis summary to console."""
    print("\n" + "="*80)
    print("RUN TIME ANALYSIS SUMMARY")
    print("="*80)
    
    print(f"\nBaseline Venue: {baseline_venue}")
    
    print(f"\n{'Venue':<25} {'Men Median':>12} {'Women Median':>14} {'Men %':>10} {'Women %':>10}")
    print("-" * 80)
    
    for venue in sorted(venue_stats.keys(), key=lambda v: venue_stats[v]['men_median'] or 999999):
        stats = venue_stats[venue]
        factor = run_factors.get(venue, {})
        
        men_med = format_time(stats['men_median'])
        women_med = format_time(stats['women_median'])
        men_pct = f"{factor.get('men_correction_pct', 0):.1f}%" if factor.get('men_correction_pct') is not None else 'N/A'
        women_pct = f"{factor.get('women_correction_pct', 0):.1f}%" if factor.get('women_correction_pct') is not None else 'N/A'
        
        baseline_marker = " (Baseline)" if venue == baseline_venue else ""
        print(f"{venue:<25} {men_med:>12} {women_med:>14} {men_pct:>10} {women_pct:>10}{baseline_marker}")
    
    print("="*80)


def main():
    print("Loading data...")
    
    # Load data
    existing_corrections = load_existing_corrections()
    run_times = load_run_times()
    
    print(f"Loaded {len(run_times)} run time records")
    print(f"Loaded {len(existing_corrections)} existing venue corrections")
    
    # Calculate run-based factors
    print("\nCalculating run-based factors...")
    venue_stats = calculate_run_factors(run_times)
    baseline_venue = find_baseline_venue(venue_stats)
    run_factors = calculate_run_correction_factors(venue_stats, baseline_venue)
    
    # Print summary
    print_summary(venue_stats, run_factors, baseline_venue)
    
    # Find multi-venue athletes
    print("\nFinding multi-venue athletes...")
    multi_venue = find_multi_venue_athletes(run_times)
    print(f"Found {len(multi_venue)} athletes who competed at 2+ venues")
    
    # Create outputs
    print("\nCreating output tables...")
    create_comparison_table(venue_stats, run_factors, existing_corrections, baseline_venue)
    
    if multi_venue:
        create_multi_venue_table(multi_venue, run_factors)
    
    save_to_db(venue_stats, run_factors, existing_corrections, baseline_venue)
    
    print("\n=== ANALYSIS COMPLETE ===")


if __name__ == '__main__':
    main()
