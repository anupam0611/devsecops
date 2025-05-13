"""
Cart management utilities for the e-commerce application.

This module provides functions for managing the shopping cart functionality,
including adding items, updating quantities, and calculating totals.
"""

# Standard library imports
from decimal import Decimal

# Third-party imports
from flask import session

# Local imports
from models import Product

def get_cart():
    """
    Get the current user's shopping cart from the session.
    
    Returns:
        dict: The cart data from the session, or an empty dict if none exists
    """
    return session.get('cart', {})

def save_cart(cart_data):
    """
    Save the shopping cart to the session.
    
    Args:
        cart_data (dict): The cart data to save
    """
    session['cart'] = cart_data

def get_cart_items():
    """
    Get the items in the cart with their details.
    
    Returns:
        list: A list of dictionaries containing cart item details
    """
    cart = get_cart()
    items = []
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product and product.stock > 0:
            items.append({
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                'quantity': quantity,
                'image': product.image
            })
    return items

def add_to_cart(product, quantity):
    """
    Add a product to the shopping cart.
    
    Args:
        product (Product): The product to add
        quantity (int): The quantity to add
        
    Returns:
        bool: True if successful, False otherwise
    """
    cart = get_cart()
    product_id = str(product.id)
    
    if product.stock < quantity:
        return False
    
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity
    
    save_cart(cart)
    return True

def update_cart_item(product_id, quantity):
    """
    Update the quantity of a product in the cart.
    
    Args:
        product_id (int): The ID of the product to update
        quantity (int): The new quantity
        
    Returns:
        bool: True if successful, False otherwise
    """
    cart = get_cart()
    product_id = str(product_id)
    
    if product_id not in cart:
        return False
    
    product = Product.query.get(product_id)
    if not product or product.stock < quantity:
        return False
    
    cart[product_id] = quantity
    save_cart(cart)
    return True

def remove_from_cart(product_id):
    """
    Remove a product from the cart.
    
    Args:
        product_id (int): The ID of the product to remove
        
    Returns:
        bool: True if successful, False otherwise
    """
    cart = get_cart()
    product_id = str(product_id)
    
    if product_id not in cart:
        return False
    
    del cart[product_id]
    save_cart(cart)
    return True

def clear_cart():
    """Clear all items from the cart."""
    save_cart({})

def get_cart_total():
    """
    Calculate the total cost of items in the cart.
    
    Returns:
        Decimal: The total cost
    """
    items = get_cart_items()
    return sum(Decimal(str(item['price'])) * item['quantity'] for item in items) 