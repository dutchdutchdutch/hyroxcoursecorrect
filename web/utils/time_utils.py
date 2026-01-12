"""
Time parsing and formatting utilities.

Handles conversion between time strings (HH:MM:SS) and seconds.
"""


def parse_time_to_seconds(time_str):
    """
    Parse time string (HH:MM:SS or MM:SS) to seconds.
    
    Args:
        time_str: Time string in format "HH:MM:SS" or "MM:SS"
        
    Returns:
        int: Total seconds, or None if invalid format
    """
    try:
        if not time_str:
            return None
            
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(int, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:
            minutes, seconds = map(int, parts)
            return minutes * 60 + seconds
        else:
            return None
    except ValueError:
        return None


def format_time(seconds):
    """
    Convert seconds to HH:MM:SS format.
    
    Args:
        seconds: Time in seconds (can be float)
        
    Returns:
        str: Formatted time string "HH:MM:SS"
    """
    if seconds is None:
        return ""
        
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    # Use leading zero for hours to match test expectation "01:30:45"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"
