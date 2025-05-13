"""
Security utility functions for the e-commerce application.

This module provides various security-related functions including:
- Password validation
- File upload security
- Security event logging
- HTTPS enforcement
- CSRF protection
- Input sanitization
"""

import os
import hashlib
import functools
from datetime import datetime
from flask import request, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename as werkzeug_secure_filename

def validate_password(password):
    """
    Validate a password against security requirements.
    
    Args:
        password (str): The password to validate
        
    Returns:
        tuple: (bool, str) - (is_valid, message)
            - is_valid: True if password meets all requirements, False otherwise
            - message: Description of validation result or error message
    """
    if len(password) < 8:
        return False, 'Password must be at least 8 characters.'
    if not any(c.isdigit() for c in password):
        return False, 'Password must contain a number.'
    if not any(c.isupper() for c in password):
        return False, 'Password must contain an uppercase letter.'
    if not any(c.islower() for c in password):
        return False, 'Password must contain a lowercase letter.'
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        return False, 'Password must contain a special character.'
    return True, 'Password is valid.'

def allowed_file(filename):
    """
    Check if a file has an allowed extension.
    
    Args:
        filename (str): The name of the file to check
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def secure_filename_with_hash(filename):
    """
    Create a secure filename with a hash to prevent filename collisions.
    
    Args:
        filename (str): The original filename to secure
        
    Returns:
        str: A secure version of the filename with a hash
    """
    # Get the secure base filename
    secure_name = werkzeug_secure_filename(filename)
    
    # Generate a hash of the original filename
    name_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
    
    # Split the filename into name and extension
    name, ext = os.path.splitext(secure_name)
    
    # Combine the secure name, hash, and extension
    return f"{name}_{name_hash}{ext}"

def log_security_event(event_type, message, user_id=None):
    """
    Log security-related events for auditing and monitoring.
    
    Args:
        event_type (str): The type of security event (e.g., 'login', 'password_change')
        message (str): A description of the event
        user_id (int, optional): The ID of the user associated with the event
    """
    timestamp = datetime.utcnow().isoformat()
    log_message = f"[{timestamp}] SECURITY EVENT: {event_type} - {message}"
    if user_id:
        log_message += f" (user_id={user_id})"
    
    # Log to application logger
    current_app.logger.warning(log_message)
    
    # Also print to console for development
    if current_app.debug:
        print(log_message)

def require_https(f):
    """
    Decorator to ensure a route is only accessible via HTTPS.
    
    Args:
        f (function): The route function to decorate
        
    Returns:
        function: The decorated function that checks for HTTPS
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure and not current_app.debug:
            flash('HTTPS is required for security.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def validate_csrf_token(f):
    """
    Decorator to validate CSRF tokens for POST requests.
    
    Args:
        f (function): The route function to decorate
        
    Returns:
        function: The decorated function that validates CSRF tokens
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token')
            if not token or token != session.get('csrf_token'):
                flash('Invalid CSRF token.', 'error')
                return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def sanitize_input(value):
    """
    Sanitize user input to prevent XSS and other injection attacks.
    
    Args:
        value (str): The input value to sanitize
        
    Returns:
        str: The sanitized input value
    """
    if not isinstance(value, str):
        return value
    
    # Remove HTML tags
    value = value.replace('<', '&lt;').replace('>', '&gt;')
    
    # Remove control characters
    value = ''.join(char for char in value if ord(char) >= 32)
    
    # Strip whitespace
    return value.strip()
