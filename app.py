"""
Main application module.

This module initializes the Flask application and its extensions,
registers blueprints, and configures the application.
"""

# Standard library imports
from typing import Any

# Third-party imports
from flask import Flask, render_template
from flask_login import LoginManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

# Local imports
from app_config import Config
from models import User, db
from auth import auth as auth_blueprint
from routes import main as main_blueprint

# Initialize extensions
login_manager = LoginManager()
session = Session()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id: int) -> User:
    """Load a user from the database by ID.

    Args:
        user_id: The ID of the user to load.

    Returns:
        User: The loaded user object.
    """
    return User.query.get(int(user_id))


def create_app(config_class: Any = Config) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_class: The configuration class to use.

    Returns:
        Flask: The configured Flask application.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure the app
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    session.init_app(app)
    cors.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Configure login manager
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Register blueprints
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)

    # Define routes
    @app.route("/")
    def index():
        """Render the index page."""
        return render_template("index.html")

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)
