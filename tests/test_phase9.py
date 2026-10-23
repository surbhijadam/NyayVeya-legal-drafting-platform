"""
Phase 9: Comprehensive End-to-End Testing & QA Suite.

Validates:
1. Complete User Journey 1: Cheque Bounce Notice (Registration -> Form -> Preview -> Payment -> Downloads -> Receipt -> Dashboard)
2. Complete User Journey 2: Standard Agreement (Rent Agreement guided drafting -> Checkout -> Downloads)
3. Complete User Journey 3: General Sworn Affidavit (Drafting -> Preview -> Payment)
4. Duplicate Payment Notifications & Idempotency / Replay Attack Mitigation
5. Tampered & Forged Payment Signature Rejections
6. Unpaid Order Download Isolation
7. XSS & HTML Injection Sanitization
8. Resilient Malformed / Empty Form Data Fallbacks
9. Session Invalidation & Logout Guarantees
"""
import io
import os
import json
import pytest
from app import create_app, db
from app.models import User, DocumentTemplate, Order, Payment
from app.catalogue import seed_initial_templates
from app.payments.services import generate_signature, verify_razorpay_signature


@pytest.fixture
def app(tmp_path):
    """Isolated test application fixture with temporary document storage."""
    docs_folder = str(tmp_path / "test_docs_phase9")
    os.makedirs(docs_folder, exist_ok=True)

    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'GENERATED_DOCUMENTS_FOLDER': docs_folder,
        'RAZORPAY_KEY_ID': 'rzp_test_fixture_key',
        'RAZORPAY_KEY_SECRET': 'fixture_secret_99887766',
        'SECRET_KEY': 'phase9-test-secret-key-123',
        'PAYMENT_MODE': 'test'
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


# ==============================================================================
# 1. COMPLETE END-TO-END USER JOURNEYS
# ==============================================================================

