import os
import click
from flask import Flask
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables from .env file explicitly
load_dotenv()

# Create extension instances (not tied to any app yet)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def _run_sqlite_column_migrations(app):
    """Safely apply non-destructive schema additions to existing SQLite tables."""
    from sqlalchemy import inspect, text
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            with db.engine.connect() as conn:
                if 'users' in tables:
                    cols = [c['name'] for c in inspector.get_columns('users')]
                    if 'is_admin' not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"))
                    if 'is_active' not in cols:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))
                    conn.commit()

                if 'document_templates' in tables:
                    cols = [c['name'] for c in inspector.get_columns('document_templates')]
                    if 'language' not in cols:
                        conn.execute(text("ALTER TABLE document_templates ADD COLUMN language VARCHAR(50) NOT NULL DEFAULT 'English'"))
                    if 'faqs_json' not in cols:
                        conn.execute(text("ALTER TABLE document_templates ADD COLUMN faqs_json TEXT DEFAULT '[]'"))
                    conn.commit()
        except Exception:
            pass


@click.command('create-admin')
@click.option('--email', prompt=True, help='Administrator email')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Administrator password')
@click.option('--name', default='NyayVeya Admin', help='Administrator full name')
@with_appcontext
def create_admin_command(email, password, name):
    """CLI command to safely create or promote an administrator account."""
    from app.models import User
    email = email.lower().strip()
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        user.is_active = True
        user.full_name = name or user.full_name
        user.set_password(password)
        db.session.commit()
        click.echo(f"Success: Existing user '{email}' promoted to Administrator.")
    else:
        user = User(
            full_name=name or 'NyayVeya Administrator',
            email=email,
            is_admin=True,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Success: Administrator account created for '{email}'.")


def create_app(test_config=None, config_name=None):
    """Application factory: creates and configures the Flask app."""

    app = Flask(__name__)

    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)

    # --- Load Configuration from config.py ---
    from config import config_by_name
    env_name = config_name or os.environ.get('FLASK_ENV', 'development').lower()
    selected_config = config_by_name.get(env_name, config_by_name['default'])
    app.config.from_object(selected_config)

    # Ensure generated documents storage directory exists
    docs_folder = app.config.get('GENERATED_DOCUMENTS_FOLDER')
    if docs_folder:
        os.makedirs(docs_folder, exist_ok=True)

    # Apply test config BEFORE initializing db extension if provided
    if test_config:
        app.config.update(test_config)

    # --- Initialise extensions with this app ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Phase 8: Initialize security headers and cookie policies
    from app.security import init_security
    init_security(app)

    # Where to redirect unauthenticated users trying to access @login_required routes
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # User loader callback - Flask-Login calls this to reload the user from the session
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))

    # --- Register blueprints (route groups) ---
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    from app.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.generator import generator_bp
    app.register_blueprint(generator_bp)

    from app.admin import admin_bp
    app.register_blueprint(admin_bp)

    from app.payments import payments_bp
    app.register_blueprint(payments_bp)

    # Register CLI commands
    app.cli.add_command(create_admin_command)

    # Ensure models are imported and tables/columns are migrated
    with app.app_context():
        from app import models
        db.create_all()
        _run_sqlite_column_migrations(app)
        from app.catalogue import seed_initial_templates
        seed_initial_templates()

        # Optional: Auto-seed initial admin from environment variables if present
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_pass = os.environ.get('ADMIN_PASSWORD')
        if admin_email and admin_pass:
            admin_user = models.User.query.filter_by(email=admin_email.lower().strip()).first()
            if not admin_user:
                admin_user = models.User(
                    full_name=os.environ.get('ADMIN_NAME', 'NyayVeya Admin'),
                    email=admin_email.lower().strip(),
                    is_admin=True,
                    is_active=True
                )
                admin_user.set_password(admin_pass)
                db.session.add(admin_user)
                db.session.commit()
            elif not admin_user.is_admin:
                admin_user.is_admin = True
                admin_user.is_active = True
                db.session.commit()

        # Phase 10: Production Logging
        if not app.debug and not app.testing:
            import logging
            from logging.handlers import RotatingFileHandler
            logs_dir = os.path.abspath(os.path.join(app.root_path, '..', 'logs'))
            os.makedirs(logs_dir, exist_ok=True)
            file_handler = RotatingFileHandler(
                os.path.join(logs_dir, 'nyayveya.log'),
                maxBytes=2 * 1024 * 1024,  # 2MB
                backupCount=5
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s [%(pathname)s:%(lineno)d]: %(message)s'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('NyayVeya Online Legal Drafting Platform initialized successfully')

    return app
