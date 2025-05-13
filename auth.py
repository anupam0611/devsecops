"""
Authentication module for the e-commerce application.

This module handles user authentication, including login, registration,
password reset, and session management.
"""

# Standard library imports
from datetime import datetime, timedelta
import secrets
import string
from typing import Optional

# Third-party imports
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message

# Local imports
from models import User
from utils.security import (
    validate_password, log_security_event, require_https,
    validate_csrf_token
)

# Create auth blueprint
auth = Blueprint('auth', __name__)

def generate_reset_token(user: User) -> str:
    """Generate a password reset token for a user.
    
    Args:
        user (User): The user to generate a token for.
        
    Returns:
        str: The generated reset token.
    """
    token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    user.reset_token = token
    user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
    current_app.db.session.commit()
    return token

def verify_reset_token(token: str) -> Optional[User]:
    """Verify a password reset token and return the associated user.
    
    Args:
        token (str): The reset token to verify.
        
    Returns:
        Optional[User]: The user associated with the token if valid, None otherwise.
    """
    user = User.query.filter_by(reset_token=token).first()
    if user and user.reset_token_expiry and user.reset_token_expiry > datetime.utcnow():
        return user
    return None

def send_reset_email(email: str, token: str) -> None:
    """Send a password reset email to the user.
    
    Args:
        email (str): The recipient's email address.
        token (str): The reset token to include in the email.
    """
    reset_url = url_for('auth.reset_password_token', token=token, _external=True)
    msg = Message(
        'Password Reset Request',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[email]
    )
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, please ignore this email.
'''
    current_app.mail.send(msg)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            log_security_event('login_success', f'User {user.id} logged in', user.id)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            log_security_event('login_failed', f'Failed login attempt for {email}')
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if not validate_password(password):
            flash('Password does not meet security requirements.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        user = User(
            email=email,
            password_hash=generate_password_hash(password)
        )
        current_app.db.session.add(user)
        current_app.db.session.commit()
        
        log_security_event('registration', f'New user registered: {email}', user.id)
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    log_security_event('logout', f'User {current_user.id} logged out', current_user.id)
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    """Handle password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = generate_reset_token(user)
            # Send reset email
            send_reset_email(user.email, token)
            log_security_event('password_reset_request', f'Password reset requested for {email}')
            flash('Password reset instructions sent to your email.', 'success')
        else:
            # Don't reveal if email exists
            flash('If your email is registered, you will receive reset instructions.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html')

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    """Handle password reset with token."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    user = verify_reset_token(token)
    if not user:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.reset_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password_token.html')
        
        if not validate_password(password):
            flash('Password does not meet security requirements.', 'error')
            return render_template('reset_password_token.html')
        
        user.password_hash = generate_password_hash(password)
        current_app.db.session.commit()
        
        log_security_event('password_reset', f'Password reset for user {user.id}', user.id)
        flash('Your password has been reset. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password_token.html') 