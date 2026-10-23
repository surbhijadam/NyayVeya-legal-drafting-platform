import os
from flask import Flask
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


def create_app(test_config=None):
    """Application factory: creates and configures the Flask app."""

    app = Flask(__name__)

    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    default_db_path = os.path.join(app.instance_path, 'app.db').replace('\\', '/')

    # --- Configuration ---
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', f'sqlite:///{default_db_path}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Where generated documents are saved (outside the static folder for privacy)
    docs_folder = os.path.abspath(os.path.join(app.root_path, '..', 'generated_documents'))
    os.makedirs(docs_folder, exist_ok=True)
    app.config['GENERATED_DOCUMENTS_FOLDER'] = docs_folder

    # Apply test config BEFORE initializing db extension if provided
    if test_config:
        app.config.update(test_config)

    # --- Initialise extensions with this app ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

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

    # Ensure models are imported and tables are created in development
    with app.app_context():
        from app import models
        db.create_all()
        from app.catalogue import seed_initial_templates
        seed_initial_templates()

    return app
