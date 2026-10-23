"""
Unit and integration tests for standard legal drafting of all documents:
Rent Agreement, Affidavit, NDA, General Legal Notice, Business Agreement,
Formal Application, and Declaration Letter.
"""
import os
import pytest
from app import create_app, db
from app.models import User, DocumentTemplate, Order
from app.catalogue import seed_initial_templates


@pytest.fixture
def app_and_client(tmp_path):
    """Create app and test client with in-memory DB and isolated temp storage."""
    docs_folder = str(tmp_path / "test_docs")
    os.makedirs(docs_folder, exist_ok=True)

    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'GENERATED_DOCUMENTS_FOLDER': docs_folder,
    })

    with app.app_context():
        db.create_all()
        seed_initial_templates()

        user = User(
            email='rajesh@example.com',
            full_name='Rajesh Kumar'
        )
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with app.test_client() as client:
        # Log in
        client.post('/auth/login', data={
            'email': 'rajesh@example.com',
            'password': 'Password123!'
        })
        yield app, client, user_id


def test_rent_agreement_form_loads(app_and_client):
    """GET /generator/draft/rent loads guided form with pre-filled defaults."""
    app, client, user_id = app_and_client
    response = client.get('/generator/draft/rent')
    assert response.status_code == 200
    assert b'Rent Agreement' in response.data
    assert b'First Party (Landlord / Lessor)' in response.data
    assert b'Second Party (Tenant / Lessee)' in response.data
    assert b'Monthly Rent' in response.data
    assert b'Rajesh Kumar' in response.data


def test_affidavit_form_loads(app_and_client):
    """GET /generator/draft/affidavit loads deponent-focused form."""
    app, client, user_id = app_and_client
    response = client.get('/generator/draft/affidavit')
    assert response.status_code == 200
    assert b'Affidavit' in response.data
    assert b'Deponent' in response.data
    assert b'Sworn Statements' in response.data


def test_rent_agreement_submission_and_preview(app_and_client):
    """POST /generator/draft/rent creates order, docx, pdf, and redirects to preview."""
    app, client, user_id = app_and_client

    post_data = {
        'document_date': '2026-10-23',
        'city': 'Bengaluru',
        'first_party_name': 'Rajesh Kumar',
        'first_party_details': 'S/o Ramesh Kumar, 45 Indiranagar, Bengaluru - 560038',
        'second_party_name': 'Amit Verma',
        'second_party_details': 'S/o Suresh Verma, 12 Koramangala, Bengaluru - 560034',
        'subject_purpose': 'Flat No. 402, Palm Breeze Apartments, Indiranagar, Bengaluru',
        'amount': 25000,
        'duration_period': '11 Months',
        'key_terms': (
            '1. Monthly rent payable on or before 5th of each month.\n'
            '2. Interest-free security deposit of Rs 1,00,000 paid by tenant.\n'
            '3. Notice period shall be 30 days.'
        )
    }

    response = client.post('/generator/draft/rent', data=post_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Review your statutory draft' in response.data
    assert b'RESIDENTIAL LEASE / RENT AGREEMENT' in response.data
    assert b'Rajesh Kumar' in response.data
    assert b'Amit Verma' in response.data
    assert b'25,000' in response.data

    with app.app_context():
        order = Order.query.filter_by(user_id=user_id).first()
        assert order is not None
        assert order.status == 'pending'
        assert order.docx_filename is not None
        assert order.pdf_filename is not None
        assert order.amount == 249  # Rent Agreement price


def test_nda_draft_submission_and_preview(app_and_client):
    """POST /generator/draft/nda creates order and produces valid preview."""
    app, client, user_id = app_and_client

    post_data = {
        'document_date': '2026-10-23',
        'city': 'Mumbai',
        'first_party_name': 'Alpha Tech Pvt Ltd',
        'first_party_details': 'Registered office at BKC, Bandra East, Mumbai - 400051',
        'second_party_name': 'Beta Solutions LLP',
        'second_party_details': 'Registered office at Andheri East, Mumbai - 400069',
        'subject_purpose': 'Evaluation of AI legal tech integration and algorithms',
        'amount': 0,
        'duration_period': '2 Years',
        'key_terms': '1. Both parties agree to protect source code and algorithms.\n2. Disclosure strictly on need-to-know basis.'
    }

    response = client.post('/generator/draft/nda', data=post_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'MUTUAL NON-DISCLOSURE AGREEMENT' in response.data
    assert b'Alpha Tech' in response.data
    assert b'Beta Solutions' in response.data


def test_affidavit_draft_submission_and_preview(app_and_client):
    """POST /generator/draft/affidavit creates order and produces sworn jurat preview."""
    app, client, user_id = app_and_client

    post_data = {
        'document_date': '2026-10-23',
        'city': 'Pune',
        'first_party_name': 'Rajesh Kumar',
        'first_party_details': 'Age 35 years, S/o Ramesh Kumar, Shivajinagar, Pune - 411005',
        'second_party_name': 'Notary Public',
        'second_party_details': 'District Court, Shivajinagar, Pune',
        'subject_purpose': 'Name Clarification and Address Verification',
        'amount': 0,
        'duration_period': 'Permanent',
        'key_terms': (
            '1. That my name is Rajesh Kumar as per my Aadhaar and Passport.\n'
            '2. That Rajesh K. in bank records refers to one and the same person.'
        )
    }

    response = client.post('/generator/draft/affidavit', data=post_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'GENERAL AFFIDAVIT / SWORN DECLARATION' in response.data
    assert b'DEPONENT' in response.data
    assert b'VERIFICATION:' in response.data


def test_download_standard_draft(app_and_client):
    """Paid order allows Word and PDF downloads."""
    app, client, user_id = app_and_client

    with app.app_context():
        tmpl = DocumentTemplate.query.filter_by(slug='rent').first()
        order = Order(
            order_number='ORD-TEST-RENT-001',
            user_id=user_id,
            document_template_id=tmpl.id,
            amount=tmpl.price,
            status='paid',
            form_data={
                'first_party_name': 'Rajesh Kumar',
                'first_party_details': 'Indiranagar, Bengaluru',
                'second_party_name': 'Amit Verma',
                'second_party_details': 'Koramangala, Bengaluru',
                'subject_purpose': 'Apartment 402, Bengaluru',
                'amount': 20000,
                'city': 'Bengaluru',
                'key_terms': 'Standard tenancy covenants'
            }
        )
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    # Download docx
    res_docx = client.get(f'/generator/download/{order_id}/docx')
    assert res_docx.status_code == 200
    assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in res_docx.content_type

    # Download pdf
    res_pdf = client.get(f'/generator/download/{order_id}/pdf')
    assert res_pdf.status_code == 200
    assert res_pdf.content_type == 'application/pdf'
