import os
from flask import Flask
from extensions import db, migrate, login_manager, session, cors, limiter, mail
from routes import main as main_blueprint
from auth import auth as auth_blueprint
from models import User, Product


def create_app():
    app = Flask(__name__)
    app.config.from_object("app_config.BaseConfig")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    session.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register Blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app


def init_db():
    app = create_app()

    with app.app_context():
        db.create_all()

        # Seed default admin user
        if not User.query.filter_by(email="admin@example.com").first():
            admin = User(username="admin", email="admin@example.com")
            admin.set_password("admin123")
            admin.is_admin = True  # only if this attribute exists
            db.session.add(admin)

        # Seed sample product
        if not Product.query.filter_by(name="Sample Product").first():
            sample_product = Product(
                name="Sample Product",
                description="This is a sample product.",
                price=9.99,
                stock=100,
                featured=True,
            )
            db.session.add(sample_product)

        db.session.commit()


if __name__ == "__main__":
    init_db()
