"""Database models for the e-commerce application.

This module defines the SQLAlchemy models for users, products, and orders.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    """
    User model representing registered users in the system.

    Attributes:
        id (int): Primary key
        username (str): Unique username
        email (str): Unique email address
        password_hash (str): Hashed password
        reset_token (str): Token for password reset
        reset_token_expiry (datetime): Expiry time for reset token
        orders (list): List of orders made by the user
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    reset_token = db.Column(db.String(100), unique=True)
    reset_token_expiry = db.Column(db.DateTime)
    orders = db.relationship("Order", backref="user", lazy=True)

    def __repr__(self):
        """Return a string representation of the user."""
        return f"<User {self.username}>"

    def set_password(self, password):
        """
        Set the user's password hash.

        Args:
            password (str): The plain text password to hash
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        """
        Check if the provided password matches the stored hash.

        Args:
            password (str): The plain text password to check

        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_active_orders(self):
        """
        Get all active orders for this user.

        Returns:
            list: List of active Order objects
        """
        return Order.query.filter_by(user_id=self.id, status="active").all()


class Product(db.Model):
    """
    Product model representing items available for purchase.

    Attributes:
        id (int): Primary key
        name (str): Product name
        description (str): Product description
        price (float): Product price
        stock (int): Available stock quantity
        order_items (list): List of order items containing this product
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    order_items = db.relationship("OrderItem", backref="product", lazy=True)

    def __repr__(self):
        """Return a string representation of the product."""
        return f"<Product {self.name}>"

    def update_stock(self, quantity):
        """
        Update the product's stock quantity.

        Args:
            quantity (int): The quantity to add (positive) or remove (negative)

        Returns:
            bool: True if update was successful, False if resulting stock would be negative
        """
        new_stock = self.stock + quantity
        if new_stock >= 0:
            self.stock = new_stock
            return True
        return False

    def is_in_stock(self):
        """
        Check if the product is currently in stock.

        Returns:
            bool: True if stock > 0, False otherwise
        """
        return self.stock > 0


class Order(db.Model):
    """
    Order model representing customer purchases.

    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User
        date_ordered (datetime): Order date and time
        status (str): Order status
        items (list): List of items in the order
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="pending")
    items = db.relationship("OrderItem", backref="order", lazy=True)

    def __repr__(self):
        """Return a string representation of the order."""
        return f"<Order {self.id}>"

    def get_total(self):
        """
        Calculate the total cost of the order.

        Returns:
            float: Total cost of all items in the order
        """
        return sum(item.price * item.quantity for item in self.items)

    def update_status(self, new_status):
        """
        Update the order status.

        Args:
            new_status (str): The new status to set

        Returns:
            bool: True if status was updated, False if invalid status
        """
        valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        if new_status in valid_statuses:
            self.status = new_status
            return True
        return False


class OrderItem(db.Model):
    """
    OrderItem model representing individual items within an order.

    Attributes:
        id (int): Primary key
        order_id (int): Foreign key to Order
        product_id (int): Foreign key to Product
        quantity (int): Quantity of the product ordered
        price (float): Price of the product at time of order
    """

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        """Return a string representation of the order item."""
        return f"<OrderItem {self.id}>"

    def get_subtotal(self):
        """
        Calculate the subtotal for this order item.

        Returns:
            float: Subtotal (price * quantity)
        """
        return self.price * self.quantity

    def update_quantity(self, new_quantity):
        """
        Update the quantity of this order item.

        Args:
            new_quantity (int): The new quantity to set

        Returns:
            bool: True if quantity was updated, False if invalid quantity

        Raises:
            ValueError: If new_quantity is less than or equal to zero
        """
        if new_quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        self.quantity = new_quantity
        return True
