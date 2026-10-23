"""
Document catalogue data and database integration.

Defines all available and upcoming legal templates across categories.
Strict constraint: Only the Cheque Bounce Notice is marked 'active' for the initial workflow.
Other templates are marked 'coming_soon' to populate the catalogue structure.
"""
from app.models import DocumentTemplate
from app import db

DOCUMENT_CATEGORIES = {
    'notices': {
        'name': 'Legal Notices',
        'key': 'notices',
        'slug': 'notices',
        'description': 'Formal statutory notices required under various Indian statutes before legal action.',
        'icon': 'mail',
    },
    'agreements': {
        'name': 'Agreements & Contracts',
        'key': 'agreements',
        'slug': 'agreements',
        'description': 'Standard legal contracts and binding commercial or residential agreements.',
        'icon': 'file-text',
    },
    'affidavits': {
        'name': 'Affidavits & Declarations',
        'key': 'affidavits',
        'slug': 'affidavits',
        'description': 'Sworn statements and legal declarations on stamp paper formats.',
        'icon': 'shield-check',
    },
    'applications': {
        'name': 'Applications',
        'key': 'applications',
        'slug': 'applications',
        'description': 'Structured formal petitions, requests, and administrative applications.',
        'icon': 'file-signature',
    },
    'other': {
        'name': 'Other Documents',
        'key': 'other',
        'slug': 'other',
        'description': 'General declarations, authorizations, and miscellaneous legal letters.',
        'icon': 'folder',
    },
}

