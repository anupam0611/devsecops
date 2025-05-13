"""
Main application module for the e-commerce platform.

This module contains the main application logic, including routes for
product display, cart management, and order processing.
"""

from decimal import Decimal
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    jsonify, session, current_app
)
from flask_login import login_required, current_user

from models import db, Product, Order, OrderItem
from utils.cart import (
    get_cart, get_cart_items, add_to_cart, update_cart_item,
    remove_from_cart, clear_cart
)

# Create main blueprint
main = Blueprint('main', __name__)

def get_cart():
    """Get the current user's shopping cart from the session."""
    return session.get('cart', {})

def save_cart(cart_data):
    """Save the shopping cart to the session."""
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
    cart_items, total = get_cart_items()
    return render_template('cart.html', products=cart_items, total=total)

@main.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart_route(product_id):
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
        
        if add_to_cart(product_id, quantity):
            flash('Product added to cart', 'success')
        else:
            flash('Error adding product to cart', 'error')
    except (ValueError, KeyError) as e:
        current_app.logger.error('Error adding to cart: %s', str(e))
        flash('Error adding product to cart', 'error')
    
    return redirect(url_for('main.cart'))

@main.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
def update_cart_route(product_id):
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
        
        product = Product.query.get_or_404(product_id)
        if quantity > 0 and product.stock < quantity:
            flash('Not enough stock available', 'error')
            return redirect(url_for('main.cart'))
        
        if update_cart_item(product_id, quantity):
            flash('Cart updated', 'success')
        else:
            flash('Error updating cart', 'error')
    except (ValueError, KeyError) as e:
        current_app.logger.error('Error updating cart: %s', str(e))
        flash('Error updating cart', 'error')
    
    return redirect(url_for('main.cart'))

@main.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
def remove_from_cart_route(product_id):
    """
    Remove a product from the cart.
    
    Args:
        product_id (int): The ID of the product to remove
    """
    try:
        if remove_from_cart(product_id):
            flash('Product removed from cart', 'success')
        else:
            flash('Error removing product from cart', 'error')
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
            clear_cart()
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