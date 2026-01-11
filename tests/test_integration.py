"""
Integration tests for Flask web application.

Tests API endpoints and web interface functionality.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        assert len(data) == 10  # Should have 10 venues
        
        # Check structure of first venue
        first_venue = data[0]
        assert 'name' in first_venue
        assert 'handicap' in first_venue
        assert 'difficulty' in first_venue


class TestTimeConversion:
    """Test time conversion API."""
    
    def test_convert_valid_time(self, client):
        """Test converting a valid time."""
        response = client.post('/convert', json={
            'finish_time': '01:30:00',
            'from_venue': 'Anaheim 2025',
            'to_venue': 'London Excel 2025'
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
            'from_venue': 'Anaheim 2025',
            'to_venue': 'normalized'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'Normalized' in data['to_venue']
    
    def test_convert_invalid_time_format(self, client):
        """Test converting with invalid time format."""
        response = client.post('/convert', json={
            'finish_time': 'invalid',
            'from_venue': 'Anaheim 2025',
            'to_venue': 'London Excel 2025'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_convert_unknown_venue(self, client):
        """Test converting with unknown venue."""
        response = client.post('/convert', json={
            'finish_time': '01:30:00',
            'from_venue': 'Unknown Venue',
            'to_venue': 'London Excel 2025'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data


class TestVenueHandicaps:
    """Test venue handicap loading and validation."""
    
    def test_all_venues_have_handicaps(self, client):
        """Test that all venues have handicap factors."""
        response = client.get('/venues')
        data = response.get_json()
        
        for venue in data:
            assert venue['handicap'] > 0
            assert venue['handicap'] < 2  # Reasonable range
    
    def test_reference_venue_exists(self, client):
        """Test that reference venue (handicap = 1.0) exists."""
        response = client.get('/venues')
        data = response.get_json()
        
        reference_venues = [v for v in data if abs(v['handicap'] - 1.0) < 0.01]
        assert len(reference_venues) >= 1  # At least one reference venue
    
    def test_venues_sorted_by_handicap(self, client):
        """Test that venues are sorted by handicap factor."""
        response = client.get('/venues')
        data = response.get_json()
        
        handicaps = [v['handicap'] for v in data]
        assert handicaps == sorted(handicaps)  # Should be sorted ascending


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
