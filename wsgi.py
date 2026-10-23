"""
Production WSGI Entrypoint for NyayVeya Online Legal Drafting Platform.

Usage:
  Linux / Cloud (Render, DigitalOcean, Railway, AWS):
    gunicorn wsgi:app --workers 2 --bind 0.0.0.0:5000

  Windows Server:
    waitress-serve --port=5000 wsgi:app
"""
import os
from app import create_app

# Default to production environment if not explicitly set
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

app = create_app()

if __name__ == '__main__':
    app.run()
