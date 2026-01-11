#!/usr/bin/env python3
"""
HYROX Course Correct - Flask Web Application

Web interface for converting HYROX finish times between venues using
gender-specific course correction factors.
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
from pathlib import Path
import os

app = Flask(__name__)

# Get the project root directory (parent of web/)
PROJECT_ROOT = Path(__file__).parent.parent

# Load gender-specific venue course corrections
CORRECTIONS_FILE = PROJECT_ROOT / 'data' / 'venue_handicaps_by_gender.json'

def load_venue_corrections():
    """Load gender-specific venue course correction factors from JSON."""
    if CORRECTIONS_FILE.exists():
        with open(CORRECTIONS_FILE, 'r') as f:
            return json.load(f)
    else:
        # Fallback corrections if file not found (in seconds)
        return {
            'men': {
                'London Excel 2025': -754.0,
                'Bordeaux 2025': -477.0,
                'Dublin 2025': -464.5,
                'Valencia 2025': -128.5,
                'Frankfurt 2025': -84.5,
                'Maastricht 2025': 0.0,
                'Utrecht 2025': 20.0,
                'Chicago 2025': 244.0,
                'Anaheim 2025': 346.5,
                'Atlanta 2025': 421.5
            },
            'women': {
                'London Excel 2025': -787.0,
                'Bordeaux 2025': -149.0,
                'Dublin 2025': -288.0,
                'Valencia 2025': -136.0,
                'Frankfurt 2025': -53.0,
                'Maastricht 2025': 0.0,
                'Utrecht 2025': 39.0,
                'Chicago 2025': -49.0,
                'Anaheim 2025': 260.0,
                'Atlanta 2025': 103.0
            }
        }

def get_baseline_venue(corrections):
    """
    Identify the baseline venue (correction = 0.0 for men).
    This is the median-difficulty venue used as reference.
    """
    men_corrections = corrections['men']
    # Find venue with correction closest to 0.0
    baseline_venue = min(men_corrections.items(), key=lambda x: abs(x[1]))[0]
    return baseline_venue

def calculate_percentage_correction(correction_seconds, baseline_median_seconds):
    """
    Calculate percentage-based course correction with INVERTED logic.
    
    Inverted logic means:
    - Faster venues (negative time correction) = POSITIVE percentage (you add time to baseline)
    - Slower venues (positive time correction) = NEGATIVE percentage (you subtract time from baseline)
    
    This is more intuitive from an athlete's perspective:
    "If I run at Bordeaux (fast course), I need to add X% to my baseline time"
    
    Args:
        correction_seconds: Time correction in seconds (negative = faster, positive = slower)
        baseline_median_seconds: Median finish time at baseline venue in seconds
    
    Returns:
        Percentage correction (inverted sign)
    """
    if baseline_median_seconds == 0:
        return 0.0
    
    # Invert the sign: negative time correction becomes positive percentage
    percentage = -(correction_seconds / baseline_median_seconds) * 100
    return percentage

def format_correction(correction_percentage):
    """
    Format course correction percentage to a user-friendly string.
    
    Args:
        correction_percentage: Correction value as percentage (can be negative or positive)
    
    Returns:
        Formatted string like "+5.2%" or "-3.1%"
    """
    if abs(correction_percentage) < 0.05:
        return "0.0%"
    
    sign = "+" if correction_percentage > 0 else ""
    return f"{sign}{correction_percentage:.1f}%"

# Baseline median times (in seconds) for percentage calculations
# These are the median finish times at Maastricht 2025 (baseline venue)
BASELINE_MEN_MEDIAN = 4800.0  # 80 minutes
BASELINE_WOMEN_MEDIAN = 5526.0  # 92.1 minutes

VENUE_CORRECTIONS = load_venue_corrections()
BASELINE_VENUE = get_baseline_venue(VENUE_CORRECTIONS)
VENUES = sorted(list(set(list(VENUE_CORRECTIONS['men'].keys()) + list(VENUE_CORRECTIONS['women'].keys()))))


def parse_time_to_seconds(time_str):
    """Parse time string (HH:MM:SS or MM:SS) to seconds."""
    parts = time_str.strip().split(':')
    
    try:
        if len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return None
    except ValueError:
        return None


def format_time(seconds):
    """Convert seconds to HH:MM:SS format."""
    if seconds is None:
        return ""
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def convert_time(time_seconds, from_venue, to_venue):
    """
    Convert finish time from one venue to another.
    
    Args:
        time_seconds: Finish time in seconds
        from_venue: Source venue name
        to_venue: Target venue name
    
    Returns:
        Converted time in seconds
    """
    from_handicap = VENUE_HANDICAPS.get(from_venue, 1.0)
    to_handicap = VENUE_HANDICAPS.get(to_venue, 1.0)
    
    # Normalize to reference venue, then apply target venue handicap
    normalized_time = time_seconds / from_handicap
    converted_time = normalized_time * to_handicap
    
    return converted_time


@app.route('/')
def index():
    """Render the main page."""
    # Pass men's corrections for display (as reference)
    return render_template('index.html', venues=VENUES, corrections=VENUE_CORRECTIONS['men'])


@app.route('/convert', methods=['POST'])
def convert():
    """Handle time conversion request."""
    data = request.get_json()
    
    finish_time = data.get('finish_time')
    from_venue = data.get('from_venue')
    to_venue = data.get('to_venue', 'normalized')
    gender = data.get('gender')  # Required: 'M' or 'W'
    
    # Validate gender
    if not gender or gender not in ['M', 'W']:
        return jsonify({'error': 'Gender is required. Must be "M" (men) or "W" (women)'}), 400
    
    # Parse time
    time_seconds = parse_time_to_seconds(finish_time)
    
    if time_seconds is None:
        return jsonify({'error': 'Invalid time format. Use HH:MM:SS or MM:SS'}), 400
    
    # Get gender-specific corrections
    gender_key = 'men' if gender == 'M' else 'women'
    corrections = VENUE_CORRECTIONS[gender_key]
    baseline_median = BASELINE_MEN_MEDIAN if gender == 'M' else BASELINE_WOMEN_MEDIAN
    
    if from_venue not in corrections:
        return jsonify({'error': f'Unknown venue: {from_venue}'}), 400
    
    # Convert time using additive corrections
    if to_venue == 'normalized':
        # Normalize to reference venue (correction = 0.0)
        from_correction = corrections[from_venue]
        # Remove the from_venue correction to get normalized time
        converted_seconds = time_seconds - from_correction
        result_venue = 'Normalized (Reference)'
        to_correction = 0.0
        to_correction_pct = 0.0
    else:
        if to_venue not in corrections:
            return jsonify({'error': f'Unknown target venue: {to_venue}'}), 400
        
        from_correction = corrections[from_venue]
        to_correction = corrections[to_venue]
        # Remove from_venue correction, then apply to_venue correction
        converted_seconds = time_seconds - from_correction + to_correction
        result_venue = to_venue
        to_correction_pct = calculate_percentage_correction(to_correction, baseline_median)
    
    # Calculate percentage corrections (inverted)
    from_correction_pct = calculate_percentage_correction(from_correction, baseline_median)
    
    # Calculate time difference
    time_diff = converted_seconds - time_seconds
    
    return jsonify({
        'original_time': finish_time,
        'original_seconds': time_seconds,
        'from_venue': from_venue,
        'from_correction': from_correction,
        'from_correction_display': format_correction(from_correction_pct),
        'gender': 'Men' if gender == 'M' else 'Women',
        'to_venue': result_venue,
        'to_correction': to_correction,
        'to_correction_display': format_correction(to_correction_pct) if to_venue != 'normalized' else '0.0%',
        'converted_time': format_time(converted_seconds),
        'converted_seconds': converted_seconds,
        'time_difference': format_time(abs(time_diff)),
        'faster': time_diff < 0,
    })


@app.route('/venues')
def venues():
    """Return list of venues and their course corrections."""
    # Use men's corrections for sorting/display
    men_corrections = VENUE_CORRECTIONS['men']
    venue_data = [
        {
            'name': venue,
            'correction': correction,
            'correction_pct': calculate_percentage_correction(correction, BASELINE_MEN_MEDIAN),
            'correction_display': format_correction(calculate_percentage_correction(correction, BASELINE_MEN_MEDIAN)),
            'correction_label': 'Baseline' if venue == BASELINE_VENUE else format_correction(calculate_percentage_correction(correction, BASELINE_MEN_MEDIAN))
        }
        for venue, correction in sorted(men_corrections.items(), key=lambda x: x[1])
    ]
    
    return jsonify(venue_data)


@app.route('/analysis')
def analysis():
    """Render the venue analysis page with gender-specific distribution charts."""
    # Load processed results if available
    results_file = PROJECT_ROOT / 'data' / 'hyrox_9venues_100each.csv'
    
    # Check admin mode
    admin_mode = os.environ.get('HYROX_ADMIN_MODE', 'false').lower() == 'true'
    
    if results_file.exists():
        df = pd.read_csv(results_file)
        
        # Prepare data for box plots (overall, men, women)
        venue_data_all = []
        men_data = []
        women_data = []
        venue_stats = []
        
        colors = ['#FF6B35', '#004E89', '#06D6A0', '#F77F00', '#9B59B6', '#E74C3C']
        
        # Use men's corrections for sorting/display
        men_corrections = VENUE_CORRECTIONS['men']
        
        for idx, (venue, correction) in enumerate(sorted(men_corrections.items(), key=lambda x: x[1])):
            # Overall data (all genders)
            venue_times_all = df[df['venue'] == venue]['finish_seconds'].tolist()
            
            # Men's data
            venue_times_men = df[(df['venue'] == venue) & (df['gender'] == 'M')]['finish_seconds'].tolist()
            
            # Women's data
            venue_times_women = df[(df['venue'] == venue) & (df['gender'] == 'W')]['finish_seconds'].tolist()
            
            color = colors[idx % len(colors)]
            
            if venue_times_all:
                venue_data_all.append({
                    'name': venue,
                    'times': venue_times_all,
                    'color': color
                })
            
            if venue_times_men:
                men_data.append({
                    'name': venue,
                    'times': venue_times_men,
                    'color': color
                })
            
            if venue_times_women:
                women_data.append({
                    'name': venue,
                    'times': venue_times_women,
                    'color': color
                })
            
            if venue_times_all:
                correction_pct = calculate_percentage_correction(correction, BASELINE_MEN_MEDIAN)
                venue_stats.append({
                    'name': venue,
                    'count': len(venue_times_all),
                    'mean': format_time(sum(venue_times_all) / len(venue_times_all)),
                    'median': format_time(sorted(venue_times_all)[len(venue_times_all) // 2]),
                    'correction': correction,
                    'correction_pct': correction_pct,
                    'correction_display': format_correction(correction_pct),
                    'correction_label': 'Baseline' if venue == BASELINE_VENUE else format_correction(correction_pct)
                })
        
        # Calculate summary stats
        fastest_venue = min(men_corrections.items(), key=lambda x: x[1])[0]
        slowest_venue = max(men_corrections.items(), key=lambda x: x[1])[0]
        slowest_correction = men_corrections[slowest_venue]
        slowest_correction_pct = calculate_percentage_correction(slowest_correction, BASELINE_MEN_MEDIAN)
        slowest_diff = format_correction(slowest_correction_pct)
        
        return render_template('analysis.html',
                             venue_data=venue_data_all,
                             men_data=men_data,
                             women_data=women_data,
                             venue_stats=venue_stats,
                             fastest_venue=fastest_venue,
                             slowest_venue=slowest_venue,
                             slowest_diff=slowest_diff,
                             total_athletes=len(df),
                             num_venues=len(men_corrections),
                             admin_mode=admin_mode)
    else:
        # No data available - use sample data
        venue_data = [
            {
                'name': 'London Excel 2025',
                'times': [4100, 4200, 4300, 4250, 4150, 4400, 4500],
                'color': '#06D6A0'
            },
            {
                'name': 'Anaheim 2025',
                'times': [4200, 4300, 4400, 4350, 4250, 4500, 4600],
                'color': '#FF6B35'
            }
        ]
        
        venue_stats = [
            {
                'name': 'London Excel 2025',
                'count': 266,
                'mean': '1:11:42',
                'median': '1:11:02',
                'handicap': 1.000,
                'difficulty': 'Reference'
            },
            {
                'name': 'Anaheim 2025',
                'count': 251,
                'mean': '1:13:09',
                'median': '1:12:28',
                'handicap': 1.022,
                'difficulty': '+2.2%'
            }
        ]
        
        return render_template('analysis.html',
                             venue_data=venue_data,
                             venue_stats=venue_stats,
                             fastest_venue='London Excel 2025',
                             slowest_venue='Anaheim 2025',
                             slowest_diff='+2.2%',
                             total_athletes=517,
                             num_venues=2)




@app.route('/statistics')
def statistics():
    """Render detailed statistics table page."""
    results_file = PROJECT_ROOT / 'data' / 'hyrox_9venues_100each.csv'
    
    if results_file.exists():
        df = pd.read_csv(results_file)
        
        # Calculate detailed statistics for each venue
        stats_data = []
        
        # Use men's corrections for sorting
        men_corrections = VENUE_CORRECTIONS['men']
        
        for venue, correction in sorted(men_corrections.items(), key=lambda x: x[1]):
            venue_df = df[df['venue'] == venue]
            venue_times = venue_df['finish_seconds'].tolist()
            
            # Calculate gender-specific benchmarks
            men_times = venue_df[venue_df['gender'] == 'M']['finish_seconds'].tolist()
            women_times = venue_df[venue_df['gender'] == 'W']['finish_seconds'].tolist()
            
            if venue_times:
                sorted_times = sorted(venue_times)
                sorted_men = sorted(men_times) if men_times else []
                sorted_women = sorted(women_times) if women_times else []
                
                correction_pct = calculate_percentage_correction(correction, BASELINE_MEN_MEDIAN)
                stats_data.append({
                    'name': venue,
                    'count': len(venue_times),
                    'fastest': format_time(min(venue_times)),
                    'slowest': format_time(max(venue_times)),
                    'average': format_time(sum(venue_times) / len(venue_times)),
                    'benchmark': format_time(sorted_times[len(sorted_times) // 2]),
                    'men_benchmark': format_time(sorted_men[len(sorted_men) // 2]) if sorted_men else 'N/A',
                    'women_benchmark': format_time(sorted_women[len(sorted_women) // 2]) if sorted_women else 'N/A',
                    'std_dev': format_time(pd.Series(venue_times).std()),
                    'correction': correction,
                    'correction_pct': correction_pct,
                    'correction_display': format_correction(correction_pct),
                    'correction_label': 'Baseline' if venue == BASELINE_VENUE else format_correction(correction_pct)
                })
        
        return render_template('statistics.html',
                             stats_data=stats_data,
                             total_athletes=len(df),
                             num_venues=len(VENUE_CORRECTIONS))
    else:
        # No data available
        return render_template('statistics.html',
                             stats_data=[],
                             total_athletes=0,
                             num_venues=0)


if __name__ == '__main__':
    # Run in debug mode for development
    app.run(debug=True, host='127.0.0.1', port=5000)
