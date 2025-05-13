"""
Cart utility module for the e-commerce application.

This module provides functions for managing the shopping cart functionality.
"""

from flask import session
from decimal import Decimal
from models import Product

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

def get_cart_items():
    """
    Get the cart items with product details.
    
    Returns:
        tuple: (cart_items, total) where cart_items is a list of dicts containing
              product details and total is the Decimal sum of all items
    """
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
    
    return cart_items, total

def add_to_cart(product_id, quantity):
    """
    Add a product to the shopping cart.
    
    Args:
        product_id (int): The ID of the product to add
        quantity (int): The quantity to add
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cart_data = get_cart()
        cart_data[product_id] = cart_data.get(product_id, 0) + quantity
        save_cart(cart_data)
        return True
    except (ValueError, KeyError):
        return False

def update_cart_item(product_id, quantity):
    """
    Update the quantity of a product in the cart.
    
    Args:
        product_id (int): The ID of the product to update
        quantity (int): The new quantity
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cart_data = get_cart()
        if quantity == 0:
            cart_data.pop(product_id, None)
        else:
            cart_data[product_id] = quantity
        save_cart(cart_data)
        return True
    except (ValueError, KeyError):
        return False

def remove_from_cart(product_id):
    """
    Remove a product from the cart.
    
    Args:
        product_id (int): The ID of the product to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cart_data = get_cart()
        cart_data.pop(product_id, None)
        save_cart(cart_data)
        return True
    except KeyError:
        return False

def clear_cart():
    """Clear the shopping cart."""
    save_cart({}) 