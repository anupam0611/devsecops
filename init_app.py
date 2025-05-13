"""
Application initialization module.

This module handles the initialization of the Flask application,
including database setup, extension configuration, and blueprint registration.
"""

# Standard library imports
import os

# Third-party imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from werkzeug.security import generate_password_hash
from flask_session import Session

# Local imports
from app_config import Config
from models import User, Product
from routes import main as main_blueprint
from auth import auth as auth_blueprint

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
session = Session()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

@login_manager.user_loader
def load_user(user_id):
    """Load a user from the database by ID."""
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    """Create and configure the Flask application.

    Args:
        config_class: The configuration class to use.

    Returns:
        Flask: The configured Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    session.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize database
    with app.app_context():
        db.create_all()

        # Create admin user if it doesn't exist
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

    return app

def init_db():
    """
    Initialize the database with required tables and initial data.

    This function creates all database tables and populates them with
    initial data if they don't exist.
    """
    flask_app = create_app()
    with flask_app.app_context():
        # Create all database tables
        db.create_all()

        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                name='Admin User',
                is_admin=True
            )
            admin.set_password('Admin@123')  # Change this in production
            db.session.add(admin)

        # Add sample products if none exist
        if not Product.query.first():
            products = [
                Product(
                    name='Sample Product 1',
                    description='This is a sample product description',
                    price=99.99,
                    stock=100,
                    category='Electronics'
                ),
                Product(
                    name='Sample Product 2',
                    description='Another sample product description',
                    price=149.99,
                    stock=50,
                    category='Clothing'
                )
            ]
            db.session.add_all(products)

        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()

# Add a final newline at the end of the file
