"""
Legal notice template text formatting for Section 138 of Negotiable Instruments Act, 1881.
"""
from datetime import datetime, date


def format_cheque_bounce_notice(data):
    """
    Generate structured legal notice text based on validated user input.
    Returns a dictionary with structured sections and full text.
    """
    notice_date_str = (
        data['notice_date'].strftime('%d-%m-%Y')
        if isinstance(data.get('notice_date'), (date, datetime))
        else str(data.get('notice_date'))
    )
    cheque_date_str = (
        data['cheque_date'].strftime('%d-%m-%Y')
        if isinstance(data.get('cheque_date'), (date, datetime))
        else str(data.get('cheque_date'))
    )
    memo_date_str = (
        data['memo_date'].strftime('%d-%m-%Y')
        if isinstance(data.get('memo_date'), (date, datetime))
        else str(data.get('memo_date'))
    )

    amount_formatted = f"₹{int(data['cheque_amount']):,}"

    # Header section
    header = "REGISTERED POST WITH ACKNOWLEDGEMENT DUE (RPAD) / SPEED POST"

    # Sender (Payee or Advocate)
    sender_block = (
        f"FROM:\n"
        f"{data['advocate_name']}\nAdvocate\n{data['advocate_address']}\n(Under instructions of Client: {data['payee_name']})"
        if data.get('advocate_name')
        else f"FROM:\n{data['payee_name']}\n{data['payee_address']}\nPhone: {data['payee_phone']}"
    )

    recipient_block = (
        f"TO:\n"
        f"{data['drawer_name']}\n"
        f"{data['drawer_address']}"
    )

    subject = (
        "SUBJECT: LEGAL NOTICE OF DEMAND UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881 "
        f"FOR DISHONOUR OF CHEQUE BEARING NO. {data['cheque_number']} FOR {amount_formatted}."
    )

    paragraphs = [
        (
            f"1. That you, the Noticee/Addressee, approached my Client ({data['payee_name']}) "
            f"and entered into a transaction wherein in discharge of your legally enforceable debt and liability, "
            f"namely: {data['transaction_details']}."
        ),
        (
            f"2. That towards part/full discharge of the aforesaid legally enforceable debt and liability, "
            f"you issued and delivered Cheque bearing No. {data['cheque_number']}, dated {cheque_date_str}, "
            f"drawn for a sum of {amount_formatted} ({data['cheque_amount_words']}) "
            f"on {data['bank_name']}, {data['bank_branch']} in favour of my Client."
        ),
        (
            f"3. That at the time of issuing the aforesaid cheque, you specifically represented and assured "
            f"that the same was good for payment and would be promptly honoured upon presentation to your bankers."
        ),
        (
            f"4. That acting on your express representations and assurances, my Client presented the said cheque "
            f"for encashment within its period of statutory validity through banker. However, to the utter shock and "
            f"dismay of my Client, the said cheque was returned unpaid and dishonoured by your bank vide Return Memo "
            f"dated {memo_date_str} with the endorsement/reason: \"{data['dishonour_reason']}\"."
        ),
        (
            f"5. That your aforesaid conduct clearly demonstrates dishonest and fraudulent intention from the inception, "
            f"and you have failed to maintain sufficient balance in your bank account, thereby committing an offence "
            f"punishable under Section 138 of the Negotiable Instruments Act, 1881."
        ),
        (
            f"6. Now, therefore, through this statutory legal demand notice, you are hereby called upon and demanded "
            f"to make the full payment of the cheque amount of {amount_formatted} ({data['cheque_amount_words']}) "
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
        f"{data.get('advocate_name') or data['payee_name']}\n"
        f"{'Advocate for Complainant' if data.get('advocate_name') else 'Payee / Complainant'}\n"
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
