"""
WTForms form classes for authentication.

Flask-WTF provides:
- CSRF protection on all forms automatically
- Server-side validation before data reaches the database
- Clean error messages for the user
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, ValidationError
)
from app.models import User


class RegistrationForm(FlaskForm):
    """User registration form with validation."""

    full_name = StringField('Full Name', validators=[
        DataRequired(message='Please enter your full name.'),
        Length(min=2, max=150, message='Name must be between 2 and 150 characters.'),
    ])

    email = StringField('Email Address', validators=[
        DataRequired(message='Please enter your email address.'),
        Email(message='Please enter a valid email address.'),
        Length(max=254, message='Email address is too long.'),
    ])

    password = PasswordField('Password', validators=[
        DataRequired(message='Please choose a password.'),
        Length(min=8, max=128, message='Password must be at least 8 characters long.'),
    ])

    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords do not match.'),
    ])

    submit = SubmitField('Create Account')

    def validate_email(self, field):
        """Check that the email is not already registered."""
        existing_user = User.query.filter_by(email=field.data.lower().strip()).first()
        if existing_user:
            raise ValidationError(
                'An account with this email address already exists. '
                'Please log in instead.'
            )


class LoginForm(FlaskForm):
    """User login form."""

    email = StringField('Email Address', validators=[
        DataRequired(message='Please enter your email address.'),
        Email(message='Please enter a valid email address.'),
    ])

    password = PasswordField('Password', validators=[
        DataRequired(message='Please enter your password.'),
    ])

    remember_me = BooleanField('Remember Me')

    submit = SubmitField('Log In')
