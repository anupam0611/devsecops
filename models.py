"""
Database models for the e-commerce application.

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
        orders (list): List of orders made by the user
    """
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    orders = db.relationship('Order', backref='user', lazy=True)

    def __repr__(self):
        """Return a string representation of the user."""
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

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
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def __repr__(self):
        """Return a string representation of the product."""
        return f'<Product {self.name}>'

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_ordered = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        """Return a string representation of the order."""
        return f'<Order {self.id}>'

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
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        """Return a string representation of the order item."""
        return f'<OrderItem {self.id}>' 