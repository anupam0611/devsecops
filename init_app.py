"""
Application initialization module.

This module handles the initialization and configuration of Flask extensions
and the application factory pattern.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# Third-party imports
from flask import Flask
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session

# Local imports
from config import Config
from models import User, Product
from routes import main as main_blueprint
from auth import auth as auth_blueprint

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
cors = CORS()
csrf = CSRFProtect()
session = Session()

@login_manager.user_loader
def load_user(user_id):
    """
    Load a user from the database by ID.
    
    Args:
        user_id (int): The user's ID
        
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
        Flask: The configured Flask application instance
    """
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    limiter.init_app(flask_app)
    talisman.init_app(flask_app)
    cors.init_app(flask_app)
    csrf.init_app(flask_app)
    session.init_app(flask_app)

    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/ecommerce.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    flask_app.logger.addHandler(file_handler)
    flask_app.logger.setLevel(logging.INFO)
    flask_app.logger.info('E-commerce startup')

    # Register blueprints
    flask_app.register_blueprint(main_blueprint)
    flask_app.register_blueprint(auth_blueprint)

    return flask_app

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