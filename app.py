"""
Main application module for the e-commerce platform.

This module initializes and configures the Flask application, sets up routes,
and handles various e-commerce functionality including product display,
cart management, and order processing.
"""

# Standard library imports
import os
from datetime import datetime

# Third-party imports
from flask import (
    Flask, render_template, request, redirect, url_for, flash, 
    session, Blueprint, current_app
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

# Local imports
from config import Config
from utils.security import (
    allowed_file, secure_filename_with_hash, validate_password,
    log_security_event, require_https, validate_csrf_token, sanitize_input
)

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Create main blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Display the home page with featured products."""
    products = Product.query.filter_by(featured=True).all()
    return render_template('index.html', products=products)

@main.route('/product/<int:product_id>')
def product_detail(product_id):
    """Display detailed information about a specific product."""
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@main.route('/cart')
@login_required
def cart():
    """Display the user's shopping cart."""
    cart_items = get_cart_items()
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@main.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
@validate_csrf_token
def add_to_cart(product_id):
    """Add a product to the user's shopping cart."""
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        flash('Invalid quantity.', 'error')
        return redirect(url_for('main.product_detail', product_id=product_id))
    
    add_to_cart(product, quantity)
    flash('Product added to cart.', 'success')
    return redirect(url_for('main.cart'))

@main.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
@validate_csrf_token
def update_cart(product_id):
    """Update the quantity of a product in the cart."""
    quantity = int(request.form.get('quantity', 0))
    
    if quantity <= 0:
        remove_from_cart(product_id)
    else:
        update_cart_item(product_id, quantity)
    
    flash('Cart updated.', 'success')
    return redirect(url_for('main.cart'))

@main.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
@validate_csrf_token
def remove_from_cart(product_id):
    """Remove a product from the cart."""
    remove_from_cart(product_id)
    flash('Product removed from cart.', 'success')
    return redirect(url_for('main.cart'))

@main.route('/checkout', methods=['GET', 'POST'])
@login_required
@require_https
@validate_csrf_token
def checkout():
    """Handle the checkout process."""
    if request.method == 'POST':
        # Process payment and create order
        try:
            # Create order
            order = Order(
                user_id=current_user.id,
                total=sum(item['price'] * item['quantity'] for item in get_cart_items())
            )
            db.session.add(order)
            
            # Add order items
            for item in get_cart_items():
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['id'],
                    quantity=item['quantity'],
                    price=item['price']
                )
                db.session.add(order_item)
            
            db.session.commit()
            clear_cart()
            
            flash('Order placed successfully!', 'success')
            return redirect(url_for('main.order_confirmation', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Checkout error: {str(e)}')
            flash('An error occurred during checkout. Please try again.', 'error')
            return redirect(url_for('main.cart'))
    
    return render_template('checkout.html', cart_items=get_cart_items())

@main.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Display order confirmation details."""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    return render_template('order_confirmation.html', order=order)

def create_app(config_class=Config):
    """Create and configure the Flask application."""
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