DOCUMENTS = {
    'cheque-bounce-notice': {
        'id': 'cheque-bounce-notice',
        'title': 'Cheque Bounce Notice',
        'display_title': 'Cheque Bounce Legal Notice',
        'subtitle': 'Demand Notice under Section 138 of the Negotiable Instruments Act, 1881',
        'category': 'notices',
        'category_name': 'Legal Notices',
        'category_slug': 'notices',
        'price': 199,  # In INR
        'status': 'active',  # Active for full workflow!
        'version': 'v1.0 (NI Act Compliant)',
        'image_url': 'https://images.pexels.com/photos/6862457/pexels-photo-6862457.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Organise sample information relating to a returned cheque matter and generate an immediate statutory demand notice.'
        ),

        'long_description': (
            'When a cheque presented by you is dishonoured by the bank due to insufficient funds '
            'or other reasons, Indian law requires you to send a formal written demand notice to the '
            'cheque issuer (drawer) within exactly 30 days of receiving the bank\'s dishonour memo.\n\n'
            'Under Section 138(b) of the Negotiable Instruments Act, 1881, serving this notice is a '
            'strict legal prerequisite. The notice gives the drawer 15 days from the date of receipt '
            'to settle the cheque amount. If they fail to pay within 15 days, a cause of action arises, '
            'permitting you to file a criminal complaint before the Judicial Magistrate.\n\n'
            'This guided generator produces a standard, properly structured legal demand notice '
            'incorporating all statutory ingredients recognized by Indian courts.'
        ),

        'what_you_get': [
            'Instant preview of your fully drafted legal notice.',
            'Editable Microsoft Word (.docx) file for advocate customization.',
            'Print-ready, clean PDF document (.pdf).',
            'Step-by-step dispatch guidelines (RPAD / Speed Post delivery).',
            'Permanent access from your order dashboard.',
        ],

        'information_needed': [
            'Cheque Number, cheque date, and exact amount in figures and words.',
            'Drawee bank name and branch location.',
            'Bank return memo date and reason for dishonour.',
            'Drawer / Accused full name and complete delivery address.',
            'Transaction background explaining the legally enforceable debt.',
        ],

        'important_notes': [
            'Strict 30-Day Deadline: Notice must be issued within 30 days of receiving the bank dishonour memo.',
            'Mandatory Dispatch Method: Send via Registered Post Acknowledgement Due (RPAD) or Speed Post.',
            'Evidence Preservation: Retain the postal dispatch receipt and the online tracking delivery report.',
            '15-Day Payment Window: The drawer gets 15 days from delivery to make payment before a complaint can be filed.',
            'Disclaimer: This is a standard template generator and does not constitute personalised legal advice.',
        ],

        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
    },

    'rent': {
        'id': 'rent',
        'title': 'Rent Agreement',
        'subtitle': '11-Month Standard Residential Lease Agreement for Landlords & Tenants',
        'category': 'agreements',
        'category_slug': 'agreements',
        'price': 249,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',
        'image_url': 'https://images.pexels.com/photos/12955837/pexels-photo-12955837.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Outline illustrative rental terms, monthly rent, security deposits, and maintenance responsibilities.'
        ),

        'long_description': (
            'A comprehensive residential tenancy agreement template designed for 11-month lease periods '
            'under standard state rent control practices. Outlines security deposits, rent cycles, notice periods, '
            'and tenant/landlord covenants.'
        ),

        'what_you_get': [
            'Editable lease agreement in Word (.docx) and PDF.',
            'Standard clauses covering maintenance, notice period, and deposit refund.',
        ],

        'information_needed': [
            'Landlord and Tenant identification and ID proofs.',
            'Premises address and inventory details.',
            'Monthly rent, security deposit, and lock-in period.',
        ],

        'important_notes': [
            'Template under professional advocate review.',
            'Must be executed on appropriate state non-judicial stamp paper.',
        ],

        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },

    'affidavit': {
        'id': 'affidavit',
        'title': 'Affidavit',
        'subtitle': 'General Sworn Statement for Government and Administrative Verifications',
        'category': 'affidavits',
        'category_slug': 'affidavits',
        'price': 149,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',
        'image_url': 'https://images.pexels.com/photos/9858904/pexels-photo-9858904.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Organise factual statements in an illustrative sworn declaration format.'
        ),

        'long_description': (
            'A general affidavit template for swearing factual statements before an Executive Magistrate or Notary Public. '
            'Commonly used for address proof, name discrepancy, loss of documents, or official government declarations.'
        ),

        'what_you_get': [
            'Affidavit draft in Word (.docx) and PDF.',
            'Format compatible with standard non-judicial e-stamp paper.',
        ],

        'information_needed': [
            'Deponent details and photo ID references.',
            'Factual statements to be sworn.',
        ],

        'important_notes': [
            'Must be printed on stamp paper and notarized to be legally valid.',
        ],

        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },

    'notice': {
        'id': 'notice',
        'title': 'General Legal Notice',
        'subtitle': 'A structured starting point for formal legal correspondence and demands',
        'category': 'notices',
        'category_slug': 'notices',
        'price': 299,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',
        'image_url': 'https://images.pexels.com/photos/4792282/pexels-photo-4792282.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'A structured starting point for formal correspondence, breach notices, or money recovery demands.'
        ),

        'long_description': (
            'A versatile legal notice template suitable for civil grievances, breach of contract, or demand for debt recovery. '
            'Formalizes grievances with statutory limitation considerations.'
        ),

        'what_you_get': [
            'Word and PDF legal draft formats.',
            'Guidance on limitation periods under the Limitation Act, 1963.',
        ],

        'information_needed': [
            'Sender and recipient full details.',
            'Chronology of events and dispute details.',
            'Specific demand and compliance deadline.',
        ],

        'important_notes': [
            'Template under professional legal review.',
        ],

        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },

    'nda': {
        'id': 'nda',
        'title': 'Non-Disclosure Agreement',
        'subtitle': 'Standard Mutual or Unilateral Confidentiality Agreement',
        'category': 'agreements',
        'category_slug': 'agreements',
        'price': 199,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',
        'image_url': 'https://images.pexels.com/photos/3760067/pexels-photo-3760067.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Set out sample confidentiality expectations and protect sensitive information between parties.'
        ),

        'long_description': (
            'A standard non-disclosure agreement to protect trade secrets, intellectual property, and proprietary data '
            'during business discussions or partnerships.'
        ),

        'what_you_get': [
            'Customizable NDA in Word and PDF.',
            'Standard confidentiality and non-solicitation clauses.',
        ],

        'information_needed': [
            'Disclosing and Receiving party identities.',
            'Scope of confidential information.',
            'Duration of confidentiality obligation.',
        ],

        'important_notes': [
            'Coming soon.',
        ],

        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },

    'business': {
        'id': 'business',
        'title': 'Business Agreement',
        'subtitle': 'Commercial Contract for Services, Vendors, and Deliverables',
        'category': 'agreements',
        'category_slug': 'agreements',
        'price': 349,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',
        'image_url': 'https://images.pexels.com/photos/7641994/pexels-photo-7641994.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Structure illustrative terms, scopes of work, and payment schedules for a business arrangement.'
        ),

        'long_description': (
            'A commercial contract template establishing obligations, deliverables, payment milestones, and dispute resolution mechanisms.'
        ),

        'what_you_get': [
            'Commercial agreement in Word (.docx) and PDF.',
        ],

        'information_needed': [
            'Entity names and registration numbers.',
            'Scope of work and payment terms.',
        ],

        'important_notes': [
            'Coming soon.',
        ],

        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },

    'application': {
        'id': 'application',
        'title': 'Formal Application',
        'subtitle': 'Structured Written Application for Official and Institutional Filings',
        'category': 'applications',
        'category_slug': 'applications',
        'price': 149,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',
        'image_url': 'https://images.pexels.com/photos/8730987/pexels-photo-8730987.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Prepare a structured sample written application for official or administrative bodies.'
        ),

        'long_description': (
            'A structured formal application format for government departments, universities, authorities, or courts.'
        ),

        'what_you_get': [
            'Application format in Word and PDF.',
        ],

        'information_needed': [
            'Authority designation and address.',
            'Applicant credentials and grounds of application.',
        ],

        'important_notes': [
            'Coming soon.',
        ],

        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },

    'letter': {
        'id': 'letter',
        'title': 'Declaration Letter',
        'subtitle': 'Formal Declaration Statement for Administrative Use',
        'category': 'other',
        'category_slug': 'other',
        'price': 99,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',
        'image_url': 'https://images.pexels.com/photos/190295/pexels-photo-190295.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Draft a simple illustrative declaration statement for general personal or commercial use.'
        ),

        'long_description': (
            'A formal declaration letter certifying facts, status, or self-attestations.'
        ),

        'what_you_get': [
            'Declaration letter in Word and PDF.',
        ],

        'information_needed': [
            'Declarant identity.',
            'Specific facts being certified.',
        ],

        'important_notes': [
            'Coming soon.',
        ],

        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },
}


