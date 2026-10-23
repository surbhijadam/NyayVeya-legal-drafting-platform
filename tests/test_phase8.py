"""
Tests for Phase 8: Security & Privacy.

Covers:
1. HTTP Security Headers (X-Frame-Options, X-Content-Type-Options, CSP, Referrer-Policy, Permissions-Policy)
2. Session & Cookie Security Attributes (HttpOnly, SameSite)
3. CSRF Protection Enforcement
4. Insecure Direct Object References (IDOR) Ownership Protection (Preview, Checkout, Downloads, Receipts)
5. Sliding-Window Rate Limiting & 429 HTTP Responses
6. Private Document Storage Isolation & Direct URL Access Prevention
"""
import pytest
from app import create_app, db
from app.models import User, DocumentTemplate, Order, Payment
from app.catalogue import seed_initial_templates
from app.security import limiter


@pytest.fixture
def app(tmp_path):
    """Create test application with in-memory DB and isolated storage."""
    docs_folder = str(tmp_path / "test_docs")
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'GENERATED_DOCUMENTS_FOLDER': docs_folder,
        'SECRET_KEY': 'test-security-secret-key-123',
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
def user_alice(app):
    with app.app_context():
        user = User(
            full_name='Alice Sharma',
            email='alice@example.com'
        )
        user.set_password('AliceSecurePass123!')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def user_bob(app):
    with app.app_context():
        user = User(
            full_name='Bob Verma',
            email='bob@example.com'
        )
        user.set_password('BobSecurePass123!')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def alice_order(app, user_alice):
    with app.app_context():
        tmpl = DocumentTemplate.query.filter_by(slug='rent').first()
        order = Order(
            order_number='ORD-ALICE-SEC-001',
            user_id=user_alice,
            document_template_id=tmpl.id,
            amount=249,
            status='pending',
            form_data={
                'first_party_name': 'Alice Sharma',
                'first_party_details': 'New Delhi',
                'second_party_name': 'Landlord X',
                'subject_purpose': 'Apartment Tenancy',
                'city': 'New Delhi',
                'key_terms': 'Private tenancy terms'
            }
        )
        db.session.add(order)
        db.session.commit()
        return order.id


# ==============================================================================
# 1. HTTP SECURITY HEADERS & COOKIE POLICIES
# ==============================================================================

def test_security_headers_present(client):
    """Responses contain mandatory defensive HTTP security headers."""
    response = client.get('/')
    assert response.status_code == 200

    headers = response.headers
    assert headers.get('X-Frame-Options') == 'SAMEORIGIN'
    assert headers.get('X-Content-Type-Options') == 'nosniff'
    assert headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
    assert 'geolocation=()' in headers.get('Permissions-Policy', '')

    csp = headers.get('Content-Security-Policy', '')
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'self'" in csp


def test_session_cookie_security_attributes(app):
    """Application configuration enforces secure cookie flags."""
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'
    assert app.config['REMEMBER_COOKIE_HTTPONLY'] is True
    assert app.config['REMEMBER_COOKIE_SAMESITE'] == 'Lax'


# ==============================================================================
# 2. CSRF PROTECTION ENFORCEMENT
# ==============================================================================

def test_csrf_protection_rejects_missing_token(app):
    """State-changing POST requests without CSRF tokens are rejected with 400 Bad Request."""
    csrf_app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': True,
        'SECRET_KEY': 'csrf-test-key-321'
    })

    with csrf_app.test_client() as csrf_client:
        # POST to login without CSRF token
        response = csrf_client.post('/auth/login', data={
            'email': 'alice@example.com',
            'password': 'Password123!'
        })
        assert response.status_code == 400
        assert b'CSRF token' in response.data or b'bad request' in response.data.lower()


# ==============================================================================
# 3. OBJECT OWNERSHIP & IDOR PROTECTION
# ==============================================================================

def test_idor_preview_unauthorized_user_blocked(client, user_bob, alice_order):
    """Bob cannot access or preview Alice's private draft order (403 Forbidden)."""
    # Log in as Bob
    client.post('/auth/login', data={'email': 'bob@example.com', 'password': 'BobSecurePass123!'})

    response = client.get(f'/generator/preview/{alice_order}')
    assert response.status_code == 403


def test_idor_checkout_unauthorized_user_blocked(client, user_bob, alice_order):
    """Bob cannot access checkout for Alice's order (403 Forbidden)."""
    client.post('/auth/login', data={'email': 'bob@example.com', 'password': 'BobSecurePass123!'})

    response = client.get(f'/payments/checkout/{alice_order}')
    assert response.status_code == 403


def test_idor_download_unauthorized_user_blocked(client, user_bob, alice_order):
    """Bob cannot download Alice's private Word or PDF drafts (403 Forbidden)."""
    client.post('/auth/login', data={'email': 'bob@example.com', 'password': 'BobSecurePass123!'})

    res_docx = client.get(f'/generator/download/{alice_order}/docx')
    assert res_docx.status_code == 403

    res_pdf = client.get(f'/generator/download/{alice_order}/pdf')
    assert res_pdf.status_code == 403


def test_idor_payment_process_unauthorized_user_blocked(client, user_bob, alice_order):
    """Bob cannot trigger payment processing for Alice's order (403 Forbidden)."""
    client.post('/auth/login', data={'email': 'bob@example.com', 'password': 'BobSecurePass123!'})

    response = client.post('/payments/process-checkout', json={
        'order_id': alice_order,
        'payment_method': 'upi_qr'
    })
    assert response.status_code == 403


# ==============================================================================
# 4. RATE LIMITING & BRUTE FORCE DEFENSE
# ==============================================================================

def test_rate_limiter_blocks_excessive_requests(client, app):
    """Repeated calls exceeding the rate threshold return HTTP 429 with Retry-After header."""
    app.config['ENABLE_RATE_LIMIT_TEST'] = True
    limiter.reset()

    # Hit contact route rapidly (max 10 allowed)
    for _ in range(10):
        client.get('/contact')

    # 11th request should be blocked
    blocked = client.get('/contact')
    assert blocked.status_code == 429
    assert 'Retry-After' in blocked.headers
    assert b'Too Many Requests' in blocked.data or b'429' in blocked.data

    # Cleanup
    app.config['ENABLE_RATE_LIMIT_TEST'] = False
    limiter.reset()


# ==============================================================================
# 5. PRIVATE DOCUMENT STORAGE ISOLATION
# ==============================================================================

def test_private_generated_documents_not_in_static(client):
    """Direct URL queries attempting directory traversal to private documents fail."""
    response = client.get('/static/../generated_documents/secret.docx')
    assert response.status_code in (400, 404)
