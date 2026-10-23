"""
PDF document (.pdf) builder for Section 138 Legal Notice.
Uses ReportLab to compile print-ready, professional PDF legal documents.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable


def build_cheque_bounce_pdf(formatted_notice, output_filepath):
    """
    Build and save a clean, print-ready PDF legal notice.
    """
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    # 1 inch margins on A4
    margin = 54  # 0.75 inch for crisp layout
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    styles = getSampleStyleSheet()

    # Custom styles
    header_style = ParagraphStyle(
        'NoticeHeader',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#222222')
    )

    date_style = ParagraphStyle(
        'NoticeDate',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10.5,
        leading=14,
        alignment=TA_RIGHT
    )

    block_style = ParagraphStyle(
        'NoticeBlock',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10.5,
        leading=14,
        alignment=TA_LEFT
    )

    subject_style = ParagraphStyle(
        'NoticeSubject',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#111111')
    )

    body_style = ParagraphStyle(
        'NoticeBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#222222')
    )

    sign_style = ParagraphStyle(
        'NoticeSign',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10.5,
        leading=14,
        alignment=TA_RIGHT
    )

    story = []

    # 1. Header
    story.append(Paragraph(formatted_notice['header'], header_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#888888'), spaceBefore=2, spaceAfter=12))

    # 2. Date
    story.append(Paragraph(f"<b>Date:</b> {formatted_notice['notice_date']}", date_style))
    story.append(Spacer(1, 10))

    # 3. Sender Block (if advocate)
    if 'Advocate' in formatted_notice['sender_block']:
        sender_html = formatted_notice['sender_block'].replace('\n', '<br/>')
        story.append(Paragraph(sender_html, block_style))
        story.append(Spacer(1, 10))

    # 4. Recipient Block
    recipient_html = formatted_notice['recipient_block'].replace('\n', '<br/>')
    story.append(Paragraph(recipient_html, block_style))
    story.append(Spacer(1, 12))

    # 5. Subject
    story.append(Paragraph(formatted_notice['subject'], subject_style))
    story.append(Spacer(1, 12))

    # Salutation
    story.append(Paragraph("Sir / Madam,", block_style))
    story.append(Spacer(1, 8))

    # 6. Paragraphs
    for para in formatted_notice['paragraphs']:
        story.append(Paragraph(para, body_style))
        story.append(Spacer(1, 8))

    # 7. Signoff
    story.append(Spacer(1, 14))
    sign_html = formatted_notice['signoff'].replace('\n', '<br/>')
    story.append(Paragraph(sign_html, sign_style))

    # Build the document
    doc.build(story)
    return output_filepath


def build_legal_draft_pdf(formatted_doc, output_filepath):
    """
    Build and save a clean, print-ready PDF legal document
    for any category (Agreement, Affidavit, Notice, Application, Declaration).
    """
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    margin = 54  # 0.75 inch
    doc = SimpleDocTemplate(
        output_filepath,
        pagesize=A4,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'DocHeader',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#142D4E')
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#555555')
    )

    block_style = ParagraphStyle(
        'DocBlock',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT
    )

    subject_style = ParagraphStyle(
        'DocSubject',
        parent=styles['Normal'],
        fontName='Times-Bold',
        fontSize=10.5,
        leading=14,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#111111')
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        leading=14.5,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#222222')
    )

    sign_style = ParagraphStyle(
        'DocSign',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=9.5,
        leading=13.5,
        alignment=TA_LEFT
    )

    story = []

    # 1. Header
    story.append(Paragraph(formatted_doc.get('header', 'LEGAL DRAFT'), header_style))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#142D4E'), spaceBefore=2, spaceAfter=10))

    # 2. Date / City
    date_str = formatted_doc.get('notice_date') or formatted_doc.get('document_date') or ''
    city_str = formatted_doc.get('city') or ''
    meta_parts = []
    if date_str:
        meta_parts.append(f"<b>Date:</b> {date_str}")
    if city_str:
        meta_parts.append(f"<b>Place:</b> {city_str}")
    if meta_parts:
        story.append(Paragraph(" · ".join(meta_parts), meta_style))
        story.append(Spacer(1, 10))

    # 3. Recipient block if Notice or Application
    recipient_block = formatted_doc.get('recipient_block')
    if recipient_block and any(k in formatted_doc.get('header', '').upper() for k in ('NOTICE', 'APPLICATION', 'AFFIDAVIT')):
        recip_html = recipient_block.replace('\n', '<br/>')
        story.append(Paragraph(recip_html, block_style))
        story.append(Spacer(1, 10))

    # 4. Subject
    if formatted_doc.get('subject'):
        story.append(Paragraph(formatted_doc['subject'], subject_style))
        story.append(Spacer(1, 10))

    # Salutation if Notice
    if 'NOTICE' in formatted_doc.get('header', '').upper():
        story.append(Paragraph("Sir / Madam,", block_style))
        story.append(Spacer(1, 8))

    # 5. Paragraphs
    for para in formatted_doc.get('paragraphs', []):
        story.append(Paragraph(para, body_style))
        story.append(Spacer(1, 8))

    # 6. Signoff
    signoff = formatted_doc.get('signoff', '')
    if signoff:
        story.append(Spacer(1, 12))
        sign_html = signoff.replace('\n', '<br/>')
        story.append(Paragraph(sign_html, sign_style))

    doc.build(story)
    return output_filepath
