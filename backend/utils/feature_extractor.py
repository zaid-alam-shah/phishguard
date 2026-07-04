import re
import math
from urllib.parse import urlparse

from backend.utils.constants import SUSPICIOUS_TLDS, TARGETED_BRANDS, SENSITIVE_KEYWORDS

_ip_pattern = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')


def shannon_entropy(s):
    if not s:
        return 0
    entropy = 0
    for x in set(s):
        p = s.count(x) / len(s)
        if p > 0:
            entropy += -p * math.log2(p)
    return entropy


def extract_features(url):
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    try:
        parsed = urlparse(url)
    except Exception:
        parsed = urlparse('')

    hostname = parsed.hostname or ''
    path = parsed.path or '/'
    query = parsed.query or ''
    fragment = parsed.fragment or ''

    url_length = len(url)
    domain_length = len(hostname)
    path_length = len(path)
    num_dots = url.count('.')

    hostname_parts = hostname.split('.')
    num_subdomains = max(0, len(hostname_parts) - 2) if len(hostname_parts) >= 2 else 0

    has_https = 1 if url.startswith('https') else 0
    has_ip = 1 if _ip_pattern.match(hostname) else 0

    num_digits_in_domain = sum(1 for c in hostname if c.isdigit())
    digit_ratio_in_domain = num_digits_in_domain / max(len(hostname), 1)
    num_hyphens_in_domain = hostname.count('-')
    domain_has_hyphen = 1 if '-' in hostname else 0
    tld = hostname[hostname.rfind('.'):].lower() if '.' in hostname else ''
    tld_length = len(tld)
    is_suspicious_tld = 1 if tld in SUSPICIOUS_TLDS else 0

    has_brand_in_domain = 0
    hostname_lower = hostname.lower()
    url_lower = url.lower()
    for brand in TARGETED_BRANDS:
        if brand in hostname_lower:
            has_brand_in_domain = 2
            break
        if brand in url_lower:
            has_brand_in_domain = 1

    num_query_params = len([p for p in query.split('&') if p]) if query else 0
    num_fragments = 1 if fragment else 0
    has_at_symbol = 1 if '@' in url else 0

    without_protocol = url[url.find('://') + 3:] if '://' in url else url
    has_double_slash_redirect = 1 if '//' in without_protocol else 0

    num_encoded_chars = url.count('%')
    num_slashes = url.count('/') - 2
    num_question_marks = url.count('?')
    num_hyphens_in_url = url.count('-')
    num_equals = url.count('=')
    num_underscores = url.count('_')

    special_chars_set = set('@_-~!*\'();:&=+$,?#[]')
    num_special_chars = sum(1 for c in url if c in special_chars_set)

    path_lower = path.lower()
    has_sensitive_keywords = 1 if any(kw in path_lower for kw in SENSITIVE_KEYWORDS) else 0

    has_paypal_keywords_in_path = 1 if any(kw in path_lower for kw in ['cgi-bin', 'webscr', 'cmd=']) else 0

    has_multiple_http = 1 if len(re.findall(r'https?://', url)) > 1 else 0

    url_entropy = shannon_entropy(url)

    path_tokens = path.split('/')
    longest_token_length = max((len(t) for t in path_tokens if t), default=0)

    num_redirect_arrows = url.count('>')

    return [
        url_length,
        num_subdomains,
        has_https,
        domain_length,
        path_length,
        num_dots,
        has_ip,
        num_digits_in_domain,
        digit_ratio_in_domain,
        num_hyphens_in_domain,
        domain_has_hyphen,
        tld_length,
        is_suspicious_tld,
        has_brand_in_domain,
        num_query_params,
        num_fragments,
        has_at_symbol,
        has_double_slash_redirect,
        num_encoded_chars,
        num_special_chars,
        has_sensitive_keywords,
        has_multiple_http,
        url_entropy,
        longest_token_length,
        num_slashes,
        num_question_marks,
        num_hyphens_in_url,
        num_equals,
        num_underscores,
        num_redirect_arrows,
        has_paypal_keywords_in_path,
    ]


FEATURE_NAMES = [
    'url_length',
    'num_subdomains',
    'has_https',
    'domain_length',
    'path_length',
    'num_dots',
    'has_ip',
    'num_digits_in_domain',
    'digit_ratio_in_domain',
    'num_hyphens_in_domain',
    'domain_has_hyphen',
    'tld_length',
    'is_suspicious_tld',
    'has_brand_in_domain',
    'num_query_params',
    'num_fragments',
    'has_at_symbol',
    'has_double_slash_redirect',
    'num_encoded_chars',
    'num_special_chars',
    'has_sensitive_keywords',
    'has_multiple_http',
    'url_entropy',
    'longest_token_length',
    'num_slashes',
    'num_question_marks',
    'num_hyphens_in_url',
    'num_equals',
    'num_underscores',
    'num_redirect_arrows',
    'has_paypal_keywords_in_path',
]
