"""
WTForms forms for NyayVeya Administration.
Provides CSRF validation, sanitization, and structured data handling.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    TextAreaField, SelectField, IntegerField
)
from wtforms.validators import (
    DataRequired, Email, Length, NumberRange, Optional, Regexp
)


class AdminLoginForm(FlaskForm):
    """Secure login form for administrator portal."""
    email = StringField('Admin Email Address', validators=[
        DataRequired(message='Please enter your administrator email.'),
        Email(message='Please provide a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password.')
    ])
    remember_me = BooleanField('Stay signed in for this device')
    submit = SubmitField('Sign In to Admin')


class TemplateForm(FlaskForm):
    """Form for creating and editing legal document templates."""
    slug = StringField('URL Slug', validators=[
        DataRequired(message='Slug is required for the document URL.'),
        Length(min=3, max=100, message='Slug must be between 3 and 100 characters.'),
        Regexp(r'^[a-z0-9-]+$', message='Slug must contain only lowercase letters, numbers, and hyphens.')
    ])
    title = StringField('Document Title', validators=[
        DataRequired(message='Document title is required.'),
        Length(max=200, message='Title cannot exceed 200 characters.')
    ])
    subtitle = StringField('Subtitle / Statutory Reference', validators=[
        Optional(),
        Length(max=300, message='Subtitle cannot exceed 300 characters.')
    ])
    category = SelectField('Category', choices=[
        ('notices', 'Legal Notices'),
        ('agreements', 'Agreements & Contracts'),
        ('affidavits', 'Affidavits & Declarations'),
        ('applications', 'Applications'),
        ('other', 'Other Documents')
    ], validators=[DataRequired(message='Please select a category.')])
    price = IntegerField('Price (in ₹ INR)', validators=[
        DataRequired(message='Price is required.'),
        NumberRange(min=0, max=100000, message='Price must be between ₹0 and ₹1,00,000.')
    ], default=199)
    status = SelectField('Publication Status', choices=[
        ('active', 'Active — Published & Available for Guided Generation'),
        ('coming_soon', 'Coming Soon — Preview In Catalogue Only'),
        ('draft', 'Draft — Hidden from Public Site')
    ], validators=[DataRequired()])
    language = SelectField('Language', choices=[
        ('English', 'English'),
        ('Hindi', 'Hindi'),
        ('Bilingual', 'Bilingual (English + Hindi)')
    ], default='English', validators=[DataRequired()])
    short_description = TextAreaField('Short Summary', validators=[
        DataRequired(message='Short description is required for catalogue cards.')
    ])
    long_description = TextAreaField('Full Statutory Description', validators=[
        DataRequired(message='Full statutory description is required.')
    ])
    icon = StringField('Icon Identifier', default='bi-file-earmark-medical', validators=[
        Optional(), Length(max=100)
    ])
    badge_text = StringField('Card Badge Text (e.g. Popular, Essential)', validators=[
        Optional(), Length(max=50)
    ])
    badge_class = SelectField('Badge Styling', choices=[
        ('bg-primary', 'Primary Navy'),
        ('bg-amber-600', 'Gold / Amber'),
        ('bg-emerald-600', 'Emerald Green'),
        ('bg-[#6F1D2C]', 'Crimson Accent'),
        ('bg-slate-700', 'Slate Grey')
    ], default='bg-primary')

    # Multi-item list fields (entered line by line)
    what_you_get = TextAreaField('What You Get (Enter each bullet point on a new line)')
    information_needed = TextAreaField('Information Needed (Enter each requirement on a new line)')
    important_notes = TextAreaField('Important Notes & Statutory Warnings (Enter each note on a new line)')
    faqs = TextAreaField('Frequently Asked Questions (Format: Question | Answer per line)')

    submit = SubmitField('Save Template')


class OrderStatusForm(FlaskForm):
    """Admin form for updating order status."""
    status = SelectField('Order Status', choices=[
        ('pending', 'Pending Payment'),
        ('paid', 'Paid (Verified)'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ], validators=[DataRequired()])
    notes = TextAreaField('Admin Audit Note', validators=[Optional()])
    submit = SubmitField('Update Order Status')


class SupportInquiryUpdateForm(FlaskForm):
    """Admin form for updating inquiry status and resolution notes."""
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved')
    ], validators=[DataRequired()])
    admin_notes = TextAreaField('Internal Administrator Notes', validators=[Optional()])
    submit = SubmitField('Save Resolution Notes')


class UserUpdateForm(FlaskForm):
    """Admin form to modify user privileges and status."""
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Name is required.'),
        Length(min=2, max=150)
    ])
    is_admin = BooleanField('Grant Administrator Privileges')
    is_active = BooleanField('Account Active (Uncheck to suspend login)')
    submit = SubmitField('Update User')
