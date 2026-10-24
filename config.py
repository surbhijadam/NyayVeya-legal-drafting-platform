import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration class with common default settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-fallback-secret-key-change-in-prod'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Private document storage folder outside static/
    GENERATED_DOCUMENTS_FOLDER = os.environ.get(
        'GENERATED_DOCUMENTS_FOLDER',
        os.path.abspath(os.path.join(basedir, 'generated_documents'))
    )

    # Razorpay Gateway Defaults
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_sample_key')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'sample_secret_key_12345')
    PAYMENT_MODE = os.environ.get('PAYMENT_MODE', 'test')

    # Session & Cookie Security (Phase 8 baseline)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'


def _normalize_db_url(url: str | None) -> str | None:
    """Normalize legacy postgres:// URIs supplied by cloud PaaS (Render/Heroku) to postgresql://."""
    if url and url.startswith('postgres://'):
        return url.replace('postgres://', 'postgresql://', 1)
    return url


class DevelopmentConfig(Config):
    """Local development configuration (uses SQLite by default)."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ.get('DATABASE_URL')) or (
        f"sqlite:///{os.path.join(basedir, 'instance', 'app.db').replace(os.sep, '/')}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
    }
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing configuration for automated pytest suite."""
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production deployment configuration (enforces HTTPS, secure cookies, and MySQL/Postgres URI)."""
    DEBUG = False
    TESTING = False
    # In production, DATABASE_URL is normalized to handle Render's postgres:// or MySQL mysql+pymysql://
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(os.environ.get('DATABASE_URL')) or (
        f"sqlite:///{os.path.join(basedir, 'instance', 'app.db').replace(os.sep, '/')}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
        'pool_timeout': 30,
    }
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
