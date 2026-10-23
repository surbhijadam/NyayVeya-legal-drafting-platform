"""
Payments blueprint package for NyayVeya.
Handles Razorpay online checkout, cryptographic signature verification,
order state progression, tax invoices, and payment receipts.
"""
from flask import Blueprint

payments_bp = Blueprint('payments', __name__, url_prefix='/payments')

from app.payments import routes  # noqa: E402, F401
