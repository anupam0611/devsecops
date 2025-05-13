import functools
from flask import request, redirect, url_for, flash
from werkzeug.utils import secure_filename as werkzeug_secure_filename

# Password validation stub
def validate_password(password):
    # Example: require at least 8 chars, one number, one uppercase
    if len(password) < 8:
        return False, 'Password must be at least 8 characters.'
    if not any(c.isdigit() for c in password):
        return False, 'Password must contain a number.'
    if not any(c.isupper() for c in password):
        return False, 'Password must contain an uppercase letter.'
    return True, 'Password is valid.'

# Allowed file extensions stub
def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Secure filename with hash stub
def secure_filename_with_hash(filename):
    # For now, just use werkzeug's secure_filename
    return werkzeug_secure_filename(filename)

# Log security event stub
def log_security_event(event_type, message, user_id=None):
    print(f"SECURITY EVENT: {event_type} - {message} (user_id={user_id})")

# Require HTTPS decorator stub
def require_https(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_secure:
            flash('HTTPS is required.')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# CSRF token validation decorator stub
def validate_csrf_token(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # In production, check CSRF token here
        return f(*args, **kwargs)
    return decorated_function

# Input sanitization stub
def sanitize_input(value):
    # For now, just strip whitespace
    if isinstance(value, str):
        return value.strip()
    return value 