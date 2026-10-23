"""
Tests for Phase 4 - Database Models, Migrations, Relationships, and Constraints.
"""
import pytest
from app import create_app, db
from app.models import User, DocumentTemplate, Order, Payment
from app.catalogue import seed_initial_templates


@pytest.fixture
def app():
    """Create test application with isolated in-memory SQLite database."""
    app = create_app()
    app.config.update({
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
def sample_user(app):
    """Create and return a sample user."""
    with app.app_context():
        user = User(
            full_name='Vikram Seth',
            email='vikram@example.com'
        )
        user.set_password('SecretPass456')
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def sample_template(app):
    """Create and return a sample document template."""
    with app.app_context():
        template = DocumentTemplate(
            slug='test-notice',
            title='Test Legal Notice',
            subtitle='Section 138 NI Act',
            category='notices',
            price=199,
            status='active',
            short_description='Short summary for test',
            long_description='Long detailed statutory explanation',
            icon='bi-file-text',
            badge_text='Popular',
            badge_class='bg-primary'
        )
        template.what_you_get = ['Word Document', 'PDF Document']
        template.information_needed = ['Name', 'Address', 'Cheque Number']
        template.important_notes = ['Send via RPAD within 30 days']
        db.session.add(template)
        db.session.commit()
        return template.id


# --- DocumentTemplate Tests ---

def test_document_template_json_helpers(app, sample_template):
    """Test that JSON helper properties correctly serialize and deserialize lists."""
    with app.app_context():
        template = db.session.get(DocumentTemplate, sample_template)
        assert isinstance(template.what_you_get, list)
        assert 'Word Document' in template.what_you_get
        assert 'PDF Document' in template.what_you_get
        assert len(template.information_needed) == 3
        assert 'Send via RPAD within 30 days' in template.important_notes


def test_document_template_slug_unique(app, sample_template):
    """Test that duplicate template slugs are rejected by database uniqueness constraint."""
    with app.app_context():
        dup = DocumentTemplate(
            slug='test-notice',  # same slug as sample_template
            title='Duplicate Notice',
            short_description='Desc',
            long_description='Desc'
        )
        db.session.add(dup)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


# --- Order Model Tests ---

def test_order_creation_and_relationships(app, sample_user, sample_template):
    """Test Order creation and bidirectional relationships with User and DocumentTemplate."""
    with app.app_context():
        user = db.session.get(User, sample_user)
        template = db.session.get(DocumentTemplate, sample_template)

        order = Order(
            order_number='ORD-20261023-0001',
            user=user,
            document_template=template,
            amount=199,
            status='pending'
        )
        order.form_data = {
            'drawer_name': 'Ramesh Kumar',
            'cheque_amount': 50000,
            'cheque_number': '123456'
        }
        db.session.add(order)
        db.session.commit()

        # Query back
        saved_order = Order.query.filter_by(order_number='ORD-20261023-0001').first()
        assert saved_order is not None
        assert saved_order.user.email == 'vikram@example.com'
        assert saved_order.document_template.slug == 'test-notice'
        assert saved_order.form_data['cheque_amount'] == 50000
        assert saved_order.status == 'pending'

        # Verify reverse relationship from user
        assert len(user.orders) == 1
        assert user.orders[0].order_number == 'ORD-20261023-0001'


def test_order_number_unique(app, sample_user, sample_template):
    """Test that duplicate order numbers violate database constraints."""
    with app.app_context():
        order1 = Order(
            order_number='ORD-UNIQUE-123',
            user_id=sample_user,
            document_template_id=sample_template,
            amount=199
        )
        order2 = Order(
            order_number='ORD-UNIQUE-123',  # Duplicate number
            user_id=sample_user,
            document_template_id=sample_template,
            amount=199
        )
        db.session.add(order1)
        db.session.commit()

        db.session.add(order2)
        with pytest.raises(Exception):
            db.session.commit()
        db.session.rollback()


# --- Payment Model Tests ---

def test_payment_creation_and_relationship(app, sample_user, sample_template):
    """Test Payment model creation, gateway reference tracking, and relationship to Order."""
    with app.app_context():
        order = Order(
            order_number='ORD-PAY-TEST-001',
            user_id=sample_user,
            document_template_id=sample_template,
            amount=199,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()

        payment = Payment(
            order=order,
            gateway='razorpay',
            gateway_order_id='order_MNOP123456',
            gateway_payment_id='pay_QRST789012',
            gateway_signature='sig_abcdef1234567890',
            amount=199,
            currency='INR',
            status='captured'
        )
        db.session.add(payment)
        db.session.commit()

        # Query back
        saved_payment = Payment.query.filter_by(gateway_order_id='order_MNOP123456').first()
        assert saved_payment is not None
        assert saved_payment.order.order_number == 'ORD-PAY-TEST-001'
        assert saved_payment.status == 'captured'
        assert len(order.payments) == 1
        assert order.payments[0].gateway_payment_id == 'pay_QRST789012'


def test_cascade_delete_order_removes_payments(app, sample_user, sample_template):
    """Test that deleting an Order automatically cascades to delete its associated Payments."""
    with app.app_context():
        order = Order(
            order_number='ORD-CASCADE-001',
            user_id=sample_user,
            document_template_id=sample_template,
            amount=199
        )
        db.session.add(order)
        db.session.commit()

        payment = Payment(
            order=order,
            gateway='razorpay',
            gateway_order_id='order_CASCADE_001',
            amount=199
        )
        db.session.add(payment)
        db.session.commit()

        payment_id = payment.id

        # Delete order
        db.session.delete(order)
        db.session.commit()

        # Payment should have been cascade-deleted
        assert db.session.get(Payment, payment_id) is None


# --- Seed Function Tests ---

def test_seed_initial_templates(app):
    """Test that seed_initial_templates populates the Cheque Bounce Notice idempotently."""
    with app.app_context():
        # Clean any existing templates in test DB
        DocumentTemplate.query.delete()
        db.session.commit()

        # First run seeds the Cheque Bounce Notice
        seed_initial_templates()
        tmpl = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').first()
        assert tmpl is not None
        assert tmpl.title == 'Cheque Bounce Notice'
        assert tmpl.price == 199
        assert any('Word' in item for item in tmpl.what_you_get)

        # Second run should be idempotent (no duplicates created)
        seed_initial_templates()
        count = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').count()
        assert count == 1
