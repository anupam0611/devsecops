"""
Application initialization module.

This module handles the creation and configuration of the Flask application,
including database setup, authentication, and blueprint registration.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from routes import main as main_blueprint
from auth import auth as auth_blueprint
from models import User, Product

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application instance
    """
    flask_app = Flask(__name__)
    flask_app.config['SECRET_KEY'] = 'your-secret-key'
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    migrate.init_app(flask_app, db)

    login_manager.login_view = 'auth.login'

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