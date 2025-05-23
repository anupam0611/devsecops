from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_mail import Mail
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
session = Session()
cors = CORS()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()

#test