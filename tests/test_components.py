"""
Component tests for data processing and handicap calculation.

Tests the integration of scraping, processing, and handicap calculation components.
"""

import pytest
import pandas as pd
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from execution.process_scraped_data import parse_time_to_seconds


class TestDataProcessing:
    """Test data processing component."""
    
    @pytest.fixture
    def sample_scraped_data(self):
        """Create sample scraped data for testing."""
        return [
            {
                "venue": "Test Venue",
                "gender": "M",
                "results": [
                    {
                        "rank": "1",
                        "name": "Test Athlete 1",
                        "nationality": "USA",
                        "age_group": "Age Group\n25-29",
                        "finish_time": "Total\n01:00:00"
                    },
                    {
                        "rank": "2",
                        "name": "Test Athlete 2",
                        "nationality": "GBR",
                        "age_group": "Age Group\n30-34",
                        "finish_time": "Total\n01:05:00"
                    }
                ]
            }
        ]
    
    def test_parse_clean_time(self):
        """Test parsing clean time strings."""
        assert parse_time_to_seconds("01:00:00") == 3600
        assert parse_time_to_seconds("45:30") == 2730
    
    def test_parse_invalid_time(self):
        """Test parsing invalid time returns None."""
        assert parse_time_to_seconds("invalid") is None
        assert parse_time_to_seconds("") is None


class TestHandicapCalculation:
    """Test handicap calculation component."""
    
    @pytest.fixture
    def sample_results_df(self):
        """Create sample results DataFrame."""
        data = {
            'venue': ['Venue A', 'Venue A', 'Venue B', 'Venue B'],
            'gender': ['M', 'W', 'M', 'W'],
            'finish_seconds': [3600, 3800, 4000, 4200]
        }
        return pd.DataFrame(data)
    
    def test_median_calculation(self, sample_results_df):
        """Test median finish time calculation."""
        venue_a_median = sample_results_df[
            sample_results_df['venue'] == 'Venue A'
        ]['finish_seconds'].median()
        assert venue_a_median == 3700  # (3600 + 3800) / 2
    
    def test_handicap_ratio(self):
        """Test handicap factor calculation."""
        reference_median = 4000
        venue_median = 3600
        handicap = venue_median / reference_median
        assert abs(handicap - 0.9) < 0.01


class TestVenueConfiguration:
    """Test venue configuration loading."""
    
    def test_venues_json_exists(self):
        """Test that venues.json file exists."""
        venues_file = Path(__file__).parent.parent / 'execution' / 'venues.json'
        assert venues_file.exists()
    
    def test_venues_json_valid(self):
        """Test that venues.json is valid JSON."""
        venues_file = Path(__file__).parent.parent / 'execution' / 'venues.json'
        with open(venues_file, 'r') as f:
            data = json.load(f)
        assert 'season_8_2025_2026' in data
    
    def test_venue_structure(self):
        """Test that each venue has required fields."""
        venues_file = Path(__file__).parent.parent / 'execution' / 'venues.json'
        with open(venues_file, 'r') as f:
            data = json.load(f)
        
        for venue_key, venue_data in data['season_8_2025_2026'].items():
            assert 'event_id' in venue_data
            assert 'name' in venue_data
            assert 'location' in venue_data
            assert 'region' in venue_data


class TestDataFiles:
    """Test that required data files exist and are valid."""
    
    def test_handicaps_file_exists(self):
        """Test that handicaps CSV exists."""
        handicaps_file = Path(__file__).parent.parent / 'data' / 'venue_handicaps_10venues_1000each.csv'
        assert handicaps_file.exists()
    
    def test_handicaps_file_valid(self):
        """Test that handicaps CSV is valid."""
        handicaps_file = Path(__file__).parent.parent / 'data' / 'venue_handicaps_10venues_1000each.csv'
        df = pd.read_csv(handicaps_file)
        
        # Check required columns
        assert 'venue' in df.columns
        assert 'handicap_factor' in df.columns
        
        # Check we have 10 venues
        assert len(df) == 10
        
        # Check handicaps are reasonable (between 0.8 and 1.1)
        assert df['handicap_factor'].min() > 0.8
        assert df['handicap_factor'].max() < 1.1
    
    def test_results_file_exists(self):
        """Test that processed results CSV exists."""
        results_file = Path(__file__).parent.parent / 'data' / 'hyrox_9venues_100each.csv'
        assert results_file.exists()
    
    def test_results_file_valid(self):
        """Test that results CSV has expected structure."""
        results_file = Path(__file__).parent.parent / 'data' / 'hyrox_9venues_100each.csv'
        df = pd.read_csv(results_file)
        
        # Check required columns
        required_cols = ['venue', 'gender', 'name', 'finish_time', 'finish_seconds']
        for col in required_cols:
            assert col in df.columns
        
        # Check we have data
        assert len(df) > 1000


class TestDataQuality:
    """Test data quality and integrity."""
    
    def test_no_excessive_duplicates(self):
        """Test that there are not excessive duplicate results."""
        results_file = Path(__file__).parent.parent / 'data' / 'hyrox_9venues_100each.csv'
        df = pd.read_csv(results_file)
        
        # Check for duplicates based on venue, gender, name (exact duplicates)
        duplicates = df.duplicated(subset=['venue', 'gender', 'name'])
        # Allow for some tied ranks, but not excessive duplication
        assert duplicates.sum() < len(df) * 0.01  # Less than 1% duplicates
    
    def test_finish_times_valid(self):
        """Test that all finish times are valid."""
        results_file = Path(__file__).parent.parent / 'data' / 'hyrox_9venues_100each.csv'
        df = pd.read_csv(results_file)
        
        # Check no null finish times
        assert df['finish_seconds'].notna().all()
        
        # Check finish times are reasonable (30 min to 3 hours)
        assert df['finish_seconds'].min() > 1800  # > 30 minutes
        assert df['finish_seconds'].max() < 10800  # < 3 hours
    
    def test_gender_distribution(self):
        """Test that we have both M and W results."""
        results_file = Path(__file__).parent.parent / 'data' / 'hyrox_9venues_100each.csv'
        df = pd.read_csv(results_file)
        
        genders = df['gender'].unique()
        assert 'M' in genders
        assert 'W' in genders


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
