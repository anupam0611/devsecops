"""
Authentication module for the e-commerce application.

This module handles user authentication, including login, registration,
password reset, and session management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from models import db, User
from utils.security import validate_password

# Create auth blueprint
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    
    GET: Display login form
    POST: Process login form submission
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    
    GET: Display registration form
    POST: Process registration form submission
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html')
        
        if not validate_password(password):
            flash('Password does not meet requirements', 'error')
            return render_template('auth/register.html')
        
        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('main.index'))

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """
    Handle password reset requests.
    
    GET: Display password reset request form
    POST: Process password reset request
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # TODO: Implement password reset email functionality
            flash('Password reset instructions have been sent to your email', 'info')
            return redirect(url_for('auth.login'))
        
        flash('Email not found', 'error')
    
    return render_template('auth/reset_password_request.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Handle password reset.
    
    Args:
        token (str): The password reset token
        
    GET: Display password reset form
    POST: Process password reset form submission
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # TODO: Implement token validation
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/reset_password.html')
        
        if not validate_password(password):
            flash('Password does not meet requirements', 'error')
            return render_template('auth/reset_password.html')
        
        # TODO: Update user password
        flash('Your password has been reset', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html')

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Handle user profile management.
    
    GET: Display profile form
    POST: Process profile form submission
    """
    if request.method == 'POST':
        name = request.form.get('name')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if name:
            current_user.name = name
        
        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect', 'error')
                return render_template('auth/profile.html')
            
            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return render_template('auth/profile.html')
            
            if not validate_password(new_password):
                flash('New password does not meet requirements', 'error')
                return render_template('auth/profile.html')
            
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html') 