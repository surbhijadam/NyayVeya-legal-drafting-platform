"""
Document catalogue data.

This module holds document information in a dictionary for now.
In Phase 4, this will be replaced with database models.
Each document has an ID, title, category, price, description, and requirements.

IMPORTANT: Legal content (descriptions, requirements, statutory references)
must be reviewed by a qualified Indian advocate before publication.
Placeholder text is used during development.
"""

DOCUMENT_CATEGORIES = {
    'notices': {
        'name': 'Legal Notices',
        'description': 'Formal notices required under various Indian statutes.',
        'icon': 'bi-envelope-paper',
    },
    # Future categories (add when templates are ready):
    # 'agreements': {
    #     'name': 'Agreements & Contracts',
    #     'description': 'Standard agreements for common business and personal needs.',
    #     'icon': 'bi-file-earmark-text',
    # },
    # 'affidavits': {
    #     'name': 'Affidavits',
    #     'description': 'Sworn statements for various legal and administrative purposes.',
    #     'icon': 'bi-journal-check',
    # },
}

DOCUMENTS = {
    'cheque-bounce-notice': {
        'id': 'cheque-bounce-notice',
        'title': 'Cheque Bounce Notice',
        'subtitle': 'Demand Notice under Section 138 of the Negotiable Instruments Act, 1881',
        'category': 'notices',
        'price': 199,  # Price in INR
        'status': 'coming_soon',  # 'active', 'coming_soon', 'draft'

        'short_description': (
            'A formal legal notice to the drawer of a dishonoured cheque, '
            'demanding payment within the statutory period.'
        ),

        'long_description': (
            'When a cheque issued to you is returned unpaid (dishonoured) by the bank, '
            'Indian law requires you to send a written demand notice to the cheque issuer '
            'within 30 days of receiving the bank\'s memo of dishonour. This is a mandatory '
            'first step before you can file a criminal complaint under Section 138 of the '
            'Negotiable Instruments Act, 1881.\n\n'
            'This template generates a properly formatted demand notice that includes '
            'all the details required by law. You fill in the specific facts of your case, '
            'and the system produces a complete, ready-to-send document.'
        ),

        'what_you_get': [
            'A professionally formatted demand notice in Word and PDF format.',
            'All required statutory references included.',
            'Editable Word file so your advocate can review and customise if needed.',
            'Guidance notes on how to send the notice (registered post / speed post).',
        ],

        'information_needed': [
            'Your full name and address (the payee / complainant).',
            'The cheque issuer\'s full name and address (the drawer / accused).',
            'Cheque number, date, amount, and the bank details.',
            'Date of the bank\'s dishonour memo and the reason for dishonour.',
            'The purpose for which the cheque was issued.',
        ],

        # IMPORTANT: These points need legal review before going live
        'important_notes': [
            'This notice must be sent within 30 days of receiving the dishonour memo from the bank.',
            'Send the notice by Registered Post Acknowledgement Due (RPAD) or Speed Post.',
            'Keep a copy of the notice and the postal receipt safely.',
            'If the drawer does not pay within 15 days of receiving the notice, '
            'you may file a complaint under Section 138 of the NI Act.',
            'This is a standard template. For complex cases, consult an advocate.',
        ],

        'icon': 'bi-file-earmark-medical',
        'badge_text': 'Most Popular',
        'badge_class': 'bg-primary',
    },
    # Add more documents here as templates are developed and reviewed
}


def get_all_documents():
    """Return all documents as a list."""
    return list(DOCUMENTS.values())


def get_document_by_id(doc_id):
    """Return a single document by its ID, or None if not found."""
    return DOCUMENTS.get(doc_id)


def get_documents_by_category(category_key):
    """Return all documents in a given category."""
    return [doc for doc in DOCUMENTS.values() if doc['category'] == category_key]


def get_all_categories():
    """Return all categories with their documents."""
    categories_with_docs = {}
    for key, category in DOCUMENT_CATEGORIES.items():
        categories_with_docs[key] = {
            **category,
            'documents': get_documents_by_category(key),
        }
    return categories_with_docs
