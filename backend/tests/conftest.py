"""Pytest configuration and fixtures for unit tests."""
import pytest
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture(scope='session')
def test_config():
    """Global test configuration."""
    return {
        'test_mode': True,
        'db_path': ':memory:',  # Use in-memory DB for tests
    }


@pytest.fixture
def mock_datetime():
    """Mock datetime for time-based tests."""
    from datetime import datetime
    return datetime(2026, 1, 15, 12, 0, 0)
