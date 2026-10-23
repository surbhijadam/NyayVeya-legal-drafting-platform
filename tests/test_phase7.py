"""
Tests for Phase 7 - Orders & Payments:
Razorpay Checkout integration, server-side cryptographic HMAC-SHA256 signature verification,
audit trail logging, invoice generation, and dashboard integration.
"""
import json
import pytest
from app import create_app, db
from app.models import User, DocumentTemplate, Order, Payment
from app.catalogue import seed_initial_templates
from app.payments.services import (
    create_razorpay_order,
    verify_razorpay_signature,
    generate_signature,
    record_successful_payment,
    record_failed_payment
)


@pytest.fixture
def app(tmp_path):
    """Create test application with in-memory DB and isolated storage."""
    docs_folder = str(tmp_path / "test_docs")
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'GENERATED_DOCUMENTS_FOLDER': docs_folder,
        'RAZORPAY_KEY_ID': 'rzp_test_fixture_key',
        'RAZORPAY_KEY_SECRET': 'fixture_secret_1234567890',
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


@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            full_name='Vikram Seth',
            email='vikram@example.com'
        )
        user.set_password('SecurePass123')
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
        user.set_password('SecurePass123')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def test_order(app, test_user):
    with app.app_context():
        tmpl = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').first()
        order = Order(
            order_number='ORD-PAY-TEST-701',
            user_id=test_user,
            document_template_id=tmpl.id,
            amount=199,
            status='pending',
            form_data_json=json.dumps({
                'payee_name': 'Vikram Seth',
                'cheque_amount': '50000',
                'drawer_name': 'Anil Sharma'
            })
        )
        db.session.add(order)
        db.session.commit()
        return order.id


# --- Cryptographic & Service Tests ---

def test_signature_verification_valid(app):
    """Authentic HMAC-SHA256 signature is verified successfully."""
    with app.app_context():
        order_id = "order_123456789"
        payment_id = "pay_987654321"
        secret = "fixture_secret_1234567890"

        signature = generate_signature(order_id, payment_id, secret)
        assert verify_razorpay_signature(order_id, payment_id, signature, secret) is True


def test_signature_verification_forged_rejected(app):
    """Tampered or forged signature fails verification."""
    with app.app_context():
        order_id = "order_123456789"
        payment_id = "pay_987654321"
        secret = "fixture_secret_1234567890"

        bad_signature = "bad_forged_signature_hex_value"
        assert verify_razorpay_signature(order_id, payment_id, bad_signature, secret) is False

        # Alter payment id
        valid_signature = generate_signature(order_id, payment_id, secret)
        assert verify_razorpay_signature(order_id, "pay_altered_id", valid_signature, secret) is False


def test_create_razorpay_order_service(app, test_order):
    """create_razorpay_order calculates paise amount and returns order structure."""
    with app.app_context():
        order = db.session.get(Order, test_order)
        rzp_order = create_razorpay_order(order)

        assert rzp_order['id'].startswith('order_')
        assert rzp_order['amount'] == 19900  # 199 INR * 100 paise
        assert rzp_order['currency'] == 'INR'
        assert rzp_order['receipt'] == order.order_number


def test_record_successful_payment_idempotency(app, test_order):
    """Payment records are created once and order transitions to paid."""
    with app.app_context():
        order = db.session.get(Order, test_order)
        assert order.status == 'pending'

        p1 = record_successful_payment(
            order=order,
            gateway_order_id='order_rzp_1',
            gateway_payment_id='pay_rzp_1',
            gateway_signature='sig_valid_1',
            amount=199
        )

        assert order.status == 'paid'
        assert p1.status == 'captured'
        assert Payment.query.filter_by(order_id=order.id).count() == 1

        # Second invocation with same gateway_payment_id returns existing payment
        p2 = record_successful_payment(
            order=order,
            gateway_order_id='order_rzp_1',
            gateway_payment_id='pay_rzp_1',
            gateway_signature='sig_valid_1',
            amount=199
        )
        assert p1.id == p2.id
        assert Payment.query.filter_by(order_id=order.id).count() == 1


# --- Route & Access Control Tests ---

