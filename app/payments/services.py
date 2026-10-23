"""
Payment service module for NyayVeya.
Provides server-side order generation, cryptographic HMAC-SHA256 signature verification,
audit logging, and order state synchronization.
"""
import hmac
import hashlib
import json
import uuid
import urllib.request
import urllib.error
import base64
from datetime import datetime, timezone
from flask import current_app
from app import db
from app.models import Order, Payment


def generate_upi_qr_svg(upi_uri, size=220):
    """
    Generate an authentic, scannable inline SVG QR Code for standard Indian UPI URIs
    using built-in ReportLab barcode QR generator. Works 100% offline.
    """
    try:
        from reportlab.graphics.barcode import qr
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import renderSVG

        widget = qr.QrCodeWidget(upi_uri)
        bounds = widget.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        scale_x = size / width
        scale_y = size / height
        d = Drawing(size, size, transform=[scale_x, 0, 0, scale_y, 0, 0])
        d.add(widget)
        svg_str = renderSVG.drawToString(d)
        # Strip xml declaration if present for clean inline HTML embedding
        if '<?xml' in svg_str:
            svg_str = svg_str[svg_str.find('?>') + 2:].strip()
        return svg_str
    except Exception as e:
        current_app.logger.warning(f"Error generating UPI QR SVG with reportlab: {e}")
        return ""


def get_payment_config():
    """Retrieve payment gateway settings from application configuration."""
    key_id = current_app.config.get('RAZORPAY_KEY_ID') or 'rzp_test_sample_key'
    key_secret = current_app.config.get('RAZORPAY_KEY_SECRET') or 'sample_secret_key_12345'
    mode = current_app.config.get('PAYMENT_MODE', 'test').lower()
    return {
        'key_id': key_id,
        'key_secret': key_secret,
        'mode': mode
    }


def create_razorpay_order(order, key_id=None, key_secret=None):
    """
    Create a Razorpay order record either via Razorpay's official REST API
    or using local simulated order generation for offline/test mode.
    Returns a dict with 'id', 'amount' (in paise), 'currency', and metadata.
    """
    config = get_payment_config()
    key_id = key_id or config['key_id']
    key_secret = key_secret or config['key_secret']
    mode = config['mode']

    amount_paise = int(order.amount * 100)

    # If real test or live keys are configured and mode is not forced simulation
    is_placeholder_key = 'sample' in key_id or 'your_' in key_id or 'placeholder' in key_id

    if not is_placeholder_key and mode in ('live', 'production', 'test_api'):
        try:
            url = "https://api.razorpay.com/v1/orders"
            payload = json.dumps({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": order.order_number,
                "notes": {
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "document": order.document_template.title if order.document_template else "Legal Notice"
                }
            }).encode('utf-8')

            auth_str = f"{key_id}:{key_secret}"
            auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('ascii')

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Basic {auth_b64}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        'id': data.get('id'),
                        'amount': data.get('amount'),
                        'currency': data.get('currency', 'INR'),
                        'receipt': data.get('receipt'),
                        'is_simulated': False
                    }
        except Exception as e:
            current_app.logger.warning(
                f"Razorpay REST API order creation failed ({e}); falling back to safe local test order."
            )

    # Local Test Simulation Mode (works offline, in sandboxes, and without external network)
    short_hash = hashlib.sha256(f"{order.order_number}-{datetime.now(timezone.utc).timestamp()}".encode()).hexdigest()[:14]
    simulated_order_id = f"order_{short_hash}"

    return {
        'id': simulated_order_id,
        'amount': amount_paise,
        'currency': 'INR',
        'receipt': order.order_number,
        'is_simulated': True
    }


def verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature, key_secret=None):
    """
    Cryptographically verify Razorpay payment signature using HMAC-SHA256.
    Formula: HMAC_SHA256(razorpay_order_id + '|' + razorpay_payment_id, secret) == razorpay_signature
    """
    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return False

    config = get_payment_config()
    secret = (key_secret or config['key_secret']).strip()

    try:
        message = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
        generated_signature = hmac.new(
            secret.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to protect against timing attacks
        return hmac.compare_digest(generated_signature, razorpay_signature.strip())
    except Exception as e:
        current_app.logger.error(f"Error during HMAC signature verification: {e}")
        return False


def generate_signature(razorpay_order_id, razorpay_payment_id, key_secret=None):
    """Helper to generate an authentic HMAC-SHA256 signature for testing."""
    config = get_payment_config()
    secret = (key_secret or config['key_secret']).strip()
    message = f"{razorpay_order_id}|{razorpay_payment_id}".encode('utf-8')
    return hmac.new(secret.encode('utf-8'), message, hashlib.sha256).hexdigest()


def record_successful_payment(order, gateway_order_id, gateway_payment_id, gateway_signature, amount=None, raw_response=None):
    """
    Record verified payment transaction in the database and transition order to 'paid'.
    Ensures idempotency so duplicate webhooks/callbacks do not double-record transactions.
    """
    existing_payment = Payment.query.filter_by(
        gateway_payment_id=gateway_payment_id
    ).first()

    if existing_payment:
        if order.status != 'paid':
            order.status = 'paid'
            db.session.commit()
        return existing_payment

    payment = Payment(
        order_id=order.id,
        gateway='razorpay',
        gateway_order_id=gateway_order_id,
        gateway_payment_id=gateway_payment_id,
        gateway_signature=gateway_signature,
        amount=amount if amount is not None else order.amount,
        currency='INR',
        status='captured'
    )

    db.session.add(payment)
    order.status = 'paid'
    order.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return payment


def record_failed_payment(order, gateway_order_id=None, gateway_payment_id=None, error_code=None, error_description=None, raw_response=None):
    """Record an audit trail entry for a failed or rejected payment attempt."""
    payment = Payment(
        order_id=order.id,
        gateway='razorpay',
        gateway_order_id=gateway_order_id,
        gateway_payment_id=gateway_payment_id or f"failed_{uuid.uuid4().hex[:8]}",
        gateway_signature=None,
        amount=order.amount,
        currency='INR',
        status='failed',
        error_code=error_code or 'SIGNATURE_VERIFICATION_FAILED',
        error_description=error_description or 'HMAC signature verification failed or payment cancelled'
    )

    db.session.add(payment)
    db.session.commit()
    return payment
