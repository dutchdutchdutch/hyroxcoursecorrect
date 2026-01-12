#!/usr/bin/env python3
"""
HYROX Course Correct - Flask Web Application

Web interface for converting HYROX finish times between venues using
gender-specific course correction factors.
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
from pathlib import Path
import os

# Import utility functions
from utils import (
    load_venue_corrections,
    get_baseline_venue,
    calculate_percentage_correction,
    format_correction,
    parse_time_to_seconds,
    format_time,
    BASELINE_MEN_MEDIAN,
    BASELINE_WOMEN_MEDIAN,
    get_race_results,
    get_all_results,
    get_db_connection
)

app = Flask(__name__)

# Load venue corrections and identify baseline
VENUE_CORRECTIONS = load_venue_corrections()
BASELINE_VENUE = get_baseline_venue(VENUE_CORRECTIONS)
VENUES = sorted(list(set(list(VENUE_CORRECTIONS['men'].keys()) + list(VENUE_CORRECTIONS['women'].keys()))))

# Helper to look up country flags (basic mapping)
VENUE_FLAGS = {
    'London': '🇬🇧', 'Manchester': '🇬🇧', 'Birmingham': '🇬🇧', 'Glasgow': '🇬🇧',
    'Dublin': '🇮🇪',
    'Berlin': '🇩🇪', 'Hamburg': '🇩🇪', 'Frankfurt': '🇩🇪', 'Munich': '🇩🇪', 'Stuttgart': '🇩🇪', 'Cologne': '🇩🇪', 'Karlsruhe': '🇩🇪', 'Hannover': '🇩🇪', 'Dortmund': '🇩🇪', 'Leipzig': '🇩🇪',
    'Vienna': '🇦🇹',
    'Amsterdam': '🇳🇱', 'Maastricht': '🇳🇱', 'Rotterdam': '🇳🇱', 'Utrecht': '🇳🇱', 'Arnhem': '🇳🇱',
    'Stockholm': '🇸🇪', 'Malmo': '🇸🇪',
    'Copenhagen': '🇩🇰',
    'Madrid': '🇪🇸', 'Valencia': '🇪🇸', 'Malaga': '🇪🇸', 'Bilbao': '🇪🇸',
    'Milan': '🇮🇹', 'Rimini': '🇮🇹', 'Turin': '🇮🇹', 'Verona': '🇮🇹', 'Rome': '🇮🇹',
    'Paris': '🇫🇷', 'Nice': '🇫🇷', 'Bordeaux': '🇫🇷', 'Marseille': '🇫🇷',
    'New York': '🇺🇸', 'Chicago': '🇺🇸', 'Dallas': '🇺🇸', 'Houston': '🇺🇸', 'Los Angeles': '🇺🇸', 'Las Vegas': '🇺🇸', 'Miami': '🇺🇸', 'Fort Lauderdale': '🇺🇸', 'Anaheim': '🇺🇸', 'Boston': '🇺🇸', 'Atlanta': '🇺🇸',
    'Toronto': '🇨🇦', 'Vancouver': '🇨🇦',
    'Dubai': '🇦🇪', 'Abu Dhabi': '🇦🇪',
    'Doha': '🇶🇦',
    'Singapore': '🇸🇬',
    'Hong Kong': '🇭🇰',
    'Incheon': '🇰🇷', 'Seoul': '🇰🇷',
    'Taipei': '🇹🇼',
    'Melbourne': '🇦🇺', 'Sydney': '🇦🇺', 'Perth': '🇦🇺', 'Brisbane': '🇦🇺',
    'Warsaw': '🇵🇱', 'Katowice': '🇵🇱', 'Poznan': '🇵🇱', 'Gdansk': '🇵🇱',
    'Mexico City': '🇲🇽', 'Acapulco': '🇲🇽',
    'Cape Town': '🇿🇦', 'Johannesburg': '🇿🇦',
    'Zurich': '🇨🇭', 'Geneva': '🇨🇭', 'St. Gallen': '🇨🇭',
    'Rio de Janeiro': '🇧🇷', 'Sao Paulo': '🇧🇷',
    'Beijing': '🇨🇳', 'Shanghai': '🇨🇳', 'Shenzhen': '🇨🇳',
    'Yokohama': '🇯🇵',
    'Gent': '🇧🇪',
    'Mumbai': '🇮🇳', 'Delhi': '🇮🇳'
}

def get_flag(venue_name):
    for key, flag in VENUE_FLAGS.items():
        if key in venue_name:
            return flag
    return '🏳️'

def get_correction_table_data():
    """Prepare sorted list of venue corrections for the UI."""
    data = []
    
    # We use all venues that appear in either list
    all_venues = set(VENUE_CORRECTIONS['men'].keys()) | set(VENUE_CORRECTIONS['women'].keys())
    
    for venue in all_venues:
        men_sec = VENUE_CORRECTIONS['men'].get(venue, 0.0)
        women_sec = VENUE_CORRECTIONS['women'].get(venue, 0.0)
        
        # Calculate percentages (inverted logic: negative time = positive pct)
        men_pct = calculate_percentage_correction(men_sec, BASELINE_MEN_MEDIAN)
        women_pct = calculate_percentage_correction(women_sec, BASELINE_WOMEN_MEDIAN)
        
        # Overall is roughly the average of the two percentages
        overall_pct = (men_pct + women_pct) / 2
        
        data.append({
            'name': venue,
            'flag': get_flag(venue),
            'men_pct_val': men_pct,
            'women_pct_val': women_pct,
            'overall_pct_val': overall_pct,
            'men_display': format_correction(men_pct),
            'women_display': format_correction(women_pct),
            'overall_display': format_correction(overall_pct),
            'is_baseline': (venue == BASELINE_VENUE)
        })
    
    # Sort by Overall Percent (High to Low -> Faster to Slower)
    # Wait, positive percent = faster. So High positive is fastest.
    # User said "Rank venues by the overall factor". Usually fast to slow.
    data.sort(key=lambda x: x['overall_pct_val'], reverse=True)
    
    return data
    
    return converted_time



@app.route('/')
def index():
    """Render the main page."""
    # Check if admin mode is enabled via environment variable
    admin_mode = os.environ.get('HYROX_ADMIN_MODE', 'false').lower() == 'true'
    show_feedback_popup = os.environ.get('HYROX_SHOW_FEEDBACK_POPUP', 'true').lower() == 'true'

    # Get prepared table data
    venue_rows = get_correction_table_data()

    return render_template('index.html', 
                         venues=VENUES, 
                         corrections=VENUE_CORRECTIONS, # Kept for backward compat if needed, but venue_rows is primary
                         venue_rows=venue_rows, # NEW: Rich data for the table
                         admin_mode=admin_mode,
                         show_feedback_popup=show_feedback_popup)


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
    # Check if admin mode is enabled via environment variable
    admin_mode = os.environ.get('HYROX_ADMIN_MODE', 'false').lower() == 'true'
    
    # Fetch all results from the database
    results = get_all_results()
    
    if results:
        # Prepare data for box plots (overall, men, women)
        venue_data_all = []
        men_data = []
        women_data = []
        venue_stats = []
        
        colors = ['#FF6B35', '#004E89', '#06D6A0', '#F77F00', '#9B59B6', '#E74C3C']
        
        # Use men's corrections for sorting/display
        men_corrections = VENUE_CORRECTIONS['men']
        
        # Group records by venue and gender for processing
        venues_dist = {}
        for row in results:
            v = row['venue']
            g = row['gender']
            t = row['finish_seconds']
            
            # Filter outliers as requested:
            # < 50 mins (3000s) likely errors
            # > 2:30 (150 mins = 9000s) likely errors/injuries
            if t < 3000 or t > 9000:
                continue
            
            if v not in venues_dist:
                venues_dist[v] = {'all': [], 'M': [], 'W': []}
            venues_dist[v]['all'].append(t)
            # Use 'M' or 'W' directly as they match keys from row['gender']
            if g in ['M', 'W']:
                venues_dist[v][g].append(t)

        for idx, (venue, correction) in enumerate(sorted(men_corrections.items(), key=lambda x: x[1])):
            if venue not in venues_dist:
                continue
                
            venue_times_all = venues_dist[venue]['all']
            venue_times_men = venues_dist[venue]['M']
            venue_times_women = venues_dist[venue]['W']
            
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
                
                # Calculate medians
                overall_median_sec = sorted(venue_times_all)[len(venue_times_all) // 2]
                
                men_median_str = "N/A"
                if venue_times_men:
                    men_med_sec = sorted(venue_times_men)[len(venue_times_men) // 2]
                    # Strip leading zero on hours if possible or just use standard format
                    men_median_str = format_time(men_med_sec)
                    if men_median_str.startswith("0"): men_median_str = men_median_str[1:] # e.g. 1:18

                women_median_str = "N/A"
                if venue_times_women:
                    women_med_sec = sorted(venue_times_women)[len(venue_times_women) // 2]
                    women_median_str = format_time(women_med_sec)
                    if women_median_str.startswith("0"): women_median_str = women_median_str[1:]

                venue_stats.append({
                    'name': venue,
                    'count': len(venue_times_all),
                    'median': format_time(overall_median_sec),
                    'median_men': men_median_str,
                    'median_women': women_median_str,
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
                             total_athletes=len(results),
                             num_venues=len(men_corrections),
                             admin_mode=admin_mode,
                             show_feedback_popup=os.environ.get('HYROX_SHOW_FEEDBACK_POPUP', 'true').lower() == 'true')
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
    # Fetch all records to calculate venue stats
    results = get_all_results()
    
    if results:
        # Group and filter by venue and gender (Top 80% only)
        venues_dist = {}
        total_filtered_athletes = 0
        
        for row in results:
            v = row['venue']
            g = row['gender']
            t = row['finish_seconds']
            
            # Basic error filtering first
            if t < 3000 or t > 9000:
                continue
                
            if v not in venues_dist:
                venues_dist[v] = {'M': [], 'W': []}
            venues_dist[v][g].append(t)

        # Calculate detailed statistics for each venue
        stats_data = []
        
        # Use men's corrections for sorting
        men_corrections = VENUE_CORRECTIONS['men']
        
        for venue, correction in sorted(men_corrections.items(), key=lambda x: x[1]):
            if venue not in venues_dist:
                continue
                
            men_times = sorted(venues_dist[venue]['M'])
            women_times = sorted(venues_dist[venue]['W'])
            
            # Keep top 80% (fastest times are smaller numbers)
            # Slice from 0 to 80th percentile index
            men_cutoff_idx = int(len(men_times) * 0.8)
            women_cutoff_idx = int(len(women_times) * 0.8)
            
            men_top80 = men_times[:men_cutoff_idx] if men_times else []
            women_top80 = women_times[:women_cutoff_idx] if women_times else []
            
            all_top80 = men_top80 + women_top80
            
            # Skip if no data after filtering
            if not all_top80:
                continue
                
            total_filtered_athletes += len(all_top80)
            
            sorted_all = sorted(all_top80)
            
            # Standard Deviation
            import numpy as np
            std_dev = np.std(sorted_all)
            
            correction_pct = calculate_percentage_correction(correction, BASELINE_MEN_MEDIAN)
            stats_data.append({
                'name': venue,
                'count': len(all_top80),
                'fastest': format_time(min(sorted_all)),
                'slowest': format_time(max(sorted_all)),
                'average': format_time(sum(sorted_all) / len(sorted_all)),
                'men_benchmark': format_time(men_top80[len(men_top80) // 2]) if men_top80 else 'N/A',
                'women_benchmark': format_time(women_top80[len(women_top80) // 2]) if women_top80 else 'N/A',
                'std_dev': format_time(std_dev),
                'correction': correction,
                'correction_pct': correction_pct,
                'correction_display': format_correction(correction_pct),
                'correction_label': 'Baseline' if venue == BASELINE_VENUE else format_correction(correction_pct)
            })
        
        return render_template('statistics.html',
                             stats_data=stats_data,
                             total_athletes=total_filtered_athletes,
                             num_venues=len(stats_data),
                             show_feedback_popup=os.environ.get('HYROX_SHOW_FEEDBACK_POPUP', 'true').lower() == 'true')
    else:
        # No data available
        return render_template('statistics.html',
                             stats_data=[],
                             total_athletes=0,
                             num_venues=0)


@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback form submission."""
    data = request.get_json()
    
    rating = data.get('rating')
    comments = data.get('comments')
    liked = data.get('liked')
    learned = data.get('learned')
    lacking = data.get('lacking')
    
    if not rating:
        return jsonify({'error': 'Rating is required'}), 400
        
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO feedback (rating, comments, liked, learned, lacking) VALUES (?, ?, ?, ?, ?)',
            (rating, comments, liked, learned, lacking)
        )
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    # Run in debug mode for development
    import sys
    port = 5000
    if len(sys.argv) > 1 and sys.argv[1] == '--port':
        port = int(sys.argv[2])
    elif os.environ.get('PORT'):
        port = int(os.environ.get('PORT'))
        
    app.run(debug=True, host='127.0.0.1', port=port)
