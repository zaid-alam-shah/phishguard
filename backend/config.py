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
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', 'http://127.0.0.1:8080,http://localhost:8080').split(',')


config = Config()
