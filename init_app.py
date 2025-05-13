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
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_session import Session

from config import Config

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
cors = CORS()
csrf = CSRFProtect()

def create_app(config_class=Config):
    """
    Create and configure the Flask application.
    
    Args:
        config_class: The configuration class to use
        
    Returns:
        Flask: The configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    talisman.init_app(app)
    cors.init_app(app)
    csrf.init_app(app)
    Session(app)

    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application startup')

    # Register blueprints
    from routes import main as main_blueprint
    from auth import auth as auth_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

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