"""
Guided WTForms for legal document generation.
"""
from datetime import date
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, IntegerField, DateField, SelectField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, ValidationError
)


class ChequeBounceNoticeForm(FlaskForm):
    """
    Guided input form for Section 138 Negotiable Instruments Act Legal Notice.
    Collects complainant, drawer, cheque, bank memo, and consideration details.
    """

    # --- Notice Dispatch Details ---
    notice_date = DateField('Notice Date', default=date.today, validators=[
        DataRequired(message='Please specify the date of this notice.')
    ])

    # --- Complainant / Payee (Sender) ---
    payee_name = StringField('Your Full Name (Payee / Complainant)', validators=[
        DataRequired(message='Please enter the payee / complainant name.'),
        Length(min=2, max=150, message='Name must be between 2 and 150 characters.')
    ])

    payee_address = TextAreaField('Your Full Postal Address', validators=[
        DataRequired(message='Please enter your complete postal address with PIN code.'),
        Length(min=5, max=500, message='Address must be between 5 and 500 characters.')
    ])

    payee_phone = StringField('Contact Phone Number', validators=[
        DataRequired(message='Please enter your phone number.'),
        Length(min=10, max=15, message='Phone number must be 10-15 digits.')
    ])

    # Advocate details (optional - user can issue in self name or advocate name)
    advocate_name = StringField('Advocate Name (Optional - leave blank if issuing personally)', validators=[
        Optional(),
        Length(max=150)
    ])

    advocate_address = TextAreaField('Advocate Office Address (Optional)', validators=[
        Optional(),
        Length(max=500)
    ])

    # --- Accused / Drawer (Recipient) ---
    drawer_name = StringField('Cheque Issuer Full Name (Drawer / Accused)', validators=[
        DataRequired(message='Please enter the cheque issuer full name.'),
        Length(min=2, max=150, message='Name must be between 2 and 150 characters.')
    ])

    drawer_address = TextAreaField('Cheque Issuer Complete Postal Address', validators=[
        DataRequired(message='Please enter the issuer address (must be valid for RPAD / Speed Post delivery).'),
        Length(min=5, max=500, message='Address must be between 5 and 500 characters.')
    ])

    # --- Cheque Particulars ---
    cheque_number = StringField('Cheque Number', validators=[
        DataRequired(message='Please enter the 6-digit cheque number.'),
        Length(min=4, max=20, message='Cheque number is typically 6 digits.')
    ])

    cheque_date = DateField('Cheque Date (as written on the cheque)', validators=[
        DataRequired(message='Please specify the date written on the cheque.')
    ])

    cheque_amount = IntegerField('Cheque Amount (in ₹)', validators=[
        DataRequired(message='Please enter the cheque amount in figures.'),
        NumberRange(min=1, message='Cheque amount must be greater than ₹0.')
    ])

    cheque_amount_words = StringField('Cheque Amount in Words (e.g. Rupees Fifty Thousand Only)', validators=[
        DataRequired(message='Please enter the amount in words.'),
        Length(min=5, max=200, message='Amount in words is required.')
    ])

    bank_name = StringField('Drawee Bank Name (Bank on which cheque was drawn)', validators=[
        DataRequired(message='Please enter the bank name (e.g. State Bank of India).'),
        Length(min=2, max=150)
    ])

    bank_branch = StringField('Drawee Branch & City', validators=[
        DataRequired(message='Please enter the bank branch name and city.'),
        Length(min=2, max=150)
    ])

    # --- Bank Dishonour Memo Details ---
    memo_date = DateField('Bank Return Memo Date', validators=[
        DataRequired(message='Please specify the date printed on the bank dishonour memo.')
    ])

    dishonour_reason = SelectField('Reason for Dishonour (as stated on memo)', choices=[
        ('Funds Insufficient', 'Funds Insufficient'),
        ('Exceeds Arrangement', 'Exceeds Arrangement'),
        ('Account Closed', 'Account Closed'),
        ('Payment Stopped by Drawer', 'Payment Stopped by Drawer'),
        ('Signature Differs / Incomplete', 'Signature Differs / Incomplete'),
        ('Refer to Drawer', 'Refer to Drawer'),
        ('Other', 'Other Statutory Reason')
    ], validators=[DataRequired()])

    # --- Consideration / Transaction Context ---
    transaction_details = TextAreaField('Legal Liability / Consideration Context', validators=[
        DataRequired(message='Please describe why the cheque was issued (e.g. loan repayment, invoice payment).'),
        Length(min=10, max=1000, message='Please provide at least 10 characters explaining the debt / transaction.')
    ])

    submit = SubmitField('Generate Notice Preview')

    def validate_memo_date(self, field):
        """Validate that memo date is not in the future."""
        if field.data and field.data > date.today():
            raise ValidationError('Bank memo date cannot be in the future.')

    def validate_cheque_date(self, field):
        """Validate that cheque date is not after memo date."""
        if field.data and self.memo_date.data and field.data > self.memo_date.data:
            raise ValidationError('Cheque date cannot be later than the bank dishonour memo date.')
