"""
Tests for NyayVeya Administration Panel.

Covers:
1. Admin Authentication & Role-Based Authorization
2. Dashboard & Interactive Real-Time Business Analytics (Chart.js API)
3. Legal Document Templates CRUD & Validation
4. Order and Payment Inspection & Status Audit
5. User Governance, Status Toggle, and Self-Protection Guarantees
6. Customer Support Inquiries & Resolution Notes
7. Safe CLI Seeder Execution
"""
import json
import pytest
from app import create_app, db
from app.models import User, DocumentTemplate, Order, Payment, SupportInquiry


@pytest.fixture
def app():
    """Create test application with in-memory database."""
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key-123'
    })
    return app


@pytest.fixture
def client(app):
    """Test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def admin_user(app):
    """Create and return an active administrator user."""
    with app.app_context():
        admin = User(
            full_name='Master Administrator',
            email='admin@nyayveya.in',
            is_admin=True,
            is_active=True
        )
        admin.set_password('AdminPass123!')
        db.session.add(admin)
        db.session.commit()
        return admin.id


@pytest.fixture
def regular_user(app):
    """Create and return a regular non-admin customer user."""
    with app.app_context():
        customer = User(
            full_name='Customer Rahul',
            email='rahul@example.com',
            is_admin=False,
            is_active=True
        )
        customer.set_password('CustomerPass123!')
        db.session.add(customer)
        db.session.commit()
        return customer.id


@pytest.fixture
def inactive_admin(app):
    """Create and return an inactive administrator user."""
    with app.app_context():
        admin = User(
            full_name='Suspended Admin',
            email='suspended@nyayveya.in',
            is_admin=True,
            is_active=False
        )
        admin.set_password('AdminPass123!')
        db.session.add(admin)
        db.session.commit()
        return admin.id


# ==============================================================================
# 1. AUTHENTICATION & ACCESS CONTROL TESTS
# ==============================================================================

def test_unauthenticated_user_redirected_to_admin_login(client):
    """Unauthenticated users cannot access /admin routes and redirect to /admin/login."""
    response = client.get('/admin/dashboard', follow_redirects=False)
    assert response.status_code == 302
    assert '/admin/login' in response.headers['Location']


def test_regular_user_denied_admin_access(client, regular_user, app):
    """Regular non-admin users cannot access admin dashboard and are redirected to home."""
    # Login as regular customer
    client.post('/auth/login', data={
        'email': 'rahul@example.com',
        'password': 'CustomerPass123!'
    })

    # Try accessing admin panel
    response = client.get('/admin/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Access denied' in response.data or b'Administrator privileges are required' in response.data


def test_regular_user_denied_admin_api_access(client, regular_user):
    """Regular non-admin users get 403 Forbidden on admin API endpoints."""
    client.post('/auth/login', data={
        'email': 'rahul@example.com',
        'password': 'CustomerPass123!'
    })

    response = client.get('/admin/api/analytics')
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'Forbidden' in data['error']


def test_admin_login_page_renders(client):
    """Admin login page returns 200 with NyayVeya branding."""
    response = client.get('/admin/login')
    assert response.status_code == 200
    assert b'Nyay' in response.data
    assert b'Veya' in response.data
    assert b'Administration Gateway' in response.data


def test_admin_login_rejects_non_admin(client, regular_user):
    """Admin login form strictly rejects users without admin role."""
    response = client.post('/admin/login', data={
        'email': 'rahul@example.com',
        'password': 'CustomerPass123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'restricted strictly to authorized administrators' in response.data


def test_admin_login_rejects_inactive_admin(client, inactive_admin):
    """Admin login form rejects suspended admin accounts."""
    response = client.post('/admin/login', data={
        'email': 'suspended@nyayveya.in',
        'password': 'AdminPass123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'deactivated' in response.data or b'suspended' in response.data


def test_admin_login_succeeds_for_authorized_admin(client, admin_user):
    """Authorized administrator can successfully sign in."""
    response = client.post('/admin/login', data={
        'email': 'admin@nyayveya.in',
        'password': 'AdminPass123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Executive Business Dashboard' in response.data


def test_admin_logout(client, admin_user):
    """Admin logout signs out user and redirects to login."""
    client.post('/admin/login', data={
        'email': 'admin@nyayveya.in',
        'password': 'AdminPass123!'
    })

    response = client.get('/admin/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'signed out' in response.data


# ==============================================================================
# 2. DASHBOARD & REAL-TIME ANALYTICS API TESTS
# ==============================================================================

def test_admin_dashboard_metrics(client, admin_user, regular_user, app):
    """Admin dashboard shows real database statistics."""
    # Seed a template and order
    with app.app_context():
        tmpl = DocumentTemplate.query.first()
        order = Order(
            order_number='ORD-TEST-1001',
            user_id=regular_user,
            document_template_id=tmpl.id,
            amount=199,
            status='paid'
        )
        db.session.add(order)
        db.session.commit()

    # Login as admin
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    response = client.get('/admin/dashboard')
    assert response.status_code == 200
    assert b'ORD-TEST-1001' in response.data
    assert b'199' in response.data


def test_admin_api_analytics_endpoint(client, admin_user, regular_user, app):
    """Analytics API returns formatted JSON datasets for Chart.js."""
    with app.app_context():
        tmpl = DocumentTemplate.query.first()
        order = Order(
            order_number='ORD-ANALYTICS-1',
            user_id=regular_user,
            document_template_id=tmpl.id,
            amount=499,
            status='paid'
        )
        db.session.add(order)
        db.session.commit()

    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    # Test default 6m range
    response = client.get('/admin/api/analytics?range=6m')
    assert response.status_code == 200
    data = json.loads(response.data)

    assert data['range'] == '6m'
    assert 'labels' in data
    assert 'revenue' in data
    assert 'documents_sold' in data
    assert 'user_growth' in data
    assert 'order_status' in data
    assert sum(data['revenue']) >= 499
    assert sum(data['documents_sold']) >= 1
    assert data['order_status']['counts'][0] >= 1  # Paid orders

    # Test 7d, 30d, 12m, all filters
    for r in ['7d', '30d', '12m', 'all']:
        resp = client.get(f'/admin/api/analytics?range={r}')
        assert resp.status_code == 200
        d = json.loads(resp.data)
        assert d['range'] == r
        assert len(d['labels']) > 0


# ==============================================================================
# 3. LEGAL DOCUMENT TEMPLATES CRUD TESTS
# ==============================================================================

def test_template_list_and_search(client, admin_user):
    """Admin can view templates list and filter by search and category."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    response = client.get('/admin/templates')
    assert response.status_code == 200
    assert b'Cheque Bounce Notice' in response.data

    # Search for specific template
    search_resp = client.get('/admin/templates?q=cheque')
    assert search_resp.status_code == 200
    assert b'Cheque Bounce' in search_resp.data


