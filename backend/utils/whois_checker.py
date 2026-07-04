import logging
import threading
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

whois_cache = {}
_cache_lock = threading.Lock()

try:
    import whois as whois_lib
    HAS_WHOIS = True
except ImportError:
    HAS_WHOIS = False
    logger.warning('python-whois not installed. WHOIS checks disabled.')


def extract_domain(url):
    try:
        parsed = urlparse(url if url.startswith('http') else 'http://' + url)
        return parsed.hostname or ''
    except Exception:
        return ''


def get_domain_age_days(domain):
    if not HAS_WHOIS:
        return None

    with _cache_lock:
        if domain in whois_cache:
            return whois_cache[domain]

    try:
        w = whois_lib.whois(domain)
        creation_date = w.creation_date
        if not creation_date:
            whois_cache[domain] = None
            return None

        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if creation_date.tzinfo is None:
            now = datetime.utcnow()
        else:
            now = datetime.now(timezone.utc)

        age_days = (now - creation_date).days
        with _cache_lock:
            whois_cache[domain] = age_days
        logger.info(f'WHOIS: {domain} is {age_days} days old')
        return age_days
    except Exception as e:
        logger.warning(f'WHOIS lookup failed for {domain}: {e}')
        with _cache_lock:
            whois_cache[domain] = None
        return None


def get_domain_expiry_days(domain):
    if not HAS_WHOIS:
        return None

    try:
        w = whois_lib.whois(domain)
        exp_date = w.expiration_date
        if not exp_date:
            return None

        if isinstance(exp_date, list):
            exp_date = exp_date[0]

        if exp_date.tzinfo is None:
            now = datetime.utcnow()
        else:
            now = datetime.now(timezone.utc)

        days_left = (exp_date - now).days
        return days_left
    except Exception as e:
        logger.warning(f'WHOIS expiry lookup failed for {domain}: {e}')
        return None


def get_domain_risk_issues(url):
    domain = extract_domain(url)
    if not domain:
        return [], 0

    issues = []
    risk_score = 0

    age_days = get_domain_age_days(domain)

    if age_days is not None and age_days < 30:
        issues.append({
            'severity': 'high',
            'text': f'Domain is very new ({age_days} days old) — common phishing tactic'
        })
        risk_score += 30
    elif age_days is not None and age_days < 90:
        issues.append({
            'severity': 'medium',
            'text': f'Domain is relatively new ({age_days} days old)'
        })
        risk_score += 10
    elif age_days is not None:
        issues.append({
            'severity': 'low',
            'text': f'Domain is {age_days} days old (established)'
        })
        risk_score -= 5

    days_to_expiry = get_domain_expiry_days(domain)

    if days_to_expiry is not None and days_to_expiry < 30:
        issues.append({
            'severity': 'medium',
            'text': f'Domain expires in {days_to_expiry} days — possibly abandoned'
        })
        risk_score += 15
    elif days_to_expiry is not None and days_to_expiry < 7:
        issues.append({
            'severity': 'high',
            'text': f'Domain expiring in {days_to_expiry} days — high risk'
        })
        risk_score += 25

    return issues, min(max(risk_score, 0), 100), age_days
