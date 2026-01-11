"""
Course correction calculation and formatting utilities.

Handles percentage-based correction calculations with inverted logic
(faster venues = positive %, slower venues = negative %).
"""

# Baseline median times (in seconds) for percentage calculations
# These are the median finish times at Maastricht 2025 (baseline venue)
BASELINE_MEN_MEDIAN = 4800.0  # 80 minutes
BASELINE_WOMEN_MEDIAN = 5526.0  # 92.1 minutes


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
        float: Percentage correction (inverted sign)
        
    Example:
        >>> calculate_percentage_correction(-754, 4800)  # London Excel (fast)
        15.7  # Positive percentage
        >>> calculate_percentage_correction(421.5, 4800)  # Atlanta (slow)
        -8.8  # Negative percentage
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
        str: Formatted string like "+5.2%" or "-3.1%"
        
    Example:
        >>> format_correction(15.7)
        '+15.7%'
        >>> format_correction(-8.8)
        '-8.8%'
        >>> format_correction(0.02)
        '0.0%'
    """
    if abs(correction_percentage) < 0.05:
        return "0.0%"
    
    sign = "+" if correction_percentage > 0 else ""
    return f"{sign}{correction_percentage:.1f}%"
