"""
Data loading utilities for HYROX Course Correct.

Handles loading venue correction factors and identifying baseline venues.
"""

import json
from pathlib import Path

# Get the project root directory (parent of web/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load gender-specific venue course corrections
CORRECTIONS_FILE = PROJECT_ROOT / 'data' / 'venue_handicaps_by_gender.json'


def load_venue_corrections():
    """
    Load gender-specific venue course correction factors from JSON.
    
    Returns:
        dict: Dictionary with 'men' and 'women' keys, each containing
              venue names mapped to correction values in seconds.
              
    Example:
        {
            'men': {'London Excel 2025': -754.0, 'Maastricht 2025': 0.0, ...},
            'women': {'London Excel 2025': -787.0, 'Maastricht 2025': 0.0, ...}
        }
    """
    if CORRECTIONS_FILE.exists():
        with open(CORRECTIONS_FILE, 'r') as f:
            return json.load(f)
    else:
        # Fallback corrections if file not found
        return {
            'men': {
                'London Excel 2025': -754.0,
                'Bordeaux 2025': -475.5,
                'Dublin 2025': -305.0,
                'Valencia 2025': -154.5,
                'Frankfurt 2025': -60.0,
                'Maastricht 2025': 0.0,
                'Utrecht 2025': 105.0,
                'Arnhem 2025': 193.5,
                'Chicago 2025': 289.5,
                'Atlanta 2025': 421.5
            },
            'women': {
                'London Excel 2025': -787.0,
                'Bordeaux 2025': -532.5,
                'Dublin 2025': -334.5,
                'Valencia 2025': -193.5,
                'Frankfurt 2025': -78.0,
                'Maastricht 2025': 0.0,
                'Utrecht 2025': 82.5,
                'Arnhem 2025': 126.0,
                'Chicago 2025': 97.5,
                'Atlanta 2025': 103.0
            }
        }


def get_baseline_venue(corrections):
    """
    Identify the baseline venue (correction = 0.0 for men).
    This is the median-difficulty venue used as reference.
    
    Args:
        corrections: Dictionary of venue corrections by gender
        
    Returns:
        str: Name of the baseline venue
    """
    men_corrections = corrections['men']
    # Find venue with correction closest to 0.0
    baseline_venue = min(men_corrections.items(), key=lambda x: abs(x[1]))[0]
    return baseline_venue
