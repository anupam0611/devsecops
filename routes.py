"""
Route handlers for the e-commerce application.

This module contains all the route handlers for the application,
including product display, cart management, and order processing.
Routes are organized into logical sections:
- Product display routes
- Cart management routes
- Order processing routes
"""

# Standard library imports
from typing import Union

# Third-party imports
from flask import (
    Flask,
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    Response,
)
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

# Local imports
from models import Product, Order, OrderItem
from utils.cart import (
    get_cart_items,
    add_to_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
)
from utils.security import (
    validate_csrf_token,
    require_https,
    log_security_event,
)

# Create the Flask app
app = Flask(__name__)

# Configure database URI
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///some_very_long_database_path.db"
)

# Create main blueprint
main = Blueprint("main", __name__)

# ============================================================================
# Product Display Routes
# ============================================================================


@main.route("/")
def index() -> str:
    """Display the home page with featured products.

    Returns:
        str: Rendered template for the home page with featured products.
    """
    products = Product.query.filter_by(featured=True).all()
    return render_template("index.html", products=products)


@main.route("/product/<int:product_id>")
def product_detail(product_id: int) -> str:
    """Display detailed information about a specific product.

    Args:
        product_id (int): The ID of the product to display.

    Returns:
        str: Rendered template for the product detail page.
    """
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)


# ============================================================================
# Cart Management Routes
# ============================================================================


@main.route("/cart")
@login_required
def cart() -> str:
    """Display the user's shopping cart.

    Returns:
        str: Rendered template for the cart page with cart items and total.
    """
    cart_items = get_cart_items()
    total = sum(item["price"] * item["quantity"] for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total)


@main.route("/add_to_cart/<int:product_id>", methods=["POST"])
@login_required
@validate_csrf_token
def add_to_cart_route(product_id: int) -> Response:
    """Add a product to the user's shopping cart.

    Args:
        product_id (int): The ID of the product to add to cart.

    Returns:
        Response: Redirect response to cart or product page.
    """
    try:
        product = Product.query.get_or_404(product_id)
        quantity = int(request.form.get("quantity", 1))

        if quantity <= 0:
            flash("Invalid quantity.", "error")
            return redirect(
                url_for("main.product_detail", product_id=product_id)
            )
        if add_to_cart(product, quantity):
            flash("Product added to cart.", "success")
        else:
            flash("Failed to add product to cart.", "error")

        return redirect(url_for("main.cart"))
    except ValueError:
        flash("Invalid quantity format.", "error")
        return redirect(url_for("main.product_detail", product_id=product_id))
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error adding to cart: {str(e)}")
        flash("An error occurred while adding to cart.", "error")
        return redirect(url_for("main.index"))


@main.route("/update_cart/<int:product_id>", methods=["POST"])
@login_required
@validate_csrf_token
def update_cart_route(product_id: int) -> Response:
    """Update the quantity of a product in the cart.

    Args:
        product_id (int): The ID of the product to update in cart.

    Returns:
        Response: Redirect response to cart page.
    """
    try:
        quantity = int(request.form.get("quantity", 0))

        if quantity <= 0:
            if remove_from_cart(product_id):
                flash("Product removed from cart.", "success")
            else:
                flash("Failed to remove product from cart.", "error")
        else:
            if update_cart_item(product_id, quantity):
                flash("Cart updated.", "success")
            else:
                flash("Failed to update cart.", "error")

        return redirect(url_for("main.cart"))
    except ValueError:
        flash("Invalid quantity format.", "error")
        return redirect(url_for("main.cart"))
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database error updating cart: {str(e)}")
        flash("An error occurred while updating cart.", "error")
        return redirect(url_for("main.index"))


@main.route("/remove_from_cart/<int:product_id>", methods=["POST"])
@login_required
@validate_csrf_token
def remove_from_cart_route(product_id: int) -> Response:
    """Remove a product from the cart.

    Args:
        product_id (int): The ID of the product to remove from cart.

    Returns:
        Response: Redirect response to cart page.
    """
    try:
        if remove_from_cart(product_id):
            flash("Product removed from cart.", "success")
        else:
            flash("Failed to remove product from cart.", "error")

        return redirect(url_for("main.cart"))
    except SQLAlchemyError as e:
        current_app.logger.error(
            f"Database error removing from cart: {str(e)}"
        )
        flash("An error occurred while removing from cart.", "error")
        return redirect(url_for("main.index"))

# ============================================================================
# Order Processing
# Routes
# ============================================================================

@main.route("/checkout", methods=["GET", "POST"])
@login_required
@require_https
@validate_csrf_token

def checkout() -> Union[str, Response]:
    """Handle the checkout process.

    Returns:
        Union[str, Response]: Rendered template for checkout page or redirect response.
    """
    if request.method == "POST":
        try:
            cart_items = get_cart_items()
            if not cart_items:
                flash("Your cart is empty.", "error")
                return redirect(url_for("main.cart"))

            # Create order
            order = Order(
                user_id=current_user.id,
                total = sum(
                    item["price"] * item["quantity"]
                    for item in cart_items
                ),

            )
            current_app.db.session.add(order)

            # Add order items
            for item in cart_items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item["id"],
                    quantity=item["quantity"],
                    price=item["price"],
                )
                current_app.db.session.add(order_item)

            current_app.db.session.commit()
            clear_cart()

            log_security_event(
                "order_placed",
                f"Order {order.id} placed successfully",
                current_user.id,
            )
            flash("Order placed successfully!", "success")
            return redirect(
                url_for(
                    "main.order_confirmation",
                    order_id=order.id,
                )
            )

        except SQLAlchemyError as e:
            current_app.db.session.rollback()
            current_app.logger.error(
                f"Database error during checkout: {str(e)}"
            )
            log_security_event(
                "checkout_error", f"Database error: {str(e)}", current_user.id
            )
            flash("An error occurred during checkout. Please try again.", "error")
            return redirect(url_for("main.cart"))

    else:
        # This part will only be reached if the request method is not POST
        return render_template("checkout.html", cart_items=get_cart_items())
