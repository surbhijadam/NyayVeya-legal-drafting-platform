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
