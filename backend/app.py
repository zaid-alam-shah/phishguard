import os
import sys
import logging
import secrets
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Ensure project root is in sys.path for both direct execution and gunicorn/Docker
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.config import config
from backend.database import init_db, save_scan, get_recent_scans, clear_history, get_stats, check_rate_limit
from backend.utils.feature_extractor import extract_features
from backend.utils.validators import validate_url
from backend.utils.rule_analyzer import analyze_url
from backend.utils.unshortener import unshorten_url
from backend.utils.whois_checker import get_domain_risk_issues
from backend.utils.ssl_checker import get_ssl_risk_issues
from backend.utils.auth import generate_api_key, validate_api_key, require_api_key
from backend.models.detector import PhishingDetector
from apscheduler.schedulers.background import BackgroundScheduler
from backend import auto_retrain

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024

CORS(app, resources={r"/*": {"origins": config.CORS_ALLOWED_ORIGINS}})

detector = PhishingDetector(config.MODEL_PATH)

init_db()

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
ALLOWED_EXTENSIONS = {'.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.json', '.txt'}
BLOCKED_PATTERNS = ['.env', '.git', '.pkl', '.db', '.sqlite', '.sqlite3', '.py', '.pyd', '.so', '.dll', '.ini', '.cfg', '.yml', '.yaml', '.log', 'venv', '__pycache__', '.gitignore']

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 30

ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', secrets.token_hex(16))
REQUIRE_API_KEY = config.REQUIRE_API_KEY

# On first run, display the auto-generated admin key so the user can save it
if not os.getenv('ADMIN_API_KEY'):
    logger.info('=' * 60)
    logger.info('  FIRST-RUN SETUP: Admin API Key (save this — it will not be shown again)')
    logger.info(f'  ADMIN_API_KEY={ADMIN_API_KEY}')
    logger.info('  Set ADMIN_API_KEY in .env for persistence across restarts.')
    logger.info('=' * 60)
else:
    logger.info(f'ADMIN_API_KEY loaded from .env (first 8 chars: {ADMIN_API_KEY[:8]}...)')

if REQUIRE_API_KEY:
    logger.info(f'API key authentication is ENABLED (REQUIRE_API_KEY=true)')
else:
    logger.warning('API key authentication is DISABLED (REQUIRE_API_KEY=false) — not recommended for production')

if config.AUTO_RETRAIN_ENABLED:
    logger.info('Auto-retrain is ENABLED — model will retrain every 24 hours from user scan data')
else:
    logger.info('Auto-retrain is DISABLED (default) — enable with AUTO_RETRAIN_ENABLED=true in .env')


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '0'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self'; img-src 'self' data:; connect-src 'self'"
    return response


def is_safe_path(path):
    normalized = os.path.normpath(path).replace('\\', '/')
    if normalized.startswith('..') or '/../' in normalized or normalized == '..':
        return False
    ext = os.path.splitext(path)[1].lower()
    if ext and ext not in ALLOWED_EXTENSIONS:
        return False
    for pattern in BLOCKED_PATTERNS:
        if pattern in normalized.lower():
            return False
    return True


def validate_predict_url(url):
    if not url or not url.strip():
        return False, 'URL is required'
    url = url.strip()
    if len(url) > 2048:
        return False, 'URL exceeds maximum length of 2048 characters'
    return True, url


