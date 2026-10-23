"""
NyayVeya Administration Blueprint.

Provides secure administrative management interfaces for:
- Dashboard & interactive real-time business analytics
- Legal Document Template CRUD
- Orders & Verified Payments Inspection
- User Directory & Account Controls
- Customer Support Inquiries & Triage
"""
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from app.admin import routes  # noqa: E402, F401