def test_checkout_requires_login(client, test_order):
    """Anonymous visitors are redirected to login."""
    response = client.get(f'/payments/checkout/{test_order}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page' in response.data


def test_checkout_unauthorized_user_blocked(client, other_user, test_order):
    """A user cannot access checkout for another user's order (403 Forbidden)."""
    # Log in as other_user
    client.post('/auth/login', data={'email': 'other@example.com', 'password': 'SecurePass123'})

    response = client.get(f'/payments/checkout/{test_order}')
    assert response.status_code == 403


def test_checkout_page_renders_details(client, test_user, test_order):
    """Owner accessing checkout sees order details, price, and payment portal."""
    client.post('/auth/login', data={'email': 'vikram@example.com', 'password': 'SecurePass123'})

    response = client.get(f'/payments/checkout/{test_order}')
    assert response.status_code == 200
    assert b'ORD-PAY-TEST-701' in response.data
    assert b'199' in response.data
    assert b'Razorpay' in response.data
    assert b'rzp_test_fixture_key' in response.data


def test_checkout_already_paid_redirects_to_receipt(client, app, test_user, test_order):
    """Visiting checkout for an already paid order redirects to the success/receipt page."""
    with app.app_context():
        order = db.session.get(Order, test_order)
        order.status = 'paid'
        db.session.commit()

    client.post('/auth/login', data={'email': 'vikram@example.com', 'password': 'SecurePass123'})

    response = client.get(f'/payments/checkout/{test_order}', follow_redirects=True)
    assert response.status_code == 200
    assert b'already been paid' in response.data
    assert b'Payment Verified Successfully' in response.data


def test_verify_callback_with_valid_signature(client, app, test_user, test_order):
    """Valid callback signature completes the order and transitions state to paid."""
    client.post('/auth/login', data={'email': 'vikram@example.com', 'password': 'SecurePass123'})

    rzp_order_id = "order_rzp_real_001"
    rzp_payment_id = "pay_rzp_real_001"
    valid_signature = generate_signature(rzp_order_id, rzp_payment_id, "fixture_secret_1234567890")

    response = client.post('/payments/verify', data={
        'order_id': test_order,
        'razorpay_order_id': rzp_order_id,
        'razorpay_payment_id': rzp_payment_id,
        'razorpay_signature': valid_signature
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Payment verified successfully' in response.data
    assert b'INV-PAY-TEST-701' in response.data

    with app.app_context():
        order = db.session.get(Order, test_order)
        assert order.status == 'paid'
        payment = Payment.query.filter_by(order_id=order.id).first()
        assert payment is not None
        assert payment.gateway_payment_id == rzp_payment_id
        assert payment.status == 'captured'


def test_verify_callback_with_invalid_signature_rejected(client, app, test_user, test_order):
    """Forged or altered signature fails verification and does not mark order as paid."""
    client.post('/auth/login', data={'email': 'vikram@example.com', 'password': 'SecurePass123'})

    response = client.post('/payments/verify', data={
        'order_id': test_order,
        'razorpay_order_id': 'order_fake',
        'razorpay_payment_id': 'pay_fake',
        'razorpay_signature': 'tampered_signature_hex'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Payment verification failed' in response.data

    with app.app_context():
        order = db.session.get(Order, test_order)
        assert order.status == 'pending'
        failed_payment = Payment.query.filter_by(order_id=order.id, status='failed').first()
        assert failed_payment is not None
        assert failed_payment.error_code == 'INVALID_SIGNATURE'


def test_simulate_sandbox_payment_route(client, app, test_user, test_order):
    """Developer sandbox route enables 1-click test checkout in dev mode."""
    client.post('/auth/login', data={'email': 'vikram@example.com', 'password': 'SecurePass123'})

    response = client.get(f'/payments/simulate-test-payment/{test_order}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Sandbox payment simulated and verified successfully' in response.data
    assert b'Payment Verified Successfully' in response.data

    with app.app_context():
        order = db.session.get(Order, test_order)
        assert order.status == 'paid'


def test_success_page_unpaid_order_redirects(client, test_user, test_order):
    """Accessing success receipt for an unpaid order redirects back to checkout."""
    client.post('/auth/login', data={'email': 'vikram@example.com', 'password': 'SecurePass123'})

    response = client.get(f'/payments/success/{test_order}', follow_redirects=True)
    assert response.status_code == 200
    assert b'Payment is pending for this order' in response.data
    assert b'Complete your order' in response.data


def test_checkout_renders_upi_qr_code_and_payment_methods(client, test_user, test_order):
    """Checkout page renders dynamic UPI QR code, VPA, and payment method tabs."""
    client.post('/auth/login', data={'email': 'vikram@example.com', 'password': 'SecurePass123'})

    response = client.get(f'/payments/checkout/{test_order}')
    assert response.status_code == 200
    assert b'nyayveya@icici' in response.data
    assert b'UPI / QR' in response.data
    assert b'NetBanking' in response.data
    assert b'Cards' in response.data
    assert b'Wallets' in response.data
    assert b'Scan &amp; Pay with Any UPI App' in response.data or b'Scan & Pay with Any UPI App' in response.data


def test_process_checkout_upi_qr_payment(client, app, test_user, test_order):
    """process_checkout endpoint completes UPI QR payment and redirects to receipt."""
    client.post('/auth/login', data={'email': 'vikram@example.com', 'password': 'SecurePass123'})

    response = client.post('/payments/process-checkout', json={
        'order_id': test_order,
        'payment_method': 'upi_qr',
        'payment_ref': 'QR Scan Verified'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert f'/payments/success/{test_order}' in data['redirect_url']

    with app.app_context():
        order = db.session.get(Order, test_order)
        assert order.status == 'paid'
        payment = Payment.query.filter_by(order_id=order.id).first()
        assert payment is not None
        assert payment.status == 'captured'
        assert 'pay_upi_qr' in payment.gateway_payment_id