@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/predict', methods=['POST'])
def predict():
    client_ip = request.remote_addr or 'unknown'
    if check_rate_limit(client_ip, RATE_LIMIT_WINDOW, RATE_LIMIT_MAX):
        return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429

    if REQUIRE_API_KEY:
        auth_header = request.headers.get('Authorization', '')
        api_key = request.args.get('api_key', '')
        valid = False
        if auth_header.startswith('Bearer '):
            valid = validate_api_key(auth_header[7:])
        if not valid and api_key:
            valid = validate_api_key(api_key)
        if not valid:
            return jsonify({'error': 'Valid API key required. Set REQUIRE_API_KEY=false to disable.'}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    raw_url = data.get('url', '').strip() if data else ''
    is_valid, result = validate_predict_url(raw_url)
    if not is_valid:
        return jsonify({'error': result}), 400

    is_valid, normalized_url = validate_url(result)
    if not is_valid:
        return jsonify({'error': normalized_url}), 400

    original_url = normalized_url
    resolved_url, was_shortened = unshorten_url(normalized_url)

    scan_url = resolved_url if was_shortened else normalized_url

    rule_result = analyze_url(scan_url)

    whois_issues, whois_risk, domain_age = get_domain_risk_issues(scan_url)
    for issue in whois_issues:
        rule_result['issues'].append(issue)
    rule_result['risk_score'] = min(rule_result['risk_score'] + whois_risk, 100)

    ssl_issues, ssl_risk = get_ssl_risk_issues(scan_url)
    for issue in ssl_issues:
        rule_result['issues'].append(issue)
    rule_result['risk_score'] = min(rule_result['risk_score'] + ssl_risk, 100)

    risk_level = 'low'
    if rule_result['risk_score'] >= 75:
        risk_level = 'critical'
    elif rule_result['risk_score'] >= 50:
        risk_level = 'high'
    elif rule_result['risk_score'] >= 25:
        risk_level = 'medium'
    rule_result['risk_level'] = risk_level

    features = extract_features(scan_url)
    ml_result, ml_error = detector.predict(features)

    if ml_error:
        logger.error(f'ML prediction error: {ml_error}')
        return jsonify({'error': 'ML model unavailable'}), 503

    # Boost combined risk when multiple high-severity rule flags are present
    high_severity_count = sum(1 for issue in rule_result['issues'] if issue.get('severity') == 'high')
    combined_risk = max(rule_result['risk_score'], ml_result['phishing_probability'])
    if high_severity_count >= 2:
        combined_risk = min(combined_risk + 15, 100)

    save_scan(
        url=scan_url,
        original_url=original_url if was_shortened else None,
        ml_result=ml_result['prediction'],
        ml_score=ml_result['phishing_probability'],
        risk_score=combined_risk,
        rule_flags=[i['text'] for i in rule_result['issues']]
    )

    # 3-tier verdict: safe (<40), risky (40-59), phishing (60+)
    if combined_risk >= 60:
        verdict = 'phishing'
    elif combined_risk >= 40:
        verdict = 'risky'
    else:
        verdict = 'safe'

    return jsonify({
        'url': scan_url,
        'original_url': original_url if was_shortened else None,
        'was_shortened': was_shortened,
        'domain_age_days': domain_age,
        'rule_based': rule_result,
        'ml_result': ml_result,
        'combined_risk_score': combined_risk,
        'final_verdict': verdict
    })


@app.route('/bulk-predict', methods=['POST'])
def bulk_predict():
    client_ip = request.remote_addr or 'unknown'
    if check_rate_limit(client_ip, RATE_LIMIT_WINDOW, RATE_LIMIT_MAX):
        return jsonify({'error': 'Rate limit exceeded. Try again later.'}), 429

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    urls = data.get('urls', [])
    if not urls or not isinstance(urls, list):
        return jsonify({'error': 'Provide a list of URLs'}), 400

    if len(urls) > 20:
        return jsonify({'error': 'Maximum 20 URLs per bulk scan'}), 400

    if REQUIRE_API_KEY:
        auth_header = request.headers.get('Authorization', '')
        api_key = request.args.get('api_key', '')
        valid = False
        if auth_header.startswith('Bearer '):
            valid = validate_api_key(auth_header[7:])
        if not valid and api_key:
            valid = validate_api_key(api_key)
        if not valid:
            return jsonify({'error': 'Valid API key required. Set REQUIRE_API_KEY=false to disable.'}), 401

    def process_single_url(args):
        i, raw_url = args
        raw_url = raw_url.strip()
        if not raw_url:
            return None

        is_valid, result = validate_predict_url(raw_url)
        if not is_valid:
            return {'url': raw_url, 'error': result, 'index': i}

        is_valid, normalized_url = validate_url(result)
        if not is_valid:
            return {'url': raw_url, 'error': normalized_url, 'index': i}

        original_url = normalized_url
        resolved_url, was_shortened = unshorten_url(normalized_url)
        scan_url = resolved_url if was_shortened else normalized_url

        rule_result = analyze_url(scan_url)

        whois_issues, whois_risk, domain_age = get_domain_risk_issues(scan_url)
        for issue in whois_issues:
            rule_result['issues'].append(issue)
        rule_result['risk_score'] = min(rule_result['risk_score'] + whois_risk, 100)

        ssl_issues, ssl_risk = get_ssl_risk_issues(scan_url)
        for issue in ssl_issues:
            rule_result['issues'].append(issue)
        rule_result['risk_score'] = min(rule_result['risk_score'] + ssl_risk, 100)

        risk_level = 'low'
        if rule_result['risk_score'] >= 75:
            risk_level = 'critical'
        elif rule_result['risk_score'] >= 50:
            risk_level = 'high'
        elif rule_result['risk_score'] >= 25:
            risk_level = 'medium'
        rule_result['risk_level'] = risk_level

        features = extract_features(scan_url)
        ml_result, ml_error = detector.predict(features)

        if ml_error:
            return {'url': scan_url, 'error': 'ML model unavailable', 'index': i}

        high_severity_count = sum(1 for issue in rule_result['issues'] if issue.get('severity') == 'high')
        combined_risk = max(rule_result['risk_score'], ml_result['phishing_probability'])
        if high_severity_count >= 2:
            combined_risk = min(combined_risk + 15, 100)

        save_scan(
            url=scan_url,
            original_url=original_url if was_shortened else None,
            ml_result=ml_result['prediction'],
            ml_score=ml_result['phishing_probability'],
            risk_score=combined_risk,
            rule_flags=[j['text'] for j in rule_result['issues']]
        )

        # 3-tier verdict: safe (<40), risky (40-59), phishing (60+)
        if combined_risk >= 60:
            verdict = 'phishing'
        elif combined_risk >= 40:
            verdict = 'risky'
        else:
            verdict = 'safe'

        return {
            'index': i,
            'url': scan_url,
            'original_url': original_url if was_shortened else None,
            'was_shortened': was_shortened,
            'domain_age_days': domain_age,
            'rule_based': rule_result,
            'ml_result': ml_result,
            'combined_risk_score': combined_risk,
            'final_verdict': verdict
        }

    # Process all URLs in parallel — max 6 workers to avoid overloading
    raw_results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_idx = {
            executor.submit(process_single_url, (i, url)): i
            for i, url in enumerate(urls)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result = future.result()
                if result is not None:
                    raw_results[idx] = result
            except Exception as e:
                raw_results[idx] = {'url': urls[idx], 'error': str(e), 'index': idx}

    # Return results in original URL order
    results = [raw_results[i] for i in sorted(raw_results.keys())]

    return jsonify({
        'results': results,
        'total': len(results),
        'scanned': sum(1 for r in results if not r.get('error'))
    })


@app.route('/history', methods=['GET'])
def history():
    limit = request.args.get('limit', 50, type=int)
    limit = min(max(limit, 1), 100)
    scans = get_recent_scans(limit)
    return jsonify({'history': scans, 'count': len(scans)})


@app.route('/history', methods=['DELETE'])
def delete_history():
    clear_history()
    return jsonify({'message': 'History cleared successfully'})


@app.route('/stats', methods=['GET'])
def stats():
    return jsonify(get_stats())


CHATBOT_SYSTEM_PROMPT = (
    "You are PhishGuard's AI assistant, embedded in a phishing detection "
    "website. About this project: it detects phishing URLs in real time using "
    "rule-based analysis, a Random Forest ML model, WHOIS/SSL checks, and "
    "blacklist verification. It also has a browser extension. Help users "
    "understand how to use the site, explain phishing/cybersecurity concepts, "
    "and answer any other question the user has, just like a normal AI "
    "assistant — don't restrict yourself only to phishing topics."
)


@app.route('/chatbot', methods=['POST'])
def chatbot():
    client_ip = request.remote_addr or 'unknown'
    if check_rate_limit(client_ip, RATE_LIMIT_WINDOW, RATE_LIMIT_MAX):
        return jsonify({'reply': 'Rate limit exceeded. Please wait a moment before asking more questions.'}), 429

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'reply': 'Please send a valid message.'}), 400

    message = data.get('message', '').strip() if data else ''
    history = data.get('history', []) if data else []
    message = message[:500]

    if not message:
        return jsonify({'reply': 'Please ask me a question about phishing or online security!'})

    if not config.OPENROUTER_API_KEY:
        logger.error('OPENROUTER_API_KEY is not configured')
        return jsonify({'reply': 'Sorry, I\'m having trouble responding right now. Please try again.'}), 502

    messages = [{'role': 'system', 'content': CHATBOT_SYSTEM_PROMPT}]
    recent_history = history[-10:] if isinstance(history, list) else []
    messages.extend(recent_history)
    messages.append({'role': 'user', 'content': message})

    try:
        resp = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {config.OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'openai/gpt-oss-20b:free',
                'messages': messages,
            },
            timeout=30,
        )
        resp.raise_for_status()
        reply = resp.json()['choices'][0]['message']['content']
        return jsonify({'reply': reply})
    except Exception as e:
        logger.error(f'OpenRouter API call failed: {e}')
        return jsonify({'reply': 'Sorry, I\'m having trouble responding right now. Please try again.'}), 502


