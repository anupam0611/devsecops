"""
Main application module for the e-commerce platform.

This module initializes and configures the Flask application,
sets up extensions, and registers blueprints.
"""

# Standard library imports
import os

# Third-party imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Local imports
from config import Config
from routes import main

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

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
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main)
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app 