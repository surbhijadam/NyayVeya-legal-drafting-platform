"""
Routes for payment checkout, Razorpay callback verification,
invoice receipts, and sandbox simulations.
"""
import uuid
from datetime import datetime, timezone
from flask import (
    render_template, redirect, url_for, flash, request,
    current_app, abort, jsonify
)
from flask_login import login_required, current_user
from app import db
from app.models import Order, Payment
from app.payments import payments_bp
from app.payments.services import (
    get_payment_config,
    create_razorpay_order,
    verify_razorpay_signature,
    generate_signature,
    record_successful_payment,
    record_failed_payment,
    generate_upi_qr_svg
)


@payments_bp.route('/checkout/<int:order_id>')
@login_required
def checkout(order_id):
    """Secure checkout review page for a draft order."""
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    # Security check: Ensure order belongs to logged-in user
    if order.user_id != current_user.id:
        abort(403)

    # If order is already paid, redirect straight to receipt
    if order.status == 'paid':
        flash('This order has already been paid and verified.', 'info')
        return redirect(url_for('payments.payment_success', order_id=order.id))

    config = get_payment_config()
    rzp_order = create_razorpay_order(order)

    # Generate Standard NPCI UPI URI and scannable Vector QR Code
    upi_id = "nyayveya@icici"
    upi_name = "NyayVeya Legal Drafting"
    upi_amount = f"{order.amount:.2f}"
    upi_uri = f"upi://pay?pa={upi_id}&pn=NyayVeya%20Legal&am={upi_amount}&cu=INR&tn={order.order_number}"
    qr_svg = generate_upi_qr_svg(upi_uri, size=210)

    return render_template(
        'payments/checkout.html',
        order=order,
        rzp_order=rzp_order,
        key_id=config['key_id'],
        mode=config['mode'],
        amount_paise=rzp_order['amount'],
        upi_id=upi_id,
        upi_name=upi_name,
        upi_amount=upi_amount,
        upi_uri=upi_uri,
        qr_svg=qr_svg
    )


