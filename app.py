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
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from utils.security import (
    validate_password, allowed_file, secure_filename_with_hash,
    log_security_event, require_https, validate_csrf_token, sanitize_input
)
import logging
from logging.handlers import RotatingFileHandler
from decimal import Decimal
from datetime import timedelta

app = Flask(__name__)
app.config.from_object(Config)

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Initialize extensions
db.init_app(app)
Session(app)  # Initialize Flask-Session
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize security extensions
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Initialize Talisman for security headers
Talisman(app, 
    force_https=False,  # Set to True in production
    strict_transport_security=False,  # Set to True in production
    session_cookie_secure=False,  # Set to True in production
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

def get_cart():
    if 'cart' not in session:
        session['cart'] = {}
    if not isinstance(session['cart'], dict):
        session['cart'] = {}
    session.modified = True
    return session['cart']

def convert_to_rupees(amount):
    """Convert USD to INR (using approximate rate of 1 USD = 83 INR)"""
    return amount * Decimal('83.00')

def calculate_cart_totals(cart_items):
    try:
        subtotal = Decimal('0')
        for item in cart_items.values():
            price = Decimal(str(item['price']))  # Convert float to Decimal safely
            quantity = Decimal(str(item['quantity']))
            subtotal += price * quantity
        
        tax = subtotal * Decimal('0.18')  # 18% GST
        total = subtotal + tax
        return subtotal, tax, total
    except Exception as e:
        app.logger.error(f"Error calculating cart totals: {str(e)}")
        return Decimal('0'), Decimal('0'), Decimal('0')

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
def cart():
    try:
        cart = get_cart()
        if not cart:
            flash('Your cart is empty')
            return render_template('cart.html', cart_items=[], subtotal=0, tax=0, total=0)
            
        cart_items = []
        for product_id, item in cart.items():
            product = Product.query.get(product_id)
            if product:
                cart_items.append({
                    'id': product_id,
                    'product': product,
                    'quantity': item['quantity'],
                    'price': item['price']
                })
        
        if not cart_items:
            flash('Your cart is empty')
            return render_template('cart.html', cart_items=[], subtotal=0, tax=0, total=0)
            
        subtotal, tax, total = calculate_cart_totals(cart)
        return render_template('cart.html', cart_items=cart_items, subtotal=subtotal, tax=tax, total=total)
    except Exception as e:
        app.logger.error(f"Error viewing cart: {str(e)}")
        flash('Error loading cart')
        return render_template('cart.html', cart_items=[], subtotal=0, tax=0, total=0)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
@validate_csrf_token
def add_to_cart(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        quantity = int(request.form.get('quantity', 1))
        
        if quantity > product.stock:
            flash('Not enough stock available')
            return redirect(url_for('product_detail', product_id=product_id))
        
        cart = get_cart()
        if str(product_id) in cart:
            cart[str(product_id)]['quantity'] += quantity
        else:
            cart[str(product_id)] = {
                'quantity': quantity,
                'price': str(Decimal(str(product.price)))  # Store price as string representation of Decimal
            }
        session['cart'] = cart
        session.modified = True
        
        flash('Product added to cart')
        return redirect(url_for('cart'))
    except Exception as e:
        app.logger.error(f"Error adding to cart: {str(e)}")
        flash('Error adding product to cart')
        return redirect(url_for('product_detail', product_id=product_id))

@app.route('/update_cart/<int:item_id>', methods=['POST'])
@login_required
@validate_csrf_token
def update_cart(item_id):
    try:
        cart = get_cart()
        quantity = int(request.form.get('quantity', 1))
        product = Product.query.get_or_404(item_id)
        
        if str(item_id) not in cart:
            flash('Item not found in cart')
            return redirect(url_for('cart'))
            
        if quantity <= 0:
            del cart[str(item_id)]
            flash('Item removed from cart')
        elif quantity > product.stock:
            flash(f'Only {product.stock} items available in stock')
            # Reset to current quantity
            cart[str(item_id)]['quantity'] = cart[str(item_id)]['quantity']
        else:
            cart[str(item_id)]['quantity'] = quantity
            flash('Cart updated successfully')
        
        session['cart'] = cart
        session.modified = True
        return redirect(url_for('cart'))
    except ValueError:
        flash('Invalid quantity value')
        return redirect(url_for('cart'))
    except Exception as e:
        app.logger.error(f"Error updating cart: {str(e)}")
        flash('Error updating cart')
        return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
@validate_csrf_token
def remove_from_cart(item_id):
    try:
        cart = get_cart()
        if str(item_id) in cart:
            del cart[str(item_id)]
            session['cart'] = cart
            session.modified = True
            flash('Item removed from cart')
        else:
            flash('Item not found in cart')
        return redirect(url_for('cart'))
    except Exception as e:
        app.logger.error(f"Error removing item from cart: {str(e)}")
        flash('Error removing item from cart')
        return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
@require_https
@validate_csrf_token
def checkout():
    cart = get_cart()
    if not cart:
        flash('Your cart is empty')
        return redirect(url_for('cart'))
    
    cart_items = []
    for product_id, item in cart.items():
        product = Product.query.get(product_id)
        if product:
            cart_items.append({
                'id': product_id,
                'product': product,
                'quantity': item['quantity'],
                'price': item['price']
            })
    
    subtotal, tax, total = calculate_cart_totals(cart)
    
    if request.method == 'POST':
        # Process order logic here
        order = Order(user_id=current_user.id)
        db.session.add(order)
        
        for product_id, item in cart.items():
            product = Product.query.get(product_id)
            if product and product.stock >= item['quantity']:
                order_item = OrderItem(
                    order=order,
                    product_id=product_id,
                    quantity=item['quantity'],
                    price=item['price']
                )
                product.stock -= item['quantity']
                db.session.add(order_item)
            else:
                db.session.rollback()
                flash('Some items are no longer available')
                return redirect(url_for('cart'))
        
        db.session.commit()
        session.pop('cart', None)
        return redirect(url_for('order_confirmation', order_id=order.id))
    
    return render_template('checkout.html', cart_items=cart_items, subtotal=subtotal, tax=tax, total=total)

@app.route('/order/confirmation/<int:order_id>')
@login_required
@require_https
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    subtotal = sum(item.price * item.quantity for item in order.items)
    tax = subtotal * Decimal('0.18')  # 18% GST
    total = subtotal + tax
    
    return render_template('order_confirmation.html', 
                         order=order, 
                         subtotal=subtotal, 
                         tax=tax, 
                         total=total)

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

@app.route('/update_boss_speaker')
@login_required
def update_boss_speaker():
    # Update the product with ID 1 to be the BOSS speaker
    product = Product.query.get(1)
    if product:
        product.name = "BOSS Speaker"
        product.description = "Premium BOSS Bluetooth Speaker with exceptional sound quality and long battery life. Features include water resistance, deep bass, and 20-hour playback time."
        product.price = 199.99  # Price in USD
        product.stock = 50
        product.category = "Electronics"
        product.image_url = "boss_speaker.jpg"
        db.session.commit()
        flash('BOSS Speaker product updated successfully')
    else:
        flash('Product not found')
    return redirect(url_for('home'))

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 