def test_template_create_validation_and_creation(client, admin_user, app):
    """Admin can create a new document template with statutory metadata."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    new_data = {
        'slug': 'commercial-lease-agreement',
        'title': 'Commercial Lease Agreement',
        'subtitle': 'Statutory agreement under Transfer of Property Act, 1882',
        'category': 'agreements',
        'price': 499,
        'status': 'active',
        'language': 'English',
        'short_description': 'Comprehensive commercial shop or office lease contract.',
        'long_description': 'Statutory commercial property lease deed setting out rental terms, escalations, security deposit, and dispute resolution.',
        'badge_text': 'Commercial',
        'badge_class': 'bg-primary',
        'icon': 'bi-file-text',
        'what_you_get': 'Instant editable Word file\nPrint-ready PDF\nStamp duty guidelines',
        'information_needed': 'Lessor details\nLessee details\nPremises address and carpet area',
        'important_notes': 'Mandatory Stamp Duty required\nRegistration compulsory if term exceeds 11 months',
        'faqs': 'Is registration compulsory? | Yes, for leases exceeding 11 months.'
    }

    response = client.post('/admin/templates/new', data=new_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Commercial Lease Agreement' in response.data

    # Verify template in database
    with app.app_context():
        created = DocumentTemplate.query.filter_by(slug='commercial-lease-agreement').first()
        assert created is not None
        assert created.price == 499
        assert created.category == 'agreements'
        assert created.language == 'English'
        assert 'Instant editable Word file' in created.what_you_get
        assert len(created.faqs) == 1
        assert created.faqs[0]['question'] == 'Is registration compulsory?'


def test_template_prevent_duplicate_slug(client, admin_user):
    """Admin form rejects duplicate slug creation."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    duplicate_data = {
        'slug': 'cheque-bounce-notice',  # Already exists in catalogue
        'title': 'Duplicate Cheque Bounce',
        'category': 'notices',
        'price': 199,
        'status': 'active',
        'language': 'English',
        'short_description': 'Duplicate test',
        'long_description': 'Duplicate test long'
    }

    response = client.post('/admin/templates/new', data=duplicate_data)
    assert response.status_code == 200
    assert b'already exists' in response.data


