"""
Document catalogue data and database integration.

Defines all available legal templates across categories.
All templates are active and ready for guided drafting.
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

        'faqs': [
            {
                'question': 'What is the mandatory 15-day notice period under Section 138?',
                'answer': 'Under Section 138(c) of the Negotiable Instruments Act, 1881, the legal notice demands payment within 15 days of its receipt by the cheque drawer. The cause of action to file a criminal complaint before the Judicial Magistrate arises only after this 15-day window expires without payment.'
            },
            {
                'question': 'Within how many days of the cheque return memo must the notice be sent?',
                'answer': 'The notice must be dispatched within exactly 30 days of receiving the bank dishonour memo. If you miss this statutory 30-day deadline, you forfeit your right to initiate criminal proceedings under Section 138, leaving only a civil recovery suit.'
            },
            {
                'question': 'Is an advocate mandatory to send a Section 138 legal notice?',
                'answer': 'No. An aggrieved payee can issue a Section 138 notice directly under their own signature. However, if you prefer advocate representation, our generator supports advocate particulars and generates an editable Word (.docx) file that an advocate can print on their legal letterhead.'
            },
            {
                'question': 'Which dispatch method is recognized as valid proof of service in court?',
                'answer': 'The notice must be sent via Registered Post Acknowledgement Due (RPAD) or Speed Post with delivery tracking. In Indian courts, postal receipts and online delivery confirmations constitute statutory proof of service under Section 27 of the General Clauses Act.'
            },
            {
                'question': 'What documents must be preserved after dispatching the notice?',
                'answer': 'Keep the original dishonoured cheque, original bank return memo, signed copy of this legal notice, the postal dispatch receipt, and the printed delivery tracking report showing delivery or refusal.'
            }
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
        'status': 'active',
        'version': 'v1.0 (Ready)',
        'image_url': 'https://images.pexels.com/photos/12955837/pexels-photo-12955837.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Draft comprehensive residential rental terms, monthly rent, security deposits, and maintenance covenants.'
        ),

        'long_description': (
            'A comprehensive residential tenancy agreement template designed for 11-month lease periods '
            'under standard state rent control practices. Outlines security deposits, rent cycles, notice periods, '
            'and tenant/landlord covenants.'
        ),

        'what_you_get': [
            'Editable lease agreement in Word (.docx) and PDF.',
            'Standard clauses covering maintenance, notice period, and deposit refund.',
            'Standard two-witness execution covenants.',
        ],

        'information_needed': [
            'Landlord and Tenant identification and address.',
            'Premises address and inventory details.',
            'Monthly rent, security deposit, and lock-in period.',
        ],

        'important_notes': [
            'Must be executed on appropriate state non-judicial stamp paper.',
            'Standard 11-month duration avoids mandatory sub-registrar registration under Section 17 Registration Act.',
        ],

        'faqs': [
            {
                'question': 'Why is an 11-month duration standard for rental agreements in India?',
                'answer': 'Under Section 17 of the Registration Act, 1908, leases of immovable property for a term exceeding 11 months require mandatory registration with sub-registrar offices. An 11-month agreement on appropriate stamp paper is standard for residential tenancies to simplify execution.'
            },
            {
                'question': 'Who is responsible for paying stamp duty and registration charges?',
                'answer': 'By standard convention across Indian states, stamp duty and notarization fees are divided equally (50:50) between the landlord and tenant, unless agreed otherwise in writing.'
            },
            {
                'question': 'How is the security deposit refund timeline enforced?',
                'answer': 'Our agreement template contains explicit covenants requiring the landlord to refund the interest-free security deposit within 7 to 15 days of peaceful key handover, subject to deduction of actual unpaid utilities or documented physical damages.'
            },
            {
                'question': 'Can the landlord arbitrarily increase rent during the agreement term?',
                'answer': 'No. The monthly rent remains fixed for the entire 11-month tenure. Any mutually agreed rent escalation (typically 5% to 10%) takes effect only upon execution of a formal renewal agreement.'
            }
        ],

        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
    },

    'affidavit': {
        'id': 'affidavit',
        'title': 'Affidavit',
        'subtitle': 'General Sworn Statement for Government and Administrative Verifications',
        'category': 'affidavits',
        'category_slug': 'affidavits',
        'price': 149,
        'status': 'active',
        'version': 'v1.0 (Ready)',
        'image_url': 'https://images.pexels.com/photos/9858904/pexels-photo-9858904.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Organise factual statements in an official sworn declaration format ready for notarization.'
        ),

        'long_description': (
            'A general affidavit template for swearing factual statements before an Executive Magistrate or Notary Public. '
            'Commonly used for address proof, name discrepancy, loss of documents, or official government declarations.'
        ),

        'what_you_get': [
            'Affidavit draft in Word (.docx) and PDF.',
            'Format compatible with standard non-judicial e-stamp paper.',
            'Verification and Deponent jurat compliant with CPC Section 139.',
        ],

        'information_needed': [
            'Deponent details and photo ID references.',
            'Factual statements to be sworn.',
            'Place and city of execution.',
        ],

        'important_notes': [
            'Must be printed on appropriate state non-judicial stamp paper and notarized to be legally valid.',
        ],

        'faqs': [
            {
                'question': 'What stamp paper value is required for an affidavit in India?',
                'answer': 'Non-judicial stamp paper denominations vary by state (commonly ₹10, ₹20, ₹50, or ₹100 e-stamp). Verify your local state revenue department or notary requirements before printing.'
            },
            {
                'question': 'Who is legally authorized to attest or notarize an affidavit?',
                'answer': 'Under Section 139 of the Code of Civil Procedure, an affidavit must be sworn before an Oath Commissioner, an appointed Notary Public, or a Judicial/Executive Magistrate.'
            },
            {
                'question': 'What is the consequence of making a false statement in an affidavit?',
                'answer': 'Making a false sworn statement in an affidavit is a criminal offence punishable under Section 193 of the Indian Penal Code (perjury), carrying imprisonment of up to 7 years.'
            }
        ],

        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
    },

    'notice': {
        'id': 'notice',
        'title': 'General Legal Notice',
        'subtitle': 'A structured starting point for formal legal correspondence and demands',
        'category': 'notices',
        'category_slug': 'notices',
        'price': 299,
        'status': 'active',
        'version': 'v1.0 (Ready)',
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
            'Notice must be served via RPAD or Speed Post for admissible legal proof of delivery.',
            'Preserve postal receipts and delivery tracking reports.',
        ],

        'faqs': [
            {
                'question': 'What is the limitation period for filing a money recovery suit?',
                'answer': 'Under the Limitation Act, 1963, the limitation period to file a civil suit for debt recovery or unpaid dues is 3 years from the date the payment fell due or from the last written acknowledgment of debt.'
            },
            {
                'question': 'Can I claim interest on outstanding dues in the legal notice?',
                'answer': 'Yes. You can demand interest as per contract terms, the Interest Act 1978, or under Section 16 of the MSMED Act for registered MSME suppliers (which mandates compound interest at 3 times RBI bank rate).'
            },
            {
                'question': 'How much time should I grant the recipient to comply?',
                'answer': 'The standard practice is granting 15 to 30 days from delivery receipt for the recipient to remedy the breach or pay the outstanding dues before formal civil litigation is initiated.'
            }
        ],

        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
    },

    'nda': {
        'id': 'nda',
        'title': 'Non-Disclosure Agreement',
        'subtitle': 'Standard Mutual or Unilateral Confidentiality Agreement',
        'category': 'agreements',
        'category_slug': 'agreements',
        'price': 199,
        'status': 'active',
        'version': 'v1.0 (Ready)',
        'image_url': 'https://images.pexels.com/photos/3760067/pexels-photo-3760067.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Safeguard proprietary business data, trade secrets, and confidential discussions between parties.'
        ),

        'long_description': (
            'A standard non-disclosure agreement to protect trade secrets, intellectual property, and proprietary data '
            'during business discussions or partnerships.'
        ),

        'what_you_get': [
            'Customizable NDA in Word and PDF.',
            'Standard confidentiality and non-solicitation clauses.',
            'Injunctive relief covenants under Specific Relief Act.',
        ],

        'information_needed': [
            'Disclosing and Receiving party identities.',
            'Scope of confidential information.',
            'Duration of confidentiality obligation.',
        ],

        'important_notes': [
            'Can be executed electronically under Section 10A of the Information Technology Act, 2000.',
        ],

        'faqs': [
            {
                'question': 'What is the standard confidentiality duration under Indian law?',
                'answer': 'Commercial NDAs typically specify a confidentiality period of 2 to 5 years from disclosure. However, trade secrets and proprietary source code can be protected indefinitely as long as they remain non-public.'
            },
            {
                'question': 'Are electronic and digital signatures legally enforceable on an NDA?',
                'answer': 'Yes. Under Section 10A of the Information Technology Act, 2000, agreements executed via electronic or digital signatures have equal legal validity and evidentiary enforceability in Indian courts.'
            },
            {
                'question': 'What happens if a party breaches the NDA?',
                'answer': 'The aggrieved party can seek an immediate interim court injunction under the Specific Relief Act, 1963, to restrain further unauthorized disclosure and claim monetary damages for financial losses.'
            }
        ],

        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
    },

    'business': {
        'id': 'business',
        'title': 'Business Agreement',
        'subtitle': 'Commercial Contract for Services, Vendors, and Deliverables',
        'category': 'agreements',
        'category_slug': 'agreements',
        'price': 349,
        'status': 'active',
        'version': 'v1.0 (Ready)',
        'image_url': 'https://images.pexels.com/photos/7641994/pexels-photo-7641994.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Structure binding business contracts, scopes of work, deliverables, and payment schedules.'
        ),

        'long_description': (
            'A commercial contract template establishing obligations, deliverables, payment milestones, and dispute resolution mechanisms.'
        ),

        'what_you_get': [
            'Commercial agreement in Word (.docx) and PDF.',
            'Milestone payment and intellectual property assignment clauses.',
            'Tiered dispute resolution and arbitration provisions.',
        ],

        'information_needed': [
            'Entity names and registration numbers.',
            'Scope of work and payment terms.',
            'Dispute resolution seat and governing law.',
        ],

        'important_notes': [
            'Includes Work-Made-For-Hire intellectual property transfer terms upon receipt of consideration.',
        ],

        'faqs': [
            {
                'question': 'Who owns intellectual property created under this agreement?',
                'answer': 'Under Indian copyright law, the creator retains ownership unless a written contract explicitly assigns the IP. This draft includes comprehensive Work Made for Hire and assignment clauses that transfer ownership upon full payment.'
            },
            {
                'question': 'Are non-compete clauses enforceable in India?',
                'answer': 'Post-termination non-compete clauses are void under Section 27 of the Indian Contract Act, 1872. However, non-solicitation covenants, non-disclosure of confidential trade secrets, and non-compete restrictions during the active contract period are enforceable.'
            },
            {
                'question': 'How are contract disputes resolved under this draft?',
                'answer': 'The agreement provides for standard tiered dispute resolution: initial amicable executive negotiations, followed by expedited binding arbitration under the Arbitration and Conciliation Act, 1996.'
            }
        ],

        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
    },

    'application': {
        'id': 'application',
        'title': 'Formal Application',
        'subtitle': 'Structured Written Application for Official and Institutional Filings',
        'category': 'applications',
        'category_slug': 'applications',
        'price': 149,
        'status': 'active',
        'version': 'v1.0 (Ready)',
        'image_url': 'https://images.pexels.com/photos/8730987/pexels-photo-8730987.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Prepare a formal, structured administrative application for governmental, institutional, or university bodies.'
        ),

        'long_description': (
            'A structured formal application format for government departments, universities, authorities, or courts.'
        ),

        'what_you_get': [
            'Application format in Word and PDF.',
            'Official reference and subject hierarchy conforming to departmental standards.',
        ],

        'information_needed': [
            'Authority designation and address.',
            'Applicant credentials and grounds of application.',
            'Specific prayer or requested relief.',
        ],

        'important_notes': [
            'Submit with stamped counter-acknowledgement or send via Speed Post.',
        ],

        'faqs': [
            {
                'question': 'What are the essential ingredients of an official Indian administrative application?',
                'answer': 'An official application must clearly state the recipient authority designation, subject line with reference numbers, applicant particulars, chronological facts, specific relief or request, and verification date/signature.'
            },
            {
                'question': 'How should an application be delivered to government departments?',
                'answer': 'Deliver by Registered Post/Speed Post with acknowledgement or submit in-person at the departmental receiving counter and obtain an official stamped acknowledgement (dairy number).'
            }
        ],

        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
    },

    'letter': {
        'id': 'letter',
        'title': 'Declaration Letter',
        'subtitle': 'Formal Declaration Statement for Administrative Use',
        'category': 'other',
        'category_slug': 'other',
        'price': 99,
        'status': 'active',
        'version': 'v1.0 (Ready)',
        'image_url': 'https://images.pexels.com/photos/190295/pexels-photo-190295.jpeg?auto=compress&cs=tinysrgb&w=800',

        'short_description': (
            'Generate a formal declaration statement or self-attestation letter for administrative, commercial, or personal use.'
        ),

        'long_description': (
            'A formal declaration letter certifying facts, status, or self-attestations.'
        ),

        'what_you_get': [
            'Declaration letter in Word and PDF.',
            'Self-attestation format accepted under GoI administrative guidelines.',
        ],

        'information_needed': [
            'Declarant identity.',
            'Specific facts being certified.',
        ],

        'important_notes': [
            'Can be backed by identity document copies for official submissions.',
        ],

        'faqs': [
            {
                'question': 'When is a self-declaration letter accepted in lieu of an affidavit in India?',
                'answer': 'Under the Government of India self-attestation reforms, most administrative and educational institutions accept self-declaration letters without requiring executive magistrate stamps, unless specifically mandated by statutory rules.'
            },
            {
                'question': 'Does a declaration letter require witness signatures?',
                'answer': 'While not always compulsory, having one or two credible witnesses attest the declarant signature significantly enhances its evidentiary value before private entities, banks, and academic institutions.'
            }
        ],

        'badge_text': 'Available Now',
        'badge_class': 'bg-success',
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
