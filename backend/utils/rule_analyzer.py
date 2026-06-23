import re
from urllib.parse import urlparse


SUSPICIOUS_TLDS = ['.tk', '.ml', '.ga', '.cf', '.gq', '.xyz', '.top', '.work', '.click', '.link', '.info', '.online', '.site', '.website']
TARGETED_BRANDS = ['paypal', 'apple', 'amazon', 'microsoft', 'google', 'facebook', 'netflix', 'bank', 'chase', 'wellsfargo', 'citibank', 'dropbox', 'linkedin', 'instagram', 'twitter', 'outlook', 'office365', 'icloud']
SHORTENERS = ['bit.ly', 'tinyurl', 'goo.gl', 't.co', 'ow.ly', 'is.gd', 'buff.ly', 'adf.ly', 'bit.do']


def analyze_url(url):
    issues = []
    risk_score = 0

    try:
        url_obj = urlparse(url if url.startswith('http') else 'http://' + url)
    except Exception:
        return {'risk_score': 30, 'issues': [{'severity': 'high', 'text': 'Invalid URL format'}], 'details': {}}

    hostname = url_obj.hostname or ''
    details = {
        'Protocol': url_obj.scheme or 'N/A',
        'Domain': hostname,
        'Path': url_obj.path or '/',
        'Query Parameters': url_obj.query or 'None'
    }

    if url_obj.scheme == 'http':
        issues.append({'severity': 'medium', 'text': 'Uses insecure HTTP protocol instead of HTTPS'})
        risk_score += 15

    ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    if ip_pattern.match(hostname):
        issues.append({'severity': 'high', 'text': 'Uses IP address instead of domain name'})
        risk_score += 25

    for tld in SUSPICIOUS_TLDS:
        if hostname.endswith(tld):
            issues.append({'severity': 'medium', 'text': f'Uses suspicious TLD: {tld}'})
            risk_score += 15
            break

    for brand in TARGETED_BRANDS:
        if brand in hostname and not hostname.endswith(brand + '.com') and not hostname.endswith(brand + '.org'):
            issues.append({'severity': 'high', 'text': f'Possible {brand} impersonation detected'})
            risk_score += 30
            break

    subdomains = hostname.split('.')
    if len(subdomains) > 4:
        issues.append({'severity': 'medium', 'text': 'Excessive subdomains detected'})
        risk_score += 15

    homograph_pattern = re.compile(r'[а-яА-Я\u0400-\u04FF\u0370-\u03FF]')
    if homograph_pattern.search(url):
        issues.append({'severity': 'high', 'text': 'Contains suspicious unicode characters (possible homograph attack)'})
        risk_score += 35

    for shortener in SHORTENERS:
        if shortener in hostname:
            issues.append({'severity': 'low', 'text': 'Uses URL shortening service (destination unknown)'})
            risk_score += 10
            break

    if '@' in url:
        issues.append({'severity': 'high', 'text': 'Contains @ symbol (possible URL obfuscation)'})
        risk_score += 25

    if '%' in url and ('%2F' in url or '%3A' in url or '%40' in url):
        issues.append({'severity': 'medium', 'text': 'Contains encoded characters (possible obfuscation)'})
        risk_score += 15

    path_lower = url_obj.path.lower()
    if any(kw in path_lower for kw in ['login', 'signin', 'verify', 'secure', 'update']):
        issues.append({'severity': 'low', 'text': 'Contains sensitive action keywords in path'})
        risk_score += 10

    if len(url) > 100:
        issues.append({'severity': 'low', 'text': 'Unusually long URL'})
        risk_score += 5

    http_count = len(re.findall(r'https?://', url))
    if http_count > 1:
        issues.append({'severity': 'high', 'text': 'Contains multiple URLs (possible redirect attack)'})
        risk_score += 25

    final_score = min(risk_score, 100)
    risk_level = 'low' if final_score < 25 else ('medium' if final_score < 50 else ('high' if final_score < 75 else 'critical'))

    return {
        'risk_score': final_score,
        'risk_level': risk_level,
        'issues': issues,
        'details': details
    }
