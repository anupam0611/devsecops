"""
Main application module for the e-commerce platform.

This module initializes the Flask application and defines the main routes
for product display, cart management, and order processing.
"""

# Standard library imports
import os
from datetime import datetime

# Third-party imports
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Local imports
from config import Config
from models import User, Product, Order, OrderItem
from utils.security import (
    allowed_file, secure_filename_with_hash, validate_password,
    log_security_event
)

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
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    Session(app)
    
    # Register blueprints
    from auth import auth as auth_blueprint
    from routes import main as main_blueprint
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    
    # Initialize database
    with app.app_context():
        db.create_all()
    
    return app 