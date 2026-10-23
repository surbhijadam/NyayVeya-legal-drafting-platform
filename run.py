"""
Entry point for the Flask application.
Run with: python run.py
Or with: flask run (after setting FLASK_APP=run.py in .env)
"""
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    # Ensure database tables exist in development before starting server
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