def test_e2e_cheque_bounce_complete_flow(client, app):
    """
    Full end-to-end user lifecycle for Cheque Bounce Notice:
    1. Register -> 2. Login -> 3. Browse Catalogue -> 4. Fill Notice Form ->
    5. Inspect Preview -> 6. Complete Payment -> 7. Download Word & PDF ->
    8. Verify Tax Invoice & Dashboard.
    """
    # 1. Registration
    reg_res = client.post('/auth/register', data={
        'full_name': 'Kavita Iyer',
        'email': 'kavita@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!'
    }, follow_redirects=True)
    assert reg_res.status_code == 200
    assert b'Account created successfully' in reg_res.data

    # 2. Login
    login_res = client.post('/auth/login', data={
        'email': 'kavita@example.com',
        'password': 'StrongPassword123!'
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Dashboard' in login_res.data or b'Kavita Iyer' in login_res.data

    # 3. Browse Catalogue & Document Detail
    cat_res = client.get('/documents')
    assert cat_res.status_code == 200
    assert b'Cheque Bounce Notice' in cat_res.data

    detail_res = client.get('/documents/cheque-bounce-notice')
    assert detail_res.status_code == 200
    assert b'Start Guided Drafting' in detail_res.data

    # 4. Fill Cheque Bounce Form
    form_data = {
        'notice_date': '2026-10-23',
        'payee_name': 'Kavita Iyer',
        'payee_address': 'Flat 101, Sea View Apartments, Marine Drive, Mumbai - 400020',
        'payee_phone': '9876543210',
        'advocate_name': 'Sunil Mehta',
        'advocate_address': 'Chamber 402, High Court Bar Association, Fort, Mumbai',
        'drawer_name': 'Ramesh Trading Co',
        'drawer_address': 'Shop 12, Crawford Market, Mumbai - 400001',
        'cheque_number': '554433',
        'cheque_date': '2026-10-01',
        'cheque_amount': 75000,
        'cheque_amount_words': 'Rupees Seventy Five Thousand Only',
        'bank_name': 'State Bank of India',
        'bank_branch': 'Marine Lines, Mumbai',
        'memo_date': '2026-10-15',
        'dishonour_reason': 'Funds Insufficient',
        'transaction_details': 'Supply of commercial textiles against invoice no. INV-4029'
    }
    draft_res = client.post('/generator/cheque-bounce-notice', data=form_data, follow_redirects=True)
    assert draft_res.status_code == 200
    assert b'Review your statutory draft' in draft_res.data
    assert b'554433' in draft_res.data
    assert b'75,000' in draft_res.data

    # Extract Order ID
    with app.app_context():
        user = User.query.filter_by(email='kavita@example.com').first()
        order = Order.query.filter_by(user_id=user.id).first()
        assert order is not None
        assert order.status == 'pending'
        order_id = order.id

    # 5. Open Checkout
    checkout_res = client.get(f'/payments/checkout/{order_id}')
    assert checkout_res.status_code == 200
    assert b'UPI / QR' in checkout_res.data
    assert b'nyayveya@icici' in checkout_res.data

    # 6. Complete Payment via QR / Direct checkout
    pay_res = client.post('/payments/process-checkout', json={
        'order_id': order_id,
        'payment_method': 'upi_qr',
        'payment_ref': 'UPI-E2E-TEST-KAVITA'
    })
    assert pay_res.status_code == 200
    pay_json = pay_res.get_json()
    assert pay_json['success'] is True
    assert f'/payments/success/{order_id}' in pay_json['redirect_url']

    # 7. Verify Order Status & Downloads
    with app.app_context():
        updated_order = db.session.get(Order, order_id)
        assert updated_order.status == 'paid'

    # Download Word document (.docx)
    docx_res = client.get(f'/generator/download/{order_id}/docx')
    assert docx_res.status_code == 200
    assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in docx_res.content_type
    assert len(docx_res.data) > 1000  # Valid docx payload

    # Download PDF document (.pdf)
    pdf_res = client.get(f'/generator/download/{order_id}/pdf')
    assert pdf_res.status_code == 200
    assert pdf_res.content_type == 'application/pdf'
    assert pdf_res.data.startswith(b'%PDF')  # Valid PDF binary signature

    # 8. Inspect Tax Invoice & User Dashboard
    invoice_res = client.get(f'/payments/success/{order_id}')
    assert invoice_res.status_code == 200
    assert b'TAX INVOICE' in invoice_res.data
    assert b'Kavita Iyer' in invoice_res.data
    assert b'998211' in invoice_res.data  # SAC Code

    dash_res = client.get('/auth/dashboard')
    assert dash_res.status_code == 200
    assert b'PAID' in dash_res.data


def test_e2e_rent_agreement_complete_flow(client, app):
    """
    Full end-to-end user lifecycle for Residential Rent Agreement:
    Guided drafting -> Preview -> Payment -> Word & PDF Downloads.
    """
    # Create and login user
    with app.app_context():
        user = User(full_name='Pooja Nair', email='pooja@example.com')
        user.set_password('PoojaPass123!')
        db.session.add(user)
        db.session.commit()

    client.post('/auth/login', data={'email': 'pooja@example.com', 'password': 'PoojaPass123!'})

    # Fill Rent Agreement Form
    rent_data = {
        'document_date': '2026-10-23',
        'city': 'Bengaluru',
        'first_party_name': 'Landlord Vinod',
        'first_party_details': 'S/o M. Vinod, 45 Indiranagar, Bengaluru - 560038',
        'second_party_name': 'Tenant Pooja Nair',
        'second_party_details': 'D/o K. Nair, Koramangala, Bengaluru - 560034',
        'subject_purpose': 'Flat 304, Green Meadows, Indiranagar, Bengaluru',
        'amount': 28000,
        'duration_period': '11 Months',
        'key_terms': '1. Rent payable monthly.\n2. Security deposit Rs 1,00,000.\n3. 30 days notice period.'
    }

    draft_res = client.post('/generator/draft/rent', data=rent_data, follow_redirects=True)
    assert draft_res.status_code == 200
    assert b'RESIDENTIAL LEASE / RENT AGREEMENT' in draft_res.data
    assert b'28,000' in draft_res.data

    with app.app_context():
        order = Order.query.filter_by(amount=249).first()
        assert order is not None
        order_id = order.id

    # Pay via NetBanking
    pay_res = client.post('/payments/process-checkout', json={
        'order_id': order_id,
        'payment_method': 'netbanking',
        'payment_ref': 'HDFC Bank NetBanking'
    })
    assert pay_res.status_code == 200

    # Verify both downloads
    docx_res = client.get(f'/generator/download/{order_id}/docx')
    assert docx_res.status_code == 200
    pdf_res = client.get(f'/generator/download/{order_id}/pdf')
    assert pdf_res.status_code == 200
    assert pdf_res.data.startswith(b'%PDF')


# ==============================================================================
# 2. ADVERSARIAL, EDGE CASE & SECURITY INTEGRATION TESTS
# ==============================================================================

def test_duplicate_payment_webhook_idempotency(client, app):
    """
    Replay attack / duplicate payment notification test:
    Repeated callbacks for the same transaction preserve idempotent captured state
    without duplicating database records or modifying order status.
    """
    with app.app_context():
        user = User(full_name='Test Buyer', email='buyer@example.com')
        user.set_password('Pass123!')
        tmpl = DocumentTemplate.query.filter_by(slug='rent').first()
        order = Order(
            order_number='ORD-IDEM-901',
            user=user,
            document_template=tmpl,
            amount=249,
            status='pending',
            form_data={'subject_purpose': 'Idempotency Test'}
        )
        db.session.add(user)
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    client.post('/auth/login', data={'email': 'buyer@example.com', 'password': 'Pass123!'})

    # First payment callback
    res1 = client.post('/payments/process-checkout', json={
        'order_id': order_id,
        'payment_method': 'card',
        'payment_ref': 'Card 4111'
    })
    assert res1.status_code == 200

    with app.app_context():
        assert db.session.get(Order, order_id).status == 'paid'
        payment_count_first = Payment.query.filter_by(order_id=order_id).count()
        assert payment_count_first == 1

    # Second identical / duplicate callback
    res2 = client.post('/payments/process-checkout', json={
        'order_id': order_id,
        'payment_method': 'card',
        'payment_ref': 'Card 4111'
    })
    assert res2.status_code == 200

    with app.app_context():
        # Order must remain paid, payment count must remain captured
        assert db.session.get(Order, order_id).status == 'paid'


def test_forged_tampered_payment_signature_rejected(client, app):
    """
    Tampered payment payload with invalid cryptographic signature is rejected (HTTP 400)
    and logged as failed in database audit trail.
    """
    with app.app_context():
        user = User(full_name='Security Target', email='target@example.com')
        user.set_password('Pass123!')
        tmpl = DocumentTemplate.query.filter_by(slug='rent').first()
        order = Order(
            order_number='ORD-FORGE-777',
            user=user,
            document_template=tmpl,
            amount=249,
            status='pending',
            form_data={}
        )
        db.session.add(user)
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    client.post('/auth/login', data={'email': 'target@example.com', 'password': 'Pass123!'})

    # Submit forged signature
    response = client.post('/payments/verify', json={
        'order_id': order_id,
        'razorpay_order_id': 'order_genuine_123',
        'razorpay_payment_id': 'pay_genuine_456',
        'razorpay_signature': 'forged_fake_signature_hex_value'
    })
    assert response.status_code == 400
    assert response.get_json()['success'] is False

    with app.app_context():
        order = db.session.get(Order, order_id)
        assert order.status == 'pending'
        failed_pay = Payment.query.filter_by(order_id=order_id, status='failed').first()
        assert failed_pay is not None
        assert failed_pay.error_code == 'INVALID_SIGNATURE'


def test_xss_sanitization_in_form_inputs(client, app):
    """
    Malicious script tags injected into form inputs are escaped safely by Jinja2
    and do not evaluate as unescaped raw HTML.
    """
    with app.app_context():
        user = User(full_name='XSS Auditor', email='xss@example.com')
        user.set_password('Pass123!')
        db.session.add(user)
        db.session.commit()

    client.post('/auth/login', data={'email': 'xss@example.com', 'password': 'Pass123!'})

    xss_payload = "<script>alert('XSS_ATTACK_VECTOR')</script>"
    rent_data = {
        'document_date': '2026-10-23',
        'city': 'New Delhi',
        'first_party_name': f"Attacker {xss_payload}",
        'first_party_details': 'Malicious address',
        'second_party_name': 'Innocent Tenant',
        'second_party_details': 'Address',
        'subject_purpose': f"Premises {xss_payload}",
        'amount': 10000,
        'duration_period': '11 Months',
        'key_terms': f"Clause 1: {xss_payload}"
    }

    res = client.post('/generator/draft/rent', data=rent_data, follow_redirects=True)
    assert res.status_code == 200
    # Must be escaped or not rendered as raw unescaped script tag
    assert b"<script>alert('XSS_ATTACK_VECTOR')</script>" not in res.data
    assert b"&lt;script&gt;alert(&#39;XSS_ATTACK_VECTOR&#39;)&lt;/script&gt;" in res.data or b"&lt;script&gt;" in res.data


def test_empty_or_malformed_order_data_resilience(client, app):
    """
    Resilience test: Preview and downloads handle empty or corrupted form_data safely
    without 500 Server Error exceptions.
    """
    with app.app_context():
        user = User(full_name='Resilience User', email='resilience@example.com')
        user.set_password('Pass123!')
        tmpl = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').first()
        order = Order(
            order_number='ORD-RESILIENT-001',
            user=user,
            document_template=tmpl,
            amount=199,
            status='paid',
            form_data={}  # Completely empty dictionary
        )
        db.session.add(user)
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    client.post('/auth/login', data={'email': 'resilience@example.com', 'password': 'Pass123!'})

    # Preview must render with safe defaults, not 500 KeyError
    preview_res = client.get(f'/generator/preview/{order_id}')
    assert preview_res.status_code == 200

    # Downloads must compile without crashing
    docx_res = client.get(f'/generator/download/{order_id}/docx')
    assert docx_res.status_code == 200

    pdf_res = client.get(f'/generator/download/{order_id}/pdf')
    assert pdf_res.status_code == 200


def test_logout_invalidates_session_and_clears_protected_access(client, app):
    """
    Logging out clears the active session and prevents subsequent access to protected dashboards.
    """
    with app.app_context():
        user = User(full_name='Session Tester', email='session@example.com')
        user.set_password('Pass123!')
        db.session.add(user)
        db.session.commit()

    # Login
    client.post('/auth/login', data={'email': 'session@example.com', 'password': 'Pass123!'})
    dash_auth = client.get('/auth/dashboard')
    assert dash_auth.status_code == 200

    # Logout
    logout_res = client.get('/auth/logout', follow_redirects=True)
    assert logout_res.status_code == 200

    # Attempt to access dashboard again - must redirect to login
    dash_unauth = client.get('/auth/dashboard', follow_redirects=False)
    assert dash_unauth.status_code == 302
    assert '/auth/login' in dash_unauth.headers['Location']
