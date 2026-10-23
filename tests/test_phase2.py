"""Tests for Phase 2 - Website foundation pages."""
import pytest
from app import create_app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    with app.test_client() as client:
        yield client


# --- Home Page ---

def test_home_page_loads(client):
    """Home page returns 200."""
    response = client.get('/')
    assert response.status_code == 200


def test_home_page_has_nav_links(client):
    """Home page contains navigation to Documents and About."""
    response = client.get('/')
    assert b'Documents' in response.data
    assert b'About' in response.data


def test_home_page_shows_featured_document(client):
    """Home page displays the featured cheque bounce notice."""
    response = client.get('/')
    assert b'Cheque Bounce Notice' in response.data


def test_home_page_has_disclaimer(client):
    """Home page includes the legal disclaimer."""
    response = client.get('/')
    assert b'does not constitute legal advice' in response.data


# --- Document List Page ---

def test_document_list_loads(client):
    """Document list page returns 200."""
    response = client.get('/documents')
    assert response.status_code == 200


def test_document_list_shows_categories(client):
    """Document list page shows the Legal Notices category."""
    response = client.get('/documents')
    assert b'Legal Notices' in response.data


def test_document_list_shows_documents(client):
    """Document list page shows the cheque bounce notice."""
    response = client.get('/documents')
    assert b'Cheque Bounce Notice' in response.data


def test_document_list_shows_price(client):
    """Document list page shows the price."""
    response = client.get('/documents')
    # The rupee symbol ₹ is multi-byte in UTF-8
    assert '₹199'.encode('utf-8') in response.data


# --- Document Detail Page ---

def test_document_detail_loads(client):
    """Document detail page returns 200 for a valid document."""
    response = client.get('/documents/cheque-bounce-notice')
    assert response.status_code == 200


def test_document_detail_shows_title(client):
    """Document detail page shows the document title."""
    response = client.get('/documents/cheque-bounce-notice')
    assert b'Cheque Bounce Notice' in response.data


def test_document_detail_shows_description(client):
    """Document detail page shows the long description."""
    response = client.get('/documents/cheque-bounce-notice')
    assert b'Negotiable Instruments Act' in response.data


def test_document_detail_shows_requirements(client):
    """Document detail page lists the information needed."""
    response = client.get('/documents/cheque-bounce-notice')
    assert b'Information You Will Need' in response.data


def test_document_detail_shows_important_notes(client):
    """Document detail page shows the important legal notes."""
    response = client.get('/documents/cheque-bounce-notice')
    assert b'Important Notes' in response.data


def test_document_detail_invalid_id_returns_404(client):
    """Requesting a non-existent document returns 404."""
    response = client.get('/documents/non-existent-document')
    assert response.status_code == 404


def test_404_page_has_go_home(client):
    """Custom 404 page includes a link back to home."""
    response = client.get('/documents/non-existent-document')
    assert b'Go Home' in response.data


# --- About Page ---

def test_about_page_loads(client):
    """About page returns 200."""
    response = client.get('/about')
    assert response.status_code == 200


def test_about_page_has_mission(client):
    """About page describes the mission."""
    response = client.get('/about')
    assert b'Our Mission' in response.data


def test_about_page_has_disclaimer(client):
    """About page clarifies what the service does NOT do."""
    response = client.get('/about')
    assert b'do not provide legal advice' in response.data


# --- Contact Page Tests ---

def test_contact_page_loads(client):
    """Contact page returns 200."""
    response = client.get('/contact')
    assert response.status_code == 200
    assert b'Contact Us' in response.data
    assert b'Send Us a Message' in response.data
    assert b'support@nyayadraft.in' in response.data


def test_contact_form_submission(client):
    """Submitting contact inquiry form redirects and flashes success."""
    response = client.post('/contact', data={
        'name': 'Rahul Verma',
        'email': 'rahul@example.com',
        'subject': 'General Inquiry',
        'message': 'Need assistance with statutory cheque bounce notice format.'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Thank you for reaching out' in response.data


# --- FAQs & Policies Tests ---

def test_document_detail_shows_faqs(client):
    """Document detail page renders frequently asked questions accordion."""
    response = client.get('/documents/cheque-bounce-notice')
    assert response.status_code == 200
    assert b'Frequently Asked Questions' in response.data
    assert b'What is the mandatory 15-day notice period' in response.data


def test_policies_page_loads(client):
    """Policies page loads and contains all 4 statutory governance sections."""
    response = client.get('/policies')
    assert response.status_code == 200
    assert b'Legal Disclaimer' in response.data
    assert b'Privacy Policy' in response.data
    assert b'Terms of Service' in response.data
    assert b'Refund Policy' in response.data


def test_individual_policy_routes_load(client):
    """Direct routes for privacy, terms, refunds, and disclaimer return 200."""
    for endpoint in ['/privacy', '/terms', '/refunds', '/disclaimer']:
        response = client.get(endpoint)
        assert response.status_code == 200