def test_template_edit(client, admin_user, app):
    """Admin can edit an existing document template."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    with app.app_context():
        tmpl = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').first()
        tmpl_id = tmpl.id

    edit_data = {
        'slug': 'cheque-bounce-notice',
        'title': 'Cheque Bounce Demand Notice (Updated)',
        'subtitle': 'Updated demand under Section 138 of NI Act',
        'category': 'notices',
        'price': 249,
        'status': 'active',
        'language': 'English',
        'short_description': 'Updated short description for notice.',
        'long_description': 'Updated statutory legal description.',
        'badge_text': 'Updated',
        'badge_class': 'bg-primary',
        'icon': 'bi-file-earmark-medical',
        'what_you_get': 'Item 1\nItem 2',
        'information_needed': 'Requirement 1',
        'important_notes': 'Note 1',
        'faqs': 'Question 1 | Answer 1'
    }

    response = client.post(f'/admin/templates/{tmpl_id}/edit', data=edit_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'has been updated successfully' in response.data

    with app.app_context():
        updated = db.session.get(DocumentTemplate, tmpl_id)
        assert updated.title == 'Cheque Bounce Demand Notice (Updated)'
        assert updated.price == 249


def test_template_toggle_status(client, admin_user, app):
    """Admin can cycle or toggle template status."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    with app.app_context():
        tmpl = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').first()
        tmpl_id = tmpl.id

    # POST to toggle status
    response = client.post(f'/admin/templates/{tmpl_id}/toggle-status', data={'status': 'draft'}, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        updated = db.session.get(DocumentTemplate, tmpl_id)
        assert updated.status == 'draft'


def test_template_delete_safeguard(client, admin_user, regular_user, app):
    """Templates with existing orders are soft-deactivated to draft rather than deleted."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    with app.app_context():
        tmpl = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').first()
        order = Order(
            order_number='ORD-SAFEGUARD-1',
            user_id=regular_user,
            document_template_id=tmpl.id,
            amount=199,
            status='paid'
        )
        db.session.add(order)
        db.session.commit()
        tmpl_id = tmpl.id

    # Attempt deletion
    response = client.post(f'/admin/templates/{tmpl_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert b'cannot be deleted because it is associated with' in response.data

    with app.app_context():
        tmpl_after = db.session.get(DocumentTemplate, tmpl_id)
        assert tmpl_after is not None
        assert tmpl_after.status == 'draft'


# ==============================================================================
# 4. ORDER & PAYMENT MANAGEMENT TESTS
# ==============================================================================

def test_orders_list_and_filters(client, admin_user, regular_user, app):
    """Admin can view orders list and filter by status."""
    with app.app_context():
        tmpl = DocumentTemplate.query.first()
        o1 = Order(order_number='ORD-FLT-1', user_id=regular_user, document_template_id=tmpl.id, amount=199, status='paid')
        o2 = Order(order_number='ORD-FLT-2', user_id=regular_user, document_template_id=tmpl.id, amount=199, status='pending')
        db.session.add_all([o1, o2])
        db.session.commit()

    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    response = client.get('/admin/orders')
    assert response.status_code == 200
    assert b'ORD-FLT-1' in response.data
    assert b'ORD-FLT-2' in response.data

    # Filter paid
    paid_resp = client.get('/admin/orders?status=paid')
    assert b'ORD-FLT-1' in paid_resp.data
    assert b'ORD-FLT-2' not in paid_resp.data


def test_order_detail_and_status_update(client, admin_user, regular_user, app):
    """Admin can inspect order details and safely update status."""
    with app.app_context():
        tmpl = DocumentTemplate.query.first()
        order = Order(
            order_number='ORD-AUDIT-99',
            user_id=regular_user,
            document_template_id=tmpl.id,
            amount=199,
            status='pending',
            form_data_json=json.dumps({'drawer_name': 'Anil Sharma', 'cheque_amount': '50000'})
        )
        db.session.add(order)
        db.session.commit()
        order_id = order.id

    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    # View order detail
    detail_resp = client.get(f'/admin/orders/{order_id}')
    assert detail_resp.status_code == 200
    assert b'ORD-AUDIT-99' in detail_resp.data
    assert b'Anil Sharma' in detail_resp.data

    # Update status to refunded
    update_resp = client.post(f'/admin/orders/{order_id}/status', data={'status': 'refunded'}, follow_redirects=True)
    assert update_resp.status_code == 200
    assert b'status updated from PENDING to REFUNDED' in update_resp.data

    with app.app_context():
        updated_order = db.session.get(Order, order_id)
        assert updated_order.status == 'refunded'


# ==============================================================================
# 5. USER GOVERNANCE & SELF-PROTECTION TESTS
# ==============================================================================

def test_users_list_and_search(client, admin_user, regular_user):
    """Admin can view user directory and search accounts."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    response = client.get('/admin/users')
    assert response.status_code == 200
    assert b'Master Administrator' in response.data
    assert b'Customer Rahul' in response.data

    # Search user
    search_resp = client.get('/admin/users?q=rahul')
    assert b'Customer Rahul' in search_resp.data


def test_user_toggle_status_and_self_protection(client, admin_user, regular_user, app):
    """Admin can toggle customer status, but is protected from self-deactivation."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    # Suspend customer
    resp = client.post(f'/admin/users/{regular_user}/toggle-status', follow_redirects=True)
    assert resp.status_code == 200
    assert b'suspended' in resp.data

    with app.app_context():
        customer = db.session.get(User, regular_user)
        assert customer.is_active is False

    # CRITICAL: Attempt self-deactivation
    self_resp = client.post(f'/admin/users/{admin_user}/toggle-status', follow_redirects=True)
    assert self_resp.status_code == 200
    assert b'cannot deactivate your own administrative account' in self_resp.data

    with app.app_context():
        admin = db.session.get(User, admin_user)
        assert admin.is_active is True  # Must stay active!


def test_user_toggle_role_and_self_protection(client, admin_user, regular_user, app):
    """Admin can promote customer, but cannot revoke own admin privileges."""
    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    # Promote customer to admin
    resp = client.post(f'/admin/users/{regular_user}/toggle-role', follow_redirects=True)
    assert resp.status_code == 200
    assert b'updated to Administrator' in resp.data

    with app.app_context():
        customer = db.session.get(User, regular_user)
        assert customer.is_admin is True

    # CRITICAL: Attempt self-demotion
    self_resp = client.post(f'/admin/users/{admin_user}/toggle-role', follow_redirects=True)
    assert self_resp.status_code == 200
    assert b'cannot remove administrator privileges from your own account' in self_resp.data

    with app.app_context():
        admin = db.session.get(User, admin_user)
        assert admin.is_admin is True  # Must stay admin!


# ==============================================================================
# 6. SUPPORT INQUIRIES & RESOLUTION TESTS
# ==============================================================================

def test_contact_form_persists_inquiry(client, app):
    """Customer submitting contact form persists SupportInquiry into database."""
    response = client.post('/contact', data={
        'name': 'Priya Nair',
        'email': 'priya@example.com',
        'subject': 'Order & Download Support',
        'message': 'Need assistance with downloading cheque bounce draft.'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'received your message' in response.data

    with app.app_context():
        inquiry = SupportInquiry.query.filter_by(email='priya@example.com').first()
        assert inquiry is not None
        assert inquiry.name == 'Priya Nair'
        assert inquiry.status == 'open'


def test_admin_support_triage(client, admin_user, app):
    """Admin can view inquiries, update status, and record internal notes."""
    with app.app_context():
        inq = SupportInquiry(
            name='Vikram Seth',
            email='vikram@example.com',
            subject='Template Request',
            message='Can you add a partnership dissolution deed?',
            status='open'
        )
        db.session.add(inq)
        db.session.commit()
        inq_id = inq.id

    client.post('/admin/login', data={'email': 'admin@nyayveya.in', 'password': 'AdminPass123!'})

    # View list
    list_resp = client.get('/admin/support')
    assert list_resp.status_code == 200
    assert b'Vikram Seth' in list_resp.data

    # View detail
    detail_resp = client.get(f'/admin/support/{inq_id}')
    assert detail_resp.status_code == 200
    assert b'partnership dissolution deed' in detail_resp.data

    # Update status to resolved with notes
    update_resp = client.post(f'/admin/support/{inq_id}/status', data={
        'status': 'resolved',
        'admin_notes': 'Informed customer that partnership templates are planned for Q3.'
    }, follow_redirects=True)
    assert update_resp.status_code == 200
    assert b'updated successfully' in update_resp.data

    with app.app_context():
        updated_inq = db.session.get(SupportInquiry, inq_id)
        assert updated_inq.status == 'resolved'
        assert 'planned for Q3' in updated_inq.admin_notes


# ==============================================================================
# 7. CLI SEEDER TEST
# ==============================================================================

def test_cli_create_admin_command(app):
    """CLI create-admin command successfully creates or promotes an administrator."""
    runner = app.test_cli_runner()
    result = runner.invoke(args=[
        'create-admin',
        '--email', 'cli_admin@nyayveya.in',
        '--password', 'SecurePass123!',
        '--name', 'CLI Super Admin'
    ])
    assert result.exit_code == 0
    assert 'Administrator account created' in result.output

    with app.app_context():
        user = User.query.filter_by(email='cli_admin@nyayveya.in').first()
        assert user is not None
        assert user.is_admin is True
        assert user.is_active is True
        assert user.check_password('SecurePass123!')
