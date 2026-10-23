"""
Routes for document generation, preview, and download.
Supports Cheque Bounce Notice as well as all active legal document formats:
Rent Agreement, Affidavit, General Legal Notice, NDA, Business Agreement,
Formal Application, and Declaration Letter.
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
from app.catalogue import DOCUMENTS
from app.generator import generator_bp
from app.generator.forms import ChequeBounceNoticeForm, StandardLegalDraftForm
from app.generator.template_text import format_cheque_bounce_notice, format_standard_legal_document
from app.generator.docx_builder import build_cheque_bounce_docx, build_legal_draft_docx
from app.generator.pdf_builder import build_cheque_bounce_pdf, build_legal_draft_pdf


@generator_bp.route('/cheque-bounce-notice', methods=['GET', 'POST'])
@login_required
def cheque_bounce_form():
    """Guided form for Cheque Bounce Legal Notice."""
    template = DocumentTemplate.query.filter_by(slug='cheque-bounce-notice').first()
    if not template:
        template = DocumentTemplate(
            slug='cheque-bounce-notice',
            title='Cheque Bounce Notice',
            category='notices',
            price=199,
            status='active'
        )
        db.session.add(template)
        db.session.commit()

    form = ChequeBounceNoticeForm()

    # Pre-populate Payee name from user's account if empty
    if request.method == 'GET' and not form.payee_name.data:
        form.payee_name.data = current_user.full_name

    if form.validate_on_submit():
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

        order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            document_template_id=template.id,
            amount=template.price,
            status='pending',
        )
        order.form_data = data

        folder = current_app.config['GENERATED_DOCUMENTS_FOLDER']
        os.makedirs(folder, exist_ok=True)
        docx_name = f"{order_number}_draft.docx"
        pdf_name = f"{order_number}_draft.pdf"

        docx_path = os.path.join(folder, docx_name)
        pdf_path = os.path.join(folder, pdf_name)

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


@generator_bp.route('/draft/<string:slug>', methods=['GET', 'POST'])
@login_required
def draft_document(slug):
    """
    Unified guided form for all active legal document formats:
    Rent Agreement, Affidavit, General Legal Notice, NDA, Business Agreement,
    Formal Application, and Declaration Letter.
    """
    if slug == 'cheque-bounce-notice':
        return redirect(url_for('generator.cheque_bounce_form'))

    template = DocumentTemplate.query.filter_by(slug=slug).first()
    if not template:
        # Check catalogue dictionary
        cat_data = DOCUMENTS.get(slug)
        if cat_data:
            template = DocumentTemplate(
                slug=slug,
                title=cat_data['title'],
                subtitle=cat_data.get('subtitle'),
                category=cat_data['category'],
                price=cat_data['price'],
                status='active',
                short_description=cat_data['short_description'],
                long_description=cat_data['long_description'],
                badge_text='Available Now',
                badge_class='bg-success'
            )
            db.session.add(template)
            db.session.commit()
        else:
            abort(404)

    form = StandardLegalDraftForm()

    # Pre-populate defaults on GET
    if request.method == 'GET':
        if not form.first_party_name.data and current_user.full_name:
            form.first_party_name.data = current_user.full_name
        if not form.city.data:
            form.city.data = 'New Delhi'

        # Sensible sample clauses per category if empty
        if not form.key_terms.data:
            slug_lower = slug.lower()
            if 'rent' in slug_lower or 'lease' in slug_lower:
                form.subject_purpose.data = 'Residential Premises / Apartment'
                form.amount.data = 15000
                form.duration_period.data = '11 Months'
                form.key_terms.data = (
                    "1. The monthly rent shall be paid without delay on or before the 5th day of each calendar month.\n"
                    "2. The interest-free refundable security deposit shall be refunded upon peaceful key handover, subject to unpaid utility deductions.\n"
                    "3. The premises shall be kept in clean, habitable condition and used strictly for residential purposes.\n"
                    "4. Notice period for early termination by either party shall be 30 days in writing."
                )
            elif 'affidavit' in slug_lower:
                form.subject_purpose.data = 'Declaration of Address and Factual Verification'
                form.amount.data = 0
                form.duration_period.data = 'Permanent'
                form.key_terms.data = (
                    "1. That I have been continuously residing at the address stated above for several years.\n"
                    "2. That all particulars, identity documents, and statements furnished by me are genuine and verifiable.\n"
                    "3. That this sworn affidavit is executed for administrative verification before the concerned statutory department."
                )
            elif 'nda' in slug_lower:
                form.subject_purpose.data = 'Evaluation of Commercial Partnership and Proprietary Technology'
                form.amount.data = 0
                form.duration_period.data = '2 Years'
                form.key_terms.data = (
                    "1. Both parties agree to protect proprietary source code, technical architectures, and financial data.\n"
                    "2. The receiving party shall restrict disclosure solely to personnel with strict need-to-know obligations.\n"
                    "3. Confidentiality covenants shall survive termination of commercial discussions."
                )
            elif 'business' in slug_lower:
                form.subject_purpose.data = 'Provision of Software, Consulting, or Commercial Services'
                form.amount.data = 50000
                form.duration_period.data = '12 Months'
                form.key_terms.data = (
                    "1. The service provider shall deliver the agreed deliverables with professional skill and competence.\n"
                    "2. The client shall verify deliverables and release milestone payments within 7 business days.\n"
                    "3. Intellectual property rights shall transfer to the client upon full payment of agreed consideration."
                )
            elif 'application' in slug_lower:
                form.subject_purpose.data = 'Request for Official Grant, Certificate, or Clearance'
                form.amount.data = 0
                form.duration_period.data = '15 Days'
                form.key_terms.data = (
                    "1. That the applicant satisfies all statutory conditions and procedural requirements for the grant of requested relief.\n"
                    "2. That all necessary identity records and supporting documents are submitted herewith.\n"
                    "3. That it is respectfully prayed that the competent authority kindly grant the requested approval expeditiously."
                )
            elif 'letter' in slug_lower:
                form.subject_purpose.data = 'Self-Attestation and Certification of Facts'
                form.amount.data = 0
                form.duration_period.data = 'Immediate'
                form.key_terms.data = (
                    "1. I hereby confirm and certify the truthfulness of all particulars stated herein.\n"
                    "2. This self-declaration letter is executed in accordance with administrative and self-attestation reforms."
                )
            else:
                form.subject_purpose.data = 'Statutory Legal Notice and Demand for Compliance'
                form.amount.data = 25000
                form.duration_period.data = '15 Days'
                form.key_terms.data = (
                    "1. That a binding agreement and transaction existed between the parties.\n"
                    "2. That despite reminders, the noticee has failed and neglected to fulfill their legal obligations.\n"
                    "3. Demand is hereby made to remedy the breach and settle the dues within 15 days of receipt hereof."
                )

    if form.validate_on_submit():
        data = {
            'document_date': form.document_date.data.isoformat(),
            'city': form.city.data.strip(),
            'first_party_name': form.first_party_name.data.strip(),
            'first_party_details': form.first_party_details.data.strip(),
            'second_party_name': form.second_party_name.data.strip() if form.second_party_name.data else '',
            'second_party_details': form.second_party_details.data.strip() if form.second_party_details.data else '',
            'subject_purpose': form.subject_purpose.data.strip(),
            'amount': form.amount.data or 0,
            'duration_period': form.duration_period.data.strip() if form.duration_period.data else '',
            'key_terms': form.key_terms.data.strip(),
            'slug': slug,
            'template_title': template.title,
        }

        order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            document_template_id=template.id,
            amount=template.price,
            status='pending',
        )
        order.form_data = data

        folder = current_app.config['GENERATED_DOCUMENTS_FOLDER']
        os.makedirs(folder, exist_ok=True)
        docx_name = f"{order_number}_draft.docx"
        pdf_name = f"{order_number}_draft.pdf"

        docx_path = os.path.join(folder, docx_name)
        pdf_path = os.path.join(folder, pdf_name)

        formatted_doc = format_standard_legal_document(slug, data, template)
        build_legal_draft_docx(formatted_doc, docx_path)
        build_legal_draft_pdf(formatted_doc, pdf_path)

        order.docx_filename = docx_name
        order.pdf_filename = pdf_name

        db.session.add(order)
        db.session.commit()

        flash(f'Your {template.title} draft has been generated successfully! Review the preview below.', 'success')
        return redirect(url_for('generator.preview', order_id=order.id))

    return render_template(
        'generator/standard_form.html',
        form=form,
        template=template
    )


@generator_bp.route('/preview/<int:order_id>', endpoint='preview')
@generator_bp.route('/preview/<int:order_id>', endpoint='preview_draft')
@login_required
def preview(order_id):
    """Preview the generated legal document draft before payment."""
    order = db.session.get(Order, order_id)
    if not order:
        abort(404)

    # Security check: Ensure order belongs to logged-in user
    if order.user_id != current_user.id:
        abort(403)

    data = dict(order.form_data or {})
    template = order.document_template
    slug = template.slug if template else 'cheque-bounce-notice'

    if slug == 'cheque-bounce-notice':
        if not data.get('payee_name') and current_user.full_name:
            data['payee_name'] = current_user.full_name
        if not data.get('cheque_amount') and order.amount:
            data['cheque_amount'] = order.amount
        formatted_doc = format_cheque_bounce_notice(data)
    else:
        if not data.get('first_party_name') and current_user.full_name:
            data['first_party_name'] = current_user.full_name
        formatted_doc = format_standard_legal_document(slug, data, template)

    return render_template(
        'generator/preview.html',
        order=order,
        notice=formatted_doc,
        template=template
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

    folder = os.path.abspath(current_app.config['GENERATED_DOCUMENTS_FOLDER'])
    os.makedirs(folder, exist_ok=True)

    data = dict(order.form_data or {})
    template = order.document_template
    slug = template.slug if template else 'cheque-bounce-notice'
    template_title = template.title if template else 'Legal_Document'
    safe_title = template_title.replace(' ', '_').replace('/', '_')

    if slug == 'cheque-bounce-notice':
        if not data.get('payee_name') and current_user.full_name:
            data['payee_name'] = current_user.full_name
        if not data.get('cheque_amount') and order.amount:
            data['cheque_amount'] = order.amount
        formatted_doc = format_cheque_bounce_notice(data)
        build_docx_func = build_cheque_bounce_docx
        build_pdf_func = build_cheque_bounce_pdf
    else:
        if not data.get('first_party_name') and current_user.full_name:
            data['first_party_name'] = current_user.full_name
        formatted_doc = format_standard_legal_document(slug, data, template)
        build_docx_func = build_legal_draft_docx
        build_pdf_func = build_legal_draft_pdf

    if file_type == 'docx':
        docx_name = order.docx_filename or f"{order.order_number}_draft.docx"
        docx_path = os.path.join(folder, docx_name)
        if not os.path.exists(docx_path):
            build_docx_func(formatted_doc, docx_path)
            order.docx_filename = docx_name
            db.session.commit()
        return send_from_directory(
            folder,
            docx_name,
            as_attachment=True,
            download_name=f"{safe_title}_{order.order_number}.docx"
        )
    elif file_type == 'pdf':
        pdf_name = order.pdf_filename or f"{order.order_number}_draft.pdf"
        pdf_path = os.path.join(folder, pdf_name)
        if not os.path.exists(pdf_path):
            build_pdf_func(formatted_doc, pdf_path)
            order.pdf_filename = pdf_name
            db.session.commit()
        return send_from_directory(
            folder,
            pdf_name,
            as_attachment=True,
            download_name=f"{safe_title}_{order.order_number}.pdf"
        )
    else:
        abort(404)
