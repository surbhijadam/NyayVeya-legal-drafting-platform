"""Tests for Phase 1 - Basic application setup."""
import pytest
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home_page_loads(client):
    """Test that the home page returns a 200 status code."""
    response = client.get('/')
    assert response.status_code == 200


def test_home_page_contains_brand(client):
    """Test that the home page contains our brand name."""
    response = client.get('/')
    assert b'LegalDraft India' in response.data


def test_home_page_contains_disclaimer(client):
    """Test that the home page includes the legal disclaimer."""
    response = client.get('/')
    assert b'does not constitute legal advice' in response.data