def seed_initial_templates():
    """Seed or update document templates into the database."""
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
                badge_text=data.get('badge_text'),
                badge_class=data.get('badge_class', 'bg-primary')
            )
            tmpl.what_you_get = data.get('what_you_get', [])
            tmpl.information_needed = data.get('information_needed', [])
            tmpl.important_notes = data.get('important_notes', [])
            db.session.add(tmpl)
        else:
            existing.title = data['title']
            existing.status = data['status']
            existing.price = data['price']
            existing.badge_text = data.get('badge_text')
            existing.badge_class = data.get('badge_class')
            existing.short_description = data['short_description']
            existing.long_description = data['long_description']
            existing.what_you_get = data.get('what_you_get', [])
            existing.information_needed = data.get('information_needed', [])
            existing.important_notes = data.get('important_notes', [])
    db.session.commit()


def get_all_documents():
    """Return all active and coming_soon documents."""
    return list(DOCUMENTS.values())


def get_document_by_id(doc_id):
    """Return a single document by its ID/slug, or None if not found."""
    return DOCUMENTS.get(doc_id)


def get_documents_by_category(category_name):
    """Return all documents in a given category."""
    return [
        doc for doc in DOCUMENTS.values()
        if doc['category'].lower() == category_name.lower()
        or doc.get('category_slug', '').lower() == category_name.lower()
    ]


def get_all_categories():
    """Return all categories with their associated documents."""
    categories_with_docs = {}
    for cat_name, category in DOCUMENT_CATEGORIES.items():
        categories_with_docs[cat_name] = {
            **category,
            'documents': get_documents_by_category(cat_name),
        }
    return categories_with_docs