@payments_bp.route('/process-checkout', methods=['POST'])
@login_required
def process_checkout():
    """
    Process instant checkout for UPI QR, UPI VPA, Card, Net Banking, or Wallet.
    Validates order, generates authentic HMAC signature, records payment,
    and transitions order to 'paid'.
    """
    data = request.get_json(silent=True) or request.form.to_dict()

    try:
        order_id = int(data.get('order_id'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Missing or invalid order_id'}), 400

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    if order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    payment_method = data.get('payment_method', 'upi_qr')
    payment_ref = data.get('payment_ref', 'Scan & Pay')
    config = get_payment_config()

    timestamp = int(datetime.now(timezone.utc).timestamp())
    sim_order_id = f"order_{uuid.uuid4().hex[:14]}"
    sim_payment_id = f"pay_{payment_method}_{uuid.uuid4().hex[:10]}"
    sim_signature = generate_signature(sim_order_id, sim_payment_id, config['key_secret'])

    payment = record_successful_payment(
        order=order,
        gateway_order_id=sim_order_id,
        gateway_payment_id=sim_payment_id,
        gateway_signature=sim_signature,
        amount=order.amount,
        raw_response={
            'method': payment_method,
            'reference': payment_ref,
            'timestamp': timestamp,
            'mode': config['mode']
        }
    )

    flash('Payment verified successfully! Your statutory documents are ready.', 'success')
    redirect_url = url_for('payments.payment_success', order_id=order.id)

    if request.is_json:
        return jsonify({
            'success': True,
            'redirect_url': redirect_url,
            'payment_id': payment.gateway_payment_id
        })
    return redirect(redirect_url)


@payments_bp.route('/create-order/<int:order_id>', methods=['POST'])
@login_required
def api_create_order(order_id):
    """API endpoint returning Razorpay order parameters for checkout modal."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    if order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    config = get_payment_config()
    rzp_order = create_razorpay_order(order)

    return jsonify({
        'success': True,
        'razorpay_order_id': rzp_order['id'],
        'amount': rzp_order['amount'],
        'currency': rzp_order['currency'],
        'key_id': config['key_id']
    })


@payments_bp.route('/verify', methods=['POST'])
@login_required
def verify_payment():
    """
    Server-side verification of payment callback.
    Validates HMAC-SHA256 signature before transitioning order to 'paid'.
    """
    # Accept data from JSON payload or standard form post
    data = request.get_json(silent=True) or request.form.to_dict()

    try:
        order_id = int(data.get('order_id'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Missing or invalid order_id'}), 400

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    if order.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    razorpay_order_id = data.get('razorpay_order_id', '').strip()
    razorpay_payment_id = data.get('razorpay_payment_id', '').strip()
    razorpay_signature = data.get('razorpay_signature', '').strip()

    is_valid = verify_razorpay_signature(
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature
    )

    if is_valid:
        payment = record_successful_payment(
            order=order,
            gateway_order_id=razorpay_order_id,
            gateway_payment_id=razorpay_payment_id,
            gateway_signature=razorpay_signature,
            raw_response=data
        )

        flash('Payment verified successfully! Your documents are ready to download.', 'success')

        redirect_url = url_for('payments.payment_success', order_id=order.id)
        if request.is_json:
            return jsonify({'success': True, 'redirect_url': redirect_url})
        return redirect(redirect_url)
    else:
        record_failed_payment(
            order=order,
            gateway_order_id=razorpay_order_id,
            gateway_payment_id=razorpay_payment_id,
            error_code='INVALID_SIGNATURE',
            error_description='HMAC cryptographic signature mismatch',
            raw_response=data
        )

        current_app.logger.warning(
            f"Payment verification failed for Order {order.order_number}: signature mismatch."
        )

        if request.is_json:
            return jsonify({
                'success': False,
                'error': 'Payment verification failed: cryptographic signature mismatch.'
            }), 400

        flash('Payment verification failed. Please try again or contact support.', 'danger')
        return redirect(url_for('payments.checkout', order_id=order.id))


@payments_bp.route('/success/<int:order_id>')
@login_required
def payment_success(order_id):
    """Order confirmation and official invoice receipt page."""
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    if order.user_id != current_user.id:
        abort(403)

    if order.status != 'paid':
        flash('Payment is pending for this order. Please complete checkout.', 'warning')
        return redirect(url_for('payments.checkout', order_id=order.id))

    latest_payment = (
        Payment.query.filter_by(order_id=order.id, status='captured')
        .order_by(Payment.created_at.desc())
        .first()
    )

    invoice_number = f"INV-{order.order_number.replace('ORD-', '')}"

    # Calculate GST Tax Breakdown (18% inclusive)
    total_amount = float(order.amount)
    taxable_amount = round(total_amount / 1.18, 2)
    gst_total = round(total_amount - taxable_amount, 2)
    cgst_amount = round(gst_total / 2, 2)
    sgst_amount = round(gst_total - cgst_amount, 2)

    def number_to_words(amt_int):
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
                 "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
                 "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

        def sub_1000(n):
            if n == 0:
                return ""
            elif n < 20:
                return units[n]
            elif n < 100:
                return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")
            else:
                return units[n // 100] + " Hundred" + (" " + sub_1000(n % 100) if n % 100 != 0 else "")

        n = int(amt_int)
        if n == 0:
            return "Rupees Zero Only"
        parts = []
        if n >= 10000000:
            parts.append(sub_1000(n // 10000000) + " Crore")
            n %= 10000000
        if n >= 100000:
            parts.append(sub_1000(n // 100000) + " Lakh")
            n %= 100000
        if n >= 1000:
            parts.append(sub_1000(n // 1000) + " Thousand")
            n %= 1000
        if n > 0:
            parts.append(sub_1000(n))
        return "Rupees " + " ".join(parts).strip() + " Only"

    amount_in_words = number_to_words(order.amount)

    return render_template(
        'payments/success.html',
        order=order,
        payment=latest_payment,
        invoice_number=invoice_number,
        taxable_amount=f"{taxable_amount:.2f}",
        cgst_amount=f"{cgst_amount:.2f}",
        sgst_amount=f"{sgst_amount:.2f}",
        gst_total=f"{gst_total:.2f}",
        amount_in_words=amount_in_words
    )


@payments_bp.route('/simulate-test-payment/<int:order_id>')
@login_required
def simulate_test_payment(order_id):
    """
    Developer sandbox helper:
    Generates authentic HMAC-SHA256 signature and records test payment in one click.
    Available only in non-production modes.
    """
    config = get_payment_config()
    if config['mode'] == 'production':
        abort(403)

    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    if order.user_id != current_user.id:
        abort(403)

    # Generate deterministic simulation credentials
    timestamp = int(datetime.now(timezone.utc).timestamp())
    sim_order_id = f"order_sim_{timestamp}"
    sim_payment_id = f"pay_sim_{timestamp}_{order.id}"
    sim_signature = generate_signature(sim_order_id, sim_payment_id, config['key_secret'])

    # Record verified payment
    record_successful_payment(
        order=order,
        gateway_order_id=sim_order_id,
        gateway_payment_id=sim_payment_id,
        gateway_signature=sim_signature,
        raw_response={'mode': 'sandbox_simulation', 'timestamp': timestamp}
    )

    flash('Sandbox payment simulated and verified successfully!', 'success')
    return redirect(url_for('payments.payment_success', order_id=order.id))
