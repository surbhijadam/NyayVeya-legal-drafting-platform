from flask import Blueprint, render_template

# Create a blueprint named 'main'
# A blueprint groups related routes together
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Home page - the first page visitors see."""
    return render_template('home.html')
