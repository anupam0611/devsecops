"""
Cart management utilities for the e-commerce application.

This module provides functions for managing the shopping cart,
including adding, updating, and removing items.
"""

from typing import Dict, List
from flask import session
from models import Product
from sqlalchemy.exc import SQLAlchemyError


def get_cart() -> Dict:
    """Get the current cart from the session.

    Returns:
        Dict: The current cart dictionary.
    """
    return session.get("cart", {})


def save_cart(cart: Dict) -> None:
    """Save the cart to the session.

    Args:
        cart (Dict): The cart dictionary to save.
    """
    session["cart"] = cart


def get_cart_items() -> List[Dict]:
    """Get all items in the cart with their details.

    Returns:
        List[Dict]: List of cart items with product details.
    """
    cart = get_cart()
    items = []

    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product:
            items.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "quantity": quantity,
                    "image": product.image,
                }
            )

    return items


def add_to_cart(product: Product, quantity: int) -> bool:
    """Add a product to the cart.

    Args:
        product (Product): The product to add.
        quantity (int): The quantity to add.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        cart = get_cart()
        product_id = str(product.id)

        if product_id in cart:
            cart[product_id] += quantity
        else:
            cart[product_id] = quantity

        save_cart(cart)
        return True
    except (SQLAlchemyError, ValueError, TypeError):
        session["cart"] = get_cart()  # Restore cart on error
        return False


def update_cart_item(product_id: int, quantity: int) -> bool:
    """Update the quantity of a product in the cart.

    Args:
        product_id (int): The ID of the product to update.
        quantity (int): The new quantity.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        cart = get_cart()
        product_id_str = str(product_id)

        if product_id_str in cart:
            cart[product_id_str] = quantity
            save_cart(cart)
            return True
        return False
    except (SQLAlchemyError, ValueError, TypeError):
        session["cart"] = get_cart()  # Restore cart on error
        return False


def remove_from_cart(product_id: int) -> bool:
    """Remove a product from the cart.

    Args:
        product_id (int): The ID of the product to remove.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        cart = get_cart()
        product_id_str = str(product_id)

        if product_id_str in cart:
            del cart[product_id_str]
            save_cart(cart)
            return True
        return False
    except (SQLAlchemyError, ValueError, TypeError):
        session["cart"] = get_cart()  # Restore cart on error
        return False


def clear_cart() -> None:
    """Clear all items from the cart."""
    save_cart({})


def get_cart_total() -> float:
    """Calculate the total cost of items in the cart.

    Returns:
        float: The total cost of all items in the cart.
    """
    items = get_cart_items()
    return sum(item["price"] * item["quantity"] for item in items)
