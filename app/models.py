"""
Database models for LegalDraft India.

All database tables are defined here as SQLAlchemy models.
Flask-Migrate uses these models to generate database migration scripts.
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """
    User account model.

    UserMixin provides default implementations for:
    - is_authenticated: returns True (user is logged in)
    - is_active: returns True (account is active)
    - is_anonymous: returns False (this is a real user)
    - get_id(): returns the user ID as a string
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Account metadata
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships (will be expanded in later phases)
    # orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        """Hash and store the password. Never store plain text passwords."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check a plain-text password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'
