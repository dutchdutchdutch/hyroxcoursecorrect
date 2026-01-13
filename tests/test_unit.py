"""
Unit tests for core utility functions.

Tests time parsing, handicap calculations, and data validation functions.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))
# Add web directory to path so 'import utils' works in app.py
sys.path.insert(0, str(Path(__file__).parent.parent / 'web'))

from web.utils.time_utils import parse_time_to_seconds, format_time
from execution.process_scraped_data import parse_time_to_seconds as parse_time_processing


class TestTimeParsing:
    """Test time parsing functions."""
    
    def test_parse_hhmmss_format(self):
        """Test parsing HH:MM:SS format."""
        assert parse_time_to_seconds("01:30:45") == 5445
        assert parse_time_to_seconds("00:45:30") == 2730
        assert parse_time_to_seconds("02:00:00") == 7200
    
    def test_parse_mmss_format(self):
        """Test parsing MM:SS format."""
        assert parse_time_to_seconds("45:30") == 2730
        assert parse_time_to_seconds("90:00") == 5400
        assert parse_time_to_seconds("05:15") == 315
    
    def test_parse_invalid_format(self):
        """Test parsing invalid formats returns None."""
        assert parse_time_to_seconds("invalid") is None
        assert parse_time_to_seconds("1:2:3:4") is None
        assert parse_time_to_seconds("") is None
    
    def test_parse_with_whitespace(self):
        """Test parsing with leading/trailing whitespace."""
        assert parse_time_to_seconds("  01:30:45  ") == 5445
        assert parse_time_to_seconds("\t45:30\n") == 2730


class TestTimeFormatting:
    """Test time formatting functions."""
    
    def test_format_seconds_to_hhmmss(self):
        """Test formatting seconds to HH:MM:SS."""
        assert format_time(5445) == "01:30:45"
        assert format_time(7200) == "02:00:00"
        assert format_time(3661) == "01:01:01"
    
    def test_format_less_than_hour(self):
        """Test formatting times less than an hour."""
        assert format_time(2730) == "00:45:30"
        assert format_time(315) == "00:05:15"
        assert format_time(59) == "00:00:59"
    
    def test_format_none_value(self):
        """Test formatting None returns empty string."""
        assert format_time(None) == ""


class TestHandicapCalculations:
    """Test handicap-based time conversions."""
    
    @pytest.mark.skip(reason="convert_time function not yet implemented - TODO: implement venue handicap conversion")
    def test_convert_same_venue(self):
        """Test converting time at same venue returns same time."""
        pass
    
    @pytest.mark.skip(reason="convert_time function not yet implemented")
    def test_convert_to_faster_venue(self):
        """Test converting to faster venue reduces time."""
        pass
    
    @pytest.mark.skip(reason="convert_time function not yet implemented")
    def test_convert_to_slower_venue(self):
        """Test converting to slower venue increases time."""
        pass
    
    @pytest.mark.skip(reason="convert_time function not yet implemented")
    def test_convert_to_reference_venue(self):
        """Test converting to reference venue (handicap = 1.0)."""
        pass


class TestDataValidation:
    """Test data validation and cleaning functions."""
    
    def test_parse_time_clean(self):
        """Test parsing clean time strings."""
        result = parse_time_processing("01:30:45")
        assert result == 5445
    
    def test_parse_time_mmss(self):
        """Test parsing MM:SS format."""
        result = parse_time_processing("90:45")
        assert result == 5445


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_time(self):
        """Test handling zero time."""
        assert parse_time_to_seconds("00:00:00") == 0
        assert format_time(0) == "00:00:00"
    
    def test_very_long_time(self):
        """Test handling very long times (>24 hours)."""
        # 25 hours, 30 minutes, 45 seconds
        assert parse_time_to_seconds("25:30:45") == 91845
        assert format_time(91845) == "25:30:45"
    
    def test_single_digit_components(self):
        """Test single digit time components."""
        assert parse_time_to_seconds("1:2:3") == 3723
        assert parse_time_to_seconds("5:30") == 330


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
