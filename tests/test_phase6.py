"""
Tests for Phase 6 - Document Generator: Guided Form, Legal Notice Template, Word/PDF Builders, and Preview.
"""
import os
import pytest
from datetime import date, timedelta
from app import create_app, db
from app.models import User, DocumentTemplate, Order
from app.catalogue import seed_initial_templates
from app.generator.forms import ChequeBounceNoticeForm
from app.generator.template_text import format_cheque_bounce_notice
from app.generator.docx_builder import build_cheque_bounce_docx
from app.generator.pdf_builder import build_cheque_bounce_pdf


@pytest.fixture
def app(tmp_path):
    """Create test application with in-memory DB and isolated temp storage."""
    docs_folder = str(tmp_path / "test_generated_docs")
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
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            full_name='Rajesh Verma',
            email='rajesh@example.com'
        )
        user.set_password('TestPass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def other_user(app):
    with app.app_context():
        user = User(
            full_name='Other Person',
            email='other@example.com'
        )
        user.set_password('TestPass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def valid_notice_data():
    today = date.today()
    return {
        'notice_date': today,
        'payee_name': 'Rajesh Verma',
        'payee_address': 'Flat 201, Green View Apts, Bengaluru 560038',
        'payee_phone': '9876543210',
        'advocate_name': '',
        'advocate_address': '',
        'drawer_name': 'Anil Sharma',
        'drawer_address': 'Shop 12, Main Market, Bengaluru 560001',
        'cheque_number': '123456',
        'cheque_date': today - timedelta(days=15),
        'cheque_amount': 50000,
        'cheque_amount_words': 'Rupees Fifty Thousand Only',
        'bank_name': 'State Bank of India',
        'bank_branch': 'M.G. Road Branch, Bengaluru',
        'memo_date': today - timedelta(days=5),
        'dishonour_reason': 'Funds Insufficient',
        'transaction_details': 'Against friendly loan advanced on 1st October 2026 for business purposes.',
    }


# --- Form Validation Tests ---

def test_form_valid_data(app, valid_notice_data):
    """Test that complete, valid data satisfies form validation."""
    with app.test_request_context():
        form = ChequeBounceNoticeForm(data=valid_notice_data)
        assert form.validate() is True


def test_form_missing_required_fields(app):
    """Test that missing required fields fail form validation."""
    with app.test_request_context():
        form = ChequeBounceNoticeForm(data={})
        assert form.validate() is False
        assert 'payee_name' in form.errors
        assert 'drawer_name' in form.errors
        assert 'cheque_number' in form.errors
        assert 'cheque_amount' in form.errors


def test_form_future_memo_date_rejected(app, valid_notice_data):
    """Test that memo date in the future fails validation."""
    with app.test_request_context():
        bad_data = valid_notice_data.copy()
        bad_data['memo_date'] = date.today() + timedelta(days=5)
        form = ChequeBounceNoticeForm(data=bad_data)
        assert form.validate() is False
        assert 'memo_date' in form.errors


def test_form_cheque_date_after_memo_date_rejected(app, valid_notice_data):
    """Test that cheque date later than memo date fails validation."""
    with app.test_request_context():
        bad_data = valid_notice_data.copy()
        bad_data['cheque_date'] = date.today()
        bad_data['memo_date'] = date.today() - timedelta(days=5)
        form = ChequeBounceNoticeForm(data=bad_data)
        assert form.validate() is False
        assert 'cheque_date' in form.errors


# --- Template Text Formatting Tests ---

def test_format_cheque_bounce_notice(valid_notice_data):
    """Verify that formatted notice includes all mandatory statutory legal ingredients."""
    formatted = format_cheque_bounce_notice(valid_notice_data)
    assert 'SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881' in formatted['subject']
    assert '15 (fifteen) days' in formatted['full_text']
    assert 'Funds Insufficient' in formatted['full_text']
    assert '123456' in formatted['full_text']
    assert '₹50,000' in formatted['amount_formatted']


# --- Word (.docx) & PDF (.pdf) Builders Tests ---

def test_build_cheque_bounce_docx(tmp_path, valid_notice_data):
    """Test that python-docx compiles a valid .docx file."""
    output_file = str(tmp_path / "test_notice.docx")
    formatted = format_cheque_bounce_notice(valid_notice_data)
    result_path = build_cheque_bounce_docx(formatted, output_file)

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 1000  # Non-empty binary docx file


def test_build_cheque_bounce_pdf(tmp_path, valid_notice_data):
    """Test that ReportLab compiles a valid .pdf file."""
    output_file = str(tmp_path / "test_notice.pdf")
    formatted = format_cheque_bounce_notice(valid_notice_data)
    result_path = build_cheque_bounce_pdf(formatted, output_file)

    assert os.path.exists(result_path)
    assert os.path.getsize(result_path) > 1000

    # Verify standard PDF header magic bytes
    with open(result_path, 'rb') as f:
        header = f.read(5)
        assert header == b'%PDF-'


# --- Generator Routes & Access Control Tests ---

def test_generator_form_requires_login(client):
    """Unauthenticated users are redirected to login."""
    response = client.get('/generator/cheque-bounce-notice', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page' in response.data


def test_generator_post_creates_order_and_files(client, test_user, valid_notice_data):
    """Authenticated user submitting valid form creates an Order and redirects to preview."""
    # Log in
    client.post('/auth/login', data={'email': 'rajesh@example.com', 'password': 'TestPass123'})

    response = client.post(
        '/generator/cheque-bounce-notice',
        data=valid_notice_data,
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Draft Preview' in response.data
    assert b'ORD-' in response.data
    assert b'Section 138 of the Negotiable Instruments Act' in response.data

    # Check database
    order = Order.query.filter_by(user_id=test_user).first()
    assert order is not None
    assert order.status == 'pending'
    assert order.amount == 199
    assert order.docx_filename.endswith('.docx')
    assert order.pdf_filename.endswith('.pdf')


def test_preview_unauthorized_user_blocked(client, app, test_user, other_user, valid_notice_data):
    """A user cannot access another user's draft preview (403 Forbidden)."""
    with app.app_context():
        order = Order(
            order_number='ORD-TEST-403',
            user_id=test_user,
            document_template_id=1,
            amount=199,
            status='pending'
        )
        order.form_data = valid_notice_data
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    # Log in as other_user
    client.post('/auth/login', data={'email': 'other@example.com', 'password': 'TestPass123'})

    # Attempt to view test_user's draft preview
    response = client.get(f'/generator/preview/{order_id}')
    assert response.status_code == 403


def test_download_draft(client, test_user, valid_notice_data):
    """Authenticated owner can download Word and PDF files."""
    # Log in
    client.post('/auth/login', data={'email': 'rajesh@example.com', 'password': 'TestPass123'})

    # Submit form
    client.post('/generator/cheque-bounce-notice', data=valid_notice_data)
    order = Order.query.filter_by(user_id=test_user).first()

    # Download docx
    docx_resp = client.get(f'/generator/download/{order.id}/docx')
    assert docx_resp.status_code == 200
    assert 'wordprocessingml.document' in docx_resp.content_type

    # Download pdf
    pdf_resp = client.get(f'/generator/download/{order.id}/pdf')
    assert pdf_resp.status_code == 200
    assert 'application/pdf' in pdf_resp.content_type


def test_format_cheque_bounce_notice_resilient_to_missing_data():
    """Verify format_cheque_bounce_notice safely handles empty or partial input data."""
    # Test completely empty dict
    formatted_empty = format_cheque_bounce_notice({})
    assert 'SECTION 138' in formatted_empty['subject']
    assert formatted_empty['amount_formatted'] == '₹[Amount]'
    assert '[Drawer / Noticee Name]' in formatted_empty['recipient_block']

    # Test None
    formatted_none = format_cheque_bounce_notice(None)
    assert 'SECTION 138' in formatted_none['subject']

    # Test numeric string cheque amount
    formatted_str = format_cheque_bounce_notice({'cheque_amount': '75000'})
    assert '₹75,000' in formatted_str['amount_formatted']


def test_preview_and_download_with_empty_order_form_data(client, app, test_user):
    """Orders with empty or missing form_data render in preview and can be downloaded."""
    with app.app_context():
        order = Order(
            order_number='ORD-EMPTY-DATA-1',
            user_id=test_user,
            document_template_id=1,
            amount=199,
            status='paid',
            form_data_json=None,
            docx_filename=None,
            pdf_filename=None
        )
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    # Log in
    client.post('/auth/login', data={'email': 'rajesh@example.com', 'password': 'TestPass123'})

    # Preview
    preview_resp = client.get(f'/generator/preview/{order_id}')
    assert preview_resp.status_code == 200
    assert b'ORD-EMPTY-DATA-1' in preview_resp.data

    # On-demand docx download
    docx_resp = client.get(f'/generator/download/{order_id}/docx')
    assert docx_resp.status_code == 200
    assert 'wordprocessingml.document' in docx_resp.content_type

    # On-demand pdf download
    pdf_resp = client.get(f'/generator/download/{order_id}/pdf')
    assert pdf_resp.status_code == 200
    assert 'application/pdf' in pdf_resp.content_type

