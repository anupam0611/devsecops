"""
Main application module for the e-commerce platform.

This module initializes and configures the Flask application with all necessary
extensions and security features. It also defines all the routes and their handlers.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from decimal import Decimal

# Third-party imports
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, Blueprint, current_app
)
from flask_login import LoginManager, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_session import Session

# Local imports
from auth import auth as auth_blueprint
from models import db, User, Product, Order, OrderItem
from config import Config

# Initialize Flask extensions
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
cors = CORS()
csrf = CSRFProtect()

# Create main blueprint
main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    """
    Load a user from the database by ID.
    
    Args:
        user_id (int): The user's ID
        
    Returns:
        User: The user object if found, None otherwise
    """
    return User.query.get(int(user_id))

def get_cart():
    """
    Get the current user's shopping cart from the session.
    
    Returns:
        dict: The shopping cart dictionary
    """
    return session.get('cart', {})

def save_cart(cart_data):
    """
    Save the shopping cart to the session.
    
    Args:
        cart_data (dict): The shopping cart dictionary to save
    """
    session['cart'] = cart_data

@main.route('/')
def index():
    """Render the home page with featured products."""
    featured_products = Product.query.filter_by(stock__gt=0).limit(8).all()
    return render_template('index.html', products=featured_products)

@main.route('/products')
def products():
    """Render the products page with all available products."""
    available_products = Product.query.filter_by(stock__gt=0).all()
    return render_template('products.html', products=available_products)

@main.route('/product/<int:product_id>')
def product_detail(product_id):
    """
    Render the product detail page.
    
    Args:
        product_id (int): The ID of the product to display
    """
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@main.route('/cart')
def cart():
    """Render the shopping cart page."""
    cart_data = get_cart()
    cart_items = []
    total = Decimal('0.00')
    
    for product_id, quantity in cart_data.items():
        product = Product.query.get(product_id)
        if product and product.stock >= quantity:
            cart_items.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })
            total += Decimal(str(product.price * quantity))
    
    return render_template('cart.html', products=cart_items, total=total)

@main.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """
    Add a product to the shopping cart.
    
    Args:
        product_id (int): The ID of the product to add
    """
    try:
        quantity = int(request.form.get('quantity', 1))
        if quantity < 1:
            flash('Invalid quantity', 'error')
            return redirect(url_for('main.product_detail', product_id=product_id))
        
        product = Product.query.get_or_404(product_id)
        if product.stock < quantity:
            flash('Not enough stock available', 'error')
            return redirect(url_for('main.product_detail', product_id=product_id))
        
        cart_data = get_cart()
        cart_data[product_id] = cart_data.get(product_id, 0) + quantity
        save_cart(cart_data)
        
        flash('Product added to cart', 'success')
    except (ValueError, KeyError) as e:
        current_app.logger.error('Error adding to cart: %s', str(e))
        flash('Error adding product to cart', 'error')
    
    return redirect(url_for('main.cart'))

@main.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart(product_id):
    """
    Update the quantity of a product in the cart.
    
    Args:
        product_id (int): The ID of the product to update
    """
    try:
        quantity = int(request.form.get('quantity', 0))
        if quantity < 0:
            flash('Invalid quantity', 'error')
            return redirect(url_for('main.cart'))
        
        cart_data = get_cart()
        if quantity == 0:
            cart_data.pop(product_id, None)
        else:
            product = Product.query.get_or_404(product_id)
            if product.stock < quantity:
                flash('Not enough stock available', 'error')
                return redirect(url_for('main.cart'))
            cart_data[product_id] = quantity
        
        save_cart(cart_data)
        flash('Cart updated', 'success')
    except (ValueError, KeyError) as e:
        current_app.logger.error('Error updating cart: %s', str(e))
        flash('Error updating cart', 'error')
    
    return redirect(url_for('main.cart'))

@main.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    """
    Remove a product from the cart.
    
    Args:
        product_id (int): The ID of the product to remove
    """
    try:
        cart_data = get_cart()
        cart_data.pop(product_id, None)
        save_cart(cart_data)
        flash('Product removed from cart', 'success')
    except KeyError as e:
        current_app.logger.error('Error removing from cart: %s', str(e))
        flash('Error removing product from cart', 'error')
    
    return redirect(url_for('main.cart'))

@main.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Handle the checkout process."""
    if request.method == 'POST':
        try:
            cart_data = get_cart()
            if not cart_data:
                flash('Your cart is empty', 'error')
                return redirect(url_for('main.cart'))
            
            # Create order
            order = Order(user_id=current_user.id)
            db.session.add(order)
            
            # Create order items
            for product_id, quantity in cart_data.items():
                product = Product.query.get_or_404(product_id)
                if product.stock < quantity:
                    flash(f'Not enough stock for {product.name}', 'error')
                    return redirect(url_for('main.cart'))
                
                order_item = OrderItem(
                    order=order,
                    product_id=product_id,
                    quantity=quantity,
                    price=product.price
                )
                db.session.add(order_item)
                product.stock -= quantity
            
            db.session.commit()
            save_cart({})  # Clear cart
            flash('Order placed successfully', 'success')
            return redirect(url_for('main.order_confirmation', order_id=order.id))
            
        except (ValueError, KeyError) as e:
            db.session.rollback()
            current_app.logger.error('Error during checkout: %s', str(e))
            flash('Error processing your order', 'error')
            return redirect(url_for('main.cart'))
    
    return render_template('checkout.html')

@main.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """
    Display the order confirmation page.
    
    Args:
        order_id (int): The ID of the order to display
    """
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('order_confirmation.html', order=order)

@main.route('/orders')
@login_required
def orders():
    """Display the user's order history."""
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(
        Order.date_ordered.desc()
    ).all()
    return render_template('orders.html', orders=user_orders)

@main.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """
    Display the details of a specific order.
    
    Args:
        order_id (int): The ID of the order to display
    """
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('order_detail.html', order=order)

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application instance
    """
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    # Initialize extensions
    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    limiter.init_app(flask_app)
    talisman.init_app(flask_app)
    cors.init_app(flask_app)
    csrf.init_app(flask_app)
    Session(flask_app)

    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/ecommerce.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    flask_app.logger.addHandler(file_handler)
    flask_app.logger.setLevel(logging.INFO)
    flask_app.logger.info('E-commerce startup')

    # Register blueprints
    flask_app.register_blueprint(main)
    flask_app.register_blueprint(auth_blueprint)

    return flask_app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 