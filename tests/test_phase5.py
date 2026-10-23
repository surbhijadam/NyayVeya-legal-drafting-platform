"""
Tests for Phase 5 - Legal Document Catalogue: Categories, Cards, Requirements, and Publication Status.
"""
import pytest
from app import create_app
from app.catalogue import (
    get_all_documents,
    get_document_by_id,
    get_all_categories,
    get_documents_by_category,
)


@pytest.fixture
def client():
    """Create test client for app."""
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    with app.test_client() as client:
        yield client


# --- Catalogue Data & Structure Tests ---

def test_catalogue_categories_structure():
    """Verify core categories: notices, agreements, affidavits exist."""
    categories = get_all_categories()
    assert 'notices' in categories
    assert 'agreements' in categories
    assert 'affidavits' in categories


def test_cheque_bounce_notice_is_active():
    """Verify Cheque Bounce Notice is marked 'active' for the first complete workflow."""
    doc = get_document_by_id('cheque-bounce-notice')
    assert doc is not None
    assert doc['status'] == 'active'
    assert doc['price'] == 199
    assert doc['category'] == 'notices'


def test_upcoming_templates_are_coming_soon():
    """Verify non-primary templates are flagged 'coming_soon' until reviewed."""
    agreements = get_documents_by_category('agreements')
    assert len(agreements) > 0
    for doc in agreements:
        assert doc['status'] == 'coming_soon'


# --- Catalogue UI & Rendering Tests ---

def test_document_catalogue_renders_categories(client):
    """Document listing page displays all main categories."""
    response = client.get('/documents')
    assert response.status_code == 200
    assert b'Legal Notices' in response.data
    assert b'Agreements &amp; Contracts' in response.data or b'Agreements & Contracts' in response.data
    assert b'Affidavits &amp; Declarations' in response.data or b'Affidavits & Declarations' in response.data


def test_document_catalogue_has_search_and_filter_controls(client):
    """Catalogue page includes client search input and category filter buttons."""
    response = client.get('/documents')
    assert b'id="docSearchInput"' in response.data
    assert b'data-category="all"' in response.data
    assert b'data-category="notices"' in response.data


def test_cheque_bounce_detail_has_statutory_warning(client):
    """Cheque bounce detail page clearly flags the 30-day statutory notice limitation period."""
    response = client.get('/documents/cheque-bounce-notice')
    assert response.status_code == 200
    assert b'Strict 30-Day Statutory Limitation Period' in response.data
    assert b'Section 138(b)' in response.data


def test_cheque_bounce_detail_shows_deliverables_and_requirements(client):
    """Detail page outlines deliverables (Word + PDF) and required information."""
    response = client.get('/documents/cheque-bounce-notice')
    assert b'Deliverables Included' in response.data
    assert b'Word' in response.data
    assert b'PDF' in response.data
    assert b'Information You Will Need' in response.data
    assert b'Cheque Number' in response.data


def test_active_template_shows_draft_button(client):
    """Active template provides clear call-to-action button to begin drafting."""
    response = client.get('/documents/cheque-bounce-notice')
    assert b'Start Drafting' in response.data or b'Log in to Draft' in response.data
