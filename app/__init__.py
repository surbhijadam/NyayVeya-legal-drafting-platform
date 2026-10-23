import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create extension instances (not tied to any app yet)
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    """Application factory: creates and configures the Flask app."""

    app = Flask(__name__)

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///app.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Where generated documents are saved (outside the static folder for privacy)
    app.config['GENERATED_DOCUMENTS_FOLDER'] = os.path.join(
        app.root_path, '..', 'generated_documents'
    )

    # --- Initialise extensions with this app ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Where to redirect unauthenticated users (route created in Phase 3)
    login_manager.login_view = 'main.home'
    login_manager.login_message_category = 'warning'

    # Placeholder user loader - will be replaced with a real one in Phase 3
    # Flask-Login requires this callback to work, even on public pages
    @login_manager.user_loader
    def load_user(user_id):
        return None  # No User model yet; returns None (anonymous)

    # --- Register blueprints (route groups) ---
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
