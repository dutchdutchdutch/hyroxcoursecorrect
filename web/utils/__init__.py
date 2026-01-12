"""
HYROX Course Correct - Utility Modules

This package contains utility functions extracted from app.py for better
code organization and testability.
"""

from .data_loader import (
    load_venue_corrections, 
    get_baseline_venue, 
    CORRECTIONS_FILE,
    get_race_results,
    get_all_results
)
from .corrections import (
    calculate_percentage_correction,
    format_correction,
    BASELINE_MEN_MEDIAN,
    BASELINE_WOMEN_MEDIAN
)
from .time_utils import parse_time_to_seconds, format_time
from .database import get_db_connection

__all__ = [
    'load_venue_corrections',
    'get_baseline_venue',
    'CORRECTIONS_FILE',
    'calculate_percentage_correction',
    'format_correction',
    'BASELINE_MEN_MEDIAN',
    'BASELINE_WOMEN_MEDIAN',
    'parse_time_to_seconds',
    'format_time',
    'get_race_results',
    'get_all_results',
    'get_db_connection'
]
