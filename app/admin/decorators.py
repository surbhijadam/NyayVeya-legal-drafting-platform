"""
Security decorators for the NyayVeya Admin Panel.
Enforces strict least-privilege role checking and session verification.
"""
from functools import wraps
from flask import abort, flash, redirect, request, url_for, jsonify
from flask_login import current_user


def admin_required(f):
    """
    Decorator that ensures the current user is authenticated, has administrative role,
    and their account is currently active.
    
    If unauthenticated:
        - API requests receive 401 Unauthorized JSON.
        - Browser requests redirect to /admin/login with next URL.
        
    If authenticated but not admin (or account inactive):
        - API requests receive 403 Forbidden JSON.
        - Browser requests redirect to customer home with an access-denied flash message.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_api = request.path.startswith('/admin/api/') or request.is_json

        if not current_user.is_authenticated:
            if is_api:
                return jsonify({'error': 'Authentication required. Please log in.'}), 401
            flash('Please log in with an administrator account to access this area.', 'warning')
            return redirect(url_for('admin.login', next=request.url))

        if not getattr(current_user, 'is_admin', False) or not getattr(current_user, 'is_active', True):
            if is_api:
                return jsonify({'error': 'Forbidden. Administrator privileges required.'}), 403
            flash('Access denied. Administrator privileges are required to view this area.', 'danger')
            return redirect(url_for('main.home'))

        return f(*args, **kwargs)
    return decorated_function
