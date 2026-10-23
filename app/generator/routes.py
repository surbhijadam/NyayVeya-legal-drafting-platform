"""
Routes for document generation, preview, and download.
"""
import os
import uuid
from datetime import datetime, timezone
from flask import (
    render_template, redirect, url_for, flash, request, current_app,
    send_from_directory, abort
)
from flask_login import login_required, current_user
from app import db
from app.models import Order, DocumentTemplate
from app.generator import generator_bp
from app.generator.forms import ChequeBounceNoticeForm
from app.generator.template_text import format_cheque_bounce_notice
from app.generator.docx_builder import build_cheque_bounce_docx
from app.generator.pdf_builder import build_cheque_bounce_pdf


@generator_bp.route('/cheque-bounce-notice', methods=['GET', 'POST'])
@login_required
def cheque_bounce_form():
    """Guided form for Cheque Bounce Legal Notice."""
    template = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').first_or_404()

    form = ChequeBounceNoticeForm()

    # Pre-populate Payee name from user's account if empty
    if request.method == 'GET' and not form.payee_name.data:
        form.payee_name.data = current_user.full_name

    if form.validate_on_submit():
        # Package validated data into a serializable dict
        data = {
            'notice_date': form.notice_date.data.isoformat(),
            'payee_name': form.payee_name.data.strip(),
            'payee_address': form.payee_address.data.strip(),
            'payee_phone': form.payee_phone.data.strip(),
            'advocate_name': form.advocate_name.data.strip() if form.advocate_name.data else '',
            'advocate_address': form.advocate_address.data.strip() if form.advocate_address.data else '',
            'drawer_name': form.drawer_name.data.strip(),
            'drawer_address': form.drawer_address.data.strip(),
            'cheque_number': form.cheque_number.data.strip(),
            'cheque_date': form.cheque_date.data.isoformat(),
            'cheque_amount': form.cheque_amount.data,
            'cheque_amount_words': form.cheque_amount_words.data.strip(),
            'bank_name': form.bank_name.data.strip(),
            'bank_branch': form.bank_branch.data.strip(),
            'memo_date': form.memo_date.data.isoformat(),
            'dishonour_reason': form.dishonour_reason.data,
            'transaction_details': form.transaction_details.data.strip(),
        }

        # Generate unique order number
        order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Create Order record in database
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            document_template_id=template.id,
            amount=template.price,
            status='pending',
        )
        order.form_data = data

        # File paths inside private generated_documents directory
        folder = current_app.config['GENERATED_DOCUMENTS_FOLDER']
        docx_name = f"{order_number}_draft.docx"
        pdf_name = f"{order_number}_draft.pdf"

        docx_path = os.path.join(folder, docx_name)
        pdf_path = os.path.join(folder, pdf_name)

        # Generate both Word and PDF drafts
        formatted_notice = format_cheque_bounce_notice(form.data)
        build_cheque_bounce_docx(formatted_notice, docx_path)
        build_cheque_bounce_pdf(formatted_notice, pdf_path)

        order.docx_filename = docx_name
        order.pdf_filename = pdf_name

        db.session.add(order)
        db.session.commit()

        flash('Your legal notice draft has been generated successfully! Review the preview below.', 'success')
        return redirect(url_for('generator.preview', order_id=order.id))

    return render_template(
        'generator/cheque_bounce_form.html',
        form=form,
        template=template
    )


@generator_bp.route('/preview/<int:order_id>')
@login_required
def preview(order_id):
    """Preview the generated legal document draft before payment."""
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    # Security check: Ensure order belongs to logged-in user
    if order.user_id != current_user.id:
        abort(403)

    formatted_notice = format_cheque_bounce_notice(order.form_data)

    return render_template(
        'generator/preview.html',
        order=order,
        notice=formatted_notice
    )


@generator_bp.route('/download/<int:order_id>/<string:file_type>')
@login_required
def download_draft(order_id, file_type):
    """Download generated draft (.docx or .pdf)."""
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    # Security check: Ensure order belongs to current user
    if order.user_id != current_user.id:
        abort(403)

    folder = current_app.config['GENERATED_DOCUMENTS_FOLDER']

    if file_type == 'docx' and order.docx_filename:
        return send_from_directory(
            folder,
            order.docx_filename,
            as_attachment=True,
            download_name=f"Cheque_Bounce_Notice_{order.order_number}.docx"
        )
    elif file_type == 'pdf' and order.pdf_filename:
        return send_from_directory(
            folder,
            order.pdf_filename,
            as_attachment=True,
            download_name=f"Cheque_Bounce_Notice_{order.order_number}.pdf"
        )
    else:
        abort(404)
