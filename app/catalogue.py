"""
Document catalogue data and database integration.

Provides catalog metadata, dictionary fallbacks, and helper queries.
In Phase 4, document templates are synchronized with the database models.
"""
from app.models import DocumentTemplate
from app import db

DOCUMENT_CATEGORIES = {
    'notices': {
        'name': 'Legal Notices',
        'description': 'Formal notices required under various Indian statutes.',
        'icon': 'bi-envelope-paper',
    },
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
}


def seed_initial_templates():
    """Seed initial document templates into database if not present."""
    for slug, data in DOCUMENTS.items():
        existing = DocumentTemplate.query.filter_by(slug=slug).first()
        if not existing:
            tmpl = DocumentTemplate(
                slug=slug,
                title=data['title'],
                subtitle=data.get('subtitle'),
                category=data['category'],
                price=data['price'],
                status=data['status'],
                short_description=data['short_description'],
                long_description=data['long_description'],
                icon=data.get('icon', 'bi-file-earmark-medical'),
                badge_text=data.get('badge_text'),
                badge_class=data.get('badge_class', 'bg-primary')
            )
            tmpl.what_you_get = data.get('what_you_get', [])
            tmpl.information_needed = data.get('information_needed', [])
            tmpl.important_notes = data.get('important_notes', [])
            db.session.add(tmpl)
    db.session.commit()


def get_all_documents():
    """Return all documents as a list."""
    # Returns in-memory catalogue dictionary for fast template rendering
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
