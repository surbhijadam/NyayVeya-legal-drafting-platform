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
        'description': 'Statutory notices mandated under Indian laws before initiating legal action.',
        'icon': 'bi-envelope-paper',
    },
    'agreements': {
        'name': 'Agreements & Contracts',
        'description': 'Standard legal contracts and everyday binding agreements.',
        'icon': 'bi-file-earmark-text',
    },
    'affidavits': {
        'name': 'Affidavits & Declarations',
        'description': 'Sworn statements and declarations for legal or administrative purposes.',
        'icon': 'bi-journal-check',
    },
}

DOCUMENTS = {
    'cheque-bounce-notice': {
        'id': 'cheque-bounce-notice',
        'title': 'Cheque Bounce Notice',
        'subtitle': 'Demand Notice under Section 138 of the Negotiable Instruments Act, 1881',
        'category': 'notices',
        'price': 199,  # In INR
        'status': 'active',  # Active for drafting workflow!
        'version': 'v1.0 (NI Act Compliant)',

        'short_description': (
            'Formal statutory demand notice sent to the cheque drawer demanding payment '
            'within 15 days of receipt, mandatory before filing a Section 138 criminal complaint.'
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
            'Payee / Complainant details (Full Name, Address, Contact details).',
            'Drawer / Accused details (Cheque Issuer\'s Full Name and Address).',
            'Cheque specifics (Cheque Number, Cheque Date, Amount in ₹, Drawee Bank & Branch).',
            'Bank return memo details (Date of memo and Reason for dishonour, e.g. "Funds Insufficient").',
            'Background transaction details (e.g. Loan repayment, goods supplied, professional services).',
        ],

        'important_notes': [
            'Strict 30-Day Deadline: Notice must be issued within 30 days of receiving the bank dishonour memo.',
            'Mandatory Dispatch Method: Send via Registered Post Acknowledgement Due (RPAD) or Speed Post.',
            'Evidence Preservation: Retain the postal dispatch receipt and the online tracking delivery report.',
            '15-Day Payment Window: The drawer gets 15 days from delivery to make payment before a complaint can be filed.',
            'Disclaimer: This is a standard template generator and does not constitute personalised legal advice.',
        ],

        'icon': 'bi-file-earmark-medical',
        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
    },

    'recovery-notice': {
        'id': 'recovery-notice',
        'title': 'Money Recovery Legal Notice',
        'subtitle': 'Formal demand notice for outstanding debt / unpaid invoices',
        'category': 'notices',
        'price': 299,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',

        'short_description': (
            'Formal demand notice demanding payment of outstanding debt, unpaid invoices, or contractual dues.'
        ),

        'long_description': (
            'A formal legal notice addressed to a debtor demanding clearance of pending dues '
            'within a specified period prior to initiating civil recovery proceedings or summary suits.'
        ),

        'what_you_get': [
            'Customizable Word document (.docx).',
            'Print-ready PDF.',
            'Statutory limitation guidance under the Limitation Act, 1963.',
        ],

        'information_needed': [
            'Creditor and Debtor details.',
            'Invoice / loan agreement references.',
            'Total outstanding principal and interest calculations.',
        ],

        'important_notes': [
            'Under review by legal experts.',
            'Subject to 3-year limitation period under Indian law.',
        ],

        'icon': 'bi-cash-coin',
        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },

    'residential-rent-agreement': {
        'id': 'residential-rent-agreement',
        'title': 'Residential Rental Agreement',
        'subtitle': '11-Month Standard Lease Agreement for Landlords & Tenants',
        'category': 'agreements',
        'price': 249,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',

        'short_description': (
            'Standard 11-month residential tenancy agreement covering rent, security deposit, maintenance, and notice period.'
        ),

        'long_description': (
            'A comprehensive rental agreement template designed for residential tenancies under state rent control guidelines.'
        ),

        'what_you_get': [
            'Editable lease agreement in Word and PDF.',
            'Clauses covering maintenance, notice period, and deposit return.',
        ],

        'information_needed': [
            'Landlord and Tenant identification.',
            'Property address and inventory details.',
            'Monthly rent, security deposit, and lock-in period.',
        ],

        'important_notes': [
            'Coming soon after review.',
        ],

        'icon': 'bi-house-check',
        'badge_text': 'Coming Soon',
        'badge_class': 'bg-secondary',
    },

    'general-affidavit': {
        'id': 'general-affidavit',
        'title': 'General Affidavit',
        'subtitle': 'Sworn declaration on non-judicial stamp paper format',
        'category': 'affidavits',
        'price': 149,
        'status': 'coming_soon',
        'version': 'v1.0 (Draft)',

        'short_description': (
            'Standard sworn statement format for official, government, or administrative verifications.'
        ),

        'long_description': (
            'A general affidavit template for swearing factual statements before an Executive Magistrate or Notary Public.'
        ),

        'what_you_get': [
            'Affidavit draft in Word and PDF.',
            'Format compatible with standard non-judicial e-stamp paper.',
        ],

        'information_needed': [
            'Deponent details and photo ID references.',
            'Factual statements to be sworn.',
        ],

        'important_notes': [
            'Must be printed on stamp paper and notarized to be legally valid.',
        ],

        'icon': 'bi-patch-check',
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
                icon=data.get('icon', 'bi-file-earmark-medical'),
                badge_text=data.get('badge_text'),
                badge_class=data.get('badge_class', 'bg-primary')
            )
            tmpl.what_you_get = data.get('what_you_get', [])
            tmpl.information_needed = data.get('information_needed', [])
            tmpl.important_notes = data.get('important_notes', [])
            db.session.add(tmpl)
        else:
            # Update existing status/pricing/metadata if changed
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


def get_documents_by_category(category_key):
    """Return all documents in a given category."""
    return [doc for doc in DOCUMENTS.values() if doc['category'] == category_key]


def get_all_categories():
    """Return all categories with their associated documents."""
    categories_with_docs = {}
    for key, category in DOCUMENT_CATEGORIES.items():
        categories_with_docs[key] = {
            **category,
            'key': key,
            'documents': get_documents_by_category(key),
        }
    return categories_with_docs
