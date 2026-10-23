"""
Legal notice template text formatting for Section 138 of Negotiable Instruments Act, 1881.
"""
from datetime import datetime, date


def format_cheque_bounce_notice(data):
    """
    Generate structured legal notice text based on validated user input.
    Returns a dictionary with structured sections and full text.
    Handles missing or empty dictionary keys with safe legal defaults.
    """
    if not isinstance(data, dict):
        data = {}

    notice_date_val = data.get('notice_date')
    if isinstance(notice_date_val, (date, datetime)):
        notice_date_str = notice_date_val.strftime('%d-%m-%Y')
    elif notice_date_val:
        notice_date_str = str(notice_date_val)
    else:
        notice_date_str = date.today().strftime('%d-%m-%Y')

    cheque_date_val = data.get('cheque_date')
    if isinstance(cheque_date_val, (date, datetime)):
        cheque_date_str = cheque_date_val.strftime('%d-%m-%Y')
    elif cheque_date_val:
        cheque_date_str = str(cheque_date_val)
    else:
        cheque_date_str = date.today().strftime('%d-%m-%Y')

    memo_date_val = data.get('memo_date')
    if isinstance(memo_date_val, (date, datetime)):
        memo_date_str = memo_date_val.strftime('%d-%m-%Y')
    elif memo_date_val:
        memo_date_str = str(memo_date_val)
    else:
        memo_date_str = date.today().strftime('%d-%m-%Y')

    raw_amt = data.get('cheque_amount')
    if raw_amt is None:
        raw_amt = data.get('amount')
    if raw_amt is not None and str(raw_amt).strip() != '':
        try:
            amount_formatted = f"₹{int(float(raw_amt)):,}"
        except (ValueError, TypeError):
            amount_formatted = f"₹{raw_amt}"
    else:
        amount_formatted = "₹[Amount]"

    payee_name = (data.get('payee_name') or '').strip() or '[Payee / Complainant Name]'
    payee_address = (data.get('payee_address') or '').strip() or '[Payee Address]'
    payee_phone = (data.get('payee_phone') or '').strip() or '[Payee Phone]'

    advocate_name = (data.get('advocate_name') or '').strip()
    advocate_address = (data.get('advocate_address') or '').strip()

    drawer_name = (data.get('drawer_name') or '').strip() or '[Drawer / Noticee Name]'
    drawer_address = (data.get('drawer_address') or '').strip() or '[Drawer Address]'

    cheque_number = (data.get('cheque_number') or '').strip() or '[Cheque Number]'
    cheque_amount_words = (data.get('cheque_amount_words') or '').strip() or '[Amount in words]'
    bank_name = (data.get('bank_name') or '').strip() or '[Bank Name]'
    bank_branch = (data.get('bank_branch') or '').strip() or '[Bank Branch]'
    dishonour_reason = (data.get('dishonour_reason') or '').strip() or 'Funds Insufficient'
    transaction_details = (data.get('transaction_details') or '').strip() or '[Details of underlying transaction / legally enforceable debt]'

    # Header section
    header = "REGISTERED POST WITH ACKNOWLEDGEMENT DUE (RPAD) / SPEED POST"

    # Sender (Payee or Advocate)
    if advocate_name:
        sender_block = (
            f"FROM:\n"
            f"{advocate_name}\nAdvocate\n{advocate_address}\n(Under instructions of Client: {payee_name})"
        )
    else:
        sender_block = f"FROM:\n{payee_name}\n{payee_address}\nPhone: {payee_phone}"

    recipient_block = (
        f"TO:\n"
        f"{drawer_name}\n"
        f"{drawer_address}"
    )

    subject = (
        "SUBJECT: LEGAL NOTICE OF DEMAND UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 "
        f"FOR DISHONOUR OF CHEQUE BEARING NO. {cheque_number} FOR {amount_formatted}."
    )

    paragraphs = [
        (
            f"1. That you, the Noticee/Addressee, approached my Client ({payee_name}) "
            f"and entered into a transaction wherein in discharge of your legally enforceable debt and liability, "
            f"namely: {transaction_details}."
        ),
        (
            f"2. That towards part/full discharge of the aforesaid legally enforceable debt and liability, "
            f"you issued and delivered Cheque bearing No. {cheque_number}, dated {cheque_date_str}, "
            f"drawn for a sum of {amount_formatted} ({cheque_amount_words}) "
            f"on {bank_name}, {bank_branch} in favour of my Client."
        ),
        (
            f"3. That at the time of issuing the aforesaid cheque, you specifically represented and assured "
            f"that the same was good for payment and would be promptly honoured upon presentation to your bankers."
        ),
        (
            f"4. That acting on your express representations and assurances, my Client presented the said cheque "
            f"for encashment within its period of statutory validity through banker. However, to the utter shock and "
            f"dismay of my Client, the said cheque was returned unpaid and dishonoured by your bank vide Return Memo "
            f"dated {memo_date_str} with the endorsement/reason: \"{dishonour_reason}\"."
        ),
        (
            f"5. That your aforesaid conduct clearly demonstrates dishonest and fraudulent intention from the inception, "
            f"and you have failed to maintain sufficient balance in your bank account, thereby committing an offence "
            f"punishable under Section 138 of the Negotiable Instruments Act, 1881."
        ),
        (
            f"6. Now, therefore, through this statutory legal demand notice, you are hereby called upon and demanded "
            f"to make the full payment of the cheque amount of {amount_formatted} ({cheque_amount_words}) "
            f"to my Client within a period of 15 (fifteen) days from the date of receipt of this notice."
        ),
        (
            f"7. Please take notice that in the event you fail, neglect, or refuse to make the payment of the said amount "
            f"within the statutory period of 15 days from the date of receipt hereof, my Client shall be constrained to "
            f"initiate criminal proceedings against you under Section 138 read with Section 142 of the Negotiable "
            f"Instruments Act, 1881, as well as applicable civil proceedings for recovery of the outstanding amount "
            f"with interest and costs, at your sole risk, cost, and legal consequences."
        )
    ]

    signoff = (
        f"Yours faithfully,\n\n"
        f"___________________________\n"
        f"{advocate_name or payee_name}\n"
        f"{'Advocate for Complainant' if advocate_name else 'Payee / Complainant'}\n"
        f"Date: {notice_date_str}"
    )

    full_text = f"{header}\n\n{notice_date_str}\n\n{recipient_block}\n\n{subject}\n\n" + "\n\n".join(paragraphs) + f"\n\n{signoff}"

    return {
        'header': header,
        'notice_date': notice_date_str,
        'sender_block': sender_block,
        'recipient_block': recipient_block,
        'subject': subject,
        'paragraphs': paragraphs,
        'signoff': signoff,
        'full_text': full_text,
        'amount_formatted': amount_formatted,
    }


