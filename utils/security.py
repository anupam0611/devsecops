"""
Security utilities for the e-commerce application.

This module provides security-related functions for the application,
including password validation, file upload security, and event logging.
"""

import os
import hashlib
import re
from datetime import datetime
from functools import wraps
from typing import Callable, Optional
from flask import request, current_app, session, redirect, url_for, flash
from werkzeug.utils import secure_filename


def validate_password(password: str) -> bool:
    """Validate password strength.

    Args:
        password (str): The password to validate.

    Returns:
        bool: True if password meets requirements, False otherwise.
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


def allowed_file(filename: str) -> bool:
    """Check if a file has an allowed extension.

    Args:
        filename (str): The name of the file to check.

    Returns:
        bool: True if file extension is allowed, False otherwise.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )


def secure_filename_with_hash(filename: str) -> str:
    """Generate a secure filename with a hash to prevent collisions.

    Args:
        filename (str): The original filename.

    Returns:
        str: A secure filename with a hash.
    """
    if not filename:
        return ""
    # Get the file extension
    ext = os.path.splitext(filename)[1]
    # Generate a hash of the original filename
    hash_value = hashlib.md5(filename.encode()).hexdigest()[:8]
    # Combine the hash with the original filename
    secure_name = secure_filename(filename)
    name_without_ext = os.path.splitext(secure_name)[0]
    return f"{name_without_ext}_{hash_value}{ext}"


def log_security_event(event_type: str, message: str, user_id: Optional[int] = None) -> None:
    """Log a security-related event.

    Args:
        event_type (str): The type of security event.
        message (str): The event message.
        user_id (Optional[int]): The ID of the user involved, if any.
    """
    timestamp = datetime.utcnow().isoformat()
    log_message = f"[{timestamp}] {event_type}: {message}"
    if user_id:
        log_message += f" (User ID: {user_id})"
    current_app.logger.info(log_message)


def require_https(f: Callable) -> Callable:
    """Decorator to require HTTPS for a route.

    Args:
        f (Callable): The route function to decorate.

    Returns:
        Callable: The decorated function.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not current_app.debug:
            return redirect(request.url.replace("http://", "https://"))
        return f(*args, **kwargs)

    return decorated_function


def validate_csrf_token(f: Callable) -> Callable:
    """Decorator to validate CSRF token for a route.

    Args:
        f (Callable): The route function to decorate.

    Returns:
        Callable: The decorated function.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = request.form.get("csrf_token")
            if not token or token != session.get("csrf_token"):
                flash("Invalid CSRF token.", "error")
                return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS attacks.

    Args:
        text (str): The text to sanitize.

    Returns:
        str: The sanitized text.
    """
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Escape special characters
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")
    return text
