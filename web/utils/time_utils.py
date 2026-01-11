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
        int: Total seconds
        
    Example:
        >>> parse_time_to_seconds("1:15:30")
        4530
        >>> parse_time_to_seconds("45:30")
        2730
    """
    parts = time_str.strip().split(':')
    if len(parts) == 3:
        hours, minutes, seconds = map(int, parts)
        return hours * 3600 + minutes * 60 + seconds
    elif len(parts) == 2:
        minutes, seconds = map(int, parts)
        return minutes * 60 + seconds
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def format_time(seconds):
    """
    Convert seconds to HH:MM:SS format.
    
    Args:
        seconds: Time in seconds (can be float)
        
    Returns:
        str: Formatted time string "HH:MM:SS"
        
    Example:
        >>> format_time(4530)
        '1:15:30'
        >>> format_time(2730.5)
        '0:45:30'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}:{minutes:02d}:{secs:02d}"
