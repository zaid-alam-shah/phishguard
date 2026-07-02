import hashlib
import secrets
import logging
from datetime import datetime
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

API_KEY_HASHES = set()

try:
    from backend.database import get_connection, _execute, USE_PG
    from backend.config import config
    import sys
    import os
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _project_root not in sys.path:
        sys.path.insert(0, _project_root)

    def init_api_keys_db():
        """Initialize the API keys table."""
        conn = get_connection()
        cursor = conn.cursor()
        if USE_PG:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id SERIAL PRIMARY KEY,
                    key_hash TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME,
                    is_active INTEGER DEFAULT 1
                )
            ''')
        conn.commit()
        conn.close()

    def load_api_keys():
        global API_KEY_HASHES
        try:
            conn = get_connection()
            cursor = conn.cursor()
            _execute(cursor, "SELECT key_hash FROM api_keys WHERE is_active=1")
            rows = cursor.fetchall()
            API_KEY_HASHES = set(row[0] for row in rows)
            conn.close()
            logger.info(f'Loaded {len(API_KEY_HASHES)} active API keys')
        except Exception as e:
            logger.error(f'Failed to load API keys: {e}')

    def save_api_key(key_hash, name):
        conn = get_connection()
        cursor = conn.cursor()
        if USE_PG:
            _execute(cursor, "INSERT INTO api_keys (key_hash, name) VALUES (%s, %s) ON CONFLICT (key_hash) DO NOTHING", (key_hash, name))
        else:
            _execute(cursor, "INSERT OR IGNORE INTO api_keys (key_hash, name) VALUES (%s, %s)", (key_hash, name))
        conn.commit()
        conn.close()
        API_KEY_HASHES.add(key_hash)

    def remove_api_key(key_hash):
        conn = get_connection()
        cursor = conn.cursor()
        _execute(cursor, "UPDATE api_keys SET is_active=0 WHERE key_hash=%s", (key_hash,))
        conn.commit()
        conn.close()
        API_KEY_HASHES.discard(key_hash)

except Exception as e:
    logger.error(f'API key DB init failed: {e}')

    def init_api_keys_db():
        pass

    def load_api_keys():
        pass

    def save_api_key(key_hash, name):
        API_KEY_HASHES.add(key_hash)

    def remove_api_key(key_hash):
        API_KEY_HASHES.discard(key_hash)


def generate_api_key(name):
    raw_key = 'pg_' + secrets.token_hex(24)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    save_api_key(key_hash, name)
    logger.info(f'Generated API key for: {name}')
    return raw_key


def validate_api_key(raw_key):
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return key_hash in API_KEY_HASHES


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            raw_key = auth_header[7:]
            if validate_api_key(raw_key):
                return f(*args, **kwargs)

        api_key = request.args.get('api_key', '')
        if api_key and validate_api_key(api_key):
            return f(*args, **kwargs)

        return jsonify({'error': 'Invalid or missing API key'}), 401
    return decorated


init_api_keys_db()
load_api_keys()