def require_admin_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-Admin-Key', '')
        if key == ADMIN_API_KEY:
            return f(*args, **kwargs)
        return jsonify({'error': 'Invalid or missing admin key'}), 401
    return decorated


@app.route('/api/admin/keys', methods=['GET'])
@require_admin_key
def list_api_keys():
    from backend.database import get_connection, _execute
    conn = get_connection()
    cursor = conn.cursor()
    _execute(cursor, "SELECT id, name, created_at, last_used, is_active FROM api_keys ORDER BY created_at DESC")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({'keys': rows})


@app.route('/api/admin/keys', methods=['POST'])
@require_admin_key
def create_api_key():
    data = request.get_json(silent=True) or {}
    name = data.get('name', 'unnamed')
    raw_key = generate_api_key(name)
    return jsonify({'api_key': raw_key, 'name': name, 'message': 'Save this key — it will not be shown again'})


@app.route('/api/admin/keys/<key_hash>', methods=['DELETE'])
@require_admin_key
def revoke_api_key(key_hash):
    from backend.utils.auth import remove_api_key
    remove_api_key(key_hash)
    return jsonify({'message': 'API key revoked'})


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'model_loaded': detector.is_loaded(),
        'version': '1.1.0'
    })


@app.route('/<path:path>')
def serve_frontend(path):
    if not is_safe_path(path):
        return jsonify({'error': 'Forbidden'}), 403

    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    html_path = os.path.join(FRONTEND_DIR, path + '.html')
    if os.path.exists(html_path) and os.path.isfile(html_path):
        return send_from_directory(FRONTEND_DIR, path + '.html')
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({'error': 'Request body too large'}), 413


