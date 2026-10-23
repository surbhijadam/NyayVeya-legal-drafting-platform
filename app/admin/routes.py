"""
NyayVeya Administration Routes.

Handles:
- Secure Administrator Authentication (/admin/login, /admin/logout)
- Real-time Metrics Dashboard & Interactive Analytics API
- Legal Document Template Management (CRUD, status toggles, preview)
- Order & Verified Payment Management
- User Directory & Account Governance
- Customer Support Inquiries & Triage
"""
import os
import json
from datetime import datetime, timedelta, timezone
from flask import (
    render_template, redirect, url_for, flash, request,
    jsonify, current_app, abort
)
from flask_login import login_user, logout_user, current_user
from sqlalchemy import or_, desc, func

from app import db
from app.models import User, DocumentTemplate, Order, Payment, SupportInquiry
from app.catalogue import DOCUMENT_CATEGORIES
from app.admin import admin_bp
from app.admin.decorators import admin_required
from app.admin.forms import (
    AdminLoginForm, TemplateForm, OrderStatusForm,
    SupportInquiryUpdateForm, UserUpdateForm
)


# ==============================================================================
# AUTHENTICATION
# ==============================================================================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Dedicated admin login portal.
    Restricted strictly to users with is_admin=True and is_active=True.
    """
    if current_user.is_authenticated and getattr(current_user, 'is_admin', False):
        return redirect(url_for('admin.dashboard'))

    form = AdminLoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        # Check credentials
        if user is None or not user.check_password(form.password.data):
            flash('Invalid administrator credentials. Please check your email and password.', 'danger')
            return render_template('admin/login.html', form=form)

        # Authorization: Must be active
        if not user.is_active:
            flash('This administrator account has been deactivated. Please contact the system owner.', 'danger')
            return render_template('admin/login.html', form=form)

        # Authorization: Must have admin role
        if not user.is_admin:
            flash('Access denied. This login portal is restricted strictly to authorized administrators.', 'danger')
            return render_template('admin/login.html', form=form)

        login_user(user, remember=form.remember_me.data)
        flash(f'Signed in successfully as Administrator: {user.full_name}', 'success')

        next_page = request.args.get('next')
        if next_page and not next_page.startswith('/'):
            next_page = None
        return redirect(next_page or url_for('admin.dashboard'))

    return render_template('admin/login.html', form=form)


@admin_bp.route('/logout')
@admin_required
def logout():
    """Admin logout handler."""
    logout_user()
    flash('You have been signed out from the NyayVeya Administration Panel.', 'info')
    return redirect(url_for('admin.login'))


# ==============================================================================
# DASHBOARD & REAL-TIME ANALYTICS
# ==============================================================================

@admin_bp.route('/')
@admin_required
def root():
    """Redirect /admin to /admin/dashboard."""
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """
    Main Administration Dashboard.
    Presents verified real-time database statistics and activity feeds.
    """
    total_users = User.query.count()
    total_templates = DocumentTemplate.query.count()
    total_orders = Order.query.count()

    # Order Status counts
    paid_orders = Order.query.filter_by(status='paid').count()
    pending_orders = Order.query.filter_by(status='pending').count()
    failed_orders = Order.query.filter_by(status='failed').count()
    refunded_orders = Order.query.filter_by(status='refunded').count()

    # Total verified revenue in INR (from paid orders)
    revenue_result = db.session.query(
        func.coalesce(func.sum(Order.amount), 0)
    ).filter(Order.status == 'paid').scalar()
    total_revenue = int(revenue_result or 0)

    # Open support inquiries
    open_inquiries = SupportInquiry.query.filter_by(status='open').count()

    # Recent orders and templates
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(6).all()
    recent_templates = DocumentTemplate.query.order_by(DocumentTemplate.updated_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        total_templates=total_templates,
        total_orders=total_orders,
        paid_orders=paid_orders,
        pending_orders=pending_orders,
        failed_orders=failed_orders,
        refunded_orders=refunded_orders,
        total_revenue=total_revenue,
        open_inquiries=open_inquiries,
        recent_orders=recent_orders,
        recent_templates=recent_templates
    )


@admin_bp.route('/api/analytics')
@admin_required
def api_analytics():
    """
    JSON API for dynamic Chart.js visualizations.
    Supports range: '7d', '30d', '6m', '12m', 'all'.
    """
    date_range = request.args.get('range', '6m').lower()
    now = datetime.now(timezone.utc)

    # Determine start date and bucket resolution
    if date_range == '7d':
        days = 7
        labels = []
        date_keys = []
        for i in range(days - 1, -1, -1):
            d = now - timedelta(days=i)
            labels.append(d.strftime('%a %d %b'))
            date_keys.append(d.strftime('%Y-%m-%d'))
        bucket_format = '%Y-%m-%d'
    elif date_range == '30d':
        days = 30
        labels = []
        date_keys = []
        for i in range(days - 1, -1, -1):
            d = now - timedelta(days=i)
            labels.append(d.strftime('%d %b'))
            date_keys.append(d.strftime('%Y-%m-%d'))
        bucket_format = '%Y-%m-%d'
    elif date_range == '12m':
        months_count = 12
        labels = []
        date_keys = []
        # Generate month keys
        cur_year = now.year
        cur_month = now.month
        for i in range(months_count - 1, -1, -1):
            m = cur_month - i
            y = cur_year
            while m <= 0:
                m += 12
                y -= 1
            dt = datetime(y, m, 1, tzinfo=timezone.utc)
            labels.append(dt.strftime('%b %Y'))
            date_keys.append(dt.strftime('%Y-%m'))
        bucket_format = '%Y-%m'
    elif date_range == 'all':
        # All time: past 12 months minimum or all historical
        months_count = 12
        labels = []
        date_keys = []
        cur_year = now.year
        cur_month = now.month
        for i in range(months_count - 1, -1, -1):
            m = cur_month - i
            y = cur_year
            while m <= 0:
                m += 12
                y -= 1
            dt = datetime(y, m, 1, tzinfo=timezone.utc)
            labels.append(dt.strftime('%b %Y'))
            date_keys.append(dt.strftime('%Y-%m'))
        bucket_format = '%Y-%m'
    else:  # default '6m'
        months_count = 6
        labels = []
        date_keys = []
        cur_year = now.year
        cur_month = now.month
        for i in range(months_count - 1, -1, -1):
            m = cur_month - i
            y = cur_year
            while m <= 0:
                m += 12
                y -= 1
            dt = datetime(y, m, 1, tzinfo=timezone.utc)
            labels.append(dt.strftime('%b %Y'))
            date_keys.append(dt.strftime('%Y-%m'))
        bucket_format = '%Y-%m'

    # Initialize aggregators
    revenue_by_key = {k: 0 for k in date_keys}
    docs_sold_by_key = {k: 0 for k in date_keys}
    users_by_key = {k: 0 for k in date_keys}

    # Fetch paid orders to calculate revenue and documents sold
    paid_orders = Order.query.filter(Order.status == 'paid').all()
    for o in paid_orders:
        if o.created_at:
            key = o.created_at.strftime(bucket_format)
            if key in revenue_by_key:
                revenue_by_key[key] += o.amount
                docs_sold_by_key[key] += 1

    # Fetch all users to calculate user growth
    users = User.query.all()
    for u in users:
        if u.created_at:
            key = u.created_at.strftime(bucket_format)
            if key in users_by_key:
                users_by_key[key] += 1

    # Cumulative user growth
    user_growth_cumulative = []
    running_user_total = User.query.filter(
        User.created_at < datetime.strptime(date_keys[0], bucket_format).replace(tzinfo=timezone.utc)
    ).count() if date_keys else 0

    for k in date_keys:
        running_user_total += users_by_key[k]
        user_growth_cumulative.append(running_user_total)

    # Order status breakdown
    order_status_counts = {
        'Paid': Order.query.filter_by(status='paid').count(),
        'Pending': Order.query.filter_by(status='pending').count(),
        'Failed': Order.query.filter_by(status='failed').count(),
        'Refunded': Order.query.filter_by(status='refunded').count()
    }

    return jsonify({
        'range': date_range,
        'labels': labels,
        'revenue': [revenue_by_key[k] for k in date_keys],
        'documents_sold': [docs_sold_by_key[k] for k in date_keys],
        'user_growth': user_growth_cumulative,
        'new_users': [users_by_key[k] for k in date_keys],
        'order_status': {
            'labels': list(order_status_counts.keys()),
            'counts': list(order_status_counts.values())
        }
    })


# ==============================================================================
# LEGAL DOCUMENT TEMPLATES CRUD
# ==============================================================================

@admin_bp.route('/templates')
@admin_required
def templates_list():
    """Paginated list of document templates with search and filtering."""
    query_str = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    language = request.args.get('language', '').strip()
    page = request.args.get('page', 1, type=int)

    query = DocumentTemplate.query

    if query_str:
        query = query.filter(
            or_(
                DocumentTemplate.title.ilike(f'%{query_str}%'),
                DocumentTemplate.slug.ilike(f'%{query_str}%'),
                DocumentTemplate.short_description.ilike(f'%{query_str}%')
            )
        )

    if category and category != 'all':
        query = query.filter(DocumentTemplate.category == category)

    if status and status != 'all':
        query = query.filter(DocumentTemplate.status == status)

    if language and language != 'all':
        query = query.filter(DocumentTemplate.language == language)

    pagination = query.order_by(DocumentTemplate.title.asc()).paginate(
        page=page, per_page=12, error_out=False
    )

    return render_template(
        'admin/templates/index.html',
        pagination=pagination,
        templates=pagination.items,
        query_str=query_str,
        category=category,
        status=status,
        language=language,
        categories=DOCUMENT_CATEGORIES
    )


@admin_bp.route('/templates/new', methods=['GET', 'POST'])
@admin_required
def template_create():
    """Create a new legal document template."""
    form = TemplateForm()

    if form.validate_on_submit():
        # Check slug uniqueness
        existing = DocumentTemplate.query.filter_by(slug=form.slug.data.strip().lower()).first()
        if existing:
            form.slug.errors.append('A template with this slug already exists. Please pick a unique slug.')
            return render_template('admin/templates/form.html', form=form, title='Add New Legal Template')

        # Parse multiline fields
        what_you_get_list = [line.strip() for line in form.what_you_get.data.splitlines() if line.strip()]
        info_needed_list = [line.strip() for line in form.information_needed.data.splitlines() if line.strip()]
        notes_list = [line.strip() for line in form.important_notes.data.splitlines() if line.strip()]

        # Parse FAQs (format: Question | Answer)
        faqs_list = []
        for line in form.faqs.data.splitlines():
            line = line.strip()
            if not line:
                continue
            if '|' in line:
                q, a = line.split('|', 1)
                faqs_list.append({'question': q.strip(), 'answer': a.strip()})
            else:
                faqs_list.append({'question': line, 'answer': ''})

        template = DocumentTemplate(
            slug=form.slug.data.strip().lower(),
            title=form.title.data.strip(),
            subtitle=form.subtitle.data.strip() if form.subtitle.data else None,
            category=form.category.data,
            price=form.price.data,
            status=form.status.data,
            language=form.language.data,
            short_description=form.short_description.data.strip(),
            long_description=form.long_description.data.strip(),
            icon=form.icon.data.strip() if form.icon.data else 'bi-file-earmark-medical',
            badge_text=form.badge_text.data.strip() if form.badge_text.data else None,
            badge_class=form.badge_class.data
        )
        template.what_you_get = what_you_get_list
        template.information_needed = info_needed_list
        template.important_notes = notes_list
        template.faqs = faqs_list

        db.session.add(template)
        db.session.commit()

        flash(f'Legal document template "{template.title}" created successfully.', 'success')
        return redirect(url_for('admin.templates_list'))

    return render_template('admin/templates/form.html', form=form, title='Add New Legal Template', is_edit=False)


@admin_bp.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
@admin_required
def template_edit(template_id):
    """Edit an existing legal document template."""
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        abort(404)

    form = TemplateForm(obj=template)

    if request.method == 'GET':
        # Populate multiline fields
        form.what_you_get.data = '\n'.join(template.what_you_get or [])
        form.information_needed.data = '\n'.join(template.information_needed or [])
        form.important_notes.data = '\n'.join(template.important_notes or [])

        # Format FAQs back into Question | Answer
        faq_lines = []
        for faq in (template.faqs or []):
            if isinstance(faq, dict):
                faq_lines.append(f"{faq.get('question', '')} | {faq.get('answer', '')}")
            else:
                faq_lines.append(str(faq))
        form.faqs.data = '\n'.join(faq_lines)

    if form.validate_on_submit():
        new_slug = form.slug.data.strip().lower()
        if new_slug != template.slug:
            existing = DocumentTemplate.query.filter_by(slug=new_slug).first()
            if existing:
                form.slug.errors.append('Slug is already taken by another template.')
                return render_template('admin/templates/form.html', form=form, template=template, title='Edit Legal Template', is_edit=True)
            template.slug = new_slug

        template.title = form.title.data.strip()
        template.subtitle = form.subtitle.data.strip() if form.subtitle.data else None
        template.category = form.category.data
        template.price = form.price.data
        template.status = form.status.data
        template.language = form.language.data
        template.short_description = form.short_description.data.strip()
        template.long_description = form.long_description.data.strip()
        template.icon = form.icon.data.strip() if form.icon.data else 'bi-file-earmark-medical'
        template.badge_text = form.badge_text.data.strip() if form.badge_text.data else None
        template.badge_class = form.badge_class.data

        template.what_you_get = [line.strip() for line in form.what_you_get.data.splitlines() if line.strip()]
        template.information_needed = [line.strip() for line in form.information_needed.data.splitlines() if line.strip()]
        template.important_notes = [line.strip() for line in form.important_notes.data.splitlines() if line.strip()]

        faqs_list = []
        for line in form.faqs.data.splitlines():
            line = line.strip()
            if not line:
                continue
            if '|' in line:
                q, a = line.split('|', 1)
                faqs_list.append({'question': q.strip(), 'answer': a.strip()})
            else:
                faqs_list.append({'question': line, 'answer': ''})
        template.faqs = faqs_list

        db.session.commit()
        flash(f'Template "{template.title}" has been updated successfully.', 'success')
        return redirect(url_for('admin.templates_list'))

    return render_template('admin/templates/form.html', form=form, template=template, title='Edit Legal Template', is_edit=True)


@admin_bp.route('/templates/<int:template_id>')
@admin_required
def template_detail(template_id):
    """View details and order statistics for a specific template."""
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        abort(404)

    total_orders = Order.query.filter_by(document_template_id=template.id).count()
    paid_orders = Order.query.filter_by(document_template_id=template.id, status='paid').count()
    revenue = db.session.query(func.coalesce(func.sum(Order.amount), 0)).filter(
        Order.document_template_id == template.id,
        Order.status == 'paid'
    ).scalar() or 0

    return render_template(
        'admin/templates/detail.html',
        template=template,
        total_orders=total_orders,
        paid_orders=paid_orders,
        revenue=int(revenue)
    )


@admin_bp.route('/templates/<int:template_id>/toggle-status', methods=['POST'])
@admin_required
def template_toggle_status(template_id):
    """Toggle publication status between active, coming_soon, or draft."""
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        abort(404)

    target_status = request.form.get('status')
    if target_status in ['active', 'coming_soon', 'draft']:
        template.status = target_status
    else:
        # Default cycle: active -> draft -> coming_soon -> active
        if template.status == 'active':
            template.status = 'draft'
        elif template.status == 'draft':
            template.status = 'coming_soon'
        else:
            template.status = 'active'

    db.session.commit()
    flash(f'Status for "{template.title}" changed to {template.status.replace("_", " ").title()}.', 'success')
    return redirect(request.referrer or url_for('admin.templates_list'))


@admin_bp.route('/templates/<int:template_id>/delete', methods=['POST'])
@admin_required
def template_delete(template_id):
    """
    Safely delete a template. If orders already exist referencing this template,
    it is deactivated to 'draft' instead of hard-deleted to preserve financial history.
    """
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        abort(404)

    order_count = Order.query.filter_by(document_template_id=template.id).count()
    if order_count > 0:
        template.status = 'draft'
        db.session.commit()
        flash(
            f'Template "{template.title}" cannot be deleted because it is associated with {order_count} historical order(s). Its status has been set to Draft instead.',
            'warning'
        )
    else:
        title = template.title
        db.session.delete(template)
        db.session.commit()
        flash(f'Template "{title}" has been permanently deleted.', 'info')

    return redirect(url_for('admin.templates_list'))


# ==============================================================================
# ORDER & PAYMENT MANAGEMENT
# ==============================================================================

@admin_bp.route('/orders')
@admin_required
def orders_list():
    """Paginated list of orders with search and filtering."""
    query_str = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    template_id = request.args.get('template_id', type=int)
    page = request.args.get('page', 1, type=int)

    query = Order.query.join(User).join(DocumentTemplate)

    if query_str:
        query = query.filter(
            or_(
                Order.order_number.ilike(f'%{query_str}%'),
                User.full_name.ilike(f'%{query_str}%'),
                User.email.ilike(f'%{query_str}%')
            )
        )

    if status and status != 'all':
        query = query.filter(Order.status == status)

    if template_id:
        query = query.filter(Order.document_template_id == template_id)

    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    templates = DocumentTemplate.query.order_by(DocumentTemplate.title.asc()).all()

    return render_template(
        'admin/orders/index.html',
        pagination=pagination,
        orders=pagination.items,
        query_str=query_str,
        status=status,
        template_id=template_id,
        templates=templates
    )


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    """Detailed view of an order, customer details, files, and transaction status."""
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    # Check file existence on filesystem
    docs_folder = current_app.config.get('GENERATED_DOCUMENTS_FOLDER', '')
    docx_exists = False
    pdf_exists = False
    if order.docx_filename and os.path.isfile(os.path.join(docs_folder, order.docx_filename)):
        docx_exists = True
    if order.pdf_filename and os.path.isfile(os.path.join(docs_folder, order.pdf_filename)):
        pdf_exists = True

    status_form = OrderStatusForm(status=order.status)

    return render_template(
        'admin/orders/detail.html',
        order=order,
        docx_exists=docx_exists,
        pdf_exists=pdf_exists,
        status_form=status_form
    )


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def order_update_status(order_id):
    """Update order status (e.g. pending, paid, refunded, failed)."""
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    form = OrderStatusForm()
    if form.validate_on_submit():
        old_status = order.status
        order.status = form.status.data
        db.session.commit()
        flash(f'Order {order.order_number} status updated from {old_status.upper()} to {order.status.upper()}.', 'success')
    else:
        flash('Invalid status data provided.', 'danger')

    return redirect(url_for('admin.order_detail', order_id=order.id))


# ==============================================================================
# USER MANAGEMENT
# ==============================================================================

@admin_bp.route('/users')
@admin_required
def users_list():
    """Paginated list of registered users."""
    query_str = request.args.get('q', '').strip()
    role = request.args.get('role', '').strip()
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = User.query

    if query_str:
        query = query.filter(
            or_(
                User.full_name.ilike(f'%{query_str}%'),
                User.email.ilike(f'%{query_str}%')
            )
        )

    if role == 'admin':
        query = query.filter(User.is_admin.is_(True))
    elif role == 'customer':
        query = query.filter(User.is_admin.is_(False))

    if status == 'active':
        query = query.filter(User.is_active.is_(True))
    elif status == 'disabled':
        query = query.filter(User.is_active.is_(False))

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template(
        'admin/users/index.html',
        pagination=pagination,
        users=pagination.items,
        query_str=query_str,
        role=role,
        status=status
    )


@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """User profile overview and full order history."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    total_spent = sum(o.amount for o in orders if o.status == 'paid')

    return render_template(
        'admin/users/detail.html',
        user=user,
        orders=orders,
        total_spent=total_spent
    )


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def user_toggle_status(user_id):
    """Activate or deactivate user account with safety checks."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    # CRITICAL SECURITY RULE: Prevent self-deactivation
    if user.id == current_user.id:
        flash('Security Alert: You cannot deactivate your own administrative account.', 'danger')
        return redirect(url_for('admin.users_list'))

    user.is_active = not user.is_active
    db.session.commit()

    action = 'activated' if user.is_active else 'suspended'
    flash(f'Account for {user.email} has been {action}.', 'success')
    return redirect(request.referrer or url_for('admin.users_list'))


@admin_bp.route('/users/<int:user_id>/toggle-role', methods=['POST'])
@admin_required
def user_toggle_role(user_id):
    """Grant or revoke admin privileges with safety checks."""
    user = db.session.get(User, user_id)
    if not user:
        abort(404)

    # CRITICAL SECURITY RULE: Prevent self-demotion
    if user.id == current_user.id:
        flash('Security Alert: You cannot remove administrator privileges from your own account.', 'danger')
        return redirect(url_for('admin.users_list'))

    user.is_admin = not user.is_admin
    db.session.commit()

    role_str = 'Administrator' if user.is_admin else 'Customer'
    flash(f'Role for {user.email} updated to {role_str}.', 'success')
    return redirect(request.referrer or url_for('admin.users_list'))


# ==============================================================================
# SUPPORT INQUIRIES MANAGEMENT
# ==============================================================================

@admin_bp.route('/support')
@admin_required
def support_list():
    """List customer support inquiries and contact form submissions."""
    query_str = request.args.get('q', '').strip()
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = SupportInquiry.query

    if query_str:
        query = query.filter(
            or_(
                SupportInquiry.name.ilike(f'%{query_str}%'),
                SupportInquiry.email.ilike(f'%{query_str}%'),
                SupportInquiry.subject.ilike(f'%{query_str}%'),
                SupportInquiry.message.ilike(f'%{query_str}%')
            )
        )

    if status and status != 'all':
        query = query.filter(SupportInquiry.status == status)

    pagination = query.order_by(SupportInquiry.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template(
        'admin/support/index.html',
        pagination=pagination,
        inquiries=pagination.items,
        query_str=query_str,
        status=status
    )


@admin_bp.route('/support/<int:inquiry_id>')
@admin_required
def support_detail(inquiry_id):
    """View detailed inquiry and resolution history."""
    inquiry = db.session.get(SupportInquiry, inquiry_id)
    if not inquiry:
        abort(404)

    form = SupportInquiryUpdateForm(
        status=inquiry.status,
        admin_notes=inquiry.admin_notes
    )

    return render_template(
        'admin/support/detail.html',
        inquiry=inquiry,
        form=form
    )


@admin_bp.route('/support/<int:inquiry_id>/status', methods=['POST'])
@admin_required
def support_update_status(inquiry_id):
    """Update status and internal notes for a support inquiry."""
    inquiry = db.session.get(SupportInquiry, inquiry_id)
    if not inquiry:
        abort(404)

    form = SupportInquiryUpdateForm()
    if form.validate_on_submit():
        inquiry.status = form.status.data
        inquiry.admin_notes = form.admin_notes.data.strip() if form.admin_notes.data else None
        db.session.commit()
        flash(f'Support inquiry #{inquiry.id} updated successfully.', 'success')
    else:
        flash('Could not update inquiry status.', 'danger')

    return redirect(url_for('admin.support_detail', inquiry_id=inquiry.id))
