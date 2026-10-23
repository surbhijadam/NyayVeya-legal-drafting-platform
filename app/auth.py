"""
Authentication routes: register, login, logout, dashboard.

Security notes:
- Passwords are hashed with Werkzeug's generate_password_hash (PBKDF2 by default)
- All forms have CSRF protection via Flask-WTF
- Email is normalised to lowercase to prevent duplicate accounts
- Login failures use a generic message to avoid revealing which field is wrong
- The dashboard route requires @login_required
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import RegistrationForm, LoginForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    # If already logged in, go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    form = RegistrationForm()

    if form.validate_on_submit():
        # Create new user with hashed password
        user = User(
            full_name=form.full_name.data.strip(),
            email=form.email.data.lower().strip(),
        )
        user.set_password(form.password.data)

        # Save to database
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page."""
    # If already logged in, go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        # Look up user by email
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        # Check password - use generic error to avoid revealing if email exists
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email address or password. Please try again.', 'danger')
            return render_template('auth/login.html', form=form)

        # Log the user in
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.full_name}!', 'success')

        # Redirect to the page they were trying to access, or dashboard
        next_page = request.args.get('next')
        # Security: only allow relative URLs to prevent open redirect attacks
        if next_page and not next_page.startswith('/'):
            next_page = None
        return redirect(next_page or url_for('auth.dashboard'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log the user out and redirect to home."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - shows account info and order history."""
    return render_template('auth/dashboard.html')
