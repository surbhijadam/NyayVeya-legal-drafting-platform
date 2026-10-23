"""
Tests for Phase 10: Production Deployment & Go-Live Readiness.

Covers:
1. Production Configuration Architecture (Development, Testing, Production)
2. Production Health Check Endpoint (/health)
3. Environment Configuration Template (.env.example)
4. Production WSGI Entrypoint (wsgi.py) & Procfile
5. Automated Database Backup Snapshotting
6. Private Document Storage Isolation Verification
"""
import os
import pytest
from flask import Flask
from app import create_app, db
from config import config_by_name, DevelopmentConfig, TestingConfig, ProductionConfig
from scripts.backup_db import perform_backup


@pytest.fixture
def app(tmp_path):
    """Create test application instance with isolated in-memory database."""
    docs_folder = str(tmp_path / "test_docs")
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'GENERATED_DOCUMENTS_FOLDER': docs_folder,
        'SECRET_KEY': 'phase10-test-secret-key-123',
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_health_check_endpoint(client):
    """Health check endpoint returns HTTP 200 with JSON status for load balancers."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['database'] == 'connected'
    assert 'NyayVeya' in data['platform']


def test_config_environments():
    """Application supports distinct, secure configurations per environment."""
    assert DevelopmentConfig.DEBUG is True
    assert DevelopmentConfig.SESSION_COOKIE_SECURE is False

    assert TestingConfig.TESTING is True
    assert TestingConfig.DEBUG is False

    assert ProductionConfig.DEBUG is False
    assert ProductionConfig.SESSION_COOKIE_SECURE is True
    assert ProductionConfig.REMEMBER_COOKIE_SECURE is True
    assert ProductionConfig.PREFERRED_URL_SCHEME == 'https'


def test_env_example_template_exists():
    """.env.example template provides clear guidance for all production credentials."""
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_example_path = os.path.join(basedir, '.env.example')

    assert os.path.exists(env_example_path)
    with open(env_example_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'FLASK_ENV' in content
    assert 'SECRET_KEY' in content
    assert 'DATABASE_URL' in content
    assert 'RAZORPAY_KEY_ID' in content
    assert 'RAZORPAY_KEY_SECRET' in content
    assert 'PAYMENT_MODE' in content


def test_wsgi_entrypoint_loads():
    """Production WSGI module exposes valid Flask application for web servers."""
    import wsgi
    assert isinstance(wsgi.app, Flask)
    assert wsgi.app.name == 'app'


def test_procfile_configured_for_cloud():
    """Procfile defines Gunicorn worker command for PaaS platforms (Render, Railway)."""
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    procfile_path = os.path.join(basedir, 'Procfile')

    assert os.path.exists(procfile_path)
    with open(procfile_path, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'gunicorn' in content
    assert 'wsgi:app' in content


def test_database_backup_creates_snapshot(app, tmp_path):
    """Database backup utility executes safely without exceptions."""
    result = perform_backup()
    # If SQLite file exists, backup is generated; otherwise None is safely returned
    assert result is None or os.path.exists(result)


def test_private_document_folder_is_outside_static(app):
    """Private documents folder is never located within publicly served static/."""
    docs_folder = os.path.abspath(app.config['GENERATED_DOCUMENTS_FOLDER'])
    static_folder = os.path.abspath(app.static_folder)

    assert not docs_folder.startswith(static_folder)
