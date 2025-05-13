"""
Route handlers for the e-commerce application.

This module contains all the route handlers for the application,
including product display, cart management, and order processing.
"""

# Standard library imports
from typing import Optional

# Third-party imports
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app
)
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

# Local imports
from models import Product, Order, OrderItem
from utils.cart import (
    get_cart_items, add_to_cart, update_cart_item,
    remove_from_cart, clear_cart
)
from utils.security import (
    validate_csrf_token, require_https, log_security_event
)

# Create main blueprint
main = Blueprint('main', __name__)

@main.route('/')
def index() -> str:
    """Display the home page with featured products."""
    products = Product.query.filter_by(featured=True).all()
    return render_template('index.html', products=products)

@main.route('/product/<int:product_id>')
def product_detail(product_id: int) -> str:
    """Display detailed information about a specific product."""
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@main.route('/cart')
@login_required
def cart() -> str:
    """Display the user's shopping cart."""
    cart_items = get_cart_items()
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@main.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
@validate_csrf_token
def add_to_cart_route(product_id: int) -> str:
    """Add a product to the user's shopping cart."""
    try:
        product = Product.query.get_or_404(product_id)
        quantity = int(request.form.get('quantity', 1))
        
        if quantity <= 0:
            flash('Invalid quantity.', 'error')
            return redirect(url_for('main.product_detail', product_id=product_id))
        
        if add_to_cart(product, quantity):
            flash('Product added to cart.', 'success')
        else:
            flash('Failed to add product to cart.', 'error')
        
        return redirect(url_for('main.cart'))
    except ValueError:
        flash('Invalid quantity format.', 'error')
        return redirect(url_for('main.product_detail', product_id=product_id))
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error adding to cart: {str(e)}')
        flash('An error occurred while adding to cart.', 'error')
        return redirect(url_for('main.index'))

@main.route('/update_cart/<int:product_id>', methods=['POST'])
@login_required
@validate_csrf_token
def update_cart_route(product_id: int) -> str:
    """Update the quantity of a product in the cart."""
    try:
        quantity = int(request.form.get('quantity', 0))
        
        if quantity <= 0:
            if remove_from_cart(product_id):
                flash('Product removed from cart.', 'success')
            else:
                flash('Failed to remove product from cart.', 'error')
        else:
            if update_cart_item(product_id, quantity):
                flash('Cart updated.', 'success')
            else:
                flash('Failed to update cart.', 'error')
        
        return redirect(url_for('main.cart'))
    except ValueError:
        flash('Invalid quantity format.', 'error')
        return redirect(url_for('main.cart'))
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error updating cart: {str(e)}')
        flash('An error occurred while updating cart.', 'error')
        return redirect(url_for('main.index'))

@main.route('/remove_from_cart/<int:product_id>', methods=['POST'])
@login_required
@validate_csrf_token
def remove_from_cart_route(product_id: int) -> str:
    """Remove a product from the cart."""
    try:
        if remove_from_cart(product_id):
            flash('Product removed from cart.', 'success')
        else:
            flash('Failed to remove product from cart.', 'error')
        
        return redirect(url_for('main.cart'))
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error removing from cart: {str(e)}')
        flash('An error occurred while removing from cart.', 'error')
        return redirect(url_for('main.index'))

@main.route('/checkout', methods=['GET', 'POST'])
@login_required
@require_https
@validate_csrf_token
def checkout() -> str:
    """Handle the checkout process."""
    if request.method == 'POST':
        try:
            cart_items = get_cart_items()
            if not cart_items:
                flash('Your cart is empty.', 'error')
                return redirect(url_for('main.cart'))
            
            # Create order
            order = Order(
                user_id=current_user.id,
                total=sum(item['price'] * item['quantity'] for item in cart_items)
            )
            current_app.db.session.add(order)
            
            # Add order items
            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['id'],
                    quantity=item['quantity'],
                    price=item['price']
                )
                current_app.db.session.add(order_item)
            
            current_app.db.session.commit()
            clear_cart()
            
            log_security_event(
                'order_placed',
                f'Order {order.id} placed successfully',
                current_user.id
            )
            flash('Order placed successfully!', 'success')
            return redirect(url_for('main.order_confirmation', order_id=order.id))
            
        except SQLAlchemyError as e:
            current_app.db.session.rollback()
            current_app.logger.error(f'Database error during checkout: {str(e)}')
            log_security_event('checkout_error', f'Database error: {str(e)}', current_user.id)
            flash('An error occurred during checkout. Please try again.', 'error')
            return redirect(url_for('main.cart'))
    
    return render_template('checkout.html', cart_items=get_cart_items())

@main.route('/order_confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id: int) -> str:
    """Display order confirmation details."""
    try:
        order = Order.query.get_or_404(order_id)
        if order.user_id != current_user.id:
            log_security_event(
                'unauthorized_access',
                f'Attempted access to order {order_id}',
                current_user.id
            )
            flash('Access denied.', 'error')
            return redirect(url_for('main.index'))
        return render_template('order_confirmation.html', order=order)
    except SQLAlchemyError as e:
        current_app.logger.error(f'Database error accessing order: {str(e)}')
        flash('An error occurred while accessing order details.', 'error')
        return redirect(url_for('main.index')) 