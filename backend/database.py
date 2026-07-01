import os
import sys
import sqlite3
import json
import time

# Ensure project root is in sys.path for gunicorn/Docker compatibility
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.config import config


def get_connection():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
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
    cursor.execute('DELETE FROM rate_limits WHERE timestamp < ?', (cutoff,))
    cursor.execute('SELECT COUNT(*) FROM rate_limits WHERE ip = ? AND timestamp > ?', (ip, cutoff))
    count = cursor.fetchone()[0]
    if count >= max_requests:
        conn.close()
        return True
    cursor.execute('INSERT INTO rate_limits (ip, timestamp) VALUES (?, ?)', (ip, now))
    conn.commit()
    conn.close()
    return False


def save_scan(url, original_url=None, ml_result=None, ml_score=None, risk_score=None, rule_flags=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO scans (url, original_url, ml_result, ml_score, risk_score, rule_flags) VALUES (?, ?, ?, ?, ?, ?)',
        (url, original_url, ml_result, ml_score, risk_score, json.dumps(rule_flags) if rule_flags else '[]')
    )
    conn.commit()
    conn.close()


def get_recent_scans(limit=50):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scans ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def clear_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scans')
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM scans')
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE ml_result='phishing'")
    phishing_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM scans WHERE ml_result='safe'")
    safe_count = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(risk_score) as avg_risk FROM scans')
    avg_risk = cursor.fetchone()[0] or 0

    conn.close()

    return {
        'total_scans': total,
        'phishing_count': phishing_count,
        'phishing_percentage': round((phishing_count / max(total, 1)) * 100, 1),
        'safe_count': safe_count,
        'safe_percentage': round((safe_count / max(total, 1)) * 100, 1),
        'average_risk_score': round(avg_risk, 1)
    }
