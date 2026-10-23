"""
Routes for payment checkout, Razorpay callback verification,
invoice receipts, and sandbox simulations.
"""
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
    record_failed_payment
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

    return render_template(
        'payments/checkout.html',
        order=order,
        rzp_order=rzp_order,
        key_id=config['key_id'],
        mode=config['mode'],
        amount_paise=rzp_order['amount']
    )


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

    return render_template(
        'payments/success.html',
        order=order,
        payment=latest_payment,
        invoice_number=invoice_number
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
