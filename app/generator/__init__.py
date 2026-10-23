"""
Document Generator Package.
Handles guided forms, legal text templates, Word (.docx) generation, and PDF (.pdf) generation.
"""
from flask import Blueprint

generator_bp = Blueprint('generator', __name__, url_prefix='/generator')

from app.generator import routes
