"""
Database models for LegalDraft India.

All database tables are defined here as SQLAlchemy models.
Flask-Migrate uses these models to generate database migration scripts.
"""
import json
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """
    User account model.
    Stores account credentials, profile information, role, and links to orders.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Role & Account Status
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Metadata timestamps
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship to user's orders
    orders = db.relationship(
        'Order', back_populates='user', lazy='select',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email} (admin={self.is_admin})>'


class DocumentTemplate(db.Model):
    """
    Legal document templates offered on the platform.
    Defines template metadata, statutory references, requirements, and pricing.
    """
    __tablename__ = 'document_templates'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300), nullable=True)
    category = db.Column(db.String(100), nullable=False, default='notices')
    price = db.Column(db.Integer, nullable=False, default=199)  # In INR
    status = db.Column(db.String(50), nullable=False, default='coming_soon')  # 'active', 'coming_soon', 'draft'
    language = db.Column(db.String(50), nullable=False, default='English')

    short_description = db.Column(db.Text, nullable=False)
    long_description = db.Column(db.Text, nullable=False)

    # JSON stored fields for list metadata
    what_you_get_json = db.Column(db.Text, nullable=True, default='[]')
    information_needed_json = db.Column(db.Text, nullable=True, default='[]')
    important_notes_json = db.Column(db.Text, nullable=True, default='[]')
    faqs_json = db.Column(db.Text, nullable=True, default='[]')

    # Visual Presentation
    icon = db.Column(db.String(100), default='bi-file-earmark-medical')
    badge_text = db.Column(db.String(50), nullable=True)
    badge_class = db.Column(db.String(50), nullable=True, default='bg-primary')

    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationship to orders generated from this template
    orders = db.relationship(
        'Order', back_populates='document_template', lazy='select'
    )

    # Helper properties for list deserialization
    @property
    def what_you_get(self):
        try:
            return json.loads(self.what_you_get_json or '[]')
        except (ValueError, TypeError):
            return []

    @what_you_get.setter
    def what_you_get(self, value):
        self.what_you_get_json = json.dumps(value or [])

    @property
    def information_needed(self):
        try:
            return json.loads(self.information_needed_json or '[]')
        except (ValueError, TypeError):
            return []

    @information_needed.setter
    def information_needed(self, value):
        self.information_needed_json = json.dumps(value or [])

    @property
    def important_notes(self):
        try:
            return json.loads(self.important_notes_json or '[]')
        except (ValueError, TypeError):
            return []

    @important_notes.setter
    def important_notes(self, value):
        self.important_notes_json = json.dumps(value or [])

    @property
    def faqs(self):
        try:
            return json.loads(self.faqs_json or '[]')
        except (ValueError, TypeError):
            return []

    @faqs.setter
    def faqs(self, value):
        self.faqs_json = json.dumps(value or [])

    def __repr__(self):
        return f'<DocumentTemplate {self.slug} (₹{self.price})>'


class Order(db.Model):
    """
    Order record representing a user's request for a specific legal document draft.
    Tracks state: pending -> paid -> completed / failed.
    """
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    document_template_id = db.Column(
        db.Integer, db.ForeignKey('document_templates.id'), nullable=False, index=True
    )

    amount = db.Column(db.Integer, nullable=False)  # in INR
    status = db.Column(db.String(30), nullable=False, default='pending')  # pending, paid, failed, refunded

    # User inputs submitted through guided questionnaire stored as JSON
    form_data_json = db.Column(db.Text, nullable=True)

    # Generated files stored privately on filesystem (outside public static)
    docx_filename = db.Column(db.String(255), nullable=True)
    pdf_filename = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship('User', back_populates='orders')
    document_template = db.relationship('DocumentTemplate', back_populates='orders')
    payments = db.relationship(
        'Payment', back_populates='order', lazy='select',
        cascade='all, delete-orphan'
    )

    @property
    def form_data(self):
        if not self.form_data_json:
            return {}
        try:
            return json.loads(self.form_data_json)
        except (ValueError, TypeError):
            return {}

    @form_data.setter
    def form_data(self, value):
        self.form_data_json = json.dumps(value or {}, default=str)

    def __repr__(self):
        return f'<Order {self.order_number} ({self.status})>'


class Payment(db.Model):
    """
    Payment transaction record for an Order.
    Stores gateway references (e.g. Razorpay payment/order IDs) and audit statuses.
    """
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)

    gateway = db.Column(db.String(50), nullable=False, default='razorpay')
    gateway_order_id = db.Column(db.String(100), nullable=True, index=True)
    gateway_payment_id = db.Column(db.String(100), nullable=True, index=True)
    gateway_signature = db.Column(db.String(255), nullable=True)

    amount = db.Column(db.Integer, nullable=False)  # in INR
    currency = db.Column(db.String(10), nullable=False, default='INR')
    status = db.Column(db.String(30), nullable=False, default='created')  # created, captured, failed, refunded

    error_code = db.Column(db.String(100), nullable=True)
    error_description = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    order = db.relationship('Order', back_populates='payments')

    def __repr__(self):
        return f'<Payment {self.id} for Order {self.order_id} ({self.status})>'


class SupportInquiry(db.Model):
    """
    Customer support and contact inquiries submitted through website.
    Supports administrative tracking, status triage, and resolution notes.
    """
    __tablename__ = 'support_inquiries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(254), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='open')  # open, in_progress, resolved
    admin_notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f'<SupportInquiry {self.id} {self.email} ({self.status})>'
