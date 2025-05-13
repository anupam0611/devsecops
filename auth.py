"""
Authentication module.

This module handles user authentication, including login, registration,
password reset, and account management.
"""

# Standard library imports
from typing import Union, Optional

# Third-party imports
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash, check_password_hash

# Local imports
from models import User
from utils.security import log_security_event

# Create auth blueprint
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, redirect]:
    """Handle user login.

    Returns:
        Union[str, redirect]: Rendered template or redirect response.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            log_security_event('login', f'User {user.id} logged in', user.id)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.index'))

        log_security_event('login_failed', f'Failed login attempt for {email}')
        flash('Invalid email or password.', 'error')

    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, redirect]:
    """Handle user registration.

    Returns:
        Union[str, redirect]: Rendered template or redirect response.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')

        try:
            user = User(email=email)
            user.set_password(password)
            current_app.db.session.add(user)
            current_app.db.session.commit()

            log_security_event(
                'registration',
                f'New user registered: {email}',
                user.id
            )
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except SQLAlchemyError as e:
            current_app.db.session.rollback()
            current_app.logger.error(
                f'Database error during registration: {str(e)}'
            )
            flash('An error occurred during registration.', 'error')

    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout() -> redirect:
    """Handle user logout.

    Returns:
        redirect: Redirect response to home page.
    """
    log_security_event(
        'logout',
        f'User {current_user.id} logged out',
        current_user.id
    )
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request() -> Union[str, redirect]:
    """Handle password reset request.

    Returns:
        Union[str, redirect]: Rendered template or redirect response.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            token = user.generate_reset_token()
            reset_url = url_for(
                'auth.reset_password',
                token=token,
                _external=True
            )

            try:
                current_app.mail.send_message(
                    'Password Reset Request',
                    recipients=[user.email],
                    body=f'To reset your password, visit the following link:\n{reset_url}'
                )
                log_security_event(
                    'password_reset_request',
                    f'Reset requested for {email}',
                    user.id
                )
                flash('Password reset instructions sent to your email.', 'info')
                return redirect(url_for('auth.login'))

            except Exception as e:
                current_app.logger.error(f'Error sending reset email: {str(e)}')
                flash('Error sending reset email. Please try again.', 'error')
        else:
            flash('Email not found.', 'error')

    return render_template('auth/reset_password_request.html')

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token: str) -> Union[str, redirect]:
    """Handle password reset.

    Args:
        token: The password reset token.

    Returns:
        Union[str, redirect]: Rendered template or redirect response.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.reset_password_request'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/reset_password.html')

        try:
            user.set_password(password)
            current_app.db.session.commit()
            log_security_event(
                'password_reset',
                f'Password reset for {user.email}',
                user.id
            )
            flash('Your password has been reset.', 'success')
            return redirect(url_for('auth.login'))

        except SQLAlchemyError as e:
            current_app.db.session.rollback()
            current_app.logger.error(
                f'Database error during password reset: {str(e)}'
            )
            flash('An error occurred during password reset.', 'error')

    return render_template('auth/reset_password.html')