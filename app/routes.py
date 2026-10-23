from flask import Blueprint, render_template, abort, request, flash, redirect, url_for

from app.catalogue import (
    get_all_documents,
    get_document_by_id,
    get_all_categories,
)

# Create a blueprint named 'main'
# A blueprint groups related routes together
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Home page - the first page visitors see."""
    documents = get_all_documents()
    return render_template('home.html', documents=documents)


@main_bp.route('/documents')
def document_list():
    """Browse all available legal documents by category."""
    categories = get_all_categories()
    return render_template('documents/list.html', categories=categories)


@main_bp.route('/documents/<string:doc_id>')
def document_detail(doc_id):
    """View details about a specific legal document."""
    document = get_document_by_id(doc_id)
    if document is None:
        abort(404)
    return render_template('documents/detail.html', document=document)


@main_bp.route('/about')
def about():
    """About page - information about the platform."""
    return render_template('about.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page - platform support and inquiries."""
    if request.method == 'POST':
        flash('Thank you for reaching out! We have received your message and will respond shortly.', 'success')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')


# --- Error Handlers ---

@main_bp.app_errorhandler(404)
def page_not_found(e):
    """Custom 404 error page."""
    return render_template('errors/404.html'), 404


@main_bp.app_errorhandler(500)
def internal_server_error(e):
    """Custom 500 error page."""
    return render_template('errors/500.html'), 500
