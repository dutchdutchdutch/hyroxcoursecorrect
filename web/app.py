#!/usr/bin/env python3
"""
HYROX Course Correct - Flask Web Application

Web interface for converting HYROX finish times between venues using
course correction factors.
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
from pathlib import Path
import os

app = Flask(__name__)

# Load venue handicaps
HANDICAPS_FILE = Path('.tmp/venue_handicaps.csv')

def load_venue_handicaps():
    """Load venue handicap factors from CSV."""
    if HANDICAPS_FILE.exists():
        df = pd.read_csv(HANDICAPS_FILE)
        return df.set_index('venue')['handicap_factor'].to_dict()
    else:
        # Default handicaps for Season 8
        return {
            'London Excel 2025': 1.000,
            'Anaheim 2025': 1.022,
        }

VENUE_HANDICAPS = load_venue_handicaps()
VENUES = list(VENUE_HANDICAPS.keys())


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
    return render_template('index.html', venues=VENUES, handicaps=VENUE_HANDICAPS)


@app.route('/convert', methods=['POST'])
def convert():
    """Handle time conversion request."""
    data = request.get_json()
    
    finish_time = data.get('finish_time')
    from_venue = data.get('from_venue')
    to_venue = data.get('to_venue', 'normalized')
    
    # Parse time
    time_seconds = parse_time_to_seconds(finish_time)
    
    if time_seconds is None:
        return jsonify({'error': 'Invalid time format. Use HH:MM:SS or MM:SS'}), 400
    
    if from_venue not in VENUE_HANDICAPS:
        return jsonify({'error': f'Unknown venue: {from_venue}'}), 400
    
    # Convert time
    if to_venue == 'normalized':
        # Normalize to reference venue (handicap = 1.0)
        from_handicap = VENUE_HANDICAPS[from_venue]
        converted_seconds = time_seconds / from_handicap
        result_venue = 'Normalized (Reference)'
    else:
        if to_venue not in VENUE_HANDICAPS:
            return jsonify({'error': f'Unknown target venue: {to_venue}'}), 400
        
        converted_seconds = convert_time(time_seconds, from_venue, to_venue)
        result_venue = to_venue
    
    # Calculate time difference
    time_diff = converted_seconds - time_seconds
    
    return jsonify({
        'original_time': finish_time,
        'original_seconds': time_seconds,
        'from_venue': from_venue,
        'from_handicap': VENUE_HANDICAPS[from_venue],
        'to_venue': result_venue,
        'to_handicap': VENUE_HANDICAPS.get(to_venue, 1.0) if to_venue != 'normalized' else 1.0,
        'converted_time': format_time(converted_seconds),
        'converted_seconds': converted_seconds,
        'time_difference': format_time(abs(time_diff)),
        'faster': time_diff < 0,
    })


@app.route('/venues')
def venues():
    """Return list of venues and their handicaps."""
    venue_data = [
        {
            'name': venue,
            'handicap': handicap,
            'difficulty': 'Reference' if handicap == 1.0 else f'{(handicap - 1) * 100:+.1f}%'
        }
        for venue, handicap in sorted(VENUE_HANDICAPS.items(), key=lambda x: x[1])
    ]
    
    return jsonify(venue_data)


if __name__ == '__main__':
    # Run in debug mode for development
    app.run(debug=True, host='127.0.0.1', port=5000)
