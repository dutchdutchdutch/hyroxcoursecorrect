"""
Test configuration and fixtures.

Shared pytest configuration for all test modules.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "component: mark test as a component test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
