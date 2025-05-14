"""
Configuration module for the Flask application.

This module defines configuration classes for different environments:
- Development: Debug mode enabled, local database
- Testing: Test database, debug mode enabled
- Production: Production settings, secure defaults
"""

import os
from datetime import timedelta


class BaseConfig:
    """Base configuration class with common settings."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Add SESSION_TYPE configuration
    SESSION_TYPE = "filesystem"  # Store session data in the filesystem


class DevelopmentConfig(BaseConfig):
    """Development configuration with debug settings."""

    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False


class TestingConfig(BaseConfig):
    """Testing configuration with test database."""

    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Production configuration with secure settings."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}

Config = DevelopmentConfig  # Alias the default configuration
