from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from app import app, db
from models import User, Product

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'

    from routes import main as main_blueprint
    from auth import auth as auth_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app

def init_db():
    with app.app_context():
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