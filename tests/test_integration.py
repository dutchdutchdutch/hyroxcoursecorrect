"""
Integration tests for Flask web application.

Tests API endpoints and web interface functionality.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
# Add web directory so 'from utils import ...' works in app.py
sys.path.insert(0, str(Path(__file__).parent.parent / 'web'))

from web.app import app


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestFlaskRoutes:
    """Test Flask application routes."""
    
    def test_index_page_loads(self, client):
        """Test that index page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'HYROX Course Correct' in response.data
    
    def test_analysis_page_loads(self, client):
        """Test that analysis page loads successfully."""
        response = client.get('/analysis')
        assert response.status_code == 200
    
    def test_venues_api(self, client):
        """Test venues API endpoint."""
        response = client.get('/venues')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) >= 10  # Should have at least 10 venues (currently 44)
        
        # Check structure of first venue (API uses correction, not handicap)
        first_venue = data[0]
        assert 'name' in first_venue
        assert 'correction' in first_venue
        assert 'correction_display' in first_venue


class TestTimeConversion:
    """Test time conversion API."""
    
    def test_convert_valid_time(self, client):
        """Test converting a valid time with gender."""
        response = client.post('/convert', json={
            'finish_time': '01:30:00',
            'from_venue': '2025 Anaheim',
            'to_venue': '2025 London Excel',
            'gender': 'M'  # Gender is now required
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'original_time' in data
        assert 'converted_time' in data
        assert 'from_venue' in data
        assert 'to_venue' in data
        assert data['original_time'] == '01:30:00'
    
    def test_convert_to_normalized(self, client):
        """Test converting to normalized time."""
        response = client.post('/convert', json={
            'finish_time': '01:30:00',
            'from_venue': '2025 Anaheim',
            'to_venue': 'normalized',
            'gender': 'M'  # Gender is now required
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'Normalized' in data['to_venue']
    
    def test_convert_invalid_time_format(self, client):
        """Test converting with invalid time format."""
        response = client.post('/convert', json={
            'finish_time': 'invalid',
            'from_venue': '2025 Anaheim',
            'to_venue': '2025 London Excel',
            'gender': 'M'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_convert_unknown_venue(self, client):
        """Test converting with unknown venue."""
        response = client.post('/convert', json={
            'finish_time': '01:30:00',
            'from_venue': 'Unknown Venue',
            'to_venue': '2025 London Excel',
            'gender': 'M'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_convert_missing_gender(self, client):
        """Test converting without gender returns error."""
        response = client.post('/convert', json={
            'finish_time': '01:30:00',
            'from_venue': '2025 Anaheim',
            'to_venue': '2025 London Excel'
            # No gender provided
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestVenueCorrections:
    """Test venue correction loading and validation."""
    
    def test_all_venues_have_corrections(self, client):
        """Test that all venues have correction factors."""
        response = client.get('/venues')
        data = response.get_json()
        
        for venue in data:
            # API uses 'correction' field (seconds offset)
            assert 'correction' in venue
            # Corrections are additive offsets in seconds (can be negative or positive)
            assert isinstance(venue['correction'], (int, float))
    
    def test_baseline_venue_exists(self, client):
        """Test that baseline venue (correction = 0.0) exists or identify reference."""
        response = client.get('/venues')
        data = response.get_json()
        
        # Look for baseline venue marked in label
        baseline_venues = [v for v in data if 'Baseline' in v.get('correction_label', '')]
        # Should have at least one baseline/reference venue
        assert len(baseline_venues) >= 1
    
    def test_venues_sorted_by_correction(self, client):
        """Test that venues are sorted by correction factor."""
        response = client.get('/venues')
        data = response.get_json()
        
        corrections = [v['correction'] for v in data]
        assert corrections == sorted(corrections)  # Should be sorted ascending


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

