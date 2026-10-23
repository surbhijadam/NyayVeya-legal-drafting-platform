"""
Entry point for the Flask application.
Run with: python run.py
Or with: flask run (after setting FLASK_APP=run.py in .env)
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