@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed'}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# Auto-retrain scheduler — gated behind config flag (disabled by default)
if config.AUTO_RETRAIN_ENABLED:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=auto_retrain.main,
        trigger='interval',
        hours=24,
        id='auto_retrain',
        name='Auto-retrain every 24 hours'
    )
    try:
        scheduler.start()
        logger.info('Auto-retrain scheduler started (every 24h)')
    except Exception as e:
        logger.error(f'Scheduler start failed: {e}')
else:
    logger.info('Auto-retrain scheduler not started (disabled in config)')


# HTTPS redirect middleware
@app.before_request
def enforce_https():
    """Redirect HTTP to HTTPS when SSL is configured."""
    if config.SSL_CERT_PATH and config.SSL_KEY_PATH:
        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return '', 307, {'Location': url}


if __name__ == '__main__':
    host = config.FLASK_HOST
    port = config.FLASK_PORT
    ssl_cert = config.SSL_CERT_PATH
    ssl_key = config.SSL_KEY_PATH

    if ssl_cert and ssl_key:
        if os.path.exists(ssl_cert) and os.path.exists(ssl_key):
            logger.info(f'Starting PhishGuard API with HTTPS on {host}:{port}')
            logger.info(f'  SSL Cert: {ssl_cert}')
            logger.info(f'  SSL Key:  {ssl_key}')
            app.run(host=host, port=port, ssl_context=(ssl_cert, ssl_key), debug=config.FLASK_DEBUG)
        else:
            logger.warning(f'SSL cert/key files not found. Cert: {ssl_cert}, Key: {ssl_key}')
            logger.warning(f'Falling back to HTTP on {host}:{port}')
            from waitress import serve
            serve(app, host=host, port=port)
    else:
        logger.info(f'Starting PhishGuard API on http://{host}:{port}')
        logger.info(f'To enable HTTPS, set SSL_CERT_PATH and SSL_KEY_PATH in .env')
        from waitress import serve
        serve(app, host=host, port=port)