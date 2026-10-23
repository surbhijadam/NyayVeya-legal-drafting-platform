"""
Tests for Phase 3 - Authentication: Registration, Login, Logout, and Protected Routes.
"""
import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    """Create application configured for testing with an in-memory database."""
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for submitting HTTP requests."""
    return app.test_client()


@pytest.fixture
def registered_user(app):
    """Create a sample user in the test database."""
    with app.app_context():
        user = User(
            full_name='Aarav Sharma',
            email='aarav@example.com'
        )
        user.set_password('SecurePass123')
        db.session.add(user)
        db.session.commit()
        # Return user ID so tests can re-query cleanly across sessions
        return user.id


# --- Registration Tests ---

def test_register_page_loads(client):
    """Registration page returns HTTP 200 with required form fields."""
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'Create Account' in response.data
    assert b'Full Name' in response.data
    assert b'Email Address' in response.data
    assert b'Password' in response.data


def test_register_successful(client, app):
    """Valid registration creates a user in the database and redirects to login."""
    response = client.post('/auth/register', data={
        'full_name': 'Priya Patel',
        'email': 'priya@example.com',
        'password': 'StrongPassword123',
        'confirm_password': 'StrongPassword123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Account created successfully' in response.data
    assert b'Log In' in response.data

    with app.app_context():
        user = User.query.filter_by(email='priya@example.com').first()
        assert user is not None
        assert user.full_name == 'Priya Patel'
        assert user.check_password('StrongPassword123') is True
        # Ensure password is stored hashed, not plaintext
        assert user.password_hash != 'StrongPassword123'


def test_register_duplicate_email_rejected(client, registered_user):
    """Attempting to register with an existing email fails validation."""
    response = client.post('/auth/register', data={
        'full_name': 'Another Person',
        'email': 'aarav@example.com',  # already taken
        'password': 'NewPassword123',
        'confirm_password': 'NewPassword123'
    })

    assert response.status_code == 200
    assert b'already exists' in response.data


def test_register_password_mismatch(client):
    """Registration fails when password and confirmation do not match."""
    response = client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'PasswordOne1',
        'confirm_password': 'PasswordTwo2'
    })

    assert response.status_code == 200
    assert b'Passwords do not match' in response.data


def test_register_short_password(client):
    """Registration fails when password is shorter than 8 characters."""
    response = client.post('/auth/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'short',
        'confirm_password': 'short'
    })

    assert response.status_code == 200
    assert b'at least 8 characters' in response.data


# --- Login & Session Tests ---

def test_login_page_loads(client):
    """Login page loads with email and password fields."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Log In' in response.data
    assert b'Email Address' in response.data


def test_login_successful(client, registered_user):
    """Valid credentials successfully log in and redirect to dashboard."""
    response = client.post('/auth/login', data={
        'email': 'aarav@example.com',
        'password': 'SecurePass123',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Welcome back, Aarav Sharma!' in response.data
    assert b'Dashboard' in response.data


def test_login_wrong_password(client, registered_user):
    """Incorrect password rejects login with generic error message."""
    response = client.post('/auth/login', data={
        'email': 'aarav@example.com',
        'password': 'WrongPassword!',
    })

    assert response.status_code == 200
    assert b'Invalid email address or password' in response.data


def test_login_nonexistent_user(client):
    """Non-existent email rejects login with generic error message."""
    response = client.post('/auth/login', data={
        'email': 'nobody@example.com',
        'password': 'SomePassword123',
    })

    assert response.status_code == 200
    assert b'Invalid email address or password' in response.data


def test_login_open_redirect_prevention(client, registered_user):
    """Malicious external next URLs are stripped for security."""
    response = client.post('/auth/login?next=https://evil.com', data={
        'email': 'aarav@example.com',
        'password': 'SecurePass123',
    }, follow_redirects=False)

    # Should redirect to internal dashboard, NOT to https://evil.com
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/dashboard'


# --- Protected Route & Logout Tests ---

def test_dashboard_requires_login(client):
    """Unauthenticated access to dashboard redirects to login page."""
    response = client.get('/auth/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in to access this page.' in response.data
    assert b'Log In' in response.data


def test_dashboard_accessible_when_logged_in(client, registered_user):
    """Authenticated user can access dashboard and view account details."""
    # Log in first
    client.post('/auth/login', data={
        'email': 'aarav@example.com',
        'password': 'SecurePass123',
    })

    response = client.get('/auth/dashboard')
    assert response.status_code == 200
    assert b'Aarav Sharma' in response.data
    assert b'aarav@example.com' in response.data


def test_logout(client, registered_user):
    """Logging out terminates the session and redirects to home page."""
    # Log in
    client.post('/auth/login', data={
        'email': 'aarav@example.com',
        'password': 'SecurePass123',
    })

    # Logout
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data

    # Attempting dashboard access again should now require login
    dash_response = client.get('/auth/dashboard', follow_redirects=True)
    assert b'Please log in to access this page.' in dash_response.data


def test_navbar_changes_on_auth_state(client, registered_user):
    """Navbar displays Register/Login when anonymous, and Username/Logout when logged in."""
    # Anonymous view
    anon_resp = client.get('/')
    assert b'Register' in anon_resp.data
    assert b'Log In' in anon_resp.data
    assert b'Logout' not in anon_resp.data

    # Authenticate
    client.post('/auth/login', data={
        'email': 'aarav@example.com',
        'password': 'SecurePass123',
    })

    # Authenticated view
    auth_resp = client.get('/')
    assert b'Aarav Sharma' in auth_resp.data
    assert b'Logout' in auth_resp.data
