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
