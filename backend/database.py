import os
import sys
import json
import time

# Ensure project root is in sys.path for gunicorn/Docker compatibility
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.config import config

# ── Database type detection ──────────────────────────────────────
# Use PostgreSQL if DATABASE_URL is set (e.g., on Render), otherwise SQLite.
USE_PG = bool(config.DATABASE_URL)

if USE_PG:
    try:
        import psycopg2
        import psycopg2.extras
        PG_CONNECTED = True
    except ImportError:
        PG_CONNECTED = False
else:
    import sqlite3


def get_connection():
    if USE_PG and PG_CONNECTED:
        conn = psycopg2.connect(config.DATABASE_URL)
        conn.autocommit = False
        return conn
    elif USE_PG and not PG_CONNECTED:
        raise RuntimeError('PostgreSQL selected but psycopg2 is not installed. Run: pip install psycopg2-binary')
    else:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def _execute(cursor, query, params=None):
    """Execute a query with the correct placeholder style for the database.

    All internal queries use %s (PostgreSQL style). SQLite uses ? instead,
    so we convert when running on SQLite.
    """
    if USE_PG:
        cursor.execute(query, params or ())
    else:
        # SQLite uses ? placeholders — convert from %s
        cursor.execute(query.replace('%s', '?'), params or ())


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    if USE_PG:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                original_url TEXT,
                ml_result TEXT NOT NULL,
                ml_score DOUBLE PRECISION,
                risk_score DOUBLE PRECISION,
                rule_flags TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Check if original_url column exists (for upgrades from older schema)
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='scans' AND column_name='original_url'")
        if not cursor.fetchone():
            cursor.execute('ALTER TABLE scans ADD COLUMN original_url TEXT')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id SERIAL PRIMARY KEY,
                ip TEXT NOT NULL,
                timestamp DOUBLE PRECISION NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_ip ON rate_limits(ip)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_ts ON rate_limits(timestamp)')

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
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                original_url TEXT,
                ml_result TEXT NOT NULL,
                ml_score REAL,
                risk_score REAL,
                rule_flags TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute("PRAGMA table_info(scans)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'original_url' not in columns:
            cursor.execute('ALTER TABLE scans ADD COLUMN original_url TEXT')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                ip TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_ip ON rate_limits(ip)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_ts ON rate_limits(timestamp)')

    conn.commit()
    conn.close()


def check_rate_limit(ip, window=60, max_requests=30):
    now = time.time()
    cutoff = now - window
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, 'DELETE FROM rate_limits WHERE timestamp < %s', (cutoff,))
    _execute(cursor, 'SELECT COUNT(*) as cnt FROM rate_limits WHERE ip = %s AND timestamp > %s', (ip, cutoff))
    count = cursor.fetchone()[0]
    if count >= max_requests:
        conn.close()
        return True
    _execute(cursor, 'INSERT INTO rate_limits (ip, timestamp) VALUES (%s, %s)', (ip, now))
    conn.commit()
    conn.close()
    return False


def save_scan(url, original_url=None, ml_result=None, ml_score=None, risk_score=None, rule_flags=None):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor,
        'INSERT INTO scans (url, original_url, ml_result, ml_score, risk_score, rule_flags) VALUES (%s, %s, %s, %s, %s, %s)',
        (url, original_url, ml_result, ml_score, risk_score, json.dumps(rule_flags) if rule_flags else '[]')
    )
    conn.commit()
    conn.close()


def get_recent_scans(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, 'SELECT * FROM scans ORDER BY timestamp DESC LIMIT %s', (limit,))
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result


def clear_history():
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, 'DELETE FROM scans')
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, 'SELECT COUNT(*) as total FROM scans')
    total = cursor.fetchone()[0] or 0

    _execute(cursor, "SELECT COUNT(*) as cnt FROM scans WHERE ml_result='phishing'")
    phishing_count = cursor.fetchone()[0] or 0

    _execute(cursor, "SELECT COUNT(*) as cnt FROM scans WHERE ml_result='safe'")
    safe_count = cursor.fetchone()[0] or 0

    _execute(cursor, 'SELECT AVG(risk_score) as avg_risk FROM scans')
    avg_risk = cursor.fetchone()[0] or 0

    conn.close()

    return {
        'total_scans': total,
        'phishing_count': phishing_count,
        'phishing_percentage': round((phishing_count / max(total, 1)) * 100, 1),
        'safe_count': safe_count,
        'safe_percentage': round((safe_count / max(total, 1)) * 100, 1),
        'average_risk_score': round(float(avg_risk), 1)
    }
