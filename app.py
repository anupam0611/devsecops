"""
Main application module for the e-commerce platform.

This module initializes and configures the Flask application with all necessary
extensions and security features. It also defines all the routes and their handlers.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from decimal import Decimal
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_session import Session

from models import db, User, Product, Order, OrderItem
from config import Config
from utils.security import validate_password

# Initialize Flask extensions
login_manager = LoginManager()
limiter = Limiter(key_func=get_remote_address)
talisman = Talisman()
cors = CORS()
csrf = CSRFProtect()

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    talisman.init_app(app)
    cors.init_app(app)
    csrf.init_app(app)
    Session(app)

    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/ecommerce.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('E-commerce startup')

    # Register blueprints
    from routes import main as main_blueprint
    from auth import auth as auth_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint)

    return app

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

def save_cart(cart):
    """
    Save the shopping cart to the session.
    
    Args:
        cart (dict): The shopping cart dictionary to save
    """
    session['cart'] = cart

@app.route('/')
def index():
    """Render the home page with featured products."""
    products = Product.query.filter_by(stock__gt=0).limit(8).all()
    return render_template('index.html', products=products)

@app.route('/products')
def products():
    """Render the products page with all available products."""
    products = Product.query.filter_by(stock__gt=0).all()
    return render_template('products.html', products=products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """
    Render the product detail page.
    
    Args:
        product_id (int): The ID of the product to display
    """
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/cart')
def cart():
    """Render the shopping cart page."""
    cart = get_cart()
    products = []
    total = Decimal('0.00')
    
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product and product.stock >= quantity:
            products.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })
            total += Decimal(str(product.price * quantity))
    
    return render_template('cart.html', products=products, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
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
            return redirect(url_for('product_detail', product_id=product_id))
        
        product = Product.query.get_or_404(product_id)
        if product.stock < quantity:
            flash('Not enough stock available', 'error')
            return redirect(url_for('product_detail', product_id=product_id))
        
        cart = get_cart()
        cart[product_id] = cart.get(product_id, 0) + quantity
        save_cart(cart)
        
        flash('Product added to cart', 'success')
    except Exception as e:
        app.logger.error('Error adding to cart: %s', str(e))
        flash('Error adding product to cart', 'error')
    
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:product_id>', methods=['POST'])
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
            return redirect(url_for('cart'))
        
        cart = get_cart()
        if quantity == 0:
            cart.pop(product_id, None)
        else:
            product = Product.query.get_or_404(product_id)
            if product.stock < quantity:
                flash('Not enough stock available', 'error')
                return redirect(url_for('cart'))
            cart[product_id] = quantity
        
        save_cart(cart)
        flash('Cart updated', 'success')
    except Exception as e:
        app.logger.error('Error updating cart: %s', str(e))
        flash('Error updating cart', 'error')
    
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart(product_id):
    """
    Remove a product from the cart.
    
    Args:
        product_id (int): The ID of the product to remove
    """
    try:
        cart = get_cart()
        cart.pop(product_id, None)
        save_cart(cart)
        flash('Product removed from cart', 'success')
    except Exception as e:
        app.logger.error('Error removing from cart: %s', str(e))
        flash('Error removing product from cart', 'error')
    
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Handle the checkout process."""
    if request.method == 'POST':
        try:
            cart = get_cart()
            if not cart:
                flash('Your cart is empty', 'error')
                return redirect(url_for('cart'))
            
            # Create order
            order = Order(user_id=current_user.id)
            db.session.add(order)
            
            # Create order items
            for product_id, quantity in cart.items():
                product = Product.query.get_or_404(product_id)
                if product.stock < quantity:
                    flash(f'Not enough stock for {product.name}', 'error')
                    return redirect(url_for('cart'))
                
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
            return redirect(url_for('order_confirmation', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            app.logger.error('Error during checkout: %s', str(e))
            flash('Error processing your order', 'error')
            return redirect(url_for('cart'))
    
    return render_template('checkout.html')

@app.route('/order_confirmation/<int:order_id>')
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
        return redirect(url_for('index'))
    
    return render_template('order_confirmation.html', order=order)

@app.route('/orders')
@login_required
def orders():
    """Display the user's order history."""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_ordered.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/order/<int:order_id>')
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
        return redirect(url_for('index'))
    
    return render_template('order_detail.html', order=order)

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 