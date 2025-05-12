from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from models import db, User, Product, Order, OrderItem
from config import Config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS
from utils.security import (
    validate_password, allowed_file, secure_filename_with_hash,
    log_security_event, require_https, validate_csrf_token, sanitize_input
)
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize security extensions
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize Talisman for security headers
Talisman(app, 
    force_https=True,
    strict_transport_security=True,
    session_cookie_secure=True,
    content_security_policy=app.config['SECURITY_HEADERS']['Content-Security-Policy']
)

# Initialize CORS
CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})

# Set up logging
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('E-commerce startup')

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes with security measures
@app.route('/')
def home():
    products = Product.query.all()
    return render_template('home.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email'))
        password = request.form.get('password')
        name = sanitize_input(request.form.get('name'))
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message)
            log_security_event('password_validation_failed', message)
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            log_security_event('registration_attempt', 'Email already exists')
            return redirect(url_for('register'))
        
        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        log_security_event('user_registered', 'New user registration', user.id)
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email'))
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            log_security_event('user_login', 'Successful login', user.id)
            return redirect(url_for('home'))
        
        log_security_event('login_failed', f'Failed login attempt for email: {email}')
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    log_security_event('user_logout', 'User logged out', current_user.id)
    logout_user()
    return redirect(url_for('home'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/cart')
@login_required
@require_https
def cart():
    return render_template('cart.html')

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
@require_https
@validate_csrf_token
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > product.stock:
        flash('Not enough stock available')
        return redirect(url_for('product_detail', product_id=product_id))
    
    # Add to cart logic here (using session or database)
    flash('Product added to cart')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
@require_https
@validate_csrf_token
def checkout():
    if request.method == 'POST':
        # Process order logic here
        flash('Order placed successfully')
        return redirect(url_for('order_confirmation'))
    return render_template('checkout.html')

@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
@require_https
def admin_products():
    if not current_user.is_admin:
        log_security_event('unauthorized_access', 'Attempted admin access', current_user.id)
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = sanitize_input(request.form.get('name'))
        description = sanitize_input(request.form.get('description'))
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        category = sanitize_input(request.form.get('category'))
        
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category
        )
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename_with_hash(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image_url = filename
        
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully')
        
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 