def format_standard_legal_document(slug, data, template=None):
    """
    Format standard legal documents (Rent Agreement, Affidavit, Legal Notice,
    NDA, Business Agreement, Formal Application, Declaration Letter).
    Returns a structured dictionary compatible with preview, docx, and pdf generation.
    """
    if not isinstance(data, dict):
        data = {}

    doc_date_val = data.get('document_date') or data.get('notice_date')
    if isinstance(doc_date_val, (date, datetime)):
        doc_date_str = doc_date_val.strftime('%d-%m-%Y')
    elif doc_date_val:
        doc_date_str = str(doc_date_val)
    else:
        doc_date_str = date.today().strftime('%d-%m-%Y')

    city = (data.get('city') or 'New Delhi').strip()

    raw_amt = data.get('amount')
    if raw_amt is not None and str(raw_amt).strip() not in ('', '0'):
        try:
            amount_formatted = f"₹{int(float(raw_amt)):,}"
        except (ValueError, TypeError):
            amount_formatted = f"₹{raw_amt}"
    else:
        amount_formatted = "₹0"

    first_party_name = (data.get('first_party_name') or data.get('payee_name') or '[First Party / Deponent]').strip()
    first_party_details = (data.get('first_party_details') or data.get('payee_address') or '[First Party Address & Particulars]').strip()

    second_party_name = (data.get('second_party_name') or data.get('drawer_name') or '[Second Party / Recipient]').strip()
    second_party_details = (data.get('second_party_details') or data.get('drawer_address') or '[Second Party Address]').strip()

    subject_purpose = (data.get('subject_purpose') or data.get('transaction_details') or 'Legal Drafting Matter').strip()
    duration_period = (data.get('duration_period') or '11 Months').strip()
    key_terms = (data.get('key_terms') or 'Standard statutory terms and covenants agreed between parties.').strip()

    slug_norm = (slug or '').lower()

    if 'rent' in slug_norm or 'lease' in slug_norm:
        header = "RESIDENTIAL LEASE / RENT AGREEMENT"
        subject = f"SUBJECT: TENANCY IN RESPECT OF PREMISES AT {subject_purpose.upper()}"
        sender_block = f"LANDLORD / LESSOR:\n{first_party_name}\n{first_party_details}"
        recipient_block = f"TENANT / LESSEE:\n{second_party_name}\n{second_party_details}"
        paragraphs = [
            f"THIS LEASE AGREEMENT is executed on this {doc_date_str} at {city} by and between {first_party_name}, residing at {first_party_details} (hereinafter called the 'LESSOR / LANDLORD', which expression shall include legal heirs and assigns) of the FIRST PART;\nAND\n{second_party_name}, residing at {second_party_details} (hereinafter called the 'LESSEE / TENANT', which expression shall include legal heirs and permitted assigns) of the SECOND PART.",
            f"1. DEMISED PREMISES: The Lessor hereby agrees to let out and the Lessee agrees to take on lease the premises situated at: {subject_purpose}.",
            f"2. TERM & TENURE: The tenancy shall be for an initial fixed term of {duration_period}, commencing with effect from {doc_date_str}, unless renewed by mutual written consent on fresh terms.",
            f"3. MONTHLY RENT: The Lessee covenants to pay to the Lessor a monthly rent of {amount_formatted} (exclusive of electricity, water, and maintenance charges), payable on or before the 5th day of each English calendar month.",
            "4. REFUNDABLE SECURITY DEPOSIT: The Lessee has deposited with the Lessor an interest-free refundable security deposit, returnable without interest at the time of peaceful and vacant possession handover, subject to adjustment of any unpaid utility bills or documented physical damages.",
            "5. USE & COVENANTS: The premises shall be utilized strictly for peaceful residential purposes only. The Lessee shall not sublet, assign, or part with possession of the premises or any part thereof to third parties.",
            f"6. SPECIFIC COVENANTS & TERMS:\n{key_terms}",
            "7. NOTICE & TERMINATION: Either party may terminate this agreement prior to expiry of the tenure by providing one month's advance written notice or by paying one month's rent in lieu thereof.",
            f"8. GOVERNING LAW & JURISDICTION: This Agreement shall be governed by the laws of India and subject to the exclusive jurisdiction of the Courts at {city}."
        ]
        signoff = (
            f"IN WITNESS WHEREOF, the parties hereto have signed and executed this Agreement at {city} on this {doc_date_str}:\n\n"
            f"___________________________                     ___________________________\n"
            f"LESSOR / LANDLORD                               LESSEE / TENANT\n"
            f"({first_party_name})                            ({second_party_name})\n\n"
            f"WITNESS 1: _____________________                WITNESS 2: _____________________\n"
            f"Name:                                           Name:\n"
            f"Address:                                        Address:"
        )

    elif 'affidavit' in slug_norm:
        header = "GENERAL AFFIDAVIT / SWORN DECLARATION"
        subject = f"IN THE MATTER OF: {subject_purpose.upper()}"
        sender_block = f"DEPONENT:\n{first_party_name}\n{first_party_details}"
        recipient_block = f"BEFORE:\n{second_party_name if second_party_name != '[Second Party / Recipient]' else 'Notary Public / Oath Commissioner / Concerned Authority'}\n{city}"
        paragraphs = [
            f"I, {first_party_name}, residing at {first_party_details}, do hereby solemnly affirm and state on oath as under:",
            f"1. That I am a citizen of India, of sound mind and legal capacity, and competent to depose to this affidavit.",
            f"2. That this affidavit is being sworn in connection with: {subject_purpose}.",
            f"3. SPECIFIC FACTS AFFIRMED UNDER OATH:\n{key_terms}",
            "4. That the statements made in the foregoing paragraphs are true and correct to my personal knowledge, belief, and records, and that no material facts have been concealed or misrepresented.",
            "5. That I make this solemn declaration conscientiously believing the same to be true and in accordance with the provisions of the Oaths Act, 1969 and Section 139 of the Code of Civil Procedure."
        ]
        signoff = (
            f"VERIFICATION:\n"
            f"Verified at {city} on this {doc_date_str} that the contents of paragraphs 1 to 5 above are true and correct to the best of my personal knowledge and belief, and nothing material has been concealed therefrom.\n\n\n"
            f"___________________________\n"
            f"DEPONENT\n"
            f"({first_party_name})\n\n"
            f"Solemnly affirmed and signed before me by the Deponent who is personally known to me / identified by proof.\n\n"
            f"NOTARY PUBLIC / OATH COMMISSIONER\n"
            f"Seal & Registration No."
        )

    elif 'nda' in slug_norm:
        header = "MUTUAL NON-DISCLOSURE AGREEMENT (NDA)"
        subject = f"SUBJECT: CONFIDENTIALITY OBLIGATIONS IN RELATION TO {subject_purpose.upper()}"
        sender_block = f"DISCLOSING PARTY:\n{first_party_name}\n{first_party_details}"
        recipient_block = f"RECEIVING PARTY:\n{second_party_name}\n{second_party_details}"
        paragraphs = [
            f"THIS NON-DISCLOSURE AGREEMENT is entered into on this {doc_date_str} at {city} by and between {first_party_name}, having address at {first_party_details} ('Disclosing Party') AND {second_party_name}, having address at {second_party_details} ('Receiving Party').",
            f"1. PURPOSE: The parties wish to explore and engage in business discussions concerning: {subject_purpose}.",
            "2. CONFIDENTIAL INFORMATION: Includes all non-public technical, operational, financial, software, source code, trade secrets, customer data, and commercial information disclosed by either party.",
            "3. OBLIGATIONS OF RECEIVING PARTY: The Receiving Party agrees to hold all Confidential Information in strict confidence and use it solely for the Purpose, applying at least the standard of care applied to its own proprietary data.",
            f"4. DURATION & TERM: The confidentiality obligations herein shall remain in effect for a period of {duration_period} from the date of disclosure.",
            f"5. SPECIFIC TERMS & REMEDIES:\n{key_terms}",
            "6. INJUNCTIVE RELIEF: The parties acknowledge that unauthorized disclosure causes irreparable harm for which monetary damages alone would be inadequate, entitling the disclosing party to seek immediate injunctive relief.",
            f"7. GOVERNING LAW: Governed by the laws of India, subject to exclusive jurisdiction of the Courts at {city}."
        ]
        signoff = (
            f"IN WITNESS WHEREOF, the parties hereto have executed this Agreement on this {doc_date_str}:\n\n"
            f"___________________________                     ___________________________\n"
            f"FOR DISCLOSING PARTY                            FOR RECEIVING PARTY\n"
            f"({first_party_name})                            ({second_party_name})\n"
            f"Authorized Signatory                            Authorized Signatory"
        )

    elif 'business' in slug_norm:
        header = "COMMERCIAL SERVICES & BUSINESS AGREEMENT"
        subject = f"SUBJECT: BUSINESS ARRANGEMENT CONCERNING {subject_purpose.upper()}"
        sender_block = f"SERVICE PROVIDER / PARTY 1:\n{first_party_name}\n{first_party_details}"
        recipient_block = f"CLIENT / PARTY 2:\n{second_party_name}\n{second_party_details}"
        paragraphs = [
            f"THIS BUSINESS AGREEMENT is made on this {doc_date_str} at {city} by and between {first_party_name}, with address at {first_party_details} (hereinafter called the 'FIRST PARTY') AND {second_party_name}, with address at {second_party_details} (hereinafter called the 'SECOND PARTY').",
            f"1. SCOPE OF SERVICES: The First Party covenants to provide and perform the commercial services and deliverables in respect of: {subject_purpose}.",
            f"2. CONSIDERATION & PAYMENTS: The total agreed fee/consideration for the services is {amount_formatted}, payable in accordance with the agreed schedule upon delivery milestone verification.",
            f"3. DURATION: This Agreement shall commence on {doc_date_str} and remain in full force and effect for {duration_period}, unless terminated earlier pursuant to contract terms.",
            f"4. SPECIFIC BUSINESS TERMS & COVENANTS:\n{key_terms}",
            "5. INTELLECTUAL PROPERTY: Upon receipt of full payment, all intellectual property rights in work products created specifically for the project shall vest in the client under standard Work-Made-For-Hire principles.",
            f"6. DISPUTE RESOLUTION: Any dispute arising out of this agreement shall be settled through amicable negotiation, failing which by arbitration under the Arbitration and Conciliation Act, 1996 with seat at {city}."
        ]
        signoff = (
            f"IN WITNESS WHEREOF, the parties have executed this Agreement at {city} on {doc_date_str}:\n\n"
            f"___________________________                     ___________________________\n"
            f"FIRST PARTY                                     SECOND PARTY\n"
            f"({first_party_name})                            ({second_party_name})"
        )

    elif 'application' in slug_norm:
        header = "FORMAL ADMINISTRATIVE APPLICATION"
        subject = f"SUBJECT: APPLICATION REGARDING {subject_purpose.upper()}"
        sender_block = f"FROM:\n{first_party_name}\n{first_party_details}"
        recipient_block = f"TO:\n{second_party_name}\n{second_party_details}"
        paragraphs = [
            "Respected Sir / Madam,",
            f"1. Most respectfully showeth, that I, {first_party_name}, residing at {first_party_details}, submit this formal application for your kind consideration regarding: {subject_purpose}.",
            f"2. STATEMENT OF FACTS & GROUNDS:\n{key_terms}",
            "3. That the applicant has complied with all statutory requirements, procedural formalities, and rules applicable to this matter.",
            f"4. PRAYER / SPECIFIC RELIEF: In light of the above facts, it is respectfully prayed that the competent authority may kindly grant the approval/relief sought herein within {duration_period} in the interest of justice.",
            "5. The applicant undertakes to furnish any further documents or attend verification as may be required."
        ]
        signoff = (
            f"Thanking you,\n\n"
            f"Yours faithfully,\n\n"
            f"___________________________\n"
            f"({first_party_name})\n"
            f"Applicant\n"
            f"Date: {doc_date_str}\n"
            f"Place: {city}"
        )

    elif 'letter' in slug_norm:
        header = "FORMAL SELF-DECLARATION LETTER"
        subject = f"SUBJECT: DECLARATION CONCERNING {subject_purpose.upper()}"
        sender_block = f"DECLARANT:\n{first_party_name}\n{first_party_details}"
        recipient_block = f"TO:\n{second_party_name if second_party_name != '[Second Party / Recipient]' else 'To Whomsoever It May Concern'}\n{second_party_details if second_party_details != '[Second Party Address]' else ''}"
        paragraphs = [
            f"I, {first_party_name}, residing at {first_party_details}, do hereby solemnly declare and state as under:",
            f"1. That this declaration is made in respect of: {subject_purpose}.",
            f"2. STATEMENT OF FACTS:\n{key_terms}",
            "3. I hereby certify that the particulars furnished above are true and correct to the best of my knowledge and belief.",
            "4. I understand that any false statement or willful misrepresentation may subject me to appropriate administrative or legal action under applicable laws."
        ]
        signoff = (
            f"Declared and signed on this {doc_date_str} at {city}.\n\n"
            f"___________________________\n"
            f"({first_party_name})\n"
            f"Declarant\n"
            f"Contact: {first_party_details}"
        )

    else:
        # Generic / General Legal Notice
        header = "STATUTORY LEGAL NOTICE"
        subject = f"SUBJECT: LEGAL NOTICE OF DEMAND CONCERNING {subject_purpose.upper()}"
        sender_block = f"FROM:\n{first_party_name}\n{first_party_details}"
        recipient_block = f"TO:\n{second_party_name}\n{second_party_details}"
        paragraphs = [
            f"1. That under instructions from and on behalf of my client/principal, {first_party_name}, having address at {first_party_details}, I address this formal legal notice to you.",
            f"2. That you, the Addressee, {second_party_name}, {second_party_details}, had entered into legal obligations concerning: {subject_purpose}.",
            f"3. STATEMENT OF GRIEVANCE & BREACH:\n{key_terms}",
            f"4. That on account of your breach and failure, there is an outstanding legal liability and demand of {amount_formatted} due to my client.",
            f"5. DEMAND: You are hereby called upon and demanded to remedy the breach and pay the said sum of {amount_formatted} within a period of {duration_period or '15 Days'} from the receipt of this notice.",
            f"6. Take notice that failing compliance within the stipulated period, my client shall initiate appropriate civil, commercial, or criminal proceedings before competent courts at {city} at your risk and consequences."
        ]
        signoff = (
            f"Yours faithfully,\n\n"
            f"___________________________\n"
            f"{first_party_name}\n"
            f"Date: {doc_date_str}\n"
            f"Place: {city}"
        )

    full_text = f"{header}\n\nDate: {doc_date_str}\n\n{recipient_block}\n\n{subject}\n\n" + "\n\n".join(paragraphs) + f"\n\n{signoff}"

    return {
        'header': header,
        'notice_date': doc_date_str,
        'city': city,
        'sender_block': sender_block,
        'recipient_block': recipient_block,
        'subject': subject,
        'paragraphs': paragraphs,
        'signoff': signoff,
        'full_text': full_text,
        'amount_formatted': amount_formatted,
        'title': template.title if template else header,
    }
