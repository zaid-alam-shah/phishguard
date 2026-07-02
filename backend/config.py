import os
import secrets
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))


class Config:
    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '8080'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        os.getenv('DATABASE_PATH', 'backend/phishguard.db')
    )
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_hex(32)
    MODEL_PATH = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'backend', 'phishing_model.pkl'
    )
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    # CORS: default allows local dev. Override with CORS_ALLOWED_ORIGINS env var for custom domains.
    # On Render, the frontend and API share the same domain, so CORS is less critical.
    _default_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
    if _default_origins:
        CORS_ALLOWED_ORIGINS = _default_origins.split(',')
    elif os.getenv('DATABASE_URL'):
        # On Render/cloud — allow all origins since frontend & API are same-origin
        CORS_ALLOWED_ORIGINS = ['*']
    else:
        # Local development — restrict to localhost
        CORS_ALLOWED_ORIGINS = ['http://127.0.0.1:8080', 'http://localhost:8080']

    # Authentication: enforce API key requirement by default for security
    REQUIRE_API_KEY = os.getenv('REQUIRE_API_KEY', 'true').lower() in ('true', '1', 'yes')

    # Auto-retrain: disabled by default to prevent model degradation from user data
    AUTO_RETRAIN_ENABLED = os.getenv('AUTO_RETRAIN_ENABLED', 'false').lower() in ('true', '1', 'yes')

    # Database: set DATABASE_URL to use PostgreSQL (e.g., on Render), leave empty for SQLite
    DATABASE_URL = os.getenv('DATABASE_URL', '')

    # SSL/TLS certificate paths (optional — set these to serve HTTPS directly)
    SSL_CERT_PATH = os.getenv('SSL_CERT_PATH', '')
    SSL_KEY_PATH = os.getenv('SSL_KEY_PATH', '')


config = Config()
