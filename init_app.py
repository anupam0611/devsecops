"""
Application initialization module.

This module handles the initialization and configuration of the Flask application,
including database setup, extension initialization, and blueprint registration.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_migrate import Migrate
from flask_session import Session

from config import Config
from models import db, User, Product
from routes import main as main_blueprint
from auth import auth as auth_blueprint

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    """
    Load a user from the database by ID.
    
    Args:
        user_id: The ID of the user to load
        
    Returns:
        User: The user object if found, None otherwise
    """
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    """
    Create and configure the Flask application.
    
    Args:
        config_class: The configuration class to use
        
    Returns:
        Flask: The configured Flask application
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    talisman.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Configure session
    Session(app)
    
    